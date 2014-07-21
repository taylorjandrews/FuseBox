#!/usr/bin/env python

import os, sys
import dropbox
from errno import *
from stat import *
import fcntl
import fuse
from fuse import Fuse

fuse.fuse_python_api = (0, 2)

appinfo = open("python-examples/appkey.txt",'r')
APP_KEY = appinfo.readline().strip()
APP_SECRET = appinfo.readline().strip()
ACCESS_TOKEN = appinfo.readline().strip()

class DropboxInfo():
    def __init__(self):
        self.client = dropbox.client.DropboxClient(ACCESS_TOKEN)
        self.files = {}
        self.directories = {}

    def makefiles(self):
        self.folderdata = self.client.metadata('/Custos')
        for self.f in self.folderdata['contents']:
            self.f['path'] = self.f['path'].split('/')
            filename = self.f['path'][len(self.f['path'])-1]
            is_dir = self.f['is_dir']
            size = self.f['size']
            modified = self.f['modified']
            self.files[filename] = {'name': filename, 'size': size, 'is_dir': is_dir,
                                     'modified': modified}

class ENCFS(Fuse):
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.drop = DropboxInfo()
        self.drop.makefiles()

    def getattr(self, path):
        for f in self.drop.files:
            if not self.drop.files[f]['is_dir']:
                return dict(
                    st_mode = S_IFREG | 0444,
                    st_size = self.drop.files[f]['size'],
                    st_atime = self.drop.files[f]['modified'],
                    st_mtime = self.drop.files[f]['modified'],
                    st_ctime = self.drop.files[f]['modified'],
                    st_nlink = 1
                    )
        if path == '/':
            return dict(
                st_mode = S_IFREG | 0755,
                st_size = 0,
                st_nlink = 3)
        else:
            return dict(
                    st_mode = S_IFREG | 0444,
                    st_size = self.drop.files[f]['size'],
                    st_atime = self.drop.files[f]['modified'],
                    st_mtime = self.drop.files[f]['modified'],
                    st_ctime = self.drop.files[f]['modified'],
                    st_nlink = 1
                    )

    def readdir(self, path, offset):
        names  = ['.', '..']
        if path == '/':
            for f in self.drop.files:
                names.append(self.drop.files[f]['name'])
        return names

def main():
    usage = Fuse.fusage

    encfs = ENCFS(version="%prog " + fuse.__version__, usage = usage)
    encfs.parser.add_option(mountopt="root", metavar="PATH", default='/', help="asdf")
    encfs.parse(values=encfs, errex=1)
    encfs.main()

if __name__ == '__main__':
    main()
