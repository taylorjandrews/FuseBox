import Crypto.Cipher
import Crypto.Random
import Crypto.Util
import hashlib
import sys
import hmac
import os

block_size = Crypto.Cipher.AES.block_size
password = "password"

def get_salted_key(password, salt, key_length):
    return hashlib.sha256(password + salt).digest()[:key_length]

def get_key(password, key_length):
    return hashlib.sha256(password).digest()[:key_length]

def encrypt(buf, offset, fh, key_length=32):
    key = get_key(password, key_length)

    #incorporate nonce
    #uuid
    #server
    ctr = Crypto.Util.Counter.new(128, initial_value=long(offset))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    leftovers = len(buf) % block_size
    if len(buf) == 0 or leftovers != 0:
        padding_size = block_size - leftovers
        print(padding_size)
        buf += padding_size * chr(padding_size)

    fh.seek(offset)
    fh.write(cipher.encrypt(buf))

    return len(buf)

def decrypt(buf, offset, fh, key_length=32):
    if buf == "":
        return ""
    key = get_key(password, key_length)

    ctr = Crypto.Util.Counter.new(128, initial_value=long(offset))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    buf = cipher.decrypt(buf)
    print(buf)

    padding_size = ord(buf[-1])
    print(padding_size)
    if padding_size < 1 or padding_size > block_size:
        print("Bad padding value")
    elif buf[-padding_size:] != (padding_size * chr(padding_size)):
        print("Bad decrypt")
    buf = buf[:-padding_size]

    return buf

def main():
    #f = open('/home/taylor/Downloads/datalab-handout/bits.c', 'rb')
    #f = open('/home/taylor/Custos/custos-client-dropbox/testfile.txt', 'rb')
    f = open('/home/taylor/dmnt/test.txt', 'rb')

    out = open('testfile2.txt', 'wb')
    #enc_helper(f, out)
    fencrypt(f, out)
    out.close()
    
    f = open('testfile2.txt', 'rb')
    out = open('testfile3.txt', 'wb')
    fdecrypt(f, out)
    #dec_helper(f, out)
    f.close()
    out.close()

if __name__ == '__main__':
    main()
