"""Onionr - Private P2P Communication.

cleanup run files
"""
import os

import filepaths
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


def _safe_remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def delete_run_files():
    """Delete run files, do not error if not found.

    Test: test_cleanup.py
    """
    _safe_remove(filepaths.private_API_host_file)
    _safe_remove(filepaths.daemon_mark_file)
    _safe_remove(filepaths.lock_file)
