'''
    Onionr - P2P Microblogging Platform & Social network

    Core Onionr library, useful for external programs. Handles peer & data processing
'''
'''
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
import sqlite3, os, sys, time, math, base64, tarfile, getpass, simplecrypt, hashlib, nacl, logger, json, netcontroller, math, config
#from Crypto.Cipher import AES
#from Crypto import Random

import onionrutils, onionrcrypto, onionrproofs, onionrevents as events

if sys.version_info < (3, 6):
    try:
        import sha3
    except ModuleNotFoundError:
        logger.fatal('On Python 3 versions prior to 3.6.x, you need the sha3 module')
        sys.exit(1)

class Core:
    def __init__(self):
        '''
            Initialize Core Onionr library
        '''
        try:
            self.queueDB = 'data/queue.db'
            self.peerDB = 'data/peers.db'
            self.blockDB = 'data/blocks.db'
            self.blockDataLocation = 'data/blocks/'
            self.addressDB = 'data/address.db'
            self.hsAdder = ''

            self.bootstrapFileLocation = 'static-data/bootstrap-nodes.txt'
            self.bootstrapList = []

            if not os.path.exists('data/'):
                os.mkdir('data/')
            if not os.path.exists('data/blocks/'):
                os.mkdir('data/blocks/')
            if not os.path.exists(self.blockDB):
                self.createBlockDB()

            if os.path.exists('data/hs/hostname'):
                with open('data/hs/hostname', 'r') as hs:
                    self.hsAdder = hs.read()

            # Load bootstrap address list
            if os.path.exists(self.bootstrapFileLocation):
                with open(self.bootstrapFileLocation, 'r') as bootstrap:
                    bootstrap = bootstrap.read()
                for i in bootstrap.split('\n'):
                    self.bootstrapList.append(i)
            else:
                logger.warn('Warning: address bootstrap file not found ' + self.bootstrapFileLocation)

            self._utils = onionrutils.OnionrUtils(self)
            # Initialize the crypto object
            self._crypto = onionrcrypto.OnionrCrypto(self)

        except Exception as error:
            logger.error('Failed to initialize core Onionr library.', error=error)
            logger.fatal('Cannot recover from error.')
            sys.exit(1)
        return

    def addPeer(self, peerID, powID, name=''):
        '''
            Adds a public key to the key database (misleading function name)
        '''
        # This function simply adds a peer to the DB
        if not self._utils.validatePubKey(peerID):
            return False
        if sys.getsizeof(powID) > 120:
            logger.warn("POW token for pubkey base64 representation exceeded 120 bytes, is " + str(sys.getsizeof(powID)))
            return False

        conn = sqlite3.connect(self.peerDB)
        hashID = self._crypto.pubKeyHashID(peerID)
        c = conn.cursor()
        t = (peerID, name, 'unknown', hashID, powID)

        for i in c.execute("SELECT * FROM PEERS where id = '" + peerID + "';"):
            try:
                if i[0] == peerID:
                    conn.close()
                    return False
            except ValueError:
                pass
            except IndexError:
                pass
        c.execute('INSERT INTO peers (id, name, dateSeen, pow, hashID) VALUES(?, ?, ?, ?, ?);', t)
        conn.commit()
        conn.close()

        return True

    def addAddress(self, address):
        '''
            Add an address to the address database (only tor currently)
        '''
        if address == config.get('i2p')['ownAddr']:
            return False
        if self._utils.validateID(address):
            conn = sqlite3.connect(self.addressDB)
            c = conn.cursor()
            # check if address is in database
            # this is safe to do because the address is validated above, but we strip some chars here too just in case
            address = address.replace('\'', '').replace(';', '').replace('"', '').replace('\\', '')
            for i in c.execute("SELECT * FROM adders where address = '" + address + "';"):
                try:
                    if i[0] == address:
                        logger.warn('Not adding existing address')
                        conn.close()
                        return False
                except ValueError:
                    pass
                except IndexError:
                    pass

            t = (address, 1)
            c.execute('INSERT INTO adders (address, type) VALUES(?, ?);', t)
            conn.commit()
            conn.close()

            events.event('address_add', data = {'address': address}, onionr = None)

            return True
        else:
            return False

    def removeAddress(self, address):
        '''
            Remove an address from the address database
        '''
        if self._utils.validateID(address):
            conn = sqlite3.connect(self.addressDB)
            c = conn.cursor()
            t = (address,)
            c.execute('Delete from adders where address=?;', t)
            conn.commit()
            conn.close()

            events.event('address_remove', data = {'address': address}, onionr = None)

            return True
        else:
            return False

    def removeBlock(self, block):
        '''
            remove a block from this node
        '''
        if self._utils.validateHash(block):
            conn = sqlite3.connect(self.blockDB)
            c = conn.cursor()
            t = (block,)
            c.execute('Delete from hashes where hash=?;', t)
            conn.commit()
            conn.close()
            try:
                os.remove('data/blocks/' + block + '.dat')
            except FileNotFoundError:
                pass

    def createAddressDB(self):
        '''
            Generate the address database

            types:
                1: I2P b32 address
                2: Tor v2 (like facebookcorewwwi.onion)
                3: Tor v3
        '''
        conn = sqlite3.connect(self.addressDB)
        c = conn.cursor()
        c.execute('''CREATE TABLE adders(
            address text,
            type int,
            knownPeer text,
            speed int,
            success int,
            DBHash text,
            failure int,
            lastConnect int
            );
        ''')
        conn.commit()
        conn.close()

    def createPeerDB(self):
        '''
            Generate the peer sqlite3 database and populate it with the peers table.
        '''
        # generate the peer database
        conn = sqlite3.connect(self.peerDB)
        c = conn.cursor()
        c.execute('''CREATE TABLE peers(
            ID text not null,
            name text,
            adders text,
            blockDBHash text,
            forwardKey text,
            dateSeen not null,
            bytesStored int,
            trust int,
            pubkeyExchanged int,
            hashID text,
            pow text not null);
        ''')
        conn.commit()
        conn.close()
        return

    def createBlockDB(self):
        '''
            Create a database for blocks

            hash         - the hash of a block
            dateReceived - the date the block was recieved, not necessarily when it was created
            decrypted    - if we can successfully decrypt the block (does not describe its current state)
            dataType     - data type of the block
            dataFound    - if the data has been found for the block
            dataSaved    - if the data has been saved for the block
            sig    - optional signature by the author (not optional if author is specified)
            author       - multi-round partial sha3-256 hash of authors public key
        '''
        if os.path.exists(self.blockDB):
            raise Exception("Block database already exists")
        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        c.execute('''CREATE TABLE hashes(
            hash text not null,
            dateReceived int,
            decrypted int,
            dataType text,
            dataFound int,
            dataSaved int,
            sig text,
            author text
            );
        ''')
        conn.commit()
        conn.close()

        return

    def addToBlockDB(self, newHash, selfInsert=False, dataSaved=False):
        '''
            Add a hash value to the block db

            Should be in hex format!
        '''
        if not os.path.exists(self.blockDB):
            raise Exception('Block db does not exist')
        if self._utils.hasBlock(newHash):
            return
        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        currentTime = self._utils.getEpoch()
        if selfInsert or dataSaved:
            selfInsert = 1
        else:
            selfInsert = 0
        data = (newHash, currentTime, '', selfInsert)
        c.execute('INSERT INTO hashes (hash, dateReceived, dataType, dataSaved) VALUES(?, ?, ?, ?);', data)
        conn.commit()
        conn.close()

        return

    def getData(self, hash):
        '''
            Simply return the data associated to a hash
        '''
        try:
            # logger.debug('Opening %s' % (str(self.blockDataLocation) + str(hash) + '.dat'))
            dataFile = open(self.blockDataLocation + hash + '.dat', 'rb')
            data = dataFile.read()
            dataFile.close()
        except FileNotFoundError:
            data = False

        return data

    def setData(self, data):
        '''
            Set the data assciated with a hash
        '''
        data = data
        hasher = hashlib.sha3_256()
        if not type(data) is bytes:
            data = data.encode()
        hasher.update(data)
        dataHash = hasher.hexdigest()
        if type(dataHash) is bytes:
            dataHash = dataHash.decode()
        blockFileName = self.blockDataLocation + dataHash + '.dat'
        if os.path.exists(blockFileName):
            pass # TODO: properly check if block is already saved elsewhere
            #raise Exception("Data is already set for " + dataHash)
        else:
            blockFile = open(blockFileName, 'wb')
            blockFile.write(data)
            blockFile.close()

        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        c.execute("UPDATE hashes SET dataSaved=1 WHERE hash = '" + dataHash + "';")
        conn.commit()
        conn.close()

        return dataHash

    def dataDirEncrypt(self, password):
        '''
            Encrypt the data directory on Onionr shutdown
        '''
        if os.path.exists('data.tar'):
            os.remove('data.tar')
        tar = tarfile.open("data.tar", "w")
        for name in ['data']:
            tar.add(name)
        tar.close()
        tarData = open('data.tar', 'r',  encoding = "ISO-8859-1").read()
        encrypted = simplecrypt.encrypt(password, tarData)
        open('data-encrypted.dat', 'wb').write(encrypted)
        os.remove('data.tar')

        return

    def dataDirDecrypt(self, password):
        '''
            Decrypt the data directory on startup
        '''
        if not os.path.exists('data-encrypted.dat'):
            return (False, 'encrypted archive does not exist')
        data = open('data-encrypted.dat', 'rb').read()
        try:
            decrypted = simplecrypt.decrypt(password, data)
        except simplecrypt.DecryptionException:
            return (False, 'wrong password (or corrupted archive)')
        else:
            open('data.tar', 'wb').write(decrypted)
            tar = tarfile.open('data.tar')
            tar.extractall()
            tar.close()

        return (True, '')

    def daemonQueue(self):
        '''
            Gives commands to the communication proccess/daemon by reading an sqlite3 database

            This function intended to be used by the client. Queue to exchange data between "client" and server.
        '''
        retData = False
        if not os.path.exists(self.queueDB):
            conn = sqlite3.connect(self.queueDB)
            c = conn.cursor()
            # Create table
            c.execute('''CREATE TABLE commands
                        (id integer primary key autoincrement, command text, data text, date text)''')
            conn.commit()
        else:
            conn = sqlite3.connect(self.queueDB)
            c = conn.cursor()
            for row in c.execute('SELECT command, data, date, min(ID) FROM commands group by id'):
                retData = row
                break
            if retData != False:
                c.execute('DELETE FROM commands WHERE id=?;', (retData[3],))
        conn.commit()
        conn.close()

        events.event('queue_pop', data = {'data': retData}, onionr = None)

        return retData

    def daemonQueueAdd(self, command, data=''):
        '''
            Add a command to the daemon queue, used by the communication daemon (communicator.py)
        '''
        # Intended to be used by the web server
        date = self._utils.getEpoch()
        conn = sqlite3.connect(self.queueDB)
        c = conn.cursor()
        t = (command, data, date)
        c.execute('INSERT INTO commands (command, data, date) VALUES(?, ?, ?)', t)
        conn.commit()
        conn.close()

        events.event('queue_push', data = {'command': command, 'data': data}, onionr = None)

        return

    def clearDaemonQueue(self):
        '''
            Clear the daemon queue (somewhat dangerous)
        '''
        conn = sqlite3.connect(self.queueDB)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM commands;')
            conn.commit()
        except:
            pass
        conn.close()
        events.event('queue_clear', onionr = None)

        return

    def listAdders(self, randomOrder=True, i2p=True):
        '''
            Return a list of addresses
        '''
        conn = sqlite3.connect(self.addressDB)
        c = conn.cursor()
        if randomOrder:
            addresses = c.execute('SELECT * FROM adders ORDER BY RANDOM();')
        else:
            addresses = c.execute('SELECT * FROM adders;')
        addressList = []
        for i in addresses:
            addressList.append(i[0])
        conn.close()
        return addressList

    def listPeers(self, randomOrder=True, getPow=False):
        '''
            Return a list of public keys (misleading function name)

            randomOrder determines if the list should be in a random order
        '''
        conn = sqlite3.connect(self.peerDB)
        c = conn.cursor()
        payload = ""
        if randomOrder:
            payload = 'SELECT * FROM peers ORDER BY RANDOM();'
        else:
            payload = 'SELECT * FROM peers;'
        peerList = []
        for i in c.execute(payload):
            try:
                if len(i[0]) != 0:
                    if getPow:
                        peerList.append(i[0] + '-' + i[1])
                    else:
                        peerList.append(i[0])
            except TypeError:
                pass
        if getPow:
            try:
                peerList.append(self._crypto.pubKey + '-' + self._crypto.pubKeyPowToken)
            except TypeError:
                pass
        else:
            peerList.append(self._crypto.pubKey)
        conn.close()
        return peerList

    def getPeerInfo(self, peer, info):
        '''
            Get info about a peer from their database entry

            id text             0
            name text,          1
            adders text,        2
            forwardKey text,    3
            dateSeen not null,  4
            bytesStored int,    5
            trust int           6
            pubkeyExchanged int 7
            hashID text         8
        '''
        conn = sqlite3.connect(self.peerDB)
        c = conn.cursor()
        command = (peer,)
        infoNumbers = {'id': 0, 'name': 1, 'adders': 2, 'forwardKey': 3, 'dateSeen': 4, 'bytesStored': 5, 'trust': 6, 'pubkeyExchanged': 7, 'hashID': 8}
        info = infoNumbers[info]
        iterCount = 0
        retVal = ''
        for row in c.execute('SELECT * from peers where id=?;', command):
            for i in row:
                if iterCount == info:
                    retVal = i
                    break
                else:
                    iterCount += 1
        conn.close()

        return retVal

    def setPeerInfo(self, peer, key, data):
        '''
            Update a peer for a key
        '''
        conn = sqlite3.connect(self.peerDB)
        c = conn.cursor()
        command = (data, peer)
        # TODO: validate key on whitelist
        if key not in ('id', 'name', 'pubkey', 'blockDBHash', 'forwardKey', 'dateSeen', 'bytesStored', 'trust'):
            raise Exception("Got invalid database key when setting peer info")
        c.execute('UPDATE peers SET ' + key + ' = ? WHERE id=?', command)
        conn.commit()
        conn.close()
        return

    def getAddressInfo(self, address, info):
        '''
            Get info about an address from its database entry

            address text, 0
            type int, 1
            knownPeer text, 2
            speed int, 3
            success int, 4
            DBHash text, 5
            failure int 6
            lastConnect 7
        '''
        conn = sqlite3.connect(self.addressDB)
        c = conn.cursor()
        command = (address,)
        infoNumbers = {'address': 0, 'type': 1, 'knownPeer': 2, 'speed': 3, 'success': 4, 'DBHash': 5, 'failure': 6, 'lastConnect': 7}
        info = infoNumbers[info]
        iterCount = 0
        retVal = ''
        for row in c.execute('SELECT * from adders where address=?;', command):
            for i in row:
                if iterCount == info:
                    retVal = i
                    break
                else:
                    iterCount += 1
        conn.close()
        return retVal

    def setAddressInfo(self, address, key, data):
        '''
            Update an address for a key
        '''
        conn = sqlite3.connect(self.addressDB)
        c = conn.cursor()
        command = (data, address)
        # TODO: validate key on whitelist
        if key not in ('address', 'type', 'knownPeer', 'speed', 'success', 'DBHash', 'failure', 'lastConnect'):
            raise Exception("Got invalid database key when setting address info")
        c.execute('UPDATE adders SET ' + key + ' = ? WHERE address=?', command)
        conn.commit()
        conn.close()
        return

    def handle_direct_connection(self, data):
        '''
            Handles direct messages
        '''
        try:
            data = json.loads(data)

            # TODO: Determine the sender, verify, etc
            if ('callback' in data) and (data['callback'] is True):
                # then this is a response to the message we sent earlier
                self.daemonQueueAdd('checkCallbacks', json.dumps(data))
            else:
                # then we should handle it and respond accordingly
                self.daemonQueueAdd('incomingDirectConnection', json.dumps(data))
        except Exception as e:
            logger.warn('Failed to handle incoming direct message: %s' % str(e))

        return

    def getBlockList(self, unsaved = False): # TODO: Use unsaved
        '''
            Get list of our blocks
        '''
        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        if unsaved:
            execute = 'SELECT hash FROM hashes WHERE dataSaved != 1 ORDER BY RANDOM();'
        else:
            execute = 'SELECT hash FROM hashes ORDER BY RANDOM();'
        rows = list()
        for row in c.execute(execute):
            for i in row:
                rows.append(i)

        return rows

    def getBlockDate(self, blockHash):
        '''
            Returns the date a block was received
        '''
        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        execute = 'SELECT dateReceived FROM hashes WHERE hash=?;'
        args = (blockHash,)
        for row in c.execute(execute, args):
            for i in row:
                return int(i)

        return None

    def getBlocksByType(self, blockType):
        '''
            Returns a list of blocks by the type
        '''
        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        execute = 'SELECT hash FROM hashes WHERE dataType=?;'
        args = (blockType,)
        rows = list()
        for row in c.execute(execute, args):
            for i in row:
                rows.append(i)

        return rows

    def setBlockType(self, hash, blockType):
        '''
            Sets the type of block
        '''

        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        c.execute("UPDATE hashes SET dataType='" + blockType + "' WHERE hash = '" + hash + "';")
        conn.commit()
        conn.close()
        return

    def updateBlockInfo(self, hash, key, data):
        '''
            sets info associated with a block
        '''

        if key not in ('dateReceived', 'decrypted', 'dataType', 'dataFound', 'dataSaved', 'sig', 'author'):
            return False

        conn = sqlite3.connect(self.blockDB)
        c = conn.cursor()
        args = (data, hash)
        c.execute("UPDATE hashes SET " + key + " = ? where hash = ?;", args)
        conn.commit()
        conn.close()
        return True

    def insertBlock(self, data, header='txt', sign=False):
        '''
            Inserts a block into the network
        '''

        powProof = onionrproofs.POW(data)
        powToken = ''
        # wait for proof to complete
        try:
            while True:
                powToken = powProof.getResult()
                if powToken == False:
                    time.sleep(0.3)
                    continue
                powHash = powToken[0]
                powToken = base64.b64encode(powToken[1])
                try:
                    powToken = powToken.decode()
                except AttributeError:
                    pass
                finally:
                    break
        except KeyboardInterrupt:
            logger.warn("Got keyboard interrupt while working on inserting block, stopping.")
            powProof.shutdown()
            return ''

        try:
            data.decode()
        except AttributeError:
            data = data.encode()

        retData = ''
        metadata = {'type': header, 'powHash': powHash, 'powToken': powToken}
        sig = {}

        metadata = json.dumps(metadata)
        metadata = metadata.encode()
        signature = ''

        if sign:
            signature = self._crypto.edSign(metadata + b'\n' + data, self._crypto.privKey, encodeResult=True)
            ourID = self._crypto.pubKeyHashID()
            # Convert from bytes on some py versions?
            try:
                ourID = ourID.decode()
            except AttributeError:
                pass
        metadata = {'sig': signature, 'meta': metadata.decode()}
        metadata = json.dumps(metadata)
        metadata = metadata.encode()

        if len(data) == 0:
            logger.error('Will not insert empty block')
        else:
            addedHash = self.setData(metadata + b'\n' + data)
            self.addToBlockDB(addedHash, selfInsert=True)
            self.setBlockType(addedHash, header)
            retData = addedHash
        return retData

    def introduceNode(self):
        '''
            Introduces our node into the network by telling X many nodes our HS address
        '''

        if(self._utils.isCommunicatorRunning()):
            announceAmount = 2
            nodeList = self.listAdders()

            if len(nodeList) == 0:
                for i in self.bootstrapList:
                    if self._utils.validateID(i):
                        self.addAddress(i)
                        nodeList.append(i)

            if announceAmount > len(nodeList):
                announceAmount = len(nodeList)

            for i in range(announceAmount):
                self.daemonQueueAdd('announceNode', nodeList[i])

            events.event('introduction', onionr = None)

            return True
        else:
            logger.error('Onionr daemon is not running.')
            return False

        return
