#!/usr/bin/env python

import os, sys
import dropbox
import ConfigParser
import tempfile
import errno
from stat import S_IFDIR, S_IFLNK, S_IFREG
import fcntl
import fuse
from fuse import Fuse
import time
import datetime
from encryptor import encrypt, decrypt
import json

fuse.fuse_python_api = (0, 2)

class DropboxInit():
    # Read the config to get the oauth
    def __init__(self):
        config = ConfigParser.SafeConfigParser()
        config.read('./dropfuse.ini')
        access_token = config.get('oauth', 'token')

        self.client = dropbox.client.DropboxClient(access_token)

    # Given a file path, get the data from dropbox
    def getData(self, path):
        try:
            metadata = self.client.metadata(path)

            # If the file is deleted, don't return metadata for it
            # This is necessary since Dropbox keeps track of deleted files
            if 'is_deleted' in metadata:
                if metadata['is_deleted']:
                    return -1

            return metadata

        except dropbox.rest.ErrorResponse as e:
            # For fuse calls that are not in the users dropbox e.status will be 404
            # Potential to edit error codes based on rest responses
            if e.status == 404:
                return -1
            return -1

    # Split a path into it's directory and file name
    # Returns a dictionary
    def parsePath(self, path):
        name = path.split('/')
        name = name[len(name)-1]
        dirname = path.rsplit('/',1)[0]

        # In the case of a blank dirname, we are at the root
        if not dirname:
            dirname = '/'

        return {"name" : name, "dirname" : dirname}

    # Get the file size
    def getSize(self, metadata):
        return int(metadata['bytes'])

