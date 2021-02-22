import sys, os
sys.path.append(".")
sys.path.append("src/")
import unittest, uuid, time, threading

TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
os.environ["ONIONR_HOME"] = TEST_DIR
from utils import createdirs
createdirs.create_dirs()
from etc import waitforsetvar

def set_test_var_delay(obj, delay=0):
    if delay > 0: time.sleep(delay)
    obj.test_var = True

class TestWaitForSetVar(unittest.TestCase):
    def test_no_wait(self):
        test_object = lambda: None
        threading.Thread(target=set_test_var_delay, args=[test_object]).start()
        waitforsetvar.wait_for_set_var(test_object, 'test_var')
        self.assertTrue(test_object.test_var)

    def test_negative_wait(self):
        test_object = lambda: None
        threading.Thread(target=set_test_var_delay, args=[test_object, -1]).start()
        waitforsetvar.wait_for_set_var(test_object, 'test_var')
        self.assertTrue(test_object.test_var)

    def test_zero_wait(self):
        test_object = lambda: None
        threading.Thread(target=set_test_var_delay, args=[test_object, 0]).start()
        waitforsetvar.wait_for_set_var(test_object, 'test_var')
        self.assertTrue(test_object.test_var)

    def test_one_wait(self):
        test_object = lambda: None
        threading.Thread(target=set_test_var_delay, args=[test_object, 1]).start()
        waitforsetvar.wait_for_set_var(test_object, 'test_var')
        self.assertTrue(test_object.test_var)

    def test_three_wait(self):
        test_object = lambda: None
        threading.Thread(target=set_test_var_delay, args=[test_object, 3]).start()
        waitforsetvar.wait_for_set_var(test_object, 'test_var')
        self.assertTrue(test_object.test_var)

unittest.main()
