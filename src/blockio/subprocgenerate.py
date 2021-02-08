from base64 import b85encode
import os
import subprocess

import ujson as json

import kasten
from onionrblocks.generators.anonvdf import AnonVDFGenerator

_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../'


def vdf_block(data, data_type, ttl, **metadata):
    data = b85encode(data)
    generated = subprocess.Popen(
        [
            f'{_DIR}anonvdf-block-creator.py',
            json.dumps(metadata),
            data_type,
            str(ttl)],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE)
    generated = generated.communicate(data)[0]
    return kasten.Kasten(
        generated[:64], generated[64:],
        AnonVDFGenerator, auto_check_generator=True)

