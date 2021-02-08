"""Onionr - Private P2P Communication.

Ensure sockets don't get made to non localhost
"""
import ipaddress

import logger
from onionrexceptions import NetworkLeak
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


def detect_socket_leaks(socket_event):
    """Is called by the big brother broker whenever.

    a socket connection happens.
    raises exception & logs if not to loopback
    """
    ip_address = socket_event[1][0]

    # validate is valid ip address (no hostname, etc)
    # raises NetworkLeak if not
    try:
        ip_address = ipaddress.ip_address(ip_address)
    except ValueError:
        if ip_address == "/":
            # unix socket
            return
        logger.warn(f'Conn made to {ip_address} outside of Tor/similar')
        raise \
            NetworkLeak('Conn to host/non local IP, this is a privacy issue!')

    # Validate that the IP is localhost ipv4
    if not ip_address.is_loopback and not ip_address.is_multicast \
            and not ip_address.is_private:
        logger.warn(f'Conn made to {ip_address} outside of Tor/similar')
        raise NetworkLeak('Conn to non local IP, this is a privacy concern!')
