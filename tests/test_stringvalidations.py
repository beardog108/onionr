#!/usr/bin/env python3
import sys, os
sys.path.append(".")
sys.path.append("src/")
import unittest, uuid
TEST_DIR = 'testdata/%s-%s' % (uuid.uuid4(), os.path.basename(__file__)) + '/'
print("Test directory:", TEST_DIR)
os.environ["ONIONR_HOME"] = TEST_DIR
from onionrutils import stringvalidators

class OnionrValidations(unittest.TestCase):

    def test_peer_validator(self):
        # Test hidden service domain validities
        valid = ['ao34zusas5oocjllkh6uounorhtujyep4ffwz4k4r7qkxie5otdiwqad.onion', 'vww6ybal4bd7szmgncyruucpgfkqahzddi37ktceo3ah7ngmcopnpyyd.onion']

        invalid = [None, 'dsfewjirji0ejipdfs', '', '    ', '\n', '\r\n', 'f$ce%^okc+rewwwi.onion', 'facebookc0rewwi.onion', 'facebookcorewwwi.onion']

        for x in valid:
            print('testing', x)
            self.assertTrue(stringvalidators.validate_transport(x))

        for x in invalid:
            print('testing', x)
            self.assertFalse(stringvalidators.validate_transport(x))

    def test_hash_validator(self):
        valid = ['00003b3813a166e706e490238e9515633cc3d083efe982a67753d50d87a00c96\n', '00003b3813a166e706e490238e9515633cc3d083efe982a67753d50d87a00c96', b'00003b3813a166e706e490238e9515633cc3d083efe982a67753d50d87a00c96',
        '00003b3813a166e706e490238e9515633cc36', b'00003b3813a166e706e490238e9515633cc3d083']
        invalid = [None, 0, 1, True, False, '%#W483242#', '00003b3813a166e706e490238e9515633cc3d083efe982a67753d50d87a00c9666', '', b'',
        b'00003b3813a166e706e490238e9515633cc3d083efe982a67753d50d87a00c9666666', b'    ', '\n', '00003b3813a166e706e490238e9515633cc3d083efe982a67753d50d87a00ccccc\n']

        for x in valid:
            self.assertTrue(stringvalidators.validate_hash(x))
        for x in invalid:
            try:
                result = stringvalidators.validate_hash(x)
                print('testing', x, result)
            except AttributeError:
                result = False
            try:
                self.assertFalse(result)
            except AssertionError:
                raise AssertionError("%s returned true" % (x,))

    def test_pubkey_validator(self):
        # Test ed25519 public key validity
        valids = ['JZ5VE72GUS3C7BOHDRIYZX4B5U5EJMCMLKHLYCVBQQF3UKHYIRRQ====', 'JZ5VE72GUS3C7BOHDRIYZX4B5U5EJMCMLKHLYCVBQQF3UKHYIRRQ']
        invalid = [None, '', '    ', 'dfsg', '\n', 'JZ5VE72GUS3C7BOHDRIYZX4B5U5EJMCMLKHLYCVBQQF3UKHYIR$Q====']

        for valid in valids:
            print('testing', valid)
            self.assertTrue(stringvalidators.validate_pub_key(valid))

        for x in invalid:
            #print('testing', x)
            self.assertFalse(stringvalidators.validate_pub_key(x))

    def test_integer_string(self):
        valid = ["1", "100", 100, "-5", -5]
        invalid = ['test', "1d3434", "1e100", None]

        for x in valid:
            #print('testing', x)
            self.assertTrue(stringvalidators.is_integer_string(x))

        for x in invalid:
            #print('testing', x)
            self.assertFalse(stringvalidators.is_integer_string(x))

unittest.main()
