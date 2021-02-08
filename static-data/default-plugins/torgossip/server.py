"""
Onionr - Private P2P Communication

Gossip plugin server, multiplexing using selectors
"""
import os
import sys

import selectors
import socket
from time import sleep

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from commands import GossipCommands  # noqa
import commandhandlers

from constants import SERVER_SOCKET
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


def start_server(shared_state):

    sel = selectors.DefaultSelector()

    def accept(sock, mask):
        conn, addr = sock.accept()  # Should be ready
        conn.setblocking(False)
        sel.register(conn, selectors.EVENT_READ, read)

    def do_close(conn, msg=None):
        if msg:
            conn.sendall(msg)
            sleep(0.1)
        sel.unregister(conn)
        conn.close()

    def read(conn, mask):
        data = conn.recv(1000)  # Should be ready
        cmd = None
        if data:
            try:
                cmd = int(int(data[0]).to_bytes(1, 'little'))
                data = data[1:]
            except IndexError:
                do_close(conn, b'MALFORMED COMMAND')
            if cmd == GossipCommands.PING:
                conn.sendall(b'PONG')
            elif cmd == GossipCommands.EXIT:
                do_close(conn, b'BYE')
            elif cmd == GossipCommands.PUT_BLOCK:
                conn.sendall(
                    commandhandlers.put_block(
                        shared_state.get_by_string('SafeDB'), data
                    )
                )
            elif cmd == GossipCommands.GET_BLOCK:
                conn.sendall(
                    commandhandlers.get_block(
                        shared_state.get_by_string('SafeDB'), data))
            elif cmd == GossipCommands.LIST_BLOCKS_BY_TYPE:
                conn.sendall(
                    commandhandlers.list_blocks_by_type(
                        shared_state.get_by_string('SafeDB'), data))
            elif cmd == GossipCommands.LIST_BLOCKS_BY_TYPE_OFFSET:
                conn.sendall(
                    commandhandlers.list_blocks_by_type_and_offset(
                        shared_state.get_by_string('SafeDB'), data)
                )
            elif cmd == GossipCommands.CHECK_HAS_BLOCK:
                conn.sendall(
                    commandhandlers.handle_check_block(
                        shared_state.get_by_string('SafeDB'), data))
            elif cmd == GossipCommands.PEER_EXCHANGE:
                conn.sendall(
                    commandhandlers.peer_exchange(
                        shared_state.get_by_string('TorGossipPeers'), data))
            elif cmd == GossipCommands.ANNOUNCE_PEER:
                conn.sendall(
                    commandhandlers.announce_peer(
                        shared_state.get_by_string('TorGossipPeers'), data)
                    )
            else:
                conn.sendall(b'Unknown ' + str(cmd).encode('utf-8'))
        else:
            do_close(conn)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        os.remove(SERVER_SOCKET)
    except FileNotFoundError:
        pass

    sock.bind(SERVER_SOCKET)
    sock.listen(100)
    sock.setblocking(False)
    sel.register(sock, selectors.EVENT_READ, accept)

    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
