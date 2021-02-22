import sys
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socket import socket
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from commands import GossipCommands


def command_sender(sock: 'socket', cmd: GossipCommands, *command_data: bytes):
    sock.sendall(
        str(int(GossipCommands.LIST_BLOCKS_BY_TYPE_OFFSET)).encode(
            'utf-8') + b''.join(command_data))
