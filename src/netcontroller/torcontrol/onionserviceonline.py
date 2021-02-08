"""Onionr - Private P2P Communication.

Detect if onion service has been online recently
"""
from typing import TYPE_CHECKING, Union
from base64 import b32encode

if TYPE_CHECKING:
    from stem.control import Controller

from stem import DescriptorUnavailable, ProtocolError

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


def service_online_recently(
        tor_controller: 'Controller',
        onion_address: Union[str, bytes]) -> bool:
    """Detect if a .onion service is/recently online by getting descriptor

    Does not detect if it is an Onionr node or actually has any TCP service
    """
    if isinstance(onion_address, bytes):
        # If address is "compressed"
        # (raw bytes + no onion extension), restore it to b32 form
        onion_address = b32encode(
            onion_address).lower().decode('utf-8') + '.onion'
    try:
        tor_controller.get_hidden_service_descriptor(onion_address)
    except DescriptorUnavailable:
        return False
    except ProtocolError:
        raise ProtocolError(
            onion_address + " is likely malformed. Or stem/tor malfunctioned")
    return True
