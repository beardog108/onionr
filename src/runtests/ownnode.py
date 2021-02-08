"""Onionr - Private P2P Communication.

Test own Onionr node as it is running
"""
import config
from onionrutils import basicrequests
from utils import identifyhome
from utils import gettransports
import logger
from onionrutils import localcommand
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


def test_own_node(test_manager):
    if config.get('general.security_level', 0) > 0 or not config.get('transports.tor', True):
        return
    if config.get('runtests.skip_slow', False):
        return
    socks_port = localcommand.local_command('/gettorsocks')
    if config.get('general.security_level', 0) > 0:
        return
    own_tor_address = gettransports.get()[0]
    if 'this is an onionr node' \
            not in basicrequests.do_get_request('http://' + own_tor_address,
                                                port=socks_port,
                                                ignoreAPI=True).lower():
        logger.warn(f'Own node not reachable in test {own_tor_address}')
        raise ValueError


def test_tor_adder(test_manager):
    if config.get('general.security_level', 0) > 0 or not config.get('transports.tor', True):
        return
    with open(identifyhome.identify_home() + 'hs/hostname', 'r') as hs:
        hs = hs.read().strip()
    if not hs:
        logger.error('No Tor node address created yet')
        raise ValueError('No Tor node address created yet')

    if hs not in gettransports.get():
        logger.error('gettransports Tor not same as file: %s %s' %
                     (hs, gettransports.get()))
        raise ValueError('gettransports Tor not same as file')
