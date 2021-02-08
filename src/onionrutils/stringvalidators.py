"""
Onionr - Private P2P Communication

validate various string data types
"""
import base64

import unpaddedbase32
import nacl.signing
import nacl.encoding
from stem.util import tor_tools

from onionrutils import bytesconverter
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


def validate_hash(data, length=64):
    """Validate if a string is a valid hash hex digest (does not compare, checks length and charset)

    Length is only invalid if its *more* than the specified
    """
    retVal = True
    if data == False or data == True:
        return False
    data = data.strip()
    if len(data) > length:
        retVal = False
    else:
        try:
            int(data, 16)
        except ValueError:
            retVal = False

    return retVal


def validate_pub_key(key):
    """Validate if a string is a valid base32 encoded Ed25519 key"""
    if type(key) is type(None):
        return False
    # Accept keys that have no = padding
    key = unpaddedbase32.repad(bytesconverter.str_to_bytes(key))

    retVal = False
    try:
        nacl.signing.SigningKey(seed=key, encoder=nacl.encoding.Base32Encoder)
    except nacl.exceptions.ValueError:
        pass
    except base64.binascii.Error as err:
        pass
    else:
        retVal = True
    return retVal


def validate_transport(id: str):
    id = id.replace('.onion', '')
    return tor_tools.is_valid_hidden_service_address(
        id, version=3) and id.endswith('d')


def is_integer_string(data):
    """Check if a string is a valid base10 integer (also returns true if already an int)"""
    try:
        int(data)
    except (ValueError, TypeError) as e:
        return False
    else:
        return True
