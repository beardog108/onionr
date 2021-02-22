"""Onionr - Private P2P Communication.

Open the web interface properly into a web browser
"""
import webbrowser
from time import sleep

import logger
from onionrutils import getclientapiserver
import config
from onionrutils.localcommand import local_command

from .daemonlaunch import geturl
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


def get_url() -> str:
    """Build UI URL string and return it."""
    return geturl.get_url(config)


get_url.onionr_help = "Shows the Onionr "  # type: ignore
get_url.onionr_help += "web interface URL with API key"  # type: ignore


def open_home():
    """Command to open web interface URL in default browser."""
    try:
        url = getclientapiserver.get_client_API_server()
    except FileNotFoundError:
        logger.error(
            'Onionr seems to not be running (could not get api host)',
            terminal=True)
    else:
        sleep(3)  # Sleep a little longer to wait for web UI to init some vars it needs
        url = get_url()
        logger.info(
            'If Onionr does not open automatically, use this URL: ' + url,
            terminal=True)
        webbrowser.open_new_tab(url)


open_home.onionr_help = "Opens the Onionr UI in the default "  # type: ignore
open_home.onionr_help += "browser. Node must be running."  # type: ignore
