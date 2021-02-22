"""
Onionr - Private P2P Communication

Register plugin's flask blueprints for the client http server
"""
import onionrplugins
import config

from . import wrappedfunctions
from . import fdsafehandler
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


def load_plugin_blueprints(flaskapp, blueprint: str = 'flask_blueprint'):
    """Iterate enabled plugins and load any http endpoints they have"""
    config.reload()
    disabled = config.get('plugins.disabled')
    for plugin in onionrplugins.get_enabled_plugins():
        if plugin in disabled:
            continue
        plugin = onionrplugins.get_plugin(plugin)
        try:
            flaskapp.register_blueprint(getattr(plugin, blueprint))
        except AttributeError:
            pass
