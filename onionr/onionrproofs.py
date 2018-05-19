'''
    Onionr - P2P Microblogging Platform & Social network

    Proof of work module
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

import nacl.encoding, nacl.hash, nacl.utils, time, math, threading, binascii, logger, sys, base64
import core

class POW:
    def pow(self, reporting = False):
        startTime = math.floor(time.time())
        self.hashing = True
        self.reporting = reporting
        iFound = False # if current thread is the one that found the answer
        answer = ''
        heartbeat = 200000
        hbCount = 0
        myCore = core.Core()
        while self.hashing:
            rand = nacl.utils.random()
            token = nacl.hash.blake2b(rand + self.data).decode()
            #print(token)
            if self.puzzle == token[0:self.difficulty]:
                self.hashing = False
                iFound = True
                break
        else:
            logger.debug('POW thread exiting, another thread found result')
        if iFound:
            endTime = math.floor(time.time())
            if self.reporting:
                logger.info('Found token ' + token, timestamp=True)
                logger.info('rand value: ' + base64.b64encode(rand).decode())
                logger.info('took ' + str(endTime - startTime) + ' seconds', timestamp=True)
            self.result = (token, rand)

    def __init__(self, data):
        self.foundHash = False
        self.difficulty = 0
        self.data = data

        dataLen = sys.getsizeof(data)
        self.difficulty = math.floor(dataLen/1000000)
        if self.difficulty <= 2:
            self.difficulty = 4

        try:
            self.data = self.data.encode()
        except AttributeError:
            pass
        self.data = nacl.hash.blake2b(self.data)

        logger.debug('Computing difficulty of ' + str(self.difficulty))

        self.mainHash = '0000000000000000000000000000000000000000000000000000000000000000'#nacl.hash.blake2b(nacl.utils.random()).decode()
        self.puzzle = self.mainHash[0:self.difficulty]
        #logger.debug('trying to find ' + str(self.mainHash))
        tOne = threading.Thread(name='one', target=self.pow, args=(True,))
        tTwo = threading.Thread(name='two', target=self.pow, args=(True,))
        tThree = threading.Thread(name='three', target=self.pow, args=(True,))
        tOne.start()
        tTwo.start()
        tThree.start()
        return

    def shutdown(self):
        self.hashing = False
        self.puzzle = ''

    def changeDifficulty(self, newDiff):
        self.difficulty = newDiff

    def getResult(self):
        '''
            Returns the result then sets to false, useful to automatically clear the result
        '''
        try:
            retVal = self.result
        except AttributeError:
            retVal = False
        self.result = False
        return retVal
