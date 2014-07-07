import dropbox

appinfo = open("appkey.txt",'r')
APP_KEY = appinfo.readline().strip()
APP_SECRET = appinfo.readline().strip()
ACCESS_TOKEN = appinfo.readline().strip()

client = dropbox.client.DropboxClient(ACCESS_TOKEN)

f = open("/home/taylor/Documents/testdoc4.txt", 'r')
client.put_file('/Custos/TestFolder/testdoc4.txt', f)
