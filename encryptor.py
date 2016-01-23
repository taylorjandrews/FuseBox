# Taylor Andrews
#
# Encrypt the file as it goes up to Dropbox.
# Decrypt the file as it comes down from Dropbox.
#

import Crypto.Cipher
import Crypto.Random
import Crypto.Util
import hashlib
import sys
import hmac
import os
from keys import retrieve_key

# Save the block size for portability
block_size = Crypto.Cipher.AES.block_size

# Encrypt text
def encrypt(buf, offset, fh, cuuid, suuid):
    key = retrieve_key(cuuid, suuid)

    # TODO incorporate nonce
    ctr = Crypto.Util.Counter.new(128, initial_value=long(offset))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    leftovers = len(buf) % block_size

    # Pad the block for encrypting
    if len(buf) == 0 or leftovers != 0:
        padding_size = block_size - leftovers
        buf += padding_size * chr(padding_size)

    # Write to the file
    fh.seek(offset)
    fh.write(cipher.encrypt(buf))

    return padding_size

# Decrypt the text
def decrypt(buf, offset, fh, cuuid, suuid):
    key = retrieve_key(cuuid, suuid)

    # Return blank in the case of a blank buffer
    if buf == "":
        return ""

    # TODO incorporate nonce
    ctr = Crypto.Util.Counter.new(128, initial_value=long(offset))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    buf = cipher.decrypt(buf)

    # Undo the padding
    padding_size = ord(buf[-1])
    if padding_size < 1 or padding_size > block_size:
        print("Bad padding value")
    elif buf[-padding_size:] != (padding_size * chr(padding_size)):
        print("Bad decrypt")
    buf = buf[:-padding_size]

    # Return decrypted text
    return buf

if __name__ == '__main__':
    main()
