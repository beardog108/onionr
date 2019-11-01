"""
    Onionr - Private P2P Communication

    Command to restart Onionr
"""
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
import time
import os
import subprocess
import platform

from etc import onionrvalues
from onionrutils import localcommand
import logger
import filepaths

from . import daemonlaunch

SCRIPT_NAME = os.path.dirname(os.path.realpath(__file__)) + f'/../../{onionrvalues.SCRIPT_NAME}'

def restart():
    logger.info('Restarting Onionr', terminal=True)

    # On platforms where we can, fork out to prevent locking
    try:
        pid = os.fork()
        if pid != 0: return
    except (AttributeError, OSError) as e: pass

    daemonlaunch.kill_daemon()
    while localcommand.local_command('ping', maxWait=8) == 'pong!':
        time.sleep(0.3)
    time.sleep(15)
    while os.path.exists(filepaths.private_API_host_file) or os.path.exists(filepaths.daemon_mark_file):
        time.sleep(1)
    subprocess.Popen([SCRIPT_NAME, 'start'])

restart.onionr_help = 'Gracefully restart Onionr'
