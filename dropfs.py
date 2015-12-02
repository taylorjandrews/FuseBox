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
        self.dropfuse = DropboxInit()
        self.metadata = {}
        self.externdata = ""

    def getattr(self, path):
        self.metadata = self.dropfuse.getData(path)

        if self.metadata is not -1:
            st = fuse.Stat()
            if 'modified' in self.metadata:
                try:
                    t = datetime.datetime.strptime(str(self.metadata['modified']).strip(" +0000"), "%a, %d %b %Y %H:%M:%S")
                except ValueError:
                    t = datetime.datetime.now()
            else:
                t = datetime.datetime.now()

            ut = time.mktime(t.timetuple())
            st.st_mtime = ut
            st.st_atime = st.st_mtime
            st.st_ctime = st.st_mtime


            if self.metadata['is_dir']:
                st.st_mode = S_IFDIR | 0755
                st.st_nlink = 1
                st.st_size = 4096
                return st

            metafile = False
            #metafile, metapath = self.dropfuse.getMetaFileAndPath(path)
            pathinfo = self.dropfuse.parsePath(path)

            if pathinfo['name'][:17] == ".dropboxmetadata_":
                metafile = True

            if not metafile and not self.externdata:
                #make this into a function call please
                if pathinfo['dirname'] == '/':
                    metapath = ".dropboxmetadata_" + pathinfo['name']
                else:
                    metapath = pathinfo['dirname'] + "/.dropboxmetadata_" + pathinfo['name']

                #Store copy of real file size in the metadata
                self.externdata = self.dropfuse.client.get_file(metapath).readline()

            print(self.externdata)

            st.st_mode = S_IFREG | 0664
            st.st_nlink = 1

            fsize = self.dropfuse.getSize(self.metadata)

            st.st_size = fsize

            return st

        return -2

    def unlink(self, path):
        self.dropfuse.client.file_delete(path)

    def rename(self, oldname, newname):
        self.dropfuse.client.file_move(oldname, newname)

    def mkdir(self, path, mode):
        self.dropfuse.client.file_create_folder(path)

        return 0 #can implement error handling here

    def rmdir(self, path):
        entries = self.readdir(path, 0)
        if(len(entries) > 2):
            #print("Directory contains files cannot remove.")
            print(errno.ENOTEMPTY)
            return -errno.ENOTEMPTY
        else:
            self.dropfuse.client.file_delete(path)

    def readdir(self, path, offset):
        #fix error if folder etc. does not exist
        entries = [fuse.Direntry('.'),
                    fuse.Direntry('..')]

        if self.metadata is not -1:
            if 'contents' in self.metadata:
                for e in self.metadata['contents']:
                    path = self.dropfuse.parsePath(e['path'])
                    if path['name'][:17] != ".dropboxmetadata_":
                        entries.append(fuse.Direntry(path['name'].encode('utf-8')))

        return entries

    def open(self, path, flags):
        #compare hmac
        metadata = self.dropfuse.getData(path)
        if metadata is -1:
            return -1

        if metadata['is_dir']:
            return -1

        if 'is_deleted' in metadata:
            return -1

        # This implementation relies on append, ideally the O_TRUNC flag would be used
        # print("flags:    0b{:32b}".format(flags))
        # print("O_RDONLY: 0b{:32b}".format(os.O_RDONLY))
        # print("O_WRONLY: 0b{:32b}".format(os.O_WRONLY))
        # print("O_RDWR:   0b{:32b}".format(os.O_RDWR))
        # print("O_APPEND: 0b{:32b}".format(os.O_APPEND))
        # print("O_CREAT:  0b{:32b}".format(os.O_CREAT))
        # print("O_EXCL:   0b{:32b}".format(os.O_EXCL))
        # print("O_TRUNC:  0b{:32b}".format(os.O_TRUNC))
        if ((flags & (os.O_WRONLY | os.O_APPEND)) == os.O_WRONLY):
            fd, temp_path = tempfile.mkstemp()
            os.remove(temp_path)
            fh = os.fdopen(fd, 'wb+')
            return fh
        else:
            db_fd, temp_path = tempfile.mkstemp(prefix='drop_')
            fu_fd = os.dup(db_fd)
            os.remove(temp_path)

            data = self.dropfuse.client.get_file(path)

            db_fh = os.fdopen(db_fd, 'wb+')
            for line in data:
                db_fh.write(line)
            db_fh.close()

            fh = os.fdopen(fu_fd, 'wb+')
            return fh

    def read(self, path, length, offset, fh):
        #fh.seek(0, os.SEEK_END)
        #size = fh.tell()
        #print "size " + str(size)
        #print "o + l" + str(offset + length)
        fh.seek(offset)
        enc = fh.read(length)
        #pad = False
        #if ((offset + length) >= size):
        #    print("at end")
        #    pad = True
        #print("offset {}".format(offset))
        #fh.close()

        #dec_fd, temp_path = tempfile.mkstemp(prefix='drop_')
        #os.remove(temp_path)
        #dec_fh = os.fdpen(dec_fd, 'w+')

        #uuid, server = self.dropfuse.getServerAndID()
        uuid = self.externdata['uuid']
        server = self.externdata['server']

        dec = decrypt(enc, offset, fh, uuid, server)
        return dec

        #return fh.read(length)

    def write(self, path, buf, offset, fh):
        fh.seek(0, 0)

        uuid = self.externdata['uuid']
        server = self.externdata['server']

        dec = decrypt(fh.read(), 0, fh, uuid, server)
        #fh.seek(offset, 0)
        #print("offset {}".format(offset))
        #fh.write(buf)
        enc_size = encrypt(dec+buf, 0, fh)

        #return enc_size
        return len(buf)

    def release(self, path, flags, fh):
        pathinfo = self.dropfuse.parsePath(path)
        if pathinfo['dirname'] == '/':
            metapath = ".dropboxmetadata_" + pathinfo['name']
        else:
            metapath = pathinfo['dirname'] + "/.dropboxmetadata_" + pathinfo['name']

        fd, temp_path = tempfile.mkstemp()
        os.remove(temp_path)
        fhm = os.fdopen(fd, 'wb+')

        fhm.write(json.dumps(self.externdata))
        fhm.seek(0)

        self.dropfuse.client.put_file(metapath, fhm, overwrite=True)

        fhm.close()

        #recompute hmac
        metadata = self.dropfuse.getData(path)
        fh.seek(0)

        if fh.mode == 'wb+':
            fh.seek(0,0)
            response = self.dropfuse.client.put_file(path, fh, overwrite=True)

        fh.close()

    def access(self, path, mode):
        if not os.access(path, mode):
            #raise FuseOSError(errno EACCES)
            return 0 #should be -1 but I'm not setting permissions

    def create(self, path, mode, flags):
        if not self.externdata:
            self.externdata = {"uuid" : 0, "server" : "servername"}
        #github issue, ls attr doesn't have correct info for currently open files
        fd, temp_path = tempfile.mkstemp(prefix='drop_')
        f = open(temp_path, 'w+b')
        response = self.dropfuse.client.put_file(path, f, overwrite=True)
        os.remove(temp_path)
        return f

    #def ftruncate(self, path, length, fh):
        #truncate the tempfile denoted by fh
        #print("ftruncate")

    def truncate(self, path, length):
        fd, temp_path = tempfile.mkstemp()
        f = open(temp_path, 'wb+')
        response = self.dropfuse.client.put_file(path, f, overwrite=True)
        f.close()
        os.close(fd)
        os.remove(temp_path)
        return 0

    def utimens(self, path, ts_acc, ts_mod):
        print("utimens")
        print(type(ts_acc))
        print(str(ts_acc))

    def flush(self, path, fh):
        pos = fh.tell()
        fh.seek(0, 0)
        response = self.dropfuse.client.put_file(path, fh, overwrite=True)
        fh.seek(pos)

        return 0

def main():
    encfs = ENCFS()
    encfs.parse(errex=1)
    encfs.main()

if __name__ == '__main__':
    main()
