#!/usr/bin/env python
from base64 import b85decode
import sys
import os

import ujson as json

from onionrblocks import blockcreator

# This script creates a block without storing it. it is written to stdout
# It is used instead of in the main process to avoid GIL locking/slow down

metadata = json.loads(sys.argv[1])
block_type = sys.argv[2]
ttl = int(sys.argv[3])

data = b85decode(sys.stdin.read())

with os.fdopen(sys.stdout.fileno(), 'wb') as stdout:
    bl = blockcreator.create_anonvdf_block(data, block_type, ttl, **metadata)
    try:
        stdout.write(bl.id + bl.get_packed())
    except BrokenPipeError:
        pass
