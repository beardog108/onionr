"""Onionr - Private P2P Communication.

Sets CLI arguments for Onionr
"""
from typing import Callable

from .. import onionrstatistics, version, daemonlaunch
from .. import openwebinterface
from .. import resetplugins  # command to reinstall default plugins
from .. import softreset  # command to delete onionr blocks
from .. import restartonionr  # command to restart Onionr
from .. import runtimetestcmd  # cmd to execute the runtime integration tests

import onionrexceptions
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


def get_arguments() -> dict:
    """Return command argument dict, minus plugin cmds.

    This is a function because we need to be able to
    dynamically modify them with plugins
    """
    args = {
        ('details', 'info'): onionrstatistics.show_details,
        ('stats', 'statistics'): onionrstatistics.show_stats,
        ('version',): version.version,
        ('start', 'daemon'): daemonlaunch.start,
        ('stop', 'kill'): daemonlaunch.kill_daemon,
        ('restart',): restartonionr.restart,
        ('openhome', 'gui', 'openweb',
         'open-home', 'open-web'): openwebinterface.open_home,
        ('get-url', 'url', 'get-web'): openwebinterface.get_url,
        ('resetplugins', 'reset-plugins'): resetplugins.reset,
        ('soft-reset', 'softreset'): softreset.soft_reset,
        ('runtime-test', 'runtimetest'): runtimetestcmd.do_runtime_test
    }
    return args


def get_help(arg: str) -> str:
    """Return the help info string from a given command."""
    arguments = get_arguments()
    # Iterate the command alias tuples
    for argument in arguments:
        # Return the help message if its found in a command alias tuple
        if arg in argument:
            return arguments[argument].onionr_help
    raise KeyError


def get_func(argument: str) -> Callable:
    """Return the function for a given command argument."""
    argument = argument.lower()
    args = get_arguments()

    for arg in args.keys():  # Iterate command alias sets
        """
        If our argument is in the current alias set,
        return the command function
        """
        if argument in arg:
            return args[arg]
    raise onionrexceptions.NotFound
