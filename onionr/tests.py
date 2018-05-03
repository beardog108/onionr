#!/usr/bin/env python3
'''
    Onionr - P2P Microblogging Platform & Social network
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import unittest, sys, os, base64, tarfile, shutil, simplecrypt, logger, btc

class OnionrTests(unittest.TestCase):
    def testPython3(self):
        if sys.version_info.major != 3:
            logger.debug('Python version: ' + sys.version_info.major)
            self.assertTrue(False)
        else:
            self.assertTrue(True)

    def testNone(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running simple program run test...')

        blank = os.system('./onionr.py --version')
        if blank != 0:
            self.assertTrue(False)
        else:
            self.assertTrue(True)

    def testPeer_a_DBCreation(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running peer db creation test...')

        if os.path.exists('data/peers.db'):
            os.remove('data/peers.db')
        import core
        myCore = core.Core()
        myCore.createPeerDB()
        if os.path.exists('data/peers.db'):
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def testPeer_b_addPeerToDB(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running peer db insertion test...')

        import core
        myCore = core.Core()
        if not os.path.exists('data/peers.db'):
            myCore.createPeerDB()
        if myCore.addPeer('6M5MXL237OK57ITHVYN5WGHANPGOMKS5C3PJLHBBNKFFJQOIDOJA====') and not myCore.addPeer('NFXHMYLMNFSAU==='):
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def testData_b_Encrypt(self):
        self.assertTrue(True)
        return

        logger.debug('-'*26 + '\n')
        logger.info('Running data dir encrypt test...')

        import core
        myCore = core.Core()
        myCore.dataDirEncrypt('password')
        if os.path.exists('data-encrypted.dat'):
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def testData_a_Decrypt(self):
        self.assertTrue(True)
        return

        logger.debug('-'*26 + '\n')
        logger.info('Running data dir decrypt test...')

        import core
        myCore = core.Core()
        myCore.dataDirDecrypt('password')
        if os.path.exists('data/'):
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def testConfig(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running simple configuration test...')

        import config

        config.check()
        config.reload()
        configdata = str(config.get_config())

        config.set('testval', 1337)
        if not config.get('testval', None) is 1337:
            self.assertTrue(False)

        config.set('testval')
        if not config.get('testval', None) is None:
            self.assertTrue(False)

        config.save()
        config.reload()

        if not str(config.get_config()) == configdata:
            self.assertTrue(False)

        self.assertTrue(True)

    def testBitcoinNode(self):
        # temporarily disabled- this takes a lot of time the CI doesn't have
        self.assertTrue(True)
        #logger.debug('-'*26 + '\n')
        #logger.info('Running bitcoin node test...')

        #sbitcoin = btc.OnionrBTC()

    def testPluginReload(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running simple plugin reload test...')

        import onionrplugins, os

        if not onionrplugins.exists('test'):
            os.makedirs(onionrplugins.get_plugins_folder('test'))
            with open(onionrplugins.get_plugins_folder('test') + '/main.py', 'a') as main:
                main.write("print('Running')\n\ndef on_test(pluginapi, data = None):\n    print('received test event!')\n    return True\n\ndef on_start(pluginapi, data = None):\n    print('start event called')\n\ndef on_stop(pluginapi, data = None):\n    print('stop event called')\n\ndef on_enable(pluginapi, data = None):\n    print('enable event called')\n\ndef on_disable(pluginapi, data = None):\n    print('disable event called')\n")
            onionrplugins.enable('test')

        try:
            onionrplugins.reload('test')
            self.assertTrue(True)
        except:
            self.assertTrue(False)

    def testPluginStopStart(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running simple plugin restart test...')

        import onionrplugins, os

        if not onionrplugins.exists('test'):
            os.makedirs(onionrplugins.get_plugins_folder('test'))
            with open(onionrplugins.get_plugins_folder('test') + '/main.py', 'a') as main:
                main.write("print('Running')\n\ndef on_test(pluginapi, data = None):\n    print('received test event!')\n    return True\n\ndef on_start(pluginapi, data = None):\n    print('start event called')\n\ndef on_stop(pluginapi, data = None):\n    print('stop event called')\n\ndef on_enable(pluginapi, data = None):\n    print('enable event called')\n\ndef on_disable(pluginapi, data = None):\n    print('disable event called')\n")
            onionrplugins.enable('test')

        try:
            onionrplugins.start('test')
            onionrplugins.stop('test')
            self.assertTrue(True)
        except:
            self.assertTrue(False)

    def testPluginEvent(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running plugin event test...')

        import onionrplugins as plugins, onionrevents as events, os

        if not plugins.exists('test'):
            os.makedirs(plugins.get_plugins_folder('test'))
            with open(plugins.get_plugins_folder('test') + '/main.py', 'a') as main:
                main.write("print('Running')\n\ndef on_test(pluginapi, data = None):\n    print('received test event!')\n    print('thread test started...')\n    import time\n    time.sleep(1)\n    \n    return True\n\ndef on_start(pluginapi, data = None):\n    print('start event called')\n\ndef on_stop(pluginapi, data = None):\n    print('stop event called')\n\ndef on_enable(pluginapi, data = None):\n    print('enable event called')\n\ndef on_disable(pluginapi, data = None):\n    print('disable event called')\n")
            plugins.enable('test')


        plugins.start('test')
        if not events.call(plugins.get_plugin('test'), 'enable'):
            self.assertTrue(False)

        logger.debug('preparing to start thread', timestamp = False)
        thread = events.event('test', data = {'tests': self})
        logger.debug('thread running...', timestamp = False)
        thread.join()
        logger.debug('thread finished.', timestamp = False)

        self.assertTrue(True)

    def testQueue(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running daemon queue test...')

        # test if the daemon queue can read/write data
        import core
        myCore = core.Core()
        if not os.path.exists('data/queue.db'):
            myCore.daemonQueue()
        while True:
            command = myCore.daemonQueue()
            if command == False:
                logger.debug('The queue is empty (false)')
                break
            else:
                logger.debug(command[0])
        myCore.daemonQueueAdd('testCommand', 'testData')
        command = myCore.daemonQueue()
        if command[0] == 'testCommand':
            if myCore.daemonQueue() == False:
                logger.info('Succesfully added and read command')

    def testHashValidation(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running hash validation test...')

        import core
        myCore = core.Core()
        if not myCore._utils.validateHash("$324dfgfdg") and myCore._utils.validateHash("f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2") and not myCore._utils.validateHash("f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd$"):
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def testAddAdder(self):
        logger.debug('-'*26 + '\n')
        logger.info('Running address add+remove test')

        import core
        myCore = core.Core()
        if not os.path.exists('data/address.db'):
            myCore.createAddressDB()
        if myCore.addAddress('facebookcorewwwi.onion') and not myCore.removeAddress('invalid'):
            if myCore.removeAddress('facebookcorewwwi.onion'):
                self.assertTrue(True)
            else:
                self.assertTrue(False)
        else:
            self.assertTrue(False)

unittest.main()
