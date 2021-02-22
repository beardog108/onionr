#!/usr/bin/env python3
import sys, os
sys.path.append(".")
sys.path.append("src/")
import unittest, uuid
import time
import math

from deadsimplekv import DeadSimpleKV
import setupkvvars

TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
from utils import createdirs
createdirs.create_dirs()

import onionrsetup as setup
from utils import createdirs
setup.setup_config()

class SetupKVVarsTest(unittest.TestCase):
    def test_set_var_values(self):

        kv = DeadSimpleKV()
        setupkvvars.setup_kv(kv)
        self.assertFalse(kv.get('shutdown'))
        self.assertAlmostEqual(math.floor(kv.get('startTime')), math.floor(time.time()), places=0)
        self.assertTrue(kv.get('isOnline'))


unittest.main()
