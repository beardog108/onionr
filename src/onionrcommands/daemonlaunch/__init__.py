"""Onionr - Private P2P Communication.

launch the api servers and communicator
"""
import os
import sys
import platform
import signal
from threading import Thread
from threading import enumerate as thread_enumerate
import traceback

from stem.connection import IncorrectPassword

import toomanyobjs
import filenuke
from deadsimplekv import DeadSimpleKV
import psutil

import config
import onionrstatistics
from onionrstatistics import serializeddata
import apiservers
import logger
import communicator
from onionrplugins import onionrevents as events
from onionrutils import localcommand
from utils import identifyhome
import filepaths
from etc import onionrvalues, cleanup
import runtests
from httpapi import daemoneventsapi
from .. import version
from utils.bettersleep import better_sleep
from .killdaemon import kill_daemon  # noqa
from .showlogo import show_logo

from setupkvvars import setup_kv
from blockcreatorqueue import PassToSafeDB
from .loadsafedb import load_safe_db
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


def _proper_shutdown():
    localcommand.local_command('shutdown')
    sys.exit(1)


def _show_info_messages():
    version.version(verbosity=5, function=logger.info)
    logger.debug('Python version %s' % platform.python_version())

    if onionrvalues.DEVELOPMENT_MODE:
        logger.warn('Development mode enabled', timestamp=False, terminal=True)


def daemon():
    """Start Onionr's primary threads for communicator, API server, node, and LAN."""

    def _handle_sig_term(signum, frame):
        pid = str(os.getpid())
        main_pid = localcommand.local_command('/getpid')
        #logger.info(main_pid, terminal=True)
        if main_pid and main_pid == pid:
            logger.info(
            f"Received sigterm, shutting down gracefully. PID: {pid}", terminal=True)
            localcommand.local_command('/shutdownclean')
        else:
            logger.info(
                f"Recieved sigterm in child process or fork, exiting. PID: {pid}")
            sys.exit(0)

    def _handle_sigusr1(sig, frame):
        traceback_file = identifyhome.identify_home() + "/traceback"
        id2name = dict([(th.ident, th.name) for th in thread_enumerate()])
        code = []
        for thread_id, stack in sys._current_frames().items():
            code.append(
                "\n# Thread: %s(%d)" %
                (id2name.get(thread_id, ""), thread_id))
            for filename, lineno, name, line in traceback.extract_stack(stack):
                code.append(
                    'File: "%s", line %d, in %s' % (filename, lineno, name))
                if line:
                    code.append("  %s" % (line.strip()))
        with open(traceback_file, 'w') as tb_f:
            tb_f.write("\n".join(code))
        logger.info(
            f"Wrote traceback of all main process threads to {traceback_file}",
            terminal=True)

    def _sigusr1_thrower():
        wait_for_write_pipe = identifyhome.identify_home() + \
            "/activate-traceback"
        try:
            os.mkfifo(wait_for_write_pipe)
        except FileExistsError:
            pass
        with open(wait_for_write_pipe, "r") as f:
            f.read()
        os.kill(os.getpid(), signal.SIGUSR1)

    signal.signal(signal.SIGTERM, _handle_sig_term)
    signal.signal(signal.SIGUSR1, _handle_sigusr1)

    Thread(
        target=_sigusr1_thrower,
        daemon=True, name="siguser1 wait and throw").start()

    # Determine if Onionr is in offline mode.
    # When offline, Onionr can only use LAN and disk transport
    offline_mode = config.get('general.offline_mode', False)

    # Create shared objects

    shared_state = toomanyobjs.TooMany()

    # Add DeadSimpleKV for quasi-global variables (ephemeral key-value)
    shared_state.get(DeadSimpleKV)

    # Initialize the quasi-global variables
    setup_kv(shared_state.get(DeadSimpleKV))

    shared_state.get(daemoneventsapi.DaemonEventsBP)

    Thread(target=shared_state.get(apiservers.ClientAPI).start,
           daemon=True, name='client HTTP API').start()

    # Init run time tester
    # (ensures Onionr is running right, for testing purposes)
    # Run time tests are not normally run
    shared_state.get(runtests.OnionrRunTestManager)

    # Create singleton
    shared_state.get(serializeddata.SerializedData)

    shared_state.add(load_safe_db(config))
    shared_state.add(PassToSafeDB(shared_state.get_by_string('SafeDB')))

    shared_state.share_object()  # share the parent object to the threads

    show_logo()

    security_level = config.get('general.security_level', 1)

    _show_info_messages()

    logger.info(
        "Onionr daemon is running under " + str(os.getpid()), terminal=True)
    events.event('init', threaded=False, data=shared_state)
    events.event('daemon_start')

    communicator.startCommunicator(shared_state)

    better_sleep(5)

    cleanup.delete_run_files()
    if security_level >= 2:
        filenuke.nuke.clean_tree(identifyhome.identify_home())


def start(override: bool = False):
    """If no lock file, make one and start onionr.

    Error exit if there is and its not overridden
    """
    if os.path.exists(filepaths.lock_file) and not override:
        if os.path.exists(filepaths.restarting_indicator):
            try:
                os.remove(filepaths.restarting_indicator)
            except FileNotFoundError:
                pass
            else:
                return
        with open(filepaths.lock_file, 'r') as lock_file:
            try:
                proc = psutil.Process(int(lock_file.read())).name()
            except psutil.NoSuchProcess:
                proc = ""
            if not proc.startswith("python"):
                logger.info(
                    f"Detected stale run file, deleting {filepaths.lock_file}", terminal=True)
                try:
                    os.remove(filepaths.lock_file)
                except FileNotFoundError:
                    pass
                start(override=True)
                return
        logger.fatal('Cannot start. Daemon is already running,'
                     + ' or it did not exit cleanly.\n'
                     + ' (if you are sure that there is not a daemon running,'
                     + f' delete {filepaths.lock_file} & try again).',
                     terminal=True)
    else:
        if not onionrvalues.DEVELOPMENT_MODE:
            lock_file = open(filepaths.lock_file, 'w')
            lock_file.write(str(os.getpid()))
            lock_file.close()

        # Start Onionr daemon
        daemon()

        try:
            os.remove(filepaths.lock_file)
        except FileNotFoundError:
            pass


start.onionr_help = "Start Onionr node "  # type: ignore
start.onionr_help += "(public and clients API servers)"  # type: ignore
