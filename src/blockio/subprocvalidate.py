import subprocess
import os
from base64 import b85encode
from onionrblocks.generators import anonvdf


_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../'


def vdf_block(block_hash: bytes, block_data: bytes):
    block_data = b85encode(block_data)

    p = subprocess.Popen(
        [
            f'{_DIR}anonvdf-block-validator.py',
            b85encode(block_hash)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    result = p.communicate(block_data)
    if result[1]:
        raise anonvdf.InvalidID()
