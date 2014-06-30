import dropbox

appinfo = open("appkey.txt",'r')
APP_KEY = appinfo.readline().strip()
APP_SECRET = appinfo.readline().strip()

flow = dropbox.client.DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

authorize_url = flow.start()

authorize_url = flow.start()
print '1. Go to: ' + authorize_url
print '2. Click "Allow" (you might have to log in first)'
print '3. Copy the authorization code.'
code = raw_input("Enter the authorization code here: ").strip()

access_token, user_id = flow.finish(code)

client = dropbox.client.DropboxClient(access_token)

folder_metadata = client.metadata('/CSCI1300')
for entry in folder_metadata['contents']:
    print(entry['path'])
