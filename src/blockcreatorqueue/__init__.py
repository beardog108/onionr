"""Onionr - Private P2P Communication.

BlockCreatorQueue, generate anonvdf blocks in a queue
"""
from typing import Callable
from threading import Thread
from hashlib import sha3_224
from os import cpu_count
import time

import blockio
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


class AlreadyGenerating(Exception): pass  # noqa



class PassToSafeDB:
    def __init__(self, db: 'SafeDB'):
        self.db = db
        self.block_creator_queue = BlockCreatorQueue(self.store_kasten)

    def store_kasten(self, kasten_object):
        self.db.put(kasten_object.id, kasten_object.get_packed())

    def queue_then_store(self, block_data, block_type, ttl, **block_metadata):
        self.block_creator_queue.queue_block(block_data, block_type, ttl, **block_metadata)


class BlockCreatorQueue:
    def __init__(
            self, callback_func: Callable, *additional_callback_func_args,
            **additional_callback_func_kwargs):
        self.callback_func = callback_func
        self.queued = set()
        self.max_parallel = cpu_count()
        self.additional_callback_func_args = additional_callback_func_args
        self.additional_callback_func_kwargs = additional_callback_func_kwargs

    def block_data_in_queue(self, block_data: bytes) -> bool:
        if sha3_224(block_data).digest() in self.queued:
            return True
        return False

    def queue_block(
            self, block_data, block_type, ttl: int, **block_metadata) -> bytes:
        """Spawn a thread to make a subprocess to generate a block
        if queue is not full, else wait"""

        digest = sha3_224(block_data).digest()

        def _do_create():
            if digest in self.queued:
                raise AlreadyGenerating()
            self.queued.add(digest)
            while len(self.queued) >= self.max_parallel:
                time.sleep(1)
            result = blockio.subprocgenerate.vdf_block(
                    block_data, block_type, ttl, **block_metadata)
            self.queued.remove(digest)
            self.callback_func(
                result,
                *self.additional_callback_func_args,
                **self.additional_callback_func_kwargs)

        Thread(
            target=_do_create, daemon=True,
            name="BlockCreatorQueue block creation").start()
        return digest
