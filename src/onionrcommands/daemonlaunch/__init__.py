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
import stem
import toomanyobjs
import filenuke
from deadsimplekv import DeadSimpleKV
import psutil

import config
from netcontroller.torcontrol import onionservice, torcontroller
import onionrstatistics
from onionrstatistics import serializeddata
import apiservers
import logger
import communicator
from onionrplugins import onionrevents as events
from netcontroller import NetController
from netcontroller import clean_ephemeral_services
from onionrutils import localcommand
from utils import identifyhome
import filepaths
from etc import onionrvalues, cleanup
from onionrcrypto import getourkeypair
from utils import hastor
import runtests
from httpapi import daemoneventsapi
from .. import version
from .getapihost import get_api_host_until_available
from utils.bettersleep import better_sleep
from netcontroller.torcontrol.onionservicecreator import create_onion_service
from .killdaemon import kill_daemon  # noqa
from .showlogo import show_logo
from lan import LANManager
from lan.server import LANServer
from sneakernet import sneakernet_import_thread
from onionrstatistics.devreporting import statistics_reporter
from setupkvvars import setup_kv
from communicatorutils.housekeeping import clean_blocks_not_meeting_pow
from blockcreatorqueue import PassToSafeDB
from .spawndaemonthreads import spawn_client_threads
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

    logger.info('Using public key: %s' %
                (logger.colors.underline +
                 getourkeypair.get_keypair()[0][:52]))


def _setup_online_mode(
        use_existing_tor: bool,
        net: NetController,
        security_level: int):
    if config.get('transports.tor', True):
        # If we are using tor, check if we are using an existing tor instance
        # if we are, we need to create an onion service on it and set attrs on our NetController
        # if not, we need to tell netcontroller to start one
        if use_existing_tor:
            try:
                os.mkdir(filepaths.tor_hs_loc)
            except FileExistsError:
                pass
            net.socksPort = config.get('tor.existing_socks_port')
            try:
                net.myID = create_onion_service(
                    port=net.apiServerIP + ':' + str(net.hsPort))[0]
            except stem.SocketError:
                logger.error(
                    "Could not connect to existing Tor service", terminal=True)
                localcommand.local_command('shutdown')
                cleanup.delete_run_files()
                sys.exit(1)
            except IncorrectPassword:
                # Exit if we cannot connect to the existing Tor instance
                logger.error('Invalid Tor control password', terminal=True)
                localcommand.local_command('shutdown')
                cleanup.delete_run_files()
                sys.exit(1)

            if not net.myID.endswith('.onion'):
                net.myID += '.onion'
            with open(filepaths.tor_hs_address_file, 'w') as tor_file:
                tor_file.write(net.myID)
        else:
            logger.info('Tor is starting...', terminal=True)
            if not net.startTor():
                # Exit if we cannot start Tor.
                localcommand.local_command('shutdown')
                cleanup.delete_run_files()
                sys.exit(1)
        if len(net.myID) > 0 and security_level == 0:
            logger.debug(
                'Started .onion service: %s' %
                (logger.colors.underline + net.myID))
        else:
            logger.debug('.onion service disabled')


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

    if not hastor.has_tor():
        offline_mode = True
        logger.error("Tor is not present in system path or Onionr directory",
                     terminal=True)

    # Create shared objects

    shared_state = toomanyobjs.TooMany()

    # Add DeadSimpleKV for quasi-global variables (ephemeral key-value)
    shared_state.get(DeadSimpleKV)

    # Initialize the quasi-global variables
    setup_kv(shared_state.get(DeadSimpleKV))

    shared_state.get(daemoneventsapi.DaemonEventsBP)

    Thread(target=shared_state.get(apiservers.ClientAPI).start,
           daemon=True, name='client HTTP API').start()
    if not offline_mode:
        Thread(target=shared_state.get(apiservers.PublicAPI).start,
               daemon=True, name='public HTTP API').start()

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

    # since we randomize loopback API server hostname to protect against attacks,
    # we have to wait for it to become set
    apiHost = ''
    if not offline_mode:
        apiHost = get_api_host_until_available()

    net = NetController(config.get('client.public.port', 59497),
                        apiServerIP=apiHost)
    shared_state.add(net)

    shared_state.get(onionrstatistics.tor.TorStats)

    security_level = config.get('general.security_level', 1)
    use_existing_tor = config.get('tor.use_existing_tor', False)

    if not offline_mode:
        # we need to setup tor for use
        _setup_online_mode(use_existing_tor, net, security_level)

    _show_info_messages()

    with torcontroller.get_controller() as c:
        try:
            onionservice.load_services(c)
        except onionservice.NoServices:
            pass

    logger.info(
        "Onionr daemon is running under " + str(os.getpid()), terminal=True)
    events.event('init', threaded=False, data=shared_state)
    events.event('daemon_start')
    if config.get('transports.lan', True):
        if not onionrvalues.IS_QUBES:
            Thread(target=LANServer(shared_state).start_server,
                   daemon=True).start()
            LANManager(shared_state).start()
        else:
            logger.warn('LAN not supported on Qubes', terminal=True)
    if config.get('transports.sneakernet', True):
        Thread(target=sneakernet_import_thread, daemon=True).start()

    Thread(target=statistics_reporter,
           args=[shared_state], daemon=True).start()

    shared_state.get(DeadSimpleKV).put(
        'proxyPort', net.socksPort)
    spawn_client_threads(shared_state)

    clean_blocks_not_meeting_pow(shared_state)

    communicator.startCommunicator(shared_state)

    clean_ephemeral_services()

    if not offline_mode and not use_existing_tor:
        net.killTor()
    else:
        try:
            os.remove(filepaths.tor_hs_address_file)
        except FileNotFoundError:
            pass

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
