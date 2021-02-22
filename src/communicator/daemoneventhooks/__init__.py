"""Onionr - Private P2P Communication.

Hooks to handle daemon events
"""
from threading import Thread

from typing import TYPE_CHECKING

from gevent import sleep


if TYPE_CHECKING:
    from toomanyobjs import TooMany
    from deadsimplekv import DeadSimpleKV
    from communicator import OnionrCommunicatorDaemon
    from httpapi.daemoneventsapi import DaemonEventsBP
    from onionrtypes import BlockHash
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


def daemon_event_handlers(shared_state: 'TooMany'):
    def _get_inst(class_name: str):
        while True:
            try:
                return shared_state.get_by_string(class_name)
            except KeyError:
                sleep(0.2)
    comm_inst = _get_inst('OnionrCommunicatorDaemon')
    events_api: 'DaemonEventsBP' = _get_inst('DaemonEventsBP')
    kv: 'DeadSimpleKV' = _get_inst('DeadSimpleKV')

    def print_test(text=''):
        print("It works!", text)
        return f"It works! {text}"

    def test_runtime():
        Thread(target=comm_inst.shared_state.get_by_string(
            "OnionrRunTestManager").run_tests).start()

    events_api.register_listener(print_test)
    events_api.register_listener(test_runtime)
