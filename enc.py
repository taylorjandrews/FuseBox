import Crypto.Cipher
import Crypto.Random
import Crypto.Util
import hashlib
import sys
import hmac
import os

block_size = Crypto.Cipher.AES.block_size
amount = 128

# This function does NOT contain a salt
# Not having a salt is obviously not okay,
# but when we implement libcustos this will be replaced
def get_key(password, key_length):
    return hashlib.sha256(password).digest()[:key_length]

def get_hmac(key, message):
    return hmac.HMAC(key, message, hashlib.sha256)

def encrypt(block, offset, out_file):
    pad = False
    leftovers = len(block)%block_size
    if leftovers:
        pad = True

    if pad:
        padding_bytes = block_size - leftovers
        block += "0"*(padding_bytes - 1)
        block += str(padding_bytes - 1)
    else:
        block += "0"*(block_size - 1)
        block += str(block_size - 1)

    password = 'password'
    key = get_key(password, 32)
    h = hmac.new(key,'', hashlib.sha256)

    h.update(block)

    digest = h.hexdigest()
   
    iv = str(offset)
    ctr = Crypto.Util.Counter.new(128, initial_value=long(iv))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    out_file.seek(offset)
    out_file.write(cipher.encrypt(block))
    #out_file.write(block)

def decrypt(block, offset, pad):
    password = 'password'
    key = get_key(password, 32)
    h = hmac.new(key,'', hashlib.sha256)

    iv = str(offset)
    ctr = Crypto.Util.Counter.new(128, initial_value=long(iv))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    dec = cipher.decrypt(block)

    if pad:
        padding_bytes = int(dec[-1]) + 10*int(dec[-2])
        new_dec = dec[:-padding_bytes-1]
    else:
        #block += "0"*(block_size - 1)
        #block += str(block_size - 1)
        #print(block)
        new_dec = dec
        pass

    h.update(dec)

    digest = h.hexdigest()

    return new_dec
    #return new_block

def enc_helper(in_file, out_file):
    done = False
    offset = 0
    while not done:
        block = in_file.read(amount)
        if not block:
            done = True
        else:
            encrypt(block, offset, out_file)
        offset +=128

def dec_helper(in_file, out_file):
    done = False

    in_file.seek(0, os.SEEK_END)
    file_len = in_file.tell()
    in_file.seek(0, os.SEEK_SET)

    offset = 0
    while not done:
        block = in_file.read(amount)
        if not block:
            done = True
        else:
            pad = False
            if in_file.tell() == file_len:
                pad = True
            dec = decrypt(block, offset, pad)
            print(dec),
            out_file.seek(offset, 0)
            out_file.write(dec)
        offset +=128

def main():
    #f = open('/home/taylor/Downloads/datalab-handout/bits.c', 'rb')
    f = open('/home/taylor/Custos/custos-client-dropbox/testfile.txt', 'rb')
    out = open('testfile2.txt', 'wb')
    enc_helper(f, out)
    f.close()
    out.close()
    
    f = open('testfile2.txt', 'rb')
    out = open('testfile3.txt', 'wb')
    dec_helper(f, out)
    f.close()
    out.close()

if __name__ == '__main__':
    main()
