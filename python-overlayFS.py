#!/usr/bin/env python

import os, sys
import dropbox
from errno import *
import stat
import fcntl
import fuse
from fuse import Fuse
from time import time

fuse.fuse_python_api = (0, 2)

appinfo = open("python-examples/appkey.txt",'r')
APP_KEY = appinfo.readline().strip()
APP_SECRET = appinfo.readline().strip()
ACCESS_TOKEN = appinfo.readline().strip()

class DropboxInit():
    def __init__(self):
        self.client = dropbox.client.DropboxClient(ACCESS_TOKEN)
        self.files = {}
        self.directories = {}

    def getfiles(self):
        folder_metadata = self.client.metadata('/')
        for f in folder_metadata['contents']:
            path = self.getpath(f)
            self.files[path] = f
        
        for f in list(self.files):
            split = f.split('/')
            name = split[len(split)-1]
            split.remove(name)
            dirinfo = '/' + ''.join(split)
            
            if not dirinfo in self.files:
                self.files[dirinfo] = {'children': [], 'name': '/', 'size': 0}

            self.files[dirinfo]['children'].append(name)
            self.files[f]['name'] = name
            self.files[f]['size'] = self.files[f]['size']

            if not self.files[f]['is_dir']:
                self.files[self.getpath(f)]['children'] = []

    def getpath(self, f):
        return f['path']

    def getnlink(self, f):
        count = 0
        for child in f['children']:
            count += 1

        return count

class ENCFS(Fuse):
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.drop = DropboxInit()
        self.drop.getfiles()
        self.t = time()

    def getattr(self, path):
        t = time()
        st = fuse.Stat()
        if path in self.drop.files:
            f = self.drop.files[path]
            print("f = {:s}".format(f))
            st.st_mtime = self.t
            st.st_atime = st.st_mtime
            st.st_ctime = st.st_mtime
            
            if f['children']:
                st.st_mode = stat.S_IFDIR | 0755
                st.st_nlink = 1 + self.drop.getnlink(f)
                st.st_size = f['size']
            else:
                st.st_mode = stat.S_IFREG | 0666
                st.st_nlink = 1
                st.st_size = f['size']

            return st
        else:
            st.st_mode = stat.S_IFREG | 0444
            st.st_size = 0
            st.st_nlink = 1

            return st

    def readdir(self, path, offset):

        entries = [fuse.Direntry('.'),
                   fuse.Direntry('..') ]
        for e in self.drop.files:
            name = self.drop.files[e]['name'] 
            print("name = '{:s}'".format(name))
            print("type = {:s}".format(type(name)))
            de = fuse.Direntry(str(name))
            entries.append(de)

        print(entries)
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
