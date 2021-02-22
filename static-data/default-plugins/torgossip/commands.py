
"""
Onionr - Private P2P Communication

Gossip plugin commands
"""
from enum import IntEnum
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


class GossipCommands(IntEnum):
    PING = 1,
    CHECK_HAS_BLOCK = 2,  # Returns 1 if has block, 2 if not
    LIST_BLOCKS_BY_TYPE = 3,
    LIST_BLOCKS_BY_TYPE_OFFSET = 4,
    GET_BLOCK = 5,
    PUT_BLOCK = 6,
    PEER_EXCHANGE = 7,
    ANNOUNCE_PEER = 8,
    EXIT = 9
