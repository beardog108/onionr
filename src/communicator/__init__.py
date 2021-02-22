"""Onionr - Private P2P Communication.

This file contains both the OnionrCommunicate class for
communcating with peers and code to operate as a daemon,
getting commands from the command queue database
"""
import time

import config
import logger
import onionrplugins as plugins
from onionrcommands.openwebinterface import get_url
from . import daemoneventhooks
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

config.reload()


class OnionrCommunicatorDaemon:
    def __init__(self, shared_state, developmentMode=None):
        if developmentMode is None:
            developmentMode = config.get(
                'general.dev_mode', False)

        # configure logger and stuff
        self.config = config
        self.shared_state = shared_state  # TooManyObjects module
        shared_state.add(self)

        # populate kv values
        self.kv = self.shared_state.get_by_string('DeadSimpleKV')

        if config.get('general.offline_mode', False):
            self.kv.put('isOnline', False)


        self.shared_state.share_object()

        # loop time.sleep delay in seconds
        self.delay = 5

        # amount of threads running by name, used to prevent too many
        self.threadCounts = {}

        # Loads in and starts the enabled plugins
        plugins.reload()


        daemoneventhooks.daemon_event_handlers(shared_state)

        get_url()
        if not config.get('onboarding.done', True):
            logger.info(
                'First run detected. Run openhome to get setup.',
                terminal=True)

            while not config.get('onboarding.done', True) and \
                    not self.shared_state.get_by_string(
                        'DeadSimpleKV').get('shutdown'):
                try:
                    time.sleep(2)
                except KeyboardInterrupt:
                    self.shared_state.get_by_string(
                        'DeadSimpleKV').put('shutdown', True)

        # Main daemon loop, mainly for calling timers,
        # don't do any complex operations here to avoid locking
        try:
            while not self.shared_state.get_by_string(
                    'DeadSimpleKV').get('shutdown'):
                time.sleep(self.delay)
        except KeyboardInterrupt:
            self.shared_state.get_by_string(
                    'DeadSimpleKV').put('shutdown', True)

        logger.info(
            'Goodbye. (Onionr is cleaning up, and will exit)', terminal=True)


def startCommunicator(shared_state):
    OnionrCommunicatorDaemon(shared_state)
