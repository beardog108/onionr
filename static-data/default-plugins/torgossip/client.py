"""Onionr - Private P2P Communication.

Torgossip client

Create streams to random peers
"""
import sys
from base64 import b32encode
from os import path
from time import sleep
from typing import TYPE_CHECKING
from random import SystemRandom
from threading import Thread

import socks as socket
from stem import SocketClosed

from netcontroller.torcontrol.onionserviceonline import service_online_recently
from netcontroller.torcontrol import torcontroller
import logger

if TYPE_CHECKING:
    from .peerdb import TorGossipPeers
    from stem.control import Controller
sys.path.insert(0, path.dirname(path.realpath(__file__)))

from commands import GossipCommands

from clientfuncs import download_blocks
from constants import HOSTNAME_FILE
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


def client_funcs(shared_state, socket_pool):
    controller = torcontroller.get_controller()

    def _client_pool(shared_state,  socket_pool: dict):
        peer_db: 'TorGossipPeers' = shared_state.get_by_string(
            'TorGossipPeers')
        socks_port = shared_state.get_by_string('NetController').socksPort

        peers = peer_db.get_highest_score_peers(20)
        SystemRandom().shuffle(peers)

        for peer in peers:
            peer = peer[0]
            if peer in socket_pool:
                continue
            p_encoded = b32encode(peer).decode().lower() + ".onion"
            if not service_online_recently(controller, p_encoded):
                continue
            s = socket.socksocket()
            s.set_proxy(
                socket.SOCKS5, '127.0.0.1', socks_port, rdns=True)
            try:
                s.connect(
                    (p_encoded, 2021))
                socket_pool[peer] = s
                logger.info(f"[TorGossip] Connected to {p_encoded}", terminal=True)

            except socket.GeneralProxyError:
                s.close()

    def client_loop(shared_state, socket_pool):

        sleep_t = 60
        block_db = shared_state.get_by_string('SafeDB')

        peer_info = {}

        block_types = ['txt', 'bin', 'png']

        peers = list(socket_pool)
        SystemRandom().shuffle(peers)

        def download_all_missed():
            while not socket_pool:
                sleep(4)
            peer = list(socket_pool)[0]
            logger.info("[TorGossip] Downloading missed blocks", terminal=True)
            for bl_type in block_types:
                while True:
                    try:
                        peer_info[peer]
                    except KeyError:
                        peer_info[peer] = {'offsets': {}}
                    else:
                        try:
                            peer_info[peer]['offsets']
                        except KeyError:
                            peer_info[peer]['offsets'] = {}
                    try:
                        offset = peer_info[peer]['offsets'][bl_type]
                    except KeyError:
                        offset = 0
                    try:
                        peer_info[peer]['offsets'][bl_type] = \
                            download_blocks(
                            block_db, socket_pool[peer], offset, bl_type)
                    except BrokenPipeError:
                        del peer_info[peer]['offsets']
                        del socket_pool[peer]
                    else:
                        # Go back to for loop
                        break

        Thread(target=download_all_missed, daemon=True).start()

        while True:
            if not socket_pool:
                try:
                    _client_pool(shared_state, socket_pool)
                except SocketClosed:  # Probably shutting down, or tor crashed
                    sleep(1)
                    continue
            try:
                peers[0]
            except IndexError:
                logger.error(
                    "There are no known TorGossip peers." +
                    f" Sleeping for {sleep_t}s",
                    terminal=True)
                sleep(sleep_t)
                continue
            peers = list(socket_pool)
            SystemRandom().shuffle(peers)

    _client_pool(shared_state, socket_pool)
    client_loop(shared_state, socket_pool)


def _add_bootstrap_peers(peer_db: 'TorGossipPeers'):
    # If we have peers, ignore encrypt mark in db
    if len(peer_db.db.db_conn.keys()) > 1:
        return
    with open(HOSTNAME_FILE, "rb") as hf:
        our_host = b32encode(hf.read()).decode().lower()
    bootstap_peers = path.dirname(path.realpath(__file__)) + "/bootstrap.txt"
    with open(bootstap_peers, 'r') as bs_peers:
        peers = bs_peers.read().split(',')
        try:
            peers.remove(our_host)
        except ValueError:
            pass
        for peer in peers:
            try:
                peer_db.db.get(peer)
            except KeyError:
                pass
            else:
                continue
            if peer:
                peer_db.add_peer(peer)


def start_client(shared_state):
    # add boot strap peers to db if we need peers
    _add_bootstrap_peers(shared_state.get_by_string('TorGossipPeers'))
    # create and fill pool of sockets to peers (over tor socks)
    socket_pool = {}
    client_funcs(shared_state, socket_pool)
