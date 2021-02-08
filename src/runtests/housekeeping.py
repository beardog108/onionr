from gevent import sleep

from oldblocks import insert
import config
from coredb.blockmetadb import get_block_list


def test_inserted_housekeeping(testmanager):
    """Tests that inserted blocks are proprely deleted"""
    if config.get('runtests.skip_slow', False):
        return
    bl = insert('testdata', expire=12)
    wait_seconds = 132  # Wait two minutes plus expire time
    count = 0
    if bl in get_block_list():
        while count < wait_seconds:
            if bl in get_block_list():
                sleep(0.8)
                count += 1
            else:
                return
        raise ValueError('Inserted block with expiry not erased')
    else:
        raise ValueError('Inserted block in expiry test not present in list')
