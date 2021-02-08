#!/usr/bin/env python3

import sys
import os
from base64 import b32encode
from hashlib import sha3_256

try:
  amount = int(sys.argv[1])
except IndexError:
  amount = 1

version = int(3).to_bytes(1, "little")
for i in range(amount):
  pubkey = os.urandom(32)
  #digest = sha3_256(b".onion checksum" + pubkey + version).digest()[:2]
  digest = sha3_256()
  digest.update(b".onion checksum")
  digest.update(pubkey)
  digest.update(version)
  digest = digest.digest()[:2]
  print(b32encode(pubkey + digest + version).decode().lower() + ".onion")
