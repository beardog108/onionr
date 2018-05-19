'''
    Onionr - P2P Microblogging Platform & Social network

    This file handles all incoming http requests to the client, using Flask
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
import flask
from flask import request, Response, abort
from multiprocessing import Process
from gevent.wsgi import WSGIServer
import sys, random, threading, hmac, hashlib, base64, time, math, os, logger, config

from core import Core
import onionrutils, onionrcrypto
class API:
    '''
        Main HTTP API (Flask)
    '''
    def validateToken(self, token):
        '''
            Validate that the client token (hmac) matches the given token
        '''
        try:
            if not hmac.compare_digest(self.clientToken, token):
                return False
            else:
                return True
        except TypeError:
            return False

    def __init__(self, debug):
        '''
            Initialize the api server, preping variables for later use

            This initilization defines all of the API entry points and handlers for the endpoints and errors
            This also saves the used host (random localhost IP address) to the data folder in host.txt
        '''

        config.reload()
        
        if config.get('devmode', True):
            self._developmentMode = True
            logger.set_level(logger.LEVEL_DEBUG)
        else:
            self._developmentMode = False
            logger.set_level(logger.LEVEL_INFO)

        self.debug = debug
        self._privateDelayTime = 3
        self._core = Core()
        self._crypto = onionrcrypto.OnionrCrypto(self._core)
        self._utils = onionrutils.OnionrUtils(self._core)
        app = flask.Flask(__name__)
        bindPort = int(config.get('client')['port'])
        self.bindPort = bindPort
        self.clientToken = config.get('client')['client_hmac']
        self.timeBypassToken = base64.b16encode(os.urandom(32)).decode()

        self.i2pEnabled = config.get('i2p')['host']

        self.mimeType = 'text/plain'

        with open('data/time-bypass.txt', 'w') as bypass:
            bypass.write(self.timeBypassToken)

        if not os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            logger.debug('Your web password (KEEP SECRET): ' + logger.colors.underline + self.clientToken)

        if not debug and not self._developmentMode:
            hostNums = [random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)]
            self.host = '127.' + str(hostNums[0]) + '.' + str(hostNums[1]) + '.' + str(hostNums[2])
        else:
            self.host = '127.0.0.1'
        hostFile = open('data/host.txt', 'w')
        hostFile.write(self.host)
        hostFile.close()

        @app.before_request
        def beforeReq():
            '''
                Simply define the request as not having yet failed, before every request.
            '''
            self.requestFailed = False

            return

        @app.after_request
        def afterReq(resp):
            if not self.requestFailed:
                resp.headers['Access-Control-Allow-Origin'] = '*'
            #else:
            #    resp.headers['server'] = 'Onionr'
            resp.headers['Content-Type'] = self.mimeType
            resp.headers["Content-Security-Policy"] =  "default-src 'none'; script-src 'none'; object-src 'none'; style-src data: 'unsafe-inline'; img-src data:; media-src 'none'; frame-src 'none'; font-src 'none'; connect-src 'none'"
            resp.headers['X-Frame-Options'] = 'deny'
            resp.headers['X-Content-Type-Options'] = "nosniff"
            resp.headers['server'] = 'Onionr'

            # reset to text/plain to help prevent browser attacks
            if self.mimeType != 'text/plain':
                self.mimeType = 'text/plain'

            return resp

        @app.route('/client/')
        def private_handler():
            if request.args.get('timingToken') is None:
                timingToken = ''
            else:
                timingToken = request.args.get('timingToken')
            data = request.args.get('data')
            try:
                data = data
            except:
                data = ''
            startTime = math.floor(time.time())
            # we should keep a hash DB of requests (with hmac) to prevent replays
            action = request.args.get('action')
            #if not self.debug:
            token = request.args.get('token')

            if not self.validateToken(token):
                abort(403)
            self.validateHost('private')
            if action == 'hello':
                resp = Response('Hello, World! ' + request.host)
            elif action == 'shutdown':
                # request.environ.get('werkzeug.server.shutdown')()
                self.http_server.stop()
                resp = Response('Goodbye')
            elif action == 'ping':
                resp = Response('pong')
            elif action == 'stats':
                resp = Response('me_irl')
                raise Exception
            elif action == 'site':
                block = data
                siteData = self._core.getData(data)
                response = 'not found'
                if siteData != '' and siteData != False:
                    self.mimeType = 'text/html'
                    response = siteData.split(b'-', 2)[-1]
                resp = Response(response)
            else:
                resp = Response('(O_o) Dude what? (invalid command)')
            endTime = math.floor(time.time())
            elapsed = endTime - startTime

            # if bypass token not used, delay response to prevent timing attacks
            if not hmac.compare_digest(timingToken, self.timeBypassToken):
                if elapsed < self._privateDelayTime:
                    time.sleep(self._privateDelayTime - elapsed)

            return resp

        @app.route('/')
        def banner():
            self.mimeType = 'text/html'
            self.validateHost('public')
            try:
                with open('static-data/index.html', 'r') as html:
                    resp = Response(html.read())
            except FileNotFoundError:
                resp = Response("")
            return resp

        @app.route('/public/')
        def public_handler():
            # Public means it is publicly network accessible
            self.validateHost('public')
            action = request.args.get('action')
            requestingPeer = request.args.get('myID')
            data = request.args.get('data')
            try:
                data = data
            except:
                data = ''
            if action == 'firstConnect':
                pass
            elif action == 'ping':
                resp = Response("pong!")
            elif action == 'getHMAC':
                resp = Response(self._crypto.generateSymmetric())
            elif action == 'getSymmetric':
                resp = Response(self._crypto.generateSymmetric())
            elif action == 'getDBHash':
                resp = Response(self._utils.getBlockDBHash())
            elif action == 'getBlockHashes':
                resp = Response(self._core.getBlockList().split('\n'))
            elif action == 'directMessage':
                resp = Response(self._core.handle_direct_connection(data))
            elif action == 'announce':
                if data != '':
                    # TODO: require POW for this
                    if self._core.addAddress(data):
                        resp = Response('Success')
                    else:
                        resp = Response('')
                else:
                    resp = Response('')
            # setData should be something the communicator initiates, not this api
            elif action == 'getData':
                if self._utils.validateHash(data):
                    if not os.path.exists('data/blocks/' + data + '.db'):
                        try:
                            resp = base64.b64encode(self._core.getData(data))
                        except TypeError:
                            resp = ""
                if resp == False:
                    abort(404)
                    resp = ""
                resp = Response(resp)
            elif action == 'pex':
                response = ','.join(self._core.listAdders())
                if len(response) == 0:
                    response = 'none'
                resp = Response(response)
            elif action == 'kex':
                peers = self._core.listPeers(getPow=True)
                response = ','.join(peers)
                resp = Response(response)
            else:
                resp = Response("")

            return resp

        @app.errorhandler(404)
        def notfound(err):
            self.requestFailed = True
            resp = Response("")

            return resp

        @app.errorhandler(403)
        def authFail(err):
            self.requestFailed = True
            resp = Response("403")

            return resp

        @app.errorhandler(401)
        def clientError(err):
            self.requestFailed = True
            resp = Response("Invalid request")

            return resp
        if not os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            logger.info('Starting client on ' + self.host + ':' + str(bindPort) + '...', timestamp=True)

        try:
            self.http_server = WSGIServer((self.host, bindPort), app)
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            pass
            #app.run(host=self.host, port=bindPort, debug=False, threaded=True)
        except Exception as e:
            logger.error(str(e))
            logger.fatal('Failed to start client on ' + self.host + ':' + str(bindPort) + ', exiting...')
            exit(1)

    def validateHost(self, hostType):
        '''
            Validate various features of the request including:

            If private (/client/), is the host header local?
            If public (/public/), is the host header onion or i2p?

            Was X-Request-With used?
        '''
        if self.debug:
            return
        # Validate host header, to protect against DNS rebinding attacks
        host = self.host
        if hostType == 'private':
            if not request.host.startswith('127') and not self._utils.checkIsIP(request.host):
                abort(403)
        elif hostType == 'public':
            if not request.host.endswith('onion') and not request.host.endswith('i2p'):
                abort(403)
        # Validate x-requested-with, to protect against CSRF/metadata leaks

        if not self.i2pEnabled and request.host.endswith('i2p'):
            abort(403)

        if not self._developmentMode:
            try:
                request.headers['X-Requested-With']
            except:
                # we exit rather than abort to avoid fingerprinting
                logger.debug('Avoiding fingerprinting, exiting...')
                sys.exit(1)
