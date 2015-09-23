import ConfigParser
import dropbox

app_key = '74jo3vcthabvmif'
app_secret = 'bmp6zczabmhp0bx'

def main():
    cfile = open("./dropfuse.ini", 'w')
    config = ConfigParser.SafeConfigParser()
    config.add_section('oauth')

    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
    authorize_url = flow.start()
    print '1. Go to: ' + authorize_url
    print '2. Click "Allow" (you might have to log in first)'
    print '3. Copy the authorization code.'
    code = raw_input("Enter the authorization code here: ").strip()

    access_token, user_id = flow.finish(code)
    config.set('oauth', 'token', access_token)
    config.write(cfile)

    cfile.close()

if __name__ == '__main__':
    main()
