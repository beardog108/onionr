from typing import NamedTuple
from base64 import b32decode, b64decode

from msgpack import packb, unpackb

from safedb import SafeDB
from utils.identifyhome import identify_home

from .servicecontrol import create_new_service, restore_service


ONION_KEY_DATABASE_FILE = identify_home() + "onion-address-keys.db"


class OnionServiceTarget(NamedTuple):
    virtual_port: int
    unix_socket_path: str


class NoServices(ValueError):
    pass


def load_services(controller):
    db = SafeDB(ONION_KEY_DATABASE_FILE, protected=True)
    keys = db.db_conn.keys()
    keys.remove(b'enc')
    restored = []

    if not keys:
        db.close()
        raise NoServices("No addresses to restore")

    while keys:
        # Not most pythonic but reduces mem usage as it runs
        key = keys.pop()
        try:
            service = unpackb(db.get(key))
            service_id = restore_service(
                controller, service['k'], int(service['p']),
                unix_socket=service['s'])[0]
            restored.append((service_id, service['s']))
        except Exception as _:  # noqa
            db.close()
            raise
    db.close()
    return restored


def run_new_and_store_service(controller, target: OnionServiceTarget) -> bytes:
    address, private_key = create_new_service(
        controller, target.virtual_port, target.unix_socket_path)
    db = SafeDB(ONION_KEY_DATABASE_FILE, protected=True)

    service_info = {
        'k': b64decode(private_key),
        's': target.unix_socket_path,
        'p': target.virtual_port}

    decoded_address = b32decode(address.upper())
    db.put(decoded_address, packb(service_info))
    db.close()
    return decoded_address
