"""Onionr - Private P2P Communication.

Serialize various node information
"""
from typing import TYPE_CHECKING

from gevent import sleep

from psutil import Process
import ujson as json

from utils.sizeutils import size, human_size
from utils.identifyhome import identify_home
from onionrutils.epoch import get_epoch

if TYPE_CHECKING:
    from deadsimplekv import DeadSimpleKV
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


class SerializedData:
    def __init__(self):
        """
        Serialized data is in JSON format:
        {
            'success': bool,
            'foo': 'bar',
            etc
        }
        """

    def get_stats(self):
        """Return statistics about our node"""
        stats = {}
        proc = Process()

        def get_open_files():
            return proc.num_fds()

        try:
            self._too_many
        except AttributeError:
            sleep(1)
        kv: "DeadSimpleKV" = self._too_many.get_by_string("DeadSimpleKV")
        connected = []
        [connected.append(x)
            for x in kv.get('onlinePeers') if x not in connected]
        stats['uptime'] = get_epoch() - kv.get('startTime')
        stats['threads'] = proc.num_threads()
        stats['ramPercent'] = proc.memory_percent()
        stats['fd'] = get_open_files()
        stats['diskUsage'] = human_size(size(identify_home()))
        return json.dumps(stats)
