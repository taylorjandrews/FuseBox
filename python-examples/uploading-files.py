from dropbox import *

APP_KEY = '6p9suiav6mo1qg6'
APP_SECRET = 'qnxma4e9qkjdu9o'
ACCESS_TYPE = 'app_folder'

sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
sess.set_token("jh4s0a67jeg1sssz", "zd7w4pensthme4u")

client = client.DropboxClient(sess)

f = open('test-file.txt', 'rb')
responce = client.put_file('/test-file.txt', f)
print "uploaded:", responce
