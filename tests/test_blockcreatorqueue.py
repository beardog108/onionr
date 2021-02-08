#!/usr/bin/env python3
import sys, os
import time
sys.path.append(".")
sys.path.append("src/")
import uuid
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
import unittest, json

from utils import identifyhome, createdirs
from onionrsetup import setup_config
import blockcreatorqueue
createdirs.create_dirs()
setup_config()

# BlockCreatorQueue
# queue_block
# queue_count
# in_queue (sha3_256 hash)


class TestBlockCreatorQueue(unittest.TestCase):


    def test_blockcreator_queue_1(self):
        received_callback = [False]
        def my_store_func(result):
            self.assertIn(b"ok data", result.get_packed())  # if this fails received won't be true
            received_callback[0] = True
        blockcreatorqueue.BlockCreatorQueue(my_store_func).queue_block(b"ok data", "txt", 100)
        time.sleep(0.1)
        self.assertTrue(received_callback[0])

    def test_blockcreator_queue_2(self):
        queue = blockcreatorqueue.BlockCreatorQueue(lambda d: print(d))
        queue.queued.add(os.urandom(28))
        queue.queued.add(os.urandom(28))
        queue.queue_block(b"test", "txt", 1000)
        time.sleep(1)
        self.assertEqual(len(queue.queued), 3)

unittest.main()
