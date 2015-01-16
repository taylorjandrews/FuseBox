#!/usr/bin/env python

import os, sys
import dropbox
import tempfile
from errno import *
from stat import S_IFDIR, S_IFLNK, S_IFREG
import fcntl
import fuse
from fuse import Fuse
from time import time
from datetime import datetime

fuse.fuse_python_api = (0, 2)

appinfo = open("appkey.txt",'r')
APP_KEY = appinfo.readline().strip()
APP_SECRET = appinfo.readline().strip()
ACCESS_TOKEN = appinfo.readline().strip()

class DropboxInit():
    def __init__(self):
        self.client = dropbox.client.DropboxClient(ACCESS_TOKEN)
        self.files = {}
        
    def getfiles(self, path = '/'):   
        folder_metadata = self.client.metadata(path)
        if 'contents' in folder_metadata:
            for m in folder_metadata['contents']:
                path = m['path'].split('/', 1)
                self.files[self.getpath(m)] = m
                self.getfiles(path[-1])

    def getfileInfo(self):
        self.getfiles()
        for f in self.files.keys():
            name = f.split('/')
            name = name[len(name)-1]
            dirname = f.rsplit('/',1)[0]

            self.files[f]['name'] = name
            self.files[f]['dir'] = dirname
            if self.files[f]['dir'] == '':
                self.files[f]['dir'] = '/'

            #strip should be modified
            #try time.time()
            #t = datetime.strptime(str(self.files[f]['modified']).strip(" +0000"), "%a, %d %b %Y %H:%M:%S")
            #self.files[f]['time'] = t

    def getpath(self, f):
        return f['path']

class ENCFS(Fuse):
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.dropfuse = DropboxInit()
        self.dropfuse.getfileInfo()
        self.t = time()

    def getattr(self, path):
        st = fuse.Stat()
        
        if path == '/':
            st.st_mode = S_IFDIR | 0755
            st.st_ctime = self.t
            st.st_mtime = self.t
            st.st_atime = self.t
            st.st_nlink = 3
            st.st_size = 4096

            return st

        else:
            if path in self.dropfuse.files:
                f = self.dropfuse.files[path]
                st.st_mtime = self.t
                st.st_atime = st.st_mtime
                st.st_ctime = st.st_mtime
                
                if ('is_dir' in f and f['is_dir']):
                    st.st_mode = S_IFDIR | 0755
                    st.st_nlink = 1
                    st.st_size = 4096
                else:
                    st.st_mode = S_IFREG | 0666
                    st.st_nlink = 1
                    st.st_size = int(f['bytes'])

                return st
        
    def readdir(self, path, offset):
        #fix error if folder etc. does not exist
        entries = [fuse.Direntry('.'),
                   fuse.Direntry('..') ]
        
        for f in self.dropfuse.files.keys():
            if self.dropfuse.files[f]['dir'] == path:
                entries.append(fuse.Direntry(self.dropfuse.files[f]['name'].encode('utf-8')))

        return entries

    def open(self, path, flags):
        if path not in self.dropfuse.files:
            return -1

        if self.dropfuse.files[path]['is_dir']:
            return -1
        
        #self.fd = self.dropfuse.client.get_file(path)
        
        #file descriptor
        fd, temp_path = tempfile.mkstemp()
        #os.close(fd)

        data = self.dropfuse.client.get_file(path)
        
        f = os.fdopen(fd, 'wb')
        for line in data:
            f.write(line)
        
        if (flags & 3) == os.O_WRONLY:
            return open(temp_path, 'wb')
        elif (flags & 3) == os.O_RDONLY:
            return open(temp_path, 'rb')

    def read(self, path, length, offset, fh):
        fh.seek(offset)
        return fh.read(length)

    def write(self, path, buf, offset, fh):
        fh.seek(offset)
        fh.write(buf)
        return len(buf)

    def release(self, path, flags, fh):
        if fh.mode == 'wb':
            response = self.dropfuse.client.put_file(path, fh)
            print response
        #need an os.remove(temp_path) call potentially
        fh.close()

    def truncate(self, path, offset):
        pass
        
def main():
    encfs = ENCFS()
    encfs.parse(errex=1)
    encfs.main()

if __name__ == '__main__':
    main()
