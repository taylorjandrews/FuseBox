# Taylor Andrews
# File to set up Dropbox oauth

import ConfigParser
import dropbox

# App key and secret for Custos Dropbox App
app_key = 'co882ncielif2jf'
app_secret = 'jm6f3cc4st17h3s'


def main():
    # Open the ini
    # Will create the file if it isn't here
    cfile = open("./dropfuse.ini", 'w')
    config = ConfigParser.SafeConfigParser()
    config.add_section('oauth')

    # Have the user authenticate their Dropbox manually
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
    authorize_url = flow.start()

    print '1. Go to: ' + authorize_url
    print '2. Click "Allow" (you might have to log in first)'
    print '3. Copy the authorization code.'

    code = raw_input("Enter the authorization code here: ").strip()

    # Write the oauth token to the config file
    access_token, user_id = flow.finish(code)
    config.set('oauth', 'token', access_token)
    config.write(cfile)

    # Close the ini
    cfile.close()

if __name__ == '__main__':
    main()
