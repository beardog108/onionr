"""Onionr - Private P2P Communication.

z-fill (zero fill) a string to a specific length
intended for reconstructing block hashes
"""
from typing import Union
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


def reconstruct_hash(hex_hash: Union[str, bytes],
                     length: int = 64) -> Union[str, bytes]:
    """Pad hash hex string with zeros, return result"""
    return hex_hash.zfill(length)


def deconstruct_hash(hex_hash: Union[str, bytes]) -> Union[str, bytes]:
    """Remove leading zeros from hex hash, return result"""
    new_hash = ''
    ret_bytes = False
    try:
        hex_hash = hex_hash.decode()
        ret_bytes = True
    except AttributeError:
        pass

    c = 0
    for x in hex_hash:
        if x == '0':
            c += 1
        else:
            break
    new_hash = hex_hash[c:]

    if ret_bytes:

        new_hash = new_hash.encode()
    return new_hash
