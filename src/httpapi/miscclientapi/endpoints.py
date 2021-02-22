"""Onionr - Private P2P Communication.

Misc client API endpoints too small to need their own file and that need access to the client api inst
"""
import os
import subprocess
import platform
from sys import stdout as sys_stdout

from flask import Response, Blueprint, request, send_from_directory, abort
from flask import g
from gevent import sleep

from httpapi import apiutils
import config
from onionrstatistics.serializeddata import SerializedData
from onionrutils import bytesconverter
from etc import onionrvalues
from utils import reconstructhash
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


SCRIPT_NAME = os.path.dirname(os.path.realpath(__file__)) + \
              f'/../../../{onionrvalues.SCRIPT_NAME}'


class PrivateEndpoints:
    def __init__(self, client_api):
        private_endpoints_bp = Blueprint('privateendpoints', __name__)
        self.private_endpoints_bp = private_endpoints_bp

        @private_endpoints_bp.route('/www/<path:path>', endpoint='www')
        def wwwPublic(path):
            if not config.get("www.private.run", True):
                abort(403)
            return send_from_directory(config.get('www.private.path',
                                       'static-data/www/private/'), path)

        @private_endpoints_bp.route('/getpid')
        def get_pid():
            return Response(str(os.getpid()))

        @private_endpoints_bp.route('/isatty')
        def get_is_atty():
            return Response(str(sys_stdout.isatty()).lower())

        @private_endpoints_bp.route('/ping')
        def ping():
            # Used to check if client api is working
            return Response("pong!")

        @private_endpoints_bp.route('/shutdown')
        def shutdown():
            return apiutils.shutdown.shutdown(client_api)

        @private_endpoints_bp.route('/restartclean')
        def restart_clean():
            subprocess.Popen([SCRIPT_NAME, 'restart'])
            return Response("bye")

        @private_endpoints_bp.route('/getstats')
        def get_stats():
            """Return serialized node statistics."""
            while True:
                try:
                    return Response(client_api._too_many.get(
                        SerializedData).get_stats())
                except AttributeError:
                    pass
                except FileNotFoundError:
                    pass

        @private_endpoints_bp.route('/getuptime')
        def show_uptime():
            return Response(str(client_api.getUptime()))

        @private_endpoints_bp.route('/setonboarding', methods=['POST'])
        def set_onboarding():
            return Response(
                config.onboarding.set_config_from_onboarding(request.get_json()))

        @private_endpoints_bp.route('/os')
        def get_os_system():
            return Response(platform.system().lower())

        @private_endpoints_bp.route('/getblockstoupload')
        def get_blocks_to_upload() -> Response:
            return Response(
                ','.join(
                    g.too_many.get_by_string('DeadSimpleKV').get('blocksToUpload')
                )
            )
