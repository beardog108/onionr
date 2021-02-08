"""Onionr - Private P2P Communication.

This default plugin allows users to encrypt/decrypt messages without using blocks
"""
import locale
locale.setlocale(locale.LC_ALL, '')
import binascii

# Imports some useful libraries
import logger, config, threading, time, datetime, sys

import ujson as json
from nacl.exceptions import TypeError as NaclTypeError

from onionrutils import stringvalidators, bytesconverter
from onionrcrypto import encryption, keypair, signing, getourkeypair
import onionrexceptions, onionrusers
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

plugin_name = 'encrypt'

class PlainEncryption:
    def __init__(self, api):
        self.api = api
        return
    def encrypt(self):
        # peer, data
        plaintext = ""
        encrypted = ""
        # detect if signing is enabled
        sign = True
        try:
            if sys.argv[3].lower() == 'false':
                sign = False
        except IndexError:
            pass

        try:
            if not stringvalidators.validate_pub_key(sys.argv[2]):
                raise onionrexceptions.InvalidPubkey
        except (ValueError, IndexError) as e:
            logger.error("Peer public key not specified", terminal=True)
        except onionrexceptions.InvalidPubkey:
            logger.error("Invalid public key", terminal=True)
        else:
            pubkey = sys.argv[2]
            # Encrypt if public key is valid
            logger.info("Please enter your message (ctrl-d or -q to stop):", terminal=True)
            try:
                for line in sys.stdin:
                    if line == '-q\n':
                        break
                    plaintext += line
            except KeyboardInterrupt:
                sys.exit(1)
            # Build Message to encrypt
            data = {}
            myPub = keypair[0]
            if sign:
                data['sig'] = signing.ed_sign(plaintext, key=keypair[1], encodeResult=True)
                data['sig'] = bytesconverter.bytes_to_str(data['sig'])
                data['signer'] = myPub
            data['data'] = plaintext
            data = json.dumps(data)
            plaintext = data
            encrypted = encryption.pub_key_encrypt(plaintext, pubkey, encodedData=True)
            encrypted = bytesconverter.bytes_to_str(encrypted)
            logger.info('Encrypted Message: \n\nONIONR ENCRYPTED DATA %s END ENCRYPTED DATA' % (encrypted,), terminal=True)

    def decrypt(self):
        plaintext = ""
        data = ""
        logger.info("Please enter your message (ctrl-d or -q to stop):", terminal=True)
        keypair = getourkeypair.get_keypair()
        try:
            for line in sys.stdin:
                if line == '-q\n':
                        break
                data += line
        except KeyboardInterrupt:
            sys.exit(1)
        if len(data) <= 1:
            return
        encrypted = data.replace('ONIONR ENCRYPTED DATA ', '').replace('END ENCRYPTED DATA', '')
        myPub = keypair[0]
        decrypted = encryption.pub_key_decrypt(encrypted, privkey=keypair[1], encodedData=True)
        if decrypted == False:
            logger.error("Decryption failed", terminal=True)
        else:
            data = json.loads(decrypted)
            logger.info('Decrypted Message: \n\n%s' % data['data'], terminal=True)
            try:
                logger.info("Signing public key: %s" % (data['signer'],), terminal=True)
                if not signing.ed_verify(data['data'], data['signer'], data['sig']): raise ValueError
            except (ValueError, KeyError) as e:
                logger.warn("WARNING: THIS MESSAGE HAS A MISSING OR INVALID SIGNATURE", terminal=True)
            else:
                logger.info("Message has good signature.", terminal=True)
        return

def on_decrypt_cmd(api, data=None):
    try:
        PlainEncryption(api).decrypt()
    except binascii.Error:
        logger.error("Invalid ciphertext padding", terminal=True)
    except NaclTypeError:
        logger.error("Ciphertext too short.", terminal=True)

def on_encrypt_cmd(api, data=None):
    PlainEncryption(api).encrypt()

on_encrypt_cmd.onionr_help = """encrypt <user_key>\nEncrypt text data to an Onionr user key. Similar to PGP"""
on_decrypt_cmd.onionr_help = """decrypt\nDecrypt text data with your Onionr key. Similar to PGP"""
ONIONR_COMMANDS = ['encrypt', 'decrypt']