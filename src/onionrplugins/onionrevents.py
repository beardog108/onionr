"""Onionr - Private P2P Communication.

Onionr events API
"""
from threading import Thread

import config
import logger
import onionrplugins as plugins
from . import onionrpluginapi as pluginapi
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


def get_pluginapi(data):
    return pluginapi.SharedAPI(data)


def __event_caller(event_name, data={}):
    """
        DO NOT call this function, this is for threading code only.
        Instead, call onionrevents.event
    """
    disabled = config.get('plugins.disabled')
    for plugin in plugins.get_enabled_plugins():
        if plugin in disabled: continue
        try:
            call(plugins.get_plugin(plugin), event_name, data, get_pluginapi(data))
        except ModuleNotFoundError as e:
            logger.warn('Disabling nonexistant plugin "%s"...' % plugin, terminal=True)
            plugins.disable(plugin, stop_event = False)
        except Exception as e:
            logger.warn('Event "%s" failed for plugin "%s".' % (event_name, plugin), terminal=True)
            logger.debug((event_name + ' - ' + plugin + ' - ' + str(e)), terminal=True)


def event(event_name, data = {}, threaded = True):
    """Call an event on all plugins (if defined)."""

    if threaded:
        thread = Thread(target = __event_caller, args = (event_name, data))
        thread.start()
        return thread
    else:
        __event_caller(event_name, data)


def call(plugin, event_name, data = None, pluginapi = None):
    """Call an event on a plugin if one is defined."""

    if not plugin is None:
        try:
            attribute = 'on_' + str(event_name).lower()
            if pluginapi is None:
                pluginapi = get_pluginapi(data)
            if hasattr(plugin, attribute):
                return getattr(plugin, attribute)(pluginapi, data)

            return True
        except Exception as e:
            #logger.error(str(e), terminal=True)
            return False
    else:
        return True
