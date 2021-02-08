"""Onionr - Private P2P Communication.

Handle commands for the torgossip server
"""
import traceback
import base64

import blockio
import logger

import onionrblocks
from kasten import Kasten
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


def announce_peer(peers: 'TorGossipPeers', peer_address):
    """command 8: accept a new peer"""
    try:
        peers.add_peer(peer_address)
    except Exception as _:
        logger.warn("Error accepting announced peer " + base64.b85encode(peer_address).decode('utf-8'), terminal=True)
        logger.warn(traceback.format_exc(), terminal=True)
        return b"0"
    return b"1"


def peer_exchange(peers: 'TorGossipPeers', num_of_peers: bytes):
    """command 7: exchange a number of our top performing peers"""
    num_of_peers = int(chr(int.from_bytes(num_of_peers, 'little')))
    peers = peers.get_highest_score_peers(num_of_peers)
    just_addresses = []
    for i in peers:
        just_addresses.append(i[0])
    return b''.join(just_addresses)


def put_block(safe_db, block):
    #6
    block_hash = block[:64]
    data = block[64:]
    try:
        blockio.store_block(
            Kasten(block_hash, data, onionrblocks.generators.AnonVDFGenerator),
            safe_db)
    except ValueError:
        pass
    except Exception as _:  # noqa
        return b"0"
    return b"1"


def get_block(safe_db, block_hash) -> bytes:
    #5
    try:
        return safe_db.get(block_hash)
    except KeyError:
        return b"0"


def list_blocks_by_type_and_offset(safe_db, type_and_offset):
    #4
    offset, block_type = type_and_offset.split(b',', 1)
    try:
        offset = int(offset)
    except ValueError:
        return b""
    try:
        return list_blocks_by_type(safe_db, block_type)[offset * 64:]
    except KeyError:
        return b"0"


def list_blocks_by_type(safe_db, block_type) -> bytes:
    # 3
    block_type = block_type.decode('utf-8')

    try:
        return safe_db.get('bl-' + block_type)
    except KeyError:
        return b"0"


def handle_check_block(safe_db, block_hash):
    # 2
    if block_hash in blockio.list_all_blocks(safe_db):
        return int(1).to_bytes(1, 'little')
    else:
        return int(2).to_bytes(1, 'little')
