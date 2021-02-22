"""Flask WSGI apps for the public and private API servers.

Public is net-facing server meant for other nodes
Private is meant for controlling and accessing this node
"""

from . import private

ClientAPI = private.PrivateAPI
