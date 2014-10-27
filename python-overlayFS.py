#!/usr/bin/env python

import os, sys
import dropbox
from errno import *
from stat import S_IFDIR, S_IFLNK, S_IFREG
import fcntl
import fuse
from fuse import Fuse
from time import time

fuse.fuse_python_api = (0, 2)

appinfo = open("appkey.txt",'r')
APP_KEY = appinfo.readline().strip()
APP_SECRET = appinfo.readline().strip()
ACCESS_TOKEN = appinfo.readline().strip()

class DropboxInit():
    def __init__(self):
        self.client = dropbox.client.DropboxClient(ACCESS_TOKEN)
        self.files = {}
        self.directories = {}

    def getfiles(self, path = '/'):   
        folder_metadata = self.client.metadata(path)
        if 'contents' in folder_metadata:
            for f in folder_metadata['contents']:
                path = f['path'].split('/', 1)
                self.files[self.getpath(f)] = f
                self.getfiles(path[-1])

    def getfileInfo(self):
        self.getfiles()
        self.sortkeys = []
        self.dirs = []
        for f in self.files.keys():
            name = f.split('/')
            name = name[len(name)-1]
            dirname = f.rsplit('/',1)[0]

            self.files[f]['name'] = name
            self.files[f]['dir'] = dirname
            if self.files[f]['dir'] == '':
                self.files[f]['dir'] = '/'
            
        #    self.sortkeys.append(f)
        #    self.dirs.append(self.files[f]['dir'])
        #self.sortkeys.append('/')
        #self.sortkeys.sort()
        #self.dirs.sort()

    def getpath(self, f):
        return f['path']

class ENCFS(Fuse):
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.drop = DropboxInit()
        self.drop.getfileInfo()
        self.t = time()

    def getattr(self, path):
        st = fuse.Stat()
        st.st_mode = S_IFDIR | 0755
        st.st_nlink = 3
        st.st_size = 4096
        st.st_ctime = self.t
        st.st_mtime = self.t
        st.st_atime = self.t

        return st

        
        # st = fuse.Stat()
        # if path == '/':
        #     st.st_mode = S_IFDIR | 0755
        #     st.st_ctime = self.t
        #     st.st_mtime = self.t
        #     st.st_atime = self.t
        #     st.st_nlink = 3

        #     return st

        # else:
        #     if path in self.drop.files:
        #         f = self.drop.files[path]
        #         st.st_mtime = self.t
        #         st.st_atime = st.st_mtime
        #         st.st_ctime = st.st_mtime
                
        #         if ('is_dir' in f and f['is_dir']):
        #             st.st_mode = S_IFDIR | 0755
        #             st.st_nlink = 1
        #             st.st_size = f['size']
        #         else:
        #             st.st_mode = S_IFREG | 0666
        #             st.st_nlink = 1
        #             st.st_size = f['size']

        #         return st
        
    def readdir(self, path, offset):
        entries = [fuse.Direntry('.'),
                   fuse.Direntry('..') ]
        
        for f in self.drop.files.keys():
            print(self.drop.files[f]['dir'])
            if self.drop.files[f]['dir'] == path:
                #use lstrip for just / to make sure it doesn't break
                #test to see if the encoding fix was actually a fix
                #change docstrings to by line comments using alt ;
                entries.append(fuse.Direntry(f.encode('utf-8')[1:]))
        
        print([e.name for e in entries])
        return entries

    def open(self, path, flags):
        return 0

    def read(self, path, length, offset):
        return 0

def main():
    encfs = ENCFS()
    encfs.parse(errex=1)
    encfs.main()

if __name__ == '__main__':
    main()
