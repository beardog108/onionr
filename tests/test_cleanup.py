#!/usr/bin/env python3
import sys, os
sys.path.append(".")
sys.path.append("src/")
import uuid
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
import unittest, json

from utils import identifyhome, createdirs
createdirs.create_dirs()
from etc.cleanup import delete_run_files
import filepaths


run_file_paths = [
    filepaths.private_API_host_file,
    filepaths.daemon_mark_file,
    filepaths.lock_file]

def _run_paths_exist():
    for f in run_file_paths:
        if not os.path.exists(f):
            return False
    return True

class TestDeleteRunFiles(unittest.TestCase):
    def test_delete_run_files(self):
        for x in run_file_paths:
            with open(x, 'w') as f:
                f.write("")
        self.assertTrue(_run_paths_exist())
        delete_run_files()
        self.assertFalse(_run_paths_exist())



unittest.main()