class ENCFS(Fuse):
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.dropfuse = DropboxInit() # Initialize dropbox class
        self.metadata = {} # Initialize blank metadata
        self.externdata = "" # External metadata

    def getattr(self, path):
        # Get the metadata from dropbox
        self.metadata = self.dropfuse.getData(path)

        # If the file is found on dropbox
        if self.metadata is not -1:
            st = fuse.Stat()

            # If the modified time is in the metadata, load it in
            # Otherwise, the modified time will be the current time
            if 'modified' in self.metadata:
                try:
                    t = datetime.datetime.strptime(str(self.metadata['modified']).strip(" +0000"), "%a, %d %b %Y %H:%M:%S")
                except ValueError:
                    t = datetime.datetime.now()
            else:
                t = datetime.datetime.now()

            # Add the time to st
            ut = time.mktime(t.timetuple())
            st.st_mtime = ut
            st.st_atime = st.st_mtime
            st.st_ctime = st.st_mtime

            # If the file is a directory, set permissions to 0755 and size to 4096
            if self.metadata['is_dir']:
                st.st_mode = S_IFDIR | 0755
                st.st_nlink = 1
                st.st_size = 4096
                return st

            metafile = False # To start, assume no external metafile exists
            pathinfo = self.dropfuse.parsePath(path) # The the path infor

            # If the path begins with dropboxmetadata_ it is an external metafile
            if pathinfo['name'][:17] == ".dropboxmetadata_":
                metafile = True

            # If there isn't a metafile, create one
            if not metafile and not self.externdata:
                if pathinfo['dirname'] == '/':
                    metapath = ".dropboxmetadata_" + pathinfo['name'] # No need to append path for root
                else:
                    metapath = pathinfo['dirname'] + "/.dropboxmetadata_" + pathinfo['name']

                # Read the metafile from dropbox according to the tabulated metapath
                self.externdata = self.dropfuse.client.get_file(metapath).readline()

            # Non folder files should be opened in mode 0664
            st.st_mode = S_IFREG | 0664
            st.st_nlink = 1 # One hard link

            fsize = self.dropfuse.getSize(self.metadata) # Get the file size
            st.st_size = fsize

            return st

        return -2 # File not found

    def unlink(self, path):
        # Delete the file on dropbox to unlink
        self.dropfuse.client.file_delete(path)

    def rename(self, oldname, newname):
        # Move the file on dropbox to rename
        self.dropfuse.client.file_move(oldname, newname)

    def mkdir(self, path, mode):
        # Create a folder on dropbox for mkdir
        self.dropfuse.client.file_create_folder(path)

        return 0 # can implement error handling here

    def rmdir(self, path):
        entries = self.readdir(path, 0) # Get the number of files in the folder

        if(len(entries) > 2):
            # Directory contains files, we cannot remove it
            print(errno.ENOTEMPTY)
            return -errno.ENOTEMPTY
        else:
            # If there aren't any files, we can remove the directory
            self.dropfuse.client.file_delete(path)

    def readdir(self, path, offset):
        # Initialize entries in the dir with special files . and ..
        entries = [fuse.Direntry('.'),
                    fuse.Direntry('..')]

        # If the file is in fact in dropbox
        if self.metadata is not -1:
            # Loop through the contents
            if 'contents' in self.metadata:
                for e in self.metadata['contents']:
                    path = self.dropfuse.parsePath(e['path'])

                    # If the path is an external metafile, do not print it during ls
                    if path['name'][:17] != ".dropboxmetadata_":
                        entries.append(fuse.Direntry(path['name'].encode('utf-8')))

        return entries

    def open(self, path, flags):
        #compare hmac
        metadata = self.dropfuse.getData(path)

        # If the file is not in dropbox, do not open it
        if metadata is -1:
            return -1

        # Can't open directories
        if metadata['is_dir']:
            return -1

        # Don't open deleted files (This should be caught by -1 above)
        if 'is_deleted' in metadata:
            return -1

        # This implementation relies on append, ideally the O_TRUNC flag would be used
        if ((flags & (os.O_WRONLY | os.O_APPEND)) == os.O_WRONLY):
            fd, temp_path = tempfile.mkstemp() # Make a tempfile
            os.remove(temp_path) # Remove the temp path

            fh = os.fdopen(fd, 'wb+') # Open the temp file
            return fh
        else:
            db_fd, temp_path = tempfile.mkstemp(prefix='drop_')
            fu_fd = os.dup(db_fd) # Duplicate the file descriptor
            os.remove(temp_path)

            data = self.dropfuse.client.get_file(path) # Get the data

            db_fh = os.fdopen(db_fd, 'wb+')

            # Write the data using the dupicate, then close it
            for line in data:
                db_fh.write(line)
            db_fh.close()

            fh = os.fdopen(fu_fd, 'wb+') # Open the temp file
            return fh

    def read(self, path, length, offset, fh):
        fh.seek(offset)
        enc = fh.read(length) # Get the data

        # Get information from metadata for Custos
        uuid = self.externdata['uuid']
        server = self.externdata['server']

        # Actually decrypt the data
        dec = decrypt(enc, offset, fh, uuid, server)
        return dec

    def write(self, path, buf, offset, fh):
        fh.seek(0, 0)

        # Get information from metadata for Custos
        uuid = self.externdata['uuid']
        server = self.externdata['server']

        # Decrypt the data
        dec = decrypt(fh.read(), 0, fh, uuid, server)
        enc_size = encrypt(dec+buf, 0, fh)

        #return enc_size
        return len(buf)

    def release(self, path, flags, fh):
        pathinfo = self.dropfuse.parsePath(path)

        # Get the external metafile data
        if pathinfo['dirname'] == '/':
            metapath = ".dropboxmetadata_" + pathinfo['name']
        else:
            metapath = pathinfo['dirname'] + "/.dropboxmetadata_" + pathinfo['name']

        # Make a temporary file
        fd, temp_path = tempfile.mkstemp()
        os.remove(temp_path)
        fhm = os.fdopen(fd, 'wb+')

        # Write metadata to the temp file
        fhm.write(json.dumps(self.externdata))
        fhm.seek(0)

        # Write the metafile to Dropbox
        self.dropfuse.client.put_file(metapath, fhm, overwrite=True)

        fhm.close()

        #recompute hmac
        # Get the internal metadata
        metadata = self.dropfuse.getData(path)
        fh.seek(0)

        if fh.mode == 'wb+':
            fh.seek(0,0)
            # Write the file to Dropbox
            response = self.dropfuse.client.put_file(path, fh, overwrite=True)

        fh.close()

    def access(self, path, mode):
        # If we can't access the file
        if not os.access(path, mode):
            return 0 # Realistically should be -1

    def create(self, path, mode, flags):
        # Create the external data for the new file
        if not self.externdata:
            self.externdata = {"uuid" : 0, "server" : "servername"}

        # github issue, ls attr doesn't have correct info for currently open files
        fd, temp_path = tempfile.mkstemp(prefix='drop_')
        f = open(temp_path, 'w+b')

        # Putting the file onto dropbox
        response = self.dropfuse.client.put_file(path, f, overwrite=True)

        os.remove(temp_path)
        return f

    def truncate(self, path, length):
        fd, temp_path = tempfile.mkstemp()
        f = open(temp_path, 'wb+')

        # Put a blank file on dropbox
        response = self.dropfuse.client.put_file(path, f, overwrite=True)

        # Close all the temp files
        f.close()
        os.close(fd)
        os.remove(temp_path)

        return 0

    # def utimens(self, path, ts_acc, ts_mod):
    #     print("utimens")
    #     print(type(ts_acc))
    #     print(str(ts_acc))

    def flush(self, path, fh):
        pos = fh.tell()
        fh.seek(0, 0)

        # Write changes to Dropbox
        response = self.dropfuse.client.put_file(path, fh, overwrite=True)
        fh.seek(pos)

        return 0

def main():
    encfs = ENCFS()
    encfs.parse(errex=1)
    encfs.main()

if __name__ == '__main__':
    main()
