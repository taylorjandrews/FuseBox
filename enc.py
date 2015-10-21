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

def enc(in_file, out_file, offset):
    password = 'password'
    key = get_key(password, 32)

    iv = str(offset)
    ctr = Crypto.Util.Counter.new(128, initial_value=long(iv))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)
 
    done = False
    while not done:
        ch = in_file.read(1)
        if not ch:
            done = True
        else:
            out_file.write(cipher.encrypt(ch))

def dec(in_file, out_file, offset):
    password = 'password'
    key = get_key(password, 32)

    iv = str(offset)
    ctr = Crypto.Util.Counter.new(128, initial_value=long(iv))

    cipher = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CTR, counter=ctr)
 
    done = False
    while not done:
        ch = in_file.read(1)
        if not ch:
            done = True
        else:
            print ch
            out_file.write(cipher.decrypt(ch))

def main():
    f = open('testfile.txt', 'rb')
    out = open('testfile2.txt', 'wb')
    enc(f, out, 1)
    f.close()
    out.close()
    
    f = open('testfile2.txt', 'rb')
    out = open('testfile3.txt', 'wb')
    dec(f, out, 1)
    f.close()
    out.close()

if __name__ == '__main__':
    main()
