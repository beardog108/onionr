import sys, os
sys.path.append(".")
sys.path.append("src/")
import unittest, uuid, json
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
from utils import createdirs
createdirs.create_dirs()
from utils import readstatic
class OnionrConfig(unittest.TestCase):
    def test_default_file(self):
        json.loads(readstatic.read_static('default_config.json'))

    def test_installed_config(self):
        import onionrsetup
        onionrsetup.setup_config()
        with open(TEST_DIR + 'config.json') as conf:
            conf = json.loads(conf.read())
            self.assertEqual(conf['advanced']['security_auditing'], True)
            self.assertEqual(conf['allocations']['disk'], 1073741824)
            self.assertEqual(conf['allocations']['disk'], 1073741824)
            self.assertEqual(conf['general']['announce_node'], True)
            self.assertEqual(conf['general']['bind_address'], '')
            self.assertEqual(conf['general']['dev_mode'], False)
            self.assertEqual(conf['general']['display_header'], True)
            self.assertEqual(conf['general']['security_level'], 0)
            self.assertEqual(conf['general']['show_notifications'], True)
            self.assertEqual(conf['log']['console']['color'], True)
            self.assertEqual(conf['log']['console']['output'], True)
            self.assertEqual(conf['log']['file']['output'], True)
            self.assertEqual(conf['log']['file']['remove_on_exit'], True)
            self.assertEqual(conf['log']['verbosity'], 'default')
            self.assertEqual(conf['onboarding']['done'], False)
            self.assertEqual(conf['plugins']['disabled'], [])
            self.assertEqual(conf['plugins']['enabled'], [])
            self.assertEqual(conf['ui']['theme'], 'dark')
unittest.main()
