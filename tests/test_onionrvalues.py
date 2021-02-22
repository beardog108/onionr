#!/usr/bin/env python3
import sys, os
sys.path.append(".")
sys.path.append("src/")
import unittest, uuid

TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR

from etc import onionrvalues

class TestOnionrValues(unittest.TestCase):
    def test_api_version(self):
        self.assertEqual(onionrvalues.API_VERSION, '2')

    def test_block_export_ext(self):
        self.assertEqual(onionrvalues.BLOCK_EXPORT_FILE_EXT, '.onionr')

unittest.main()
