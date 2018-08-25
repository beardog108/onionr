'''
    Onionr - P2P Microblogging Platform & Social network.

    This file handles maintenence of a blacklist database, for blocks and peers
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
import sqlite3, os, logger
class OnionrBlackList:
    def __init__(self, coreInst):
        self.blacklistDB = 'data/blacklist.db'
        self._core = coreInst
        
        if not os.path.exists(self.blacklistDB):
            self.generateDB()
        return
    
    def inBlacklist(self, data):
        hashed = self._core._utils.bytesToStr(self._core._crypto.sha3Hash(data))
        retData = False
        if not hashed.isalnum():
            raise Exception("Hashed data is not alpha numeric")

        for i in self._dbExecute("select * from blacklist where hash='%s'" % (hashed,)):
            retData = True # this only executes if an entry is present by that hash
            break
        return retData

    def _dbExecute(self, toExec):
        conn = sqlite3.connect(self.blacklistDB)
        c = conn.cursor()
        retData = c.execute(toExec)
        conn.commit()
        return retData
    
    def deleteBeforeDate(self, date):
        # TODO, delete blacklist entries before date
        return
    
    def deleteExpired(self, dataType=0):
        '''Delete expired entries'''
        deleteList = []
        curTime = self._core._utils.getEpoch()

        try:
            int(dataType)
        except AttributeError:
            raise TypeError("dataType must be int")

        for i in self._dbExecute('select * from blacklist where dataType=%s' % (dataType,)):
            if i[1] == dataType:
                if (curTime - i[2]) >= i[3]:
                    deleteList.append(i[0])
        
        for thing in deleteList:
            self._dbExecute("delete from blacklist where hash='%s'" % (thing,))

    def generateDB(self):
        self._dbExecute('''CREATE TABLE blacklist(
            hash text primary key not null,
            dataType int,
            blacklistDate int,
            expire int
            );
        ''')
        return
    
    def clearDB(self):
        self._dbExecute('''delete from blacklist;);''')

    def getList(self):
        data = self._dbExecute('select * from blacklist')
        myList = []
        for i in data:
            myList.append(i[0])
        return myList

    def addToDB(self, data, dataType=0, expire=0):
        '''Add to the blacklist. Intended to be block hash, block data, peers, or transport addresses
        0=block
        1=peer
        2=pubkey
        '''
        # we hash the data so we can remove data entirely from our node's disk
        hashed = self._core._utils.bytesToStr(self._core._crypto.sha3Hash(data))

        if self.inBlacklist(hashed):
            return

        if not hashed.isalnum():
            raise Exception("Hashed data is not alpha numeric")
        try:
            int(dataType)
        except ValueError:
            raise Exception("dataType is not int")
        try:
            int(expire)
        except ValueError:
            raise Exception("expire is not int")
        #TODO check for length sanity
        insert = (hashed,)
        blacklistDate = self._core._utils.getEpoch()
        self._dbExecute("insert into blacklist (hash, dataType, blacklistDate, expire) VALUES('%s', %s, %s, %s);" % (hashed, dataType, blacklistDate, expire))