#!/usr/bin/env python
# This is a subprocess because block validation is somewhat CPU intensive

from base64 import b85decode, b85encode
import os
from sys import argv, stdin, stderr, stdout, exit

from kasten import Kasten
from kasten.exceptions import InvalidID
from onionrblocks.exceptions import BlockExpired
from onionrblocks.generators import AnonVDFGenerator

block_hash = b85decode(argv[1])

block_bytes = b85decode(stdin.read())


try:
    Kasten(
        block_hash, block_bytes,
        AnonVDFGenerator, auto_check_generator=True)
except InvalidID:
    stderr.write(
        "Invalid block ID for " +
        b85encode(block_hash).decode('utf-8'))
except ValueError as e:
    # Supposed to be if rounds are not specified in the block
    stderr.write(e.message)
except BlockExpired:
    stderr.write(
        b85encode(block_hash).decode('utf-8') + " is expired")
else:

    with os.fdopen(stdout.fileno(), 'wb') as std:
        std.write(b"valid")
    exit(0)
stderr.flush()
exit(1)
