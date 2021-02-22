"""Onionr - Private P2P Communication.

This module defines commands to show stats/details about the local node
"""
import os
import logger
from utils import sizeutils, getconsolewidth, identifyhome
import config
from etc import onionrvalues
from filepaths import lock_file

import psutil
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


def _is_running():
    script = onionrvalues.SCRIPT_NAME
    if os.path.isfile(lock_file):
        for process in psutil.process_iter():
            if process.name() == script:
                return True
    return False


def show_stats():
    """Print/log statistic info about our Onionr install."""
    try:
        # define stats messages here
        home = identifyhome.identify_home()

        messages = {
            # info about local client

            # This line is inaccurate if dev mode is enabled
            'Onionr Daemon Status':
            ((logger.colors.fg.green + 'Online') \
                if _is_running() \
                else logger.colors.fg.red + 'Offline'),

            # file and folder size stats
            'div1': True,  # this creates a solid line across the screen, a div
            'Total Plugin Size':
            sizeutils.human_size(sizeutils.size(home + 'plugins/')),
            'Log File Size':
            sizeutils.human_size(sizeutils.size(home + 'output.log')),

            # count stats
            'div2': True,
            'Enabled Plugins':
            str(len(config.get('plugins.enabled', list()))) + ' / ' +
            str(len(os.listdir(home + 'plugins/')))
        }

        # color configuration
        colors = {
            'title': logger.colors.bold,
            'key': logger.colors.fg.lightgreen,
            'val': logger.colors.fg.green,
            'border': logger.colors.fg.lightblue,

            'reset': logger.colors.reset
        }

        # pre-processing
        maxlength = 0
        width = getconsolewidth.get_console_width()
        for key, val in messages.items():
            if not (type(val) is bool and val is True):
                maxlength = max(len(key), maxlength)
        prewidth = maxlength + len(' | ')
        groupsize = width - prewidth - len('[+] ')

        # generate stats table
        logger.info(colors['title'] + 'Onionr v%s Statistics' %
                    onionrvalues.ONIONR_VERSION + colors['reset'],
                    terminal=True)
        logger.info(colors['border'] + '-' * (maxlength + 1) +
                    '+' + colors['reset'], terminal=True)
        for key, val in messages.items():
            if not (type(val) is bool and val is True):
                val = [str(val)[i:i + groupsize]
                       for i in range(0, len(str(val)), groupsize)]

                logger.info(colors['key'] + str(key).rjust(maxlength) +
                            colors['reset'] + colors['border'] +
                            ' | ' + colors['reset'] + colors['val'] +
                            str(val.pop(0)) + colors['reset'], terminal=True)

                for value in val:
                    logger.info(' ' * maxlength + colors['border'] + ' | ' +
                                colors['reset'] + colors['val'] + str(
                        value) + colors['reset'], terminal=True)
            else:
                logger.info(colors['border'] + '-' * (maxlength +
                                                      1) + '+' +
                            colors['reset'], terminal=True)
        logger.info(colors['border'] + '-' * (maxlength + 1) +
                    '+' + colors['reset'], terminal=True)
    except Exception as e:  # pylint: disable=W0703
        logger.error('Failed to generate statistics table. ' +
                     str(e), error=e, timestamp=False, terminal=True)


def show_details():
    """Print out details.

    node transport address(es)
    active user ID
        active user ID in mnemonic form
    """
    details = {
        'Data directory': identifyhome.identify_home()
    }

    for detail in details:
        logger.info('%s%s: \n%s%s\n' % (logger.colors.fg.lightgreen,
                                        detail, logger.colors.fg.green,
                                        details[detail]), terminal=True)


show_details.onionr_help = "Shows relevant information "  # type: ignore
show_details.onionr_help += "for your Onionr install: node "  # type: ignore
show_details.onionr_help += "address, and active public key."  # type: ignore

show_stats.onionr_help = "Shows statistics for your Onionr "  # type: ignore
show_stats.onionr_help += "node. Slow if Onionr is not running"  # type: ignore
