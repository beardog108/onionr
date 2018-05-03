'''
    Onionr - P2P Microblogging Platform & Social network

    OnionrUtils offers various useful functions to Onionr. Relatively misc.
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
# Misc functions that do not fit in the main api, but are useful
import getpass, sys, requests, os, socket, hashlib, logger, sqlite3, config, binascii, time, base64, json
import nacl.signing, nacl.encoding

if sys.version_info < (3, 6):
    try:
        import sha3
    except ModuleNotFoundError:
        logger.fatal('On Python 3 versions prior to 3.6.x, you need the sha3 module')
        sys.exit(1)

class OnionrUtils:
    '''
        Various useful function
    '''
    def __init__(self, coreInstance):
        self.fingerprintFile = 'data/own-fingerprint.txt'
        self._core = coreInstance

        self.timingToken = ''

        return

    def getTimeBypassToken(self):
        try:
            if os.path.exists('data/time-bypass.txt'):
                with open('data/time-bypass.txt', 'r') as bypass:
                    self.timingToken = bypass.read()
        except Exception as error:
            logger.error('Failed to fetch time bypass token.', error=error)

    def sendPM(self, pubkey, message):
        '''
            High level function to encrypt a message to a peer and insert it as a block
        '''

        try:
            # We sign PMs here rather than in core.insertBlock in order to mask the sender's pubkey
            payload = {'sig': '', 'msg': '', 'id': self._core._crypto.pubKey}

            sign = self._core._crypto.edSign(message, self._core._crypto.privKey, encodeResult=True)
            #encrypted = self._core._crypto.pubKeyEncrypt(message, pubkey, anonymous=True, encodedData=True).decode()

            payload['sig'] = sign
            payload['msg'] = message
            payload = json.dumps(payload)
            message = payload
            encrypted = self._core._crypto.pubKeyEncrypt(message, pubkey, anonymous=True, encodedData=True).decode()


            block = self._core.insertBlock(encrypted, header='pm', sign=False)
            if block == '':
                logger.error('Could not send PM')
            else:
                logger.info('Sent PM, hash: ' + block)
        except Exception as error:
            logger.error('Failed to send PM.', error=error)

        return

    def incrementAddressSuccess(self, address):
        '''
            Increase the recorded sucesses for an address
        '''
        increment = self._core.getAddressInfo(address, 'success') + 1
        self._core.setAddressInfo(address, 'success', increment)
        return

    def decrementAddressSuccess(self, address):
        '''
            Decrease the recorded sucesses for an address
        '''
        increment = self._core.getAddressInfo(address, 'success') - 1
        self._core.setAddressInfo(address, 'success', increment)
        return

    def mergeKeys(self, newKeyList):
        '''
            Merge ed25519 key list to our database
        '''
        try:
            retVal = False
            if newKeyList != False:
                for key in newKeyList.split(','):
                    if not key in self._core.listPeers(randomOrder=False) and type(key) != None and key != self._core._crypto.pubKey:
                        if self._core.addPeer(key):
                            retVal = True
            return retVal
        except Exception as error:
            logger.error('Failed to merge keys.', error=error)
            return False


    def mergeAdders(self, newAdderList):
        '''
            Merge peer adders list to our database
        '''
        try:
            retVal = False
            if newAdderList != False:
                for adder in newAdderList.split(','):
                    if not adder in self._core.listAdders(randomOrder=False) and adder.strip() != self.getMyAddress():
                        if self._core.addAddress(adder):
                            logger.info('Added ' + adder + ' to db.', timestamp=True)
                            retVal = True
                    else:
                        logger.debug(adder + " is either our address or already in our DB")
            return retVal
        except Exception as error:
            logger.error('Failed to merge adders.', error=error)
            return False

    def getMyAddress(self):
        try:
            with open('./data/hs/hostname', 'r') as hostname:
                return hostname.read().strip()
        except Exception as error:
            logger.error('Failed to read my address.', error=error)
            return None

    def localCommand(self, command, silent = True):
        '''
            Send a command to the local http API server, securely. Intended for local clients, DO NOT USE for remote peers.
        '''

        config.reload()
        self.getTimeBypassToken()
        # TODO: URL encode parameters, just as an extra measure. May not be needed, but should be added regardless.
        try:
            retData = requests.get('http://' + open('data/host.txt', 'r').read() + ':' + str(config.get('client')['port']) + '/client/?action=' + command + '&token=' + str(config.get('client')['client_hmac']) + '&timingToken=' + self.timingToken).text
        except Exception as error:
            if not silent:
                logger.error('Failed to make local request (command: ' + str(command) + ').', error=error)
            retData = False

        return retData

    def getPassword(self, message='Enter password: ', confirm = True):
        '''
            Get a password without showing the users typing and confirm the input
        '''
        # Get a password safely with confirmation and return it
        while True:
            print(message)
            pass1 = getpass.getpass()
            if confirm:
                print('Confirm password: ')
                pass2 = getpass.getpass()
                if pass1 != pass2:
                    logger.error("Passwords do not match.")
                    logger.readline()
                else:
                    break
            else:
                break

        return pass1

    def checkPort(self, port, host=''):
        '''
            Checks if a port is available, returns bool
        '''
        # inspired by https://www.reddit.com/r/learnpython/comments/2i4qrj/how_to_write_a_python_script_that_checks_to_see/ckzarux/
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        retVal = False
        try:
            sock.bind((host, port))
        except OSError as e:
            if e.errno is 98:
                retVal = True
        finally:
            sock.close()

        return retVal

    def checkIsIP(self, ip):
        '''
            Check if a string is a valid IPv4 address
        '''
        try:
            socket.inet_aton(ip)
        except:
            return False
        else:
            return True

    def getBlockDBHash(self):
        '''
            Return a sha3_256 hash of the blocks DB
        '''
        try:
            with open(self._core.blockDB, 'rb') as data:
                data = data.read()
            hasher = hashlib.sha3_256()
            hasher.update(data)
            dataHash = hasher.hexdigest()

            return dataHash
        except Exception as error:
            logger.error('Failed to get block DB hash.', error=error)

    def hasBlock(self, hash):
        '''
            Check for new block in the list
        '''
        conn = sqlite3.connect(self._core.blockDB)
        c = conn.cursor()
        if not self.validateHash(hash):
            raise Exception("Invalid hash")
        for result in c.execute("SELECT COUNT() FROM hashes where hash='" + hash + "'"):
            if result[0] >= 1:
                conn.commit()
                conn.close()
                return True
            else:
                conn.commit()
                conn.close()
                return False

    def hasKey(self, key):
        '''
            Check for key in list of public keys
        '''
        return key in self._core.listPeers()

    def validateHash(self, data, length=64):
        '''
            Validate if a string is a valid hex formatted hash
        '''
        retVal = True
        if data == False or data == True:
            return False
        data = data.strip()
        if len(data) != length:
            retVal = False
        else:
            try:
                int(data, 16)
            except ValueError:
                retVal = False

        return retVal

    def validatePubKey(self, key):
        '''
            Validate if a string is a valid base32 encoded Ed25519 key
        '''
        retVal = False
        try:
            nacl.signing.SigningKey(seed=key, encoder=nacl.encoding.Base32Encoder)
        except nacl.exceptions.ValueError:
            pass
        except base64.binascii.Error as err:
            pass
        else:
            retVal = True
        return retVal


    def validateID(self, id):
        '''
            Validate if an address is a valid tor or i2p hidden service
        '''
        try:
            idLength = len(id)
            retVal = True
            idNoDomain = ''
            peerType = ''
            # i2p b32 addresses are 60 characters long (including .b32.i2p)
            if idLength == 60:
                peerType = 'i2p'
                if not id.endswith('.b32.i2p'):
                    retVal = False
                else:
                    idNoDomain = id.split('.b32.i2p')[0]
            # Onion v2's are 22 (including .onion), v3's are 62 with .onion
            elif idLength == 22 or idLength == 62:
                peerType = 'onion'
                if not id.endswith('.onion'):
                    retVal = False
                else:
                    idNoDomain = id.split('.onion')[0]
            else:
                retVal = False
            if retVal:
                if peerType == 'i2p':
                    try:
                        id.split('.b32.i2p')[2]
                    except:
                        pass
                    else:
                        retVal = False
                elif peerType == 'onion':
                    try:
                        id.split('.onion')[2]
                    except:
                        pass
                    else:
                        retVal = False
                if not idNoDomain.isalnum():
                    retVal = False

            return retVal
        except:
            return False

    def loadPMs(self):
        '''
            Find, decrypt, and return array of PMs (array of dictionary, {from, text})
        '''
        #blocks = self._core.getBlockList().split('\n')
        blocks = self._core.getBlocksByType('pm')
        message = ''
        sender = ''
        for i in blocks:
            if len (i) == 0:
                continue
            try:
                with open('data/blocks/' + i + '.dat', 'r') as potentialMessage:
                    data = potentialMessage.read().split('}')
                    message = data[1]
                    sigResult = ''
                    signer = ''

                    try:
                        metadata = json.loads(data[0] + '}')
                    except json.decoder.JSONDecodeError:
                        metadata = {}
                    '''
                    sigResult = self._core._crypto.edVerify(message, signer, sig, encodedData=True)
                    #sigResult = False
                    if sigResult != False:
                        sigResult = 'Valid signature by ' + signer
                    else:
                        sigResult = 'Invalid signature by ' + signer
                    '''

                    try:
                        message = self._core._crypto.pubKeyDecrypt(message, encodedData=True, anonymous=True)
                    except nacl.exceptions.CryptoError as e:
                        logger.error('Unable to decrypt ' + i, error=e)
                    else:
                        try:
                            message = json.loads(message.decode())
                            message['msg']
                            message['id']
                            message['sig']
                        except json.decoder.JSONDecodeError:
                            logger.error('Could not decode PM JSON')
                        except KeyError:
                            logger.error('PM is missing JSON keys')
                        else:
                            if self.validatePubKey(message['id']):
                                sigResult = self._core._crypto.edVerify(message['msg'], message['id'], message['sig'], encodedData=True)
                                logger.info('-----------------------------------')
                                logger.info('Recieved message: ' + message['msg'])
                                if sigResult:
                                    logger.info('Valid signature by ' + message['id'])
                                else:
                                    logger.warn('Invalid signature by ' + message['id'])

            except FileNotFoundError:
                pass
            except Exception as error:
                logger.error('Failed to open block ' + str(i) + '.', error=error)
        return

    def getPeerByHashId(self, hash):
        '''
            Return the pubkey of the user if known from the hash
        '''
        if self._core._crypto.pubKeyHashID() == hash:
            retData = self._core._crypto.pubKey
            return retData
        conn = sqlite3.connect(self._core.peerDB)
        c = conn.cursor()
        command = (hash,)
        retData = ''
        for row in c.execute('SELECT ID FROM peers where hashID=?', command):
            if row[0] != '':
                retData = row[0]
        return retData

    def isCommunicatorRunning(self, timeout = 5, interval = 0.1):
        try:
            runcheck_file = 'data/.runcheck'

            if os.path.isfile(runcheck_file):
                os.remove(runcheck_file)
                logger.debug('%s file appears to have existed before the run check.' % runcheck_file, timestamp = False)

            self._core.daemonQueueAdd('runCheck')
            starttime = time.time()

            while True:
                time.sleep(interval)
                if os.path.isfile(runcheck_file):
                    os.remove(runcheck_file)

                    return True
                elif time.time() - starttime >= timeout:
                    return False
        except:
            return False

    def token(self, size = 32):
        return binascii.hexlify(os.urandom(size))
