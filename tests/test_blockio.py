#!/usr/bin/env python3
import sys, os

sys.path.append(".")
sys.path.append("src/")
import uuid
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
import unittest
import time
from utils import identifyhome, createdirs
from onionrsetup import setup_config, setup_default_plugins
import random

createdirs.create_dirs()
setup_config()
setup_default_plugins()

import kasten
from onionrblocks.generators import anonvdf
from onionrblocks import blockcreator
from utils import identifyhome

import safedb
import blockio
from blockio.clean.cleanblocklistentries import clean_block_list_entries
from blockio import subprocgenerate, subprocvalidate


def _remove_db(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


class TestBlockIO(unittest.TestCase):

    def test_subproc_validate(self):
        bl = blockcreator.create_anonvdf_block(b"hello" + int(3).to_bytes(1, "big"), b"txt" + int(3).to_bytes(1, "big"), 5)
        invalid = os.urandom(64)
        subprocvalidate.vdf_block(bl.id, bl.get_packed())

        self.assertRaises(anonvdf.InvalidID, subprocvalidate.vdf_block, invalid, bl.get_packed())


    def test_subproc_generate(self):
        db_file = identifyhome.identify_home() + 'test.db'
        db = safedb.SafeDB(db_file)

        bl: 'Kasten' = subprocgenerate.vdf_block(b"test", "txt", 10)

        self.assertEqual(b"test", bl.data)
        self.assertEqual("txt", bl.get_data_type())
        self.assertEqual(330, bl.get_metadata()['rds'])

        db.close()
        _remove_db(db_file)

    def test_list_all_blocks(self):
        db_file = identifyhome.identify_home() + 'test.db'
        db = safedb.SafeDB(db_file)
        expected_l = []
        for i in range(5):
            bl = blockcreator.create_anonvdf_block(b"hello" + int(i).to_bytes(1, "big"), b"txt" + int(i).to_bytes(1, "big"), 5)
            blockio.store_block(bl, db)
            expected_l.append(bl.id)

        l = blockio.load.list_all_blocks(db)
        self.assertEqual(len(l), 5)
        for i in l:
            self.assertIn(bytes(i), expected_l)


        db.close()
        _remove_db(db_file)

    def test_clean_blocklist_entries(self):
        db_file = identifyhome.identify_home() + 'test.db'
        db = safedb.SafeDB(db_file)
        bl = blockcreator.create_anonvdf_block(b"hello" + int(10).to_bytes(1, "big"), b"txt", 5)
        blockio.store_block(bl, db)
        db.db_conn[b'bl-txt'] = b''
        clean_block_list_entries(db)
        self.assertRaises(KeyError, db.get, 'bl-txt')
        db.close()
        _remove_db(db_file)

    def test_clean_expired(self):

        db_file = identifyhome.identify_home() + 'test.db'
        db = safedb.SafeDB(db_file)
        for i in range(3):
            bl = blockcreator.create_anonvdf_block(b"hello" + int(i).to_bytes(1, "big"), b"txt", 5)
            blockio.store_block(bl, db)
        blockio.clean_expired_blocks(db)
        time.sleep(1)
        self.assertEqual(len(list(blockio.list_blocks_by_type("txt", db))), 3)
        time.sleep(10.1)
        blockio.clean_expired_blocks(db)
        self.assertEqual(len(db.db_conn[b'bl-txt']), 0)
        db.close()
        _remove_db(db_file)

    def test_store_block(self):
        packed = kasten.generator.pack.pack(b"test", "tst")
        bl: kasten.Kasten = anonvdf.AnonVDFGenerator.generate(packed, rounds=1000)
        db_file = identifyhome.identify_home() + 'test.db'
        db = safedb.SafeDB(db_file)
        blockio.store_block(bl, db)
        db.close()
        _remove_db(db_file)

    def test_store_dupe(self):
        db_file = identifyhome.identify_home() + 'test.db'
        _remove_db(db_file)
        packed = kasten.generator.pack.pack(b"test", "tst")
        bl: kasten.Kasten = anonvdf.AnonVDFGenerator.generate(packed, rounds=1000)
        db = safedb.SafeDB(db_file)
        blockio.store_block(bl, db)
        self.assertRaises(ValueError, blockio.store_block, bl, db)
        db.close()
        _remove_db(db_file)

    def test_list_blocks(self):
        db_file = identifyhome.identify_home() + 'test.db'
        _remove_db(db_file)
        db = safedb.SafeDB(db_file)
        expected_list = []
        for i in range(10):
            bl = blockcreator.create_anonvdf_block(b'test' + int(i).to_bytes(1, 'big'), 'txt', 60)
            blockio.store_block(bl, db)
            expected_list.append(bl.id)
        l = blockio.list_blocks_by_type('txt', db)
        self.assertEqual(len(list(l)), len(expected_list))
        for i in l:
            self.assertIn(bytes(i), expected_list)
        db.close()
        _remove_db(db_file)


unittest.main()
