#!/usr/bin/env python3
'''
    Onionr - P2P Microblogging Platform & Social network.

    This file contains both the OnionrCommunicate class for communcating with peers
    and code to operate as a daemon, getting commands from the command queue database (see core.Core.daemonQueue)
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
import sqlite3, requests, hmac, hashlib, time, sys, os, math, logger, urllib.parse, base64, binascii, random, json, threading
import core, onionrutils, onionrcrypto, netcontroller, onionrproofs, config, onionrplugins as plugins

class OnionrCommunicate:
    def __init__(self, debug, developmentMode):
        '''
            OnionrCommunicate

            This class handles communication with nodes in the Onionr network.
        '''

        self._core = core.Core()
        self._utils = onionrutils.OnionrUtils(self._core)
        self._crypto = onionrcrypto.OnionrCrypto(self._core)
        self._netController = netcontroller.NetController(0) # arg is the HS port but not needed rn in this file

        self.newHashes = {} # use this to not keep hashes around too long if we cant get their data
        self.keepNewHash = 12
        self.ignoredHashes = []

        self.highFailureAmount = 7

        self.communicatorThreads = 0
        self.maxThreads = 75
        self.processBlocksThreads = 0
        self.lookupBlocksThreads = 0

        self.blocksProcessing = [] # list of blocks currently processing, to avoid trying a block twice at once in 2 seperate threads
        self.peerStatus = {} # network actions (active requests) for peers used mainly to prevent conflicting actions in threads

        self.communicatorTimers = {} # communicator timers, name: rate (in seconds)
        self.communicatorTimerCounts = {}
        self.communicatorTimerFuncs = {}

        self.registerTimer('blockProcess', 20)
        self.registerTimer('highFailure', 10)
        self.registerTimer('heartBeat', 10)
        self.registerTimer('pex', 120)
        logger.debug('Communicator debugging enabled.')

        with open('data/hs/hostname', 'r') as torID:
            todID = torID.read()

        apiRunningCheckRate = 10
        apiRunningCheckCount = 0

        self.peerData = {} # Session data for peers (recent reachability, speed, etc)

        if os.path.exists(self._core.queueDB):
            self._core.clearDaemonQueue()

        # Loads in and starts the enabled plugins
        plugins.reload()

        while True:
            command = self._core.daemonQueue()
            # Process blocks based on a timer
            self.timerTick() 
            # TODO: migrate below if statements to be own functions which are called in the above timerTick() function
            if self.communicatorTimers['highFailure'] == self.communicatorTimerCounts['highFailure']:
                self.communicatorTimerCounts['highFailure'] = 0
                for i in self.peerData:
                    if self.peerData[i]['failCount'] >= self.highFailureAmount:
                        self.peerData[i]['failCount'] -= 1
            if self.communicatorTimers['pex'] == self.communicatorTimerCounts['pex']:
                pT1 = threading.Thread(target=self.getNewPeers, name="pT1")
                pT1.start()
                pT2 = threading.Thread(target=self.getNewPeers, name="pT2")
                pT2.start()
                self.communicatorTimerCounts['pex'] = 0# TODO: do not reset timer if low peer count
            if self.communicatorTimers['heartBeat'] == self.communicatorTimerCounts['heartBeat']:
                logger.debug('Communicator heartbeat')
                self.communicatorTimerCounts['heartBeat'] = 0
            if self.communicatorTimers['blockProcess'] == self.communicatorTimerCounts['blockProcess']:
                lT1 = threading.Thread(target=self.lookupBlocks, name="lt1", args=(True,))
                lT2 = threading.Thread(target=self.lookupBlocks, name="lt2", args=(True,))
                lT3 = threading.Thread(target=self.lookupBlocks, name="lt3", args=(True,))
                lT4 = threading.Thread(target=self.lookupBlocks, name="lt4", args=(True,))
                pbT1 = threading.Thread(target=self.processBlocks, name='pbT1', args=(True,))
                pbT2 = threading.Thread(target=self.processBlocks, name='pbT2', args=(True,))
                pbT3 = threading.Thread(target=self.processBlocks, name='pbT3', args=(True,))
                pbT4 = threading.Thread(target=self.processBlocks, name='pbT4', args=(True,))
                if (self.maxThreads - 8) >= threading.active_count():
                    lT1.start()
                    lT2.start()
                    lT3.start()
                    lT4.start()
                    pbT1.start()
                    pbT2.start()
                    pbT3.start()
                    pbT4.start()
                    self.communicatorTimerCounts['blockProcess'] = 0
                else:
                    logger.debug(threading.active_count())
                    logger.debug('Too many threads.')
            if command != False:
                if command[0] == 'shutdown':
                    logger.info('Daemon received exit command.', timestamp=True)
                    break
                elif command[0] == 'announceNode':
                    announceAttempts = 3
                    announceAttemptCount = 0
                    announceVal = False
                    logger.info('Announcing node to ' + command[1], timestamp=True)
                    while not announceVal:
                        announceAttemptCount += 1
                        announceVal = self.performGet('announce', command[1], data=self._core.hsAdder.replace('\n', ''), skipHighFailureAddress=True)
                        logger.info(announceVal)
                        if announceAttemptCount >= announceAttempts:
                            logger.warn('Unable to announce to ' + command[1])
                            break
                elif command[0] == 'runCheck':
                    logger.info('Status check; looks good.')
                    open('data/.runcheck', 'w+').close()
                elif command[0] == 'kex':
                    self.pexCount = pexTimer - 1
                elif command[0] == 'event':
                    # todo
                    pass
                elif command[0] == 'checkCallbacks':
                    try:
                        data = json.loads(command[1])

                        logger.info('Checking for callbacks with connection %s...' % data['id'])

                        self.check_callbacks(data, config.get('dc_execcallbacks', True))

                        events.event('incoming_direct_connection', data = {'callback' : True, 'communicator' : self, 'data' : data})
                    except Exception as e:
                        logger.error('Failed to interpret callbacks for checking', e)
                elif command[0] == 'incomingDirectConnection':
                    try:
                        data = json.loads(command[1])

                        logger.info('Handling incoming connection %s...' % data['id'])

                        self.incoming_direct_connection(data)

                        events.event('incoming_direct_connection', data = {'callback' : False, 'communicator' : self, 'data' : data})
                    except Exception as e:
                        logger.error('Failed to handle callbacks for checking', e)

            apiRunningCheckCount += 1

            # check if local API is up
            if apiRunningCheckCount > apiRunningCheckRate:
                if self._core._utils.localCommand('ping') != 'pong':
                    for i in range(4):
                        if self._utils.localCommand('ping') == 'pong':
                            apiRunningCheckCount = 0
                            break # break for loop
                        time.sleep(1)
                    else:
                        # This executes if the api is NOT detected to be running
                        logger.error('Daemon detected API crash (or otherwise unable to reach API after long time), stopping...')
                        break # break main daemon loop
                apiRunningCheckCount = 0

            time.sleep(1)

        self._netController.killTor()
        return

    future_callbacks = {}
    connection_handlers = {}
    id_peer_cache = {}

    def registerTimer(self, timerName, rate, timerFunc=None):
        '''Register a communicator timer'''
        self.communicatorTimers[timerName] = rate
        self.communicatorTimerCounts[timerName] = 0
        self.communicatorTimerFuncs[timerName] = timerFunc
    
    def timerTick(self):
        '''Increments timers "ticks" and calls funcs if applicable'''
        tName = ''
        for i in self.communicatorTimers.items():
            tName = i[0]
            self.communicatorTimerCounts[tName] += 1

            if self.communicatorTimerCounts[tName] == self.communicatorTimers[tName]:
                try:
                    self.communicatorTimerFuncs[tName]()
                except TypeError:
                    pass
                else:
                    self.communicatorTimerCounts[tName] = 0


    def get_connection_handlers(self, name = None):
        '''
            Returns a list of callback handlers by name, or, if name is None, it returns all handlers.
        '''

        if name is None:
            return self.connection_handlers
        elif name in self.connection_handlers:
            return self.connection_handlers[name]
        else:
            return list()

    def add_connection_handler(self, name, handler):
        '''
            Adds a function to be called when an connection that is NOT a callback is received.
            Takes in the name of the communication type and the handler as input
        '''

        if not name in self.connection_handlers:
            self.connection_handlers[name] = list()

        self.connection_handlers[name].append(handler)

        return

    def remove_connection_handler(self, name, handler = None):
        '''
            Removes a connection handler if specified, or removes all by name
        '''

        if handler is None:
            if name in self.connection_handlers:
                self.connection_handlers[name].remove(handler)
        elif name in self.connection_handlers:
            del self.connection_handlers[name]

        return


    def set_callback(self, identifier, callback):
        '''
            (Over)writes a callback by communication identifier
        '''

        if not callback is None:
            self.future_callbacks[identifier] = callback
            return True

        return False

    def unset_callback(self, identifier):
        '''
            Unsets a callback by communication identifier, if set
        '''

        if identifier in future_callbacks:
            del self.future_callbacks[identifier]
            return True

        return False

    def get_callback(self, identifier):
        '''
            Returns a callback by communication identifier if set, or None
        '''

        if identifier in self.future_callbacks:
            return self.future_callbacks[id]

        return None

    def direct_connect(self, peer, data = None, callback = None, log = True):
        '''
            Communicates something directly with the client

            - `peer` should obviously be the peer id to request.
            - `data` should be a dict (NOT str), with the parameter "type"
              ex. {'type': 'sendMessage', 'content': 'hey, this is a dm'}
              In that dict, the key 'token' must NEVER be set. If it is, it will
              be overwritten.
            - if `callback` is set to a function, it will call that function
              back if/when the client the request is sent to decides to respond.
              Do NOT depend on a response, because users can configure their
              clients not to respond to this type of request.
            - `log` is set to True by default-- what this does is log the
              request for debug purposes. Should be False for sensitive actions.
        '''

        # TODO: Timing attack prevention
        try:
            # does not need to be secure random, only used for keeping track of async responses
            # Actually, on second thought, it does need to be secure random. Otherwise, if it is predictable, someone could trigger arbitrary callbacks that have been saved on the local node, wrecking all kinds of havoc. Better just to keep it secure random.
            identifier = self._utils.token(32)
            if 'id' in data:
                identifier = data['id']

            if not identifier in id_peer_cache:
                id_peer_cache[identifier] = peer

            if type(data) == str:
                # if someone inputs a string instead of a dict, it will assume it's the type
                data = {'type' : data}

            data['id'] = identifier
            data['token'] = '' # later put PoW stuff here or whatever is needed
            data_str = json.dumps(data)

            events.event('outgoing_direct_connection', data = {'callback' : True, 'communicator' : self, 'data' : data, 'id' : identifier, 'token' : token, 'peer' : peer, 'callback' : callback, 'log' : log})

            logger.debug('Direct connection (identifier: "%s"): %s' % (identifier, data_str))
            try:
                self.performGet('directMessage', peer, data_str)
            except:
                logger.warn('Failed to connect to peer: "%s".' % str(peer))
                return False

            if not callback is None:
                self.set_callback(identifier, callback)

            return True
        except Exception as e:
            logger.warn('Unknown error, failed to execute direct connect (peer: "%s").' % str(peer), e)

        return False

    def direct_connect_response(self, identifier, data, peer = None, callback = None, log = True):
        '''
            Responds to a previous connection. Hostname will be pulled from id_peer_cache if not specified in `peer` parameter.

            If yet another callback is requested, it can be put in the `callback` parameter.
        '''

        if config.get('dc_response', True):
            data['id'] = identifier
            data['sender'] = open('data/hs/hostname').read()
            data['callback'] = True

            if (origin is None) and (identifier in id_peer_cache):
                origin = id_peer_cache[identifier]

            if not identifier in id_peer_cache:
                id_peer_cache[identifier] = peer

            if origin is None:
                logger.warn('Failed to identify peer for connection %s' % str(identifier))
                return False
            else:
                return self.direct_connect(peer, data = data, callback = callback, log = log)
        else:
            logger.warn('Node tried to respond to direct connection id %s, but it was rejected due to `dc_response` restriction.' % str(identifier))
            return False


    def check_callbacks(self, data, execute = True, remove = True):
        '''
            Check if a callback is set, and if so, execute it
        '''

        try:
            if type(data) is str:
                data = json.loads(data)

            if 'id' in data: # TODO: prevent enumeration, require extra PoW
                identifier = data['id']

                if identifier in self.future_callbacks:
                    if execute:
                        self.get_callback(identifier)(data)
                        logger.debug('Request callback "%s" executed.' % str(identifier))
                    if remove:
                        self.unset_callback(identifier)

                    return True

                logger.warn('Unable to find request callback for ID "%s".' % str(identifier))
            else:
                logger.warn('Unable to identify callback request, `id` parameter missing: %s' % json.dumps(data))
        except Exception as e:
            logger.warn('Unknown error, failed to execute direct connection callback (peer: "%s").' % str(peer), e)

        return False

    def incoming_direct_connection(self, data):
        '''
            This code is run whenever there is a new incoming connection.
        '''

        if 'type' in data and data['type'] in self.connection_handlers:
            for handler in self.get_connection_handlers(name):
                handler(data)

        return

    def getNewPeers(self):
        '''
            Get new peers and ed25519 keys
        '''

        peersCheck = 1 # Amount of peers to ask for new peers + keys
        peersChecked = 0
        peerList = list(self._core.listAdders()) # random ordered list of peers
        newKeys = []
        newAdders = []
        if len(peerList) > 0:
            maxN = len(peerList) - 1
        else:
            peersCheck = 0
            maxN = 0

        if len(peerList) > peersCheck:
            peersCheck = len(peerList)

        while peersCheck > peersChecked:
            #i = secrets.randbelow(maxN) # cant use prior to 3.6
            i = random.randint(0, maxN)

            try:
                if self.peerStatusTaken(peerList[i], 'pex') or self.peerStatusTaken(peerList[i], 'kex'):
                    continue
            except IndexError:
                pass

            logger.info('Using %s to find new peers...' % peerList[i], timestamp=True)

            try:
                newAdders = self.performGet('pex', peerList[i], skipHighFailureAddress=True)
                if not newAdders is False: # keep the is False thing in there, it might not be bool
                    logger.debug('Attempting to merge address: %s' % str(newAdders))
                    self._utils.mergeAdders(newAdders)
            except requests.exceptions.ConnectionError:
                logger.info('%s connection failed' % peerList[i], timestamp=True)
                continue
            else:
                try:
                    logger.info('Using %s to find new keys...' % peerList[i])
                    newKeys = self.performGet('kex', peerList[i], skipHighFailureAddress=True)
                    logger.debug('Attempting to merge pubkey: %s' % str(newKeys))
                    # TODO: Require keys to come with POW token (very large amount of POW)
                    self._utils.mergeKeys(newKeys)
                except requests.exceptions.ConnectionError:
                    logger.info('%s connection failed' % peerList[i], timestamp=True)
                    continue
                else:
                    peersChecked += 1
        return

    def lookupBlocks(self, isThread=False):
        '''
            Lookup blocks and merge new ones
        '''
        if isThread:
            self.lookupBlocksThreads += 1
        peerList = self._core.listAdders()
        blockList = list()

        for i in peerList:
            if self.peerStatusTaken(i, 'getBlockHashes') or self.peerStatusTaken(i, 'getDBHash'):
                continue
            try:
                if self.peerData[i]['failCount'] >= self.highFailureAmount:
                    continue
            except KeyError:
                pass

            lastDB = self._core.getAddressInfo(i, 'DBHash')

            if lastDB == None:
                logger.debug('Fetching hash from %s, no previous known.' % str(i))
            else:
                logger.debug('Fetching hash from %s, %s last known' % (str(i), str(lastDB)))

            currentDB = self.performGet('getDBHash', i)

            if currentDB != False:
                logger.debug('%s hash db (from request): %s' % (str(i), str(currentDB)))
            else:
                logger.warn('Failed to get hash db status for %s' % str(i))

            if currentDB != False:
                if lastDB != currentDB:
                    logger.debug('Fetching hash from %s - %s current hash.' % (str(i), currentDB))
                    try:
                        blockList.append(self.performGet('getBlockHashes', i))
                    except TypeError:
                        logger.warn('Failed to get data hash from %s' % str(i))
                        self.peerData[i]['failCount'] -= 1
                if self._utils.validateHash(currentDB):
                    self._core.setAddressInfo(i, "DBHash", currentDB)

        if len(blockList) != 0:
            pass

        for i in blockList:
            if len(i.strip()) == 0:
                continue
            try:
                if self._utils.hasBlock(i):
                    continue
            except:
                logger.warn('Invalid hash') # TODO: move below validate hash check below
                pass
            if i in self.ignoredHashes:
                continue

            #logger.debug('Exchanged block (blockList): ' + i)
            if not self._utils.validateHash(i):
                # skip hash if it isn't valid
                logger.warn('Hash %s is not valid' % str(i))
                continue
            else:
                self.newHashes[i] = 0
                logger.debug('Adding %s to hash database...' % str(i))
                self._core.addToBlockDB(i)
        self.lookupBlocksThreads -= 1
        return

    def processBlocks(self, isThread=False):
        '''
            Work with the block database and download any missing blocks

            This is meant to be called from the communicator daemon on its timer.
        '''
        if isThread:
            self.processBlocksThreads += 1
        for i in self._core.getBlockList(unsaved = True):
            if i != "":
                if i in self.blocksProcessing or i in self.ignoredHashes:
                    #logger.debug('already processing ' + i)
                    continue
                else:
                    self.blocksProcessing.append(i)
                try:
                    self.newHashes[i]
                except KeyError:
                    self.newHashes[i] = 0

                # check if a new hash has been around too long, delete it from database and add it to ignore list
                if self.newHashes[i] >= self.keepNewHash:
                    logger.warn('Ignoring block %s because it took to long to get valid data.' % str(i))
                    del self.newHashes[i]
                    self._core.removeBlock(i)
                    self.ignoredHashes.append(i)
                    continue

                self.newHashes[i] += 1
                logger.warn('Block is unsaved: %s' % str(i))
                data = self.downloadBlock(i)

                # if block was successfully gotten (hash already verified)
                if data:
                    del self.newHashes[i] # remove from probation list

                    # deal with block metadata
                    blockContent = self._core.getData(i)
                    try:
                        blockContent = blockContent.encode()
                    except AttributeError:
                        pass
                    try:
                        #blockMetadata = json.loads(self._core.getData(i)).split('}')[0] + '}'
                        blockMetadata = json.loads(blockContent[:blockContent.find(b'\n')].decode())
                        try:
                            blockMeta2 = json.loads(blockMetadata['meta'])
                        except KeyError:
                            blockMeta2 = {'type': ''}
                            pass
                        blockContent = blockContent[blockContent.find(b'\n') + 1:]
                        try:
                            blockContent = blockContent.decode()
                        except AttributeError:
                            pass

                        if not self._crypto.verifyPow(blockContent, blockMeta2):
                            logger.warn("%s has invalid or insufficient proof of work token, deleting..." % str(i))
                            self._core.removeBlock(i)
                            continue
                        else:
                            if (('sig' in blockMetadata) and ('id' in blockMeta2)): # id doesn't exist in blockMeta2, so this won't workin the first place

                                #blockData = json.dumps(blockMetadata['meta']) + blockMetadata[blockMetadata.rfind(b'}') + 1:]

                                creator = self._utils.getPeerByHashId(blockMeta2['id'])
                                try:
                                    creator = creator.decode()
                                except AttributeError:
                                    pass

                                if self._core._crypto.edVerify(blockMetadata['meta'] + blockContent, creator, blockMetadata['sig'], encodedData=True):
                                    logger.info('%s was signed' % str(i))
                                    self._core.updateBlockInfo(i, 'sig', 'true')
                                else:
                                    logger.warn('%s has an invalid signature' % str(i))
                                    self._core.updateBlockInfo(i, 'sig', 'false')
                        try:
                            logger.info('Block type is %s' % str(blockMeta2['type']))
                            self._core.updateBlockInfo(i, 'dataType', blockMeta2['type'])
                            self.removeBlockFromProcessingList(i)
                            self.removeBlockFromProcessingList(i)
                        except KeyError:
                            logger.warn('Block has no type')
                            pass
                    except json.decoder.JSONDecodeError:
                        logger.warn('Could not decode block metadata')
                        self.removeBlockFromProcessingList(i)
        self.processBlocksThreads -= 1
        return

    def removeBlockFromProcessingList(self, block):
        return block in blocksProcessing

    def downloadBlock(self, hash, peerTries=3):
        '''
            Download a block from random order of peers
        '''

        retVal = False
        peerList = self._core.listAdders()
        blocks = ''
        peerTryCount = 0

        for i in peerList:
            try:
                if self.peerData[i]['failCount'] >= self.highFailureAmount:
                    continue
            except KeyError:
                pass
            if peerTryCount >= peerTries:
                break

            hasher = hashlib.sha3_256()
            data = self.performGet('getData', i, hash, skipHighFailureAddress=True)

            if data == False or len(data) > 10000000 or data == '':
                peerTryCount += 1
                continue

            try:
                data = base64.b64decode(data)
            except binascii.Error:
                data = b''

            hasher.update(data)
            digest = hasher.hexdigest()

            if type(digest) is bytes:
                digest = digest.decode()

            if digest == hash.strip():
                self._core.setData(data)
                logger.info('Successfully obtained data for %s' % str(hash), timestamp=True)
                retVal = True
                break
            else:
                logger.warn("Failed to validate %s -- hash calculated was %s" % (hash, digest))
                peerTryCount += 1

        return retVal

    def urlencode(self, data):
        '''
            URL encodes the data
        '''
        return urllib.parse.quote_plus(data)

    def performGet(self, action, peer, data=None, skipHighFailureAddress=False, selfCheck=True):
        '''
            Performs a request to a peer through Tor or i2p (currently only Tor)
        '''

        if not peer.endswith('.onion') and not peer.endswith('.onion/') and not peer.endswith('.b32.i2p'):
            raise PeerError('Currently only Tor/i2p .onion/.b32.i2p peers are supported. You must manually specify .onion/.b32.i2p')

        if len(self._core.hsAdder.strip()) == 0:
            raise Exception("Could not perform self address check in performGet due to not knowing our address")
        if selfCheck:
            if peer.replace('/', '') == self._core.hsAdder:
                logger.warn('Tried to performGet to own hidden service, but selfCheck was not set to false')
                return

        # Store peer in peerData dictionary (non permanent)
        if not peer in self.peerData:
            self.peerData[peer] = {'connectCount': 0, 'failCount': 0, 'lastConnectTime': self._utils.getEpoch()}
        socksPort = sys.argv[2]
        '''We use socks5h to use tor as DNS'''

        if peer.endswith('onion'):
            proxies = {'http': 'socks5h://127.0.0.1:' + str(socksPort), 'https': 'socks5h://127.0.0.1:' + str(socksPort)}

        elif peer.endswith('b32.i2p'):
            proxies = {'http': 'http://127.0.0.1:4444'}
        headers = {'user-agent': 'PyOnionr'}
        url = 'http://' + peer + '/public/?action=' + self.urlencode(action)

        if data != None:
            url = url + '&data=' + self.urlencode(data)
        try:
            if skipHighFailureAddress and self.peerData[peer]['failCount'] > self.highFailureAmount:
                retData = False
                logger.debug('Skipping %s because of high failure rate.' % peer)
            else:
                self.peerStatus[peer] = action
                logger.debug('Contacting %s on port %s' % (peer, str(socksPort)))
                try:
                    r = requests.get(url, headers=headers, proxies=proxies, allow_redirects=False, timeout=(15, 30))
                except ValueError:
                    proxies = {'http': 'socks5://127.0.0.1:' + str(socksPort), 'https': 'socks5://127.0.0.1:' + str(socksPort)}
                    r = requests.get(url, headers=headers, proxies=proxies, allow_redirects=False, timeout=(15, 30))
                retData = r.text
        except requests.exceptions.RequestException as e:
            logger.debug("%s failed with peer %s" % (action, peer))
            retData = False

        if not retData:
            self.peerData[peer]['failCount'] += 1
        else:
            self.peerData[peer]['connectCount'] += 1
            self.peerData[peer]['failCount'] -= 1
            self.peerData[peer]['lastConnectTime'] = self._utils.getEpoch()
            self._core.setAddressInfo(peer, 'lastConnect', self._utils.getEpoch())
        return retData

    def peerStatusTaken(self, peer, status):
        '''
            Returns if we are currently performing a specific action with a peer.
        '''
        try:
            if self.peerStatus[peer] == status:
                return True
        except KeyError:
            pass
        return False

shouldRun = False
debug = True
developmentMode = False
if config.get('devmode', True):
    developmentMode = True
try:
    if sys.argv[1] == 'run':
        shouldRun = True
except IndexError:
    pass
if shouldRun:
    try:
        OnionrCommunicate(debug, developmentMode)
    except KeyboardInterrupt:
        sys.exit(1)
        pass
