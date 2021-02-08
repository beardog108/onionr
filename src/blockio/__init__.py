"""Onionr - Private P2P Communication.

Wrap safedb for storing and fetching blocks
"""
from .store import store_block
from .load import load_block, list_blocks_by_type, list_all_blocks
from .clean import clean_expired_blocks, clean_block_list_entries
from . import subprocgenerate
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
