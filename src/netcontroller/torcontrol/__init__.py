"""Onionr - Private P2P Communication.

Netcontroller library, used to control/work with Tor and send requests through
"""
import os
import subprocess
import signal
import time
import multiprocessing

from onionrtypes import BooleanSuccessState
import logger
from .. import getopenport
from .. import watchdog
from . import customtorrc
from . import gentorrc
from . import addbridges
from . import torbinary
from utils import identifyhome
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

TOR_KILL_WAIT = 3
addbridges = addbridges.add_bridges


class NetController:
    """Handle Tor daemon and onion service setup on Tor."""

    def __init__(self, hsPort, apiServerIP='127.0.0.1'):
        # set data dir
        self.dataDir = identifyhome.identify_home()
        self.socksPort = getopenport.get_open_port()
        self.torConfigLocation = self.dataDir + 'torrc'
        self.readyState = False
        self.hsPort = hsPort
        self._torInstnace = ''
        self.myID = ''
        self.apiServerIP = apiServerIP
        self.torBinary = torbinary.tor_binary()

    def startTor(self, gen_torrc=True) -> BooleanSuccessState:
        """
            Start Tor with onion service on port 80 & socks proxy on random port
        """
        if gen_torrc:
            gentorrc.generate_torrc(self, self.apiServerIP)

        if os.path.exists('./tor'):
            self.torBinary = './tor'
        elif os.path.exists('/usr/bin/tor'):
            self.torBinary = '/usr/bin/tor'
        else:
            self.torBinary = 'tor'

        try:
            tor = subprocess.Popen([self.torBinary, '-f', self.torConfigLocation], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            logger.fatal("Tor was not found in your path or the Onionr directory. Please install Tor and try again.", terminal=True)
            return False
        else:
            # Test Tor Version
            torVersion = subprocess.Popen([self.torBinary, '--version'],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
            for line in iter(torVersion.stdout.readline, b''):
                if 'Tor 0.2.' in line.decode():
                    logger.fatal('Tor 0.3+ required', terminal=True)
                    return False
            torVersion.kill()

        # wait for tor to get to 100% bootstrap
        try:
            for line in iter(tor.stdout.readline, b''):
                for word in ('bootstrapped', '%'):
                    if word not in line.decode().lower():
                        break
                else:
                    if '100' not in line.decode():
                        logger.info(line.decode().strip(), terminal=True)
                if 'bootstrapped 100' in line.decode().lower():
                    logger.info(line.decode(), terminal=True)
                    break
                elif 'asking for networkstatus consensus' in line.decode().lower():
                    logger.warn(
                        "Tor has to load consensus, this should be faster next time," +
                        " unless Onionr data is deleted.", terminal=True)
                elif 'opening socks listener' in line.decode().lower():
                    logger.debug(line.decode().replace('\n', ''))
                else:
                    if 'err' in line.decode():
                        logger.error(
                            line.decode().replace('\n', ''), terminal=True)
                    elif 'warn' in line.decode():
                        logger.warn(
                            line.decode().replace('\n', ''), terminal=True)
                    else:
                        logger.debug(line.decode().replace('\n', ''))
            else:
                logger.fatal('Failed to start Tor. Maybe a stray instance of Tor used by Onionr is still running? This can also be a result of file permissions being too open', terminal=True)
                return False
        except KeyboardInterrupt:
            logger.fatal('Got keyboard interrupt. Onionr will exit soon.', timestamp = False, terminal=True)
            return False

        try:
            myID = open(self.dataDir + 'hs/hostname', 'r')
            self.myID = myID.read().replace('\n', '')
            myID.close()
        except FileNotFoundError:
            self.myID = ""

        with open(self.dataDir + 'torPid.txt', 'w') as tor_pid_file:
            tor_pid_file.write(str(tor.pid))

        #multiprocessing.Process(target=watchdog.watchdog,
        #                        args=[os.getpid(), tor.pid], daemon=True).start()

        logger.info('Finished starting Tor.', terminal=True)

        self.readyState = True
        return True

    def killTor(self):
        """Properly kill tor based on pid saved to file."""
        try:
            with open(self.dataDir + 'torPid.txt', 'r') as torPid:
                pidN = torPid.read()
        except FileNotFoundError:
            return

        try:
            try:
                # Extra int()
                os.kill(int(pidN), signal.SIGTERM)
            except PermissionError:
                # seems to happen on win 10
                pass
            except ValueError:
                # Happens if int() check is not valid
                logger.error("torPid.txt contained invalid integer. " +
                             "This indicates corruption " +
                             "and should not be bypassed for security reasons")
                return
            os.remove(self.dataDir + 'torPid.txt')
        except ProcessLookupError:
            pass
        except FileNotFoundError:
            pass

        try:
            time.sleep(TOR_KILL_WAIT)
        except KeyboardInterrupt:
            pass

        try:
            os.kill(int(pidN), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            os.remove(self.dataDir + 'tordata/lock')
        except FileNotFoundError:
            pass
