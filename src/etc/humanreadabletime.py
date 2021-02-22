"""
Onionr - Private P2P Communication.

human_readable_time takes integer seconds and returns a human readable string
"""
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


def human_readable_time(seconds):
    build = ''

    units = {
        'year' : 31557600,
        'month' : (31557600 / 12),
        'day' : 86400,
        'hour' : 3600,
        'minute' : 60,
        'second' : 1
    }

    for unit in units:
        amnt_unit = int(seconds / units[unit])
        if amnt_unit >= 1:
            seconds -= amnt_unit * units[unit]
            build += '%s %s' % (amnt_unit, unit) + ('s' if amnt_unit != 1 else '') + ' '

    return build.strip()