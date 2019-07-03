'''
    Onionr - Private P2P Communication

    send a command to the local API server
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
import urllib, requests, time
import logger
from onionrutils import getclientapiserver
def local_command(core_inst, command, data='', silent = True, post=False, postData = {}, maxWait=20):
    '''
        Send a command to the local http API server, securely. Intended for local clients, DO NOT USE for remote peers.
    '''
    # TODO: URL encode parameters, just as an extra measure. May not be needed, but should be added regardless.
    hostname = ''
    waited = 0
    while hostname == '':
        try:
            hostname = getclientapiserver.get_client_API_server(core_inst)
        except FileNotFoundError:
            time.sleep(1)
            waited += 1
            if waited == maxWait:
                return False
    if data != '':
        data = '&data=' + urllib.parse.quote_plus(data)
    payload = 'http://%s/%s%s' % (hostname, command, data)
    try:
        if post:
            retData = requests.post(payload, data=postData, headers={'token': core_inst.config.get('client.webpassword'), 'Connection':'close'}, timeout=(maxWait, maxWait)).text
        else:
            retData = requests.get(payload, headers={'token': core_inst.config.get('client.webpassword'), 'Connection':'close'}, timeout=(maxWait, maxWait)).text
    except Exception as error:
        if not silent:
            logger.error('Failed to make local request (command: %s):%s' % (command, error), terminal=True)
        retData = False

    return retData