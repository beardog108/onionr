"""Onionr - Private P2P Communication.

Command to soft-reset Onionr (deletes blocks)
"""
import os
import shutil

from onionrutils import localcommand
import filepaths
from onionrplugins import onionrevents
import logger
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


def _ignore_not_found_delete(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def soft_reset():
    """Command to soft reset Onionr home data.

    Onionr must not be running
    """
    if localcommand.local_command('/ping') == 'pong!':
        logger.warn('Cannot soft reset while Onionr is running',
                    terminal=True)
        return
    path = filepaths.block_data_location
    shutil.rmtree(path)
    _ignore_not_found_delete(filepaths.upload_list)
    _ignore_not_found_delete(filepaths.usage_file)
    onionrevents.event('softreset')
    logger.info("Soft reset Onionr", terminal=True)


soft_reset.onionr_help = "Deletes Onionr blocks and their "  # type: ignore
soft_reset.onionr_help += "associated metadata, except for "  # type: ignore
soft_reset.onionr_help += "any exported block files. Does NOT "  # type: ignore
soft_reset.onionr_help += "delete data on "  # type: ignore
soft_reset.onionr_help += "other nodes in the network."  # type: ignore
