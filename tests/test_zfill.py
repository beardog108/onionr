#!/usr/bin/env python3
import unittest, sys, uuid, os
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
sys.path.append(".")
sys.path.append("src/")
from utils import createdirs
createdirs.create_dirs()
from utils import reconstructhash

class ZFill_Hash(unittest.TestCase):
    def test_reconstruct(self):
        h = b"4d20d791cbc293999b97cc627aa011692d317dede3d0fbd390c763210b0d"
        self.assertEqual(reconstructhash.reconstruct_hash(h), b"0000" + h)
        h = b"4d20d791cbc293999b97cc627aa011692d317dede3d0fbd390c763210b0d"
        self.assertEqual(reconstructhash.reconstruct_hash(h, 62), b"00" + h)

    def test_deconstruct(self):
        h = b"0000e918d24999ad9b0ff00c1d414f36b74afc93871a0ece4bd452f82b56af87"
        h_no = b"e918d24999ad9b0ff00c1d414f36b74afc93871a0ece4bd452f82b56af87"
        self.assertEqual(reconstructhash.deconstruct_hash(h), h_no)
        h = "0000e918d24999ad9b0ff00c1d414f36b74afc93871a0ece4bd452f82b56af87"
        h_no = "e918d24999ad9b0ff00c1d414f36b74afc93871a0ece4bd452f82b56af87"
        self.assertEqual(reconstructhash.deconstruct_hash(h), h_no)
unittest.main()
