"""Onionr - Private P2P Communication.

LAN transport server thread
"""
import ipaddress
import time
from threading import Thread

from gevent.pywsgi import WSGIServer
from flask import Flask
from flask import Response
from flask import request
from flask import abort

from oldblocks.onionrblockapi import Block
from httpapi.fdsafehandler import FDSafeHandler
from netcontroller import get_open_port
import config
from coredb.blockmetadb import get_block_list
from lan.getip import best_ip, lan_ips
from onionrutils import stringvalidators
from httpapi.miscpublicapi.upload import accept_upload
import logger
from utils.bettersleep import better_sleep
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
ports = range(1337, 1340)
_start_time = time.time()


class LANServer:
    def __init__(self, shared_state):
        app = Flask(__name__)
        self.app = app
        self.host = config.get('lan.bind_ip', '')
        self.server = None
        if self.host == '':
            self.host = best_ip
        self.port = None

        @app.before_request
        def dns_rebinding_prevention():
            if not ipaddress.ip_address(request.remote_addr).is_private:
                abort(403)
            if request.remote_addr in lan_ips or \
                    ipaddress.ip_address(request.remote_addr).is_loopback:
                if time.time() - _start_time > 600:
                    abort(403)
            if request.host != f'{self.host}:{self.port}':
                logger.warn('Potential DNS rebinding attack on LAN server:')
                logger.warn(
                    f'Hostname {request.host} was used instead of {self.host}:{self.port}')  # noqa
                abort(403)

        @app.route('/blist/<time>')
        def get_block_list_for_lan(time):
            return Response('\n'.join(get_block_list(date_rec=time)))

        @app.route('/get/<block>')
        def get_block_data(block):
            if not stringvalidators.validate_hash(block):
                raise ValueError
            return Response(
                Block(block).raw, mimetype='application/octet-stream')

        @app.route("/ping")
        def ping():
            return Response("onionr!")

        @app.route('/upload', methods=['POST'])
        def upload_endpoint():
            return accept_upload(request)

    def start_server(self):
        def _show_lan_bind(port):
            better_sleep(1)
            if self.server.started and port == self.server.server_port:
                logger.info(
                    f'Serving to LAN on {self.host}:{self.port}',
                    terminal=True)
        if self.host == "":
            logger.info(
                "Not binding to LAN due to no private network configured.",
                terminal=True)
            return
        for i in ports:
            self.server = WSGIServer((self.host, i),
                                     self.app, log=None,
                                     handler_class=FDSafeHandler)
            self.port = self.server.server_port
            try:
                Thread(target=_show_lan_bind, args=[i], daemon=True).start()
                self.server.serve_forever()
            except OSError:
                pass
            else:
                break
        else:
            logger.warn("Could not bind to any LAN ports " +
                        str(min(ports)) + "-" + str(max(ports)), terminal=True)
            return
