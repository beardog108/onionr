"""Onionr - Private P2P Communication.

Torgossip peer safedb interface
"""
from base64 import b32decode
from struct import unpack, pack
from time import time
from typing import List

from utils.identifyhome import identify_home
import safedb
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


class TorGossipPeers:  # name it this way to avoid collisions in SharedState

    PACK_FORMAT = "qQ"

    def __init__(self, encrypt=False):
        self.db = safedb.SafeDB(
            identify_home() + "/torgossip-peers.db", protected=encrypt)

    def _shrink_peer_address(self, peer):
        # strip .onion and b32decode peer address for lower database mem usage
        if len(peer) == 62:  # constant time
            return b32decode(peer[:-6])  # O(N)
        return peer

    def _pack_and_store_info(self, peer, new_score=None, new_seen=None):
        # Repack peer information with new value(s) and store it
        peer = self._shrink_peer_address(peer)
        try:
            score, seen = unpack(self.PACK_FORMAT, self.db.get(peer))
        except KeyError:
            score = seen = 0

        if new_score:
            score = new_score
        if new_seen:
            seen = new_seen

        self.db.put(peer, pack(self.PACK_FORMAT, score, seen))

    def get_highest_score_peers(self, max) -> List:
        assert max >= 1
        peer = self.db.db_conn.firstkey()
        if peer == b'enc':
            peer = self.db.db_conn.nextkey(peer)

        assert len(peer) == 34
        if not peer:
            return []

        top = [(peer, self.db.get(peer))]

        while peer:
            peer = self.db.db_conn.nextkey(peer)
            if not peer:
                break
            if peer == b"enc":
                continue
            peer_data = self.db.get(peer)
            overwrite = None

            if len(top) != max:
                top.append((peer, peer_data))
                peer = self.db.db_conn.nextkey(peer)
                continue
            for count, cur_top in enumerate(top):
                # if peer score is greater than any set peer, overwrite
                if unpack(self.PACK_FORMAT, cur_top[1])[0] < \
                        unpack(self.PACK_FORMAT, peer_data)[0]:
                    overwrite = count
                    break  # below else won't execute, so it will be overwritten
            else:
                # if not overwriting, go to next peer
                peer = self.db.db_conn.nextkey(peer)
                continue
            top[overwrite] = (peer, peer_data)
        return top

    def add_score(self, peer, plus):
        shrunk = self._shrink_peer_address(peer)
        score, _ = unpack("qQ", self.db.get(shrunk))

        self._pack_and_store_info(
            shrunk, new_score=score + plus)

    def update_seen(self, peer):
        peer = self._shrink_peer_address(peer)
        self._pack_and_store_info(peer, new_seen=int(time()))

    def add_peer(self, peer):
        self.update_seen(peer)

    def remove_peer(self, peer):
        peer = self._shrink_peer_address(peer)
        del self.db.db_conn[peer]
