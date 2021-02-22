"""Onionr - Private P2P Communication.

Initialize Onionr configuration
"""
import os
import base64

import ujson as json

import config
import logger
from etc import onionrvalues
from logger.settings import *
from utils import readstatic, getopenport
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


def setup_config():
    if not os.path.exists(config._configfile):
        # this is the default config, it will be overwritten if a config file already exists. Else, it saves it
        conf_data = readstatic.read_static('default_config.json', ret_bin=False)
        config.set_config(json.loads(conf_data))

        config.save()

    config.reload()
    random_port = getopenport.get_open_port()

    settings = 0b000
    if config.get('log.console.color', True):
        settings = settings | USE_ANSI
    if config.get('log.console.output', True):
        settings = settings | OUTPUT_TO_CONSOLE
    if config.get('log.file.output', True):
        settings = settings | OUTPUT_TO_FILE
    set_settings(settings)

    verbosity = str(config.get('log.verbosity', 'default')).lower().strip()
    if not verbosity in ['default', 'null', 'none', 'nil']:
        map = {
            str(LEVEL_DEBUG) : LEVEL_DEBUG,
            'verbose' : LEVEL_DEBUG,
            'debug' : LEVEL_DEBUG,
            str(LEVEL_INFO) : LEVEL_INFO,
            'info' : LEVEL_INFO,
            'information' : LEVEL_INFO,
            str(LEVEL_WARN) : LEVEL_WARN,
            'warn' : LEVEL_WARN,
            'warning' : LEVEL_WARN,
            'warnings' : LEVEL_WARN,
            str(LEVEL_ERROR) : LEVEL_ERROR,
            'err' : LEVEL_ERROR,
            'error' : LEVEL_ERROR,
            'errors' : LEVEL_ERROR,
            str(LEVEL_FATAL) : LEVEL_FATAL,
            'fatal' : LEVEL_FATAL,
            str(LEVEL_IMPORTANT) : LEVEL_IMPORTANT,
            'silent' : LEVEL_IMPORTANT,
            'quiet' : LEVEL_IMPORTANT,
            'important' : LEVEL_IMPORTANT
        }

        if verbosity in map:
            set_level(map[verbosity])
        else:
            logger.warn('Verbosity level %s is not valid, using default verbosity.' % verbosity)

    if type(config.get('client.webpassword')) is type(None):
        config.set('client.webpassword', base64.b16encode(os.urandom(32)).decode('utf-8'), savefile=True)

        config.set('client.client.port', random_port, savefile=True)

    if type(config.get('client.api_version')) is type(None):
        config.set('client.api_version', onionrvalues.API_VERSION, savefile=True)
