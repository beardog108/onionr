"""Onionr - Private P2P Communication.

This file handles all incoming http requests to the client, using Flask
"""
import http
from typing import Dict
import hmac

import flask
from gevent.pywsgi import WSGIServer

from onionrutils import epoch
import httpapi
from filepaths import private_API_host_file
import logger

from etc import waitforsetvar
from . import register_private_blueprints
import config
"""
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
"""


class PrivateAPI:
    """Client HTTP api for controlling onionr and using UI."""

    callbacks: Dict[str, Dict] = {'public': {}, 'private': {}}

    def __init__(self):
        """Initialize the api server, preping variables for later use.

        This initialization defines all of the API entry points
        and handlers for the endpoints and errors
        This also saves the used host (random localhost IP address)
        to the data folder in host.txt
        """
        self.config = config

        self.startTime = epoch.get_epoch()
        app = flask.Flask(__name__)


        bind_port = int(config.get('client.client.port', 59496))
        self.bindPort = bind_port

        self.clientToken = config.get('client.webpassword')

        if config.get('general.bind_address'):
            with open(private_API_host_file, 'w') as bindFile:
                bindFile.write(config.get('general.bind_address'))
            self.host = config.get('general.bind_address')
        else:
            self.host = httpapi.apiutils.setbindip.set_bind_IP(
                private_API_host_file)
        logger.info('Running api on %s:%s' % (self.host, self.bindPort))
        self.httpServer = ''

        self.queueResponse = {}

        register_private_blueprints.register_private_blueprints(self, app)
        httpapi.load_plugin_blueprints(app)
        self.app = app

    def start(self):
        """Start client gevent API web server with flask client app."""
        waitforsetvar.wait_for_set_var(self, "_too_many")
        fd_handler = httpapi.fdsafehandler.FDSafeHandler
        self._too_many.add(httpapi.wrappedfunctions.SubProcVDFGenerator(self._too_many))
        self.httpServer = WSGIServer((self.host, self.bindPort),
                                     self.app, log=None,
                                     handler_class=fd_handler)
        self.httpServer.serve_forever()

    def validateToken(self, token):
        """Validate that the client token matches the given token.

        Used to prevent CSRF and other attacks.
        """
        if not self.clientToken:
            logger.error("client password needs to be set")
            return False
        try:
            return hmac.compare_digest(self.clientToken, token)
        except TypeError:
            return False

    def getUptime(self) -> int:
        """Safely wait for uptime to be set and return it."""
        while True:
            try:
                return epoch.get_epoch() - self.startTime
            except (AttributeError, NameError):
                # Don't error on race condition with startup
                pass

