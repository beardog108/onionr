"""Onionr - Private P2P Communication.

Permanent onion service addresses without manual torrc
"""
from typing import TYPE_CHECKING
import base64

if TYPE_CHECKING:
    from stem.control import Controller
from utils import identifyhome
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


def _add_ephemeral_service(
        controller: 'Controller', virtual_port, target, key_content=None):

    key_type = "NEW"
    if not key_content:
        key_content = "ED25519-V3"
    else:
        key_type = "ED25519-V3"
    hs = controller.create_ephemeral_hidden_service(
        {virtual_port: target},
        key_type=key_type,
        key_content=key_content,
        detached=True
        )

    return (hs.service_id, hs.private_key)


def create_new_service(
        controller: 'Controller',
        virtual_port: int,
        unix_socket: str = None,
        bind_location: str = None) -> bytes:
    target = bind_location
    if unix_socket and bind_location or (not unix_socket and not bind_location):
        raise ValueError("Must pick unix socket or ip:port, and not both")
    if unix_socket:
        target = unix_socket
        if not unix_socket.startswith("unix:"):
            target = "unix:" + target

    return _add_ephemeral_service(
        controller, virtual_port, target)


def restore_service(
        controller: 'Controller',
        key: bytes,
        virtual_port: int,
        unix_socket: str = None,
        bind_location: str = None):
    if unix_socket and bind_location or (not unix_socket and not bind_location):
        raise ValueError("Must pick unix socket or ip:port, and not both")

    key = base64.b64encode(key).decode()

    target = unix_socket
    if bind_location:
        target = bind_location
    if not target.startswith("unix:"):
        target = "unix:" + target
    return _add_ephemeral_service(
        controller, virtual_port, target, key_content=key)


