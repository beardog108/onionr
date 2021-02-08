"""Onionr - Private P2P Communication.

Torgossip client

Create streams to random peers
"""
import sys
from base64 import b32encode
from os import path
from typing import TYPE_CHECKING
from random import SystemRandom

import socks as socket

from netcontroller.torcontrol.onionserviceonline import service_online_recently
from netcontroller.torcontrol import torcontroller

if TYPE_CHECKING:
    from .peerdb import TorGossipPeers
    from stem.control import Controller
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from commands import GossipCommands
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
controller = torcontroller.get_controller()


def _add_bootstrap_peers(peer_db: 'TorGossipPeers'):
    bootstap_peers = path.dirname(path.realpath(__file__)) + "/bootstrap.txt"
    with open(bootstap_peers, 'r') as bs_peers:
        peers = bs_peers.split(',')
        for peer in peers:
            try:
                peer_db.get(peer)
            except KeyError:
                pass
            else:
                continue
            if peer and service_online_recently(controller, peer):
                peer_db.add_peer(peer)


def _client_pool(shared_state,  socket_pool: dict):
    peer_db: 'TorGossipPeers' = shared_state.get_by_string('TorGossipPeers')
    socks_port = shared_state.get_by_string('NetController').socksPort

    peers = peer_db.get_highest_score_peers(20)
    SystemRandom().shuffle(peers)

    for peer in peers:
        if peer in socket_pool:
            continue
        if not service_online_recently(controller, peer):
            continue
        s = socket.socksocket()
        s.set_proxy(
            socket.SOCKS5, '127.0.0.1', socks_port, rdns=True)
        try:
            socket_pool[peer] = s.connect(
                (b32encode(peer).decode().lower() + ".onion", 2021))

        except socket.GeneralProxyError:
            s.close()


def client_loop(shared_state, socket_pool):
    block_db = shared_state.get_by_string('SafeDB')
    peer_db = shared_state.get_by_string('TorGossipPeers')

    while True:
        if not socket_pool:
            _client_pool(shared_state, socket_pool)
        sync_




def start_client(shared_state):
    # add boot strap peers to db if we need peers
    _add_bootstrap_peers(shared_state.get_by_string('TorGossipPeers'))
    # create and fill pool of sockets to peers (over tor socks)
    socket_pool = {}
    _client_pool(shared_state, socket_pool)
    client_loop(shared_state, socket_pool)
