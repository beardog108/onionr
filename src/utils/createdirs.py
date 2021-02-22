"""Onionr - Private P2P Communication.

Create required Onionr directories
"""
import os
import stat

from . import identifyhome
import filepaths
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
home = identifyhome.identify_home()


def create_dirs():
    """Create onionr data-related directories in
    order of the hardcoded list below,
    then trigger creation of DBs"""
    gen_dirs = [home, filepaths.block_data_location]
    for path in gen_dirs:
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            if os.getuid() != os.stat(path).st_uid:
                raise onionrexceptions.InsecureDirectoryUsage(
                    "Directory " + path +
                    " already exists and is not owned by the same user")

    os.chmod(home, stat.S_IRWXU)
