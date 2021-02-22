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

def is_integer_string(data):
    """Check if a string is a valid base10 integer (also returns true if already an int)"""
    try:
        int(data)
    except (ValueError, TypeError) as e:
        return False
    else:
        return True
