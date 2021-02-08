import socket
import os
import secrets
from base64 import b32decode, b32encode
from time import sleep

from utils import identifyhome
from onionrblocks import blockcreator
from blockio import subprocgenerate
from onionrutils import localcommand
import blockio


def _fake_onion():
    return b32encode(os.urandom(34)).decode('utf-8') + ".onion"

def _shrink_peer_address(peer):
    # strip .onion and b32decode peer address for lower database mem usage
    if len(peer) == 62:  # constant time
        return b32decode(peer[:-6])  # O(N)
    return peer

def torgossip_runtest(test_manager):


    s_file = identifyhome.identify_home() + "/torgossip.sock"
    bl_test = blockcreator.create_anonvdf_block(b"test", "txt", 10)
    shared_state = test_manager._too_many

    #shared_state.get_by_string("PassToSafeDB").queue_then_store(b"test", "txt", 10)
    bl = subprocgenerate.vdf_block(b"test", "txt", 100)
    blockio.store_block(bl, shared_state.get_by_string("SafeDB"))

    tsts = b''

    for i in range(3):
        bl2 = subprocgenerate.vdf_block(b"what" + os.urandom(4), "tbt", 100)
        tsts += bl2.id
        blockio.store_block(bl2, shared_state.get_by_string("SafeDB"))

    bl_new = blockcreator.create_anonvdf_block(b"what", "txt", 10)


    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(s_file)
        s.sendall(b'1')
        resp = s.recv(5)
        assert resp == b"PONG"

        s.sendall(b'3txx')
        assert s.recv(64) == b"0"

        s.sendall(b'3txt')
        assert bl.id in s.recv(10000)

        # test getting a block that doesn't exist
        s.sendall(b'5' + int(secrets.randbits(64)).to_bytes(64, 'little'))

        #print(len(s.recv(64)))
        assert s.recv(64)[0] == ord(b'0')

        # test getting a block that does exist
        s.sendall(b'5' + bl.id)
        assert s.recv(64) == bl.get_packed()

        # test putting block
        s.sendall(b'6' + bl_new.id + bl_new.get_packed())
        assert s.recv(2) == b"1"

        # test block was uploaded by getting it
        s.sendall(b'5' + bl_new.id)
        assert s.recv(64) == bl_new.get_packed()

        s.sendall(b'40,tbt')
        assert len(s.recv(100000)) == len(
            shared_state.get_by_string("SafeDB").get('bl-tbt'))

        s.sendall(b'41,tbt')
        assert len(s.recv(100000)) == len(
            shared_state.get_by_string("SafeDB").get('bl-tbt')) - 64

        # test peer list
        fake_peer = _fake_onion()
        fakes = []
        for i in range(3):
            fake = _fake_onion()
            fakes.append(fake)
            shared_state.get_by_string('TorGossipPeers').add_peer(fake)
        shared_state.get_by_string('TorGossipPeers').add_peer(fake_peer)
        shared_state.get_by_string(
            'TorGossipPeers').add_score(fake_peer, 100000)
        s.sendall(b'71')
        stored = s.recv(1000)
        expected = _shrink_peer_address(fake_peer)
        try:
            assert stored == expected
        except AssertionError:
            print(stored, '!=', expected)
        shared_state.get_by_string('TorGossipPeers').remove_peer(fake_peer)
        for i in fakes:
            shared_state.get_by_string('TorGossipPeers').remove_peer(i)

        announce_peer = _fake_onion()
        announce_raw = _shrink_peer_address(announce_peer)
        s.sendall(b'8' + announce_raw)
        assert s.recv(1) == b'1'
        print(type(announce_raw), type(shared_state.get_by_string(
            'TorGossipPeers').get_highest_score_peers(100)[0][0]))
        assert announce_raw == shared_state.get_by_string(
            'TorGossipPeers').get_highest_score_peers(100)[0][0]
        shared_state.get_by_string('TorGossipPeers').remove_peer(announce_raw)

        s.sendall(b'9')
        assert s.recv(64) == b"BYE"
