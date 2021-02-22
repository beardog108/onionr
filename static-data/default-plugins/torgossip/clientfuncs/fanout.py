"""Onionr - Private P2P Communication.

Fanout blocks to Onionr TorGossip peer
"""
import os
import sys
from typing import TYPE_CHECKING
from random import SystemRandom
from time import sleep

if TYPE_CHECKING:
    from socket import socket

import logger

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from commands import GossipCommands
from .commandsender import command_sender
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


def fanout_to_peers(
        socket_pool: dict,
        block_hash: bytes,
        block_data: 'KastenPacked',
        fanout_count: int = 4):

    peers = list(socket_pool)
    SystemRandom().shuffle(peers)
    sent_counter = 0

    fanout_count = min(fanout_count, len(peers))
    fanout_count = max(1, fanout_count)

    while sent_counter < fanout_count:
        try:
            peer = peers.pop()
        except IndexError:
            sleep(2)

        command_sender(peer, GossipCommands.CHECK_HAS_BLOCK, block_hash)
        if peer.recv(1) == b'\x01':
            continue
        command_sender(peer, GossipCommands.PUT_BLOCK, block_hash, block_data)
        if peer.recv(1) != b'\x01':
            logger.warn(f"Failed to fanout {block_hash} to {peer}", terminal=True)
            continue
        sent_counter += 1

