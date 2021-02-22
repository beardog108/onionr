#!/usr/bin/env python3
import sys, os
sys.path.append(".")
sys.path.append("src/")
import unittest, uuid
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
from onionrutils import stringvalidators

class OnionrValidations(unittest.TestCase):

    def test_integer_string(self):
        valid = ["1", "100", 100, "-5", -5]
        invalid = ['test', "1d3434", "1e100", None]

        for x in valid:
            #print('testing', x)
            self.assertTrue(stringvalidators.is_integer_string(x))

        for x in invalid:
            #print('testing', x)
            self.assertFalse(stringvalidators.is_integer_string(x))

unittest.main()
