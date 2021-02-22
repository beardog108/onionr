#!/usr/bin/env python3
import sys, os

sys.path.append(".")
sys.path.append("src/")
import unittest, uuid

TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
from utils import getopenport

class GetOpenPortTest(unittest.TestCase):
    def test_open_port(self):
        open_port = int(getopenport.get_open_port())
        self.assertGreaterEqual(open_port, 1024)

unittest.main()
