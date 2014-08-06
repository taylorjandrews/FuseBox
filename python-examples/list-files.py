import dropbox

appinfo = open("appkey.txt",'r')
APP_KEY = appinfo.readline().strip()
APP_SECRET = appinfo.readline().strip()
ACCESS_TOKEN = appinfo.readline().strip()

client = dropbox.client.DropboxClient(ACCESS_TOKEN)

folder_metadata = client.metadata('/')
print(folder_metadata)
for entry in folder_metadata['contents']:
    entry['path'] = entry['path'].split('/')
    filename = entry['path'][len(entry['path'])-1]
    print(filename)
