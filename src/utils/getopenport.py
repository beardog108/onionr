"""
Onionr - Private P2P Communication.

get an open port
"""
import socket
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


def get_open_port():
    # taken from (but modified) https://stackoverflow.com/a/2838309 by https://stackoverflow.com/users/133374/albert ccy-by-sa-3 https://creativecommons.org/licenses/by-sa/3.0/
    # changes from source: import moved to top of file, bind specifically to localhost
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port
