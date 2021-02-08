#!/usr/bin/env python3
import sys, os
sys.path.append(".")
sys.path.append("src/")
import unittest, uuid, sqlite3
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
from utils import createdirs
createdirs.create_dirs()
from onionrcrypto import getourkeypair
getourkeypair.get_keypair()
from urllib.request import pathname2url
from coredb import keydb


class OnionrTests(unittest.TestCase):

    def test_address_add(self):
        testAddresses = ['56kmnycrvepfarolhnx6t2dvmldfeyg7jdymwgjb7jjzg47u2lqw2sad.onion', 'ao34zusas5oocjllkh6uounorhtujyep4ffwz4k4r7qkxie5otdiwqad.onion']
        for address in testAddresses:
            keydb.addkeys.add_address(address)
        dbAddresses = keydb.listkeys.list_adders()
        for address in testAddresses:
            self.assertIn(address, dbAddresses)

        invalidAddresses = [None, '', '   ', '\t', '\n', ' test ', 24, 'fake.onion', 'fake.b32.i2p']
        for address in invalidAddresses:
            try:
                keydb.addkeys.add_address(address)
            except TypeError:
                pass
        dbAddresses = keydb.listkeys.list_adders()
        for address in invalidAddresses:
            self.assertNotIn(address, dbAddresses)

    def test_address_info(self):
        adder = 'ao34zusas5oocjllkh6uounorhtujyep4ffwz4k4r7qkxie5otdiwqad.onion'
        keydb.addkeys.add_address(adder)
        self.assertNotEqual(keydb.transportinfo.get_address_info(adder, 'success'), 1000)
        keydb.transportinfo.set_address_info(adder, 'success', 1000)
        self.assertEqual(keydb.transportinfo.get_address_info(adder, 'success'), 1000)

unittest.main()
