# Include the Dropbox SDK
from dropbox import client, rest, session

# Get your app key and secret from the Dropbox developer website
APP_KEY = '6p9suiav6mo1qg6'
APP_SECRET = 'qnxma4e9qkjdu9o'
ACCESS_TYPE = 'app_folder'

sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
sess.set_token("jh4s0a67jeg1sssz", "zd7w4pensthme4u")

client = client.DropboxClient(sess)

'''

request_token = sess.obtain_request_token()
url = sess.build_authorize_url(request_token)
 
# Make the user sign in and authorize this token
print "url:", url
print "Please visit this website and press the 'Allow' button, then hit 'Enter' here."
raw_input()
 
# This will fail if the user didn't visit the above URL
access_token = sess.obtain_access_token(request_token)

'''
