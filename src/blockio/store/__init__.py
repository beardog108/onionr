"""Onionr - Private P2P Communication.

Store blocks and cache meta info such as block type
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kasten import Kasten
    from safedb import SafeDB
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


def store_block(block: 'Kasten', safe_db: 'SafeDB', own_block=False):
    # This does not handle validation of blocks
    # safe_db is initialized by the daemon when starting normally
    # so any other commands need to initialize it seperately

    block_type = block.get_data_type()
    try:
        block_list_for_type = safe_db.get(f'bl-{block_type}')
        if block.id in block_list_for_type:
            raise ValueError("Cannot store duplicate block")
    except KeyError:
        block_list_for_type = b''

    safe_db.put(block.id, block.get_packed())
    # Append the block to the list of blocks for this given type
    block_list_for_type += block.id
    safe_db.put(f'bl-{block_type}', block_list_for_type)

