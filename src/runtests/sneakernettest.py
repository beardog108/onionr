import os
from shutil import move

from oldblocks import insert
from onionrstorage import deleteBlock
from onionrcommands.exportblocks import export_block
from filepaths import export_location, block_data_location, data_nonce_file
from etc.onionrvalues import BLOCK_EXPORT_FILE_EXT
from onionrstorage.removeblock import remove_block
from onionrstorage import deleteBlock
from coredb.blockmetadb import get_block_list
import config
from gevent import sleep

def test_sneakernet_import(test_manager):
    if not config.get('transports.lan', False):
        return
    if config.get('runtests.skip_slow', False):
        return
    in_db = lambda b: b in get_block_list()
    bl = insert(os.urandom(10))
    assert in_db(bl)
    export_block(bl)
    assert os.path.exists(export_location + bl + BLOCK_EXPORT_FILE_EXT)
    remove_block(bl)
    deleteBlock(bl)
    assert not in_db(bl)
    os.remove(data_nonce_file)
    move(export_location + bl + BLOCK_EXPORT_FILE_EXT, block_data_location)
    sleep(1)
    assert in_db(bl)
