from base64 import b85encode
import os
import subprocess
import threading

import ujson as json
import kasten

from onionrplugins import onionrevents
from blockio import store_block
from onionrblocks.generators.anonvdf import AnonVDFGenerator

_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../'


def vdf_block(data, data_type, ttl, **metadata):
    try:
        data = data.encode('utf-8')
    except AttributeError:
        pass
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


def gen_and_store_vdf_block(shared_state, *args, **kwargs):
    safe_db = shared_state.get_by_string('SafeDB')
    k = vdf_block(*args, **kwargs)
    store_block(
        k,
        safe_db,
        own_block=True
    )
    onionrevents.event('blockcreated', data=shared_state, threaded=True)

