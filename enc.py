import Crypto.Cipher
import Crypto.Random
import Crypto.Util
import hashlib
import sys

# This function does NOT contain a salt
# Not having a salt is obviously not okay,
# but when we implement libcustos this will be replaced
def get_key(password, key_length):
    return hashlib.sha256(password).digest()[:key_length]

def enc(block, offset, out_file):
    password = 'password'
    key = get_key(password, 32)

    iv = str(offset)
    ctr = Crypto.Util.Counter.new(128, initial_value=long(iv))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    out_file.seek(offset)
    out_file.write(cipher.encrypt(block))

def dec(block, offset, out_file):
    password = 'password'
    key = get_key(password, 32)

    iv = str(offset)
    ctr = Crypto.Util.Counter.new(128, initial_value=long(iv))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)

    out_file.seek(offset)
    out_file.write(cipher.decrypt(block))
    
def enc_helper(in_file, out_file):
    done = False
    offset = 0
    while not done:
        block = in_file.read(1024)
        if not block:
            done = True
        else:
            enc(block, offset, out_file)
        offset +=1024

def dec_helper(in_file, out_file):
    done = False
    offset = 0
    while not done:
        block = in_file.read(1024)
        if not block:
            done = True
        else:
            dec(block, offset, out_file)
        offset +=1024

def main():
    f = open('/home/taylor/Downloads/datalab-handout/bits.c', 'rb')
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
