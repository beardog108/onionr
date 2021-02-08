from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from socket import socket


def download_blocks(sock: 'socket', offset: int):
    sock.sendall()
