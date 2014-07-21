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
        self.folderdata = self.client.metadata('/Custos/TestFolder')
        for self.f in folderdata['contents']:
            self.f['path'] = self.f['path'].split('/')
            filename = self.f['path'][len(self.f['path'])-1]
            self.files[filename] = {'name': filename}

class ENCFS(Fuse):
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.drop = DropboxInfo()
        print(self.drop.files)

    def getattr(self, path):
        return 0

    def readdir(self, path, offset, filler):
        return 0

def main():
    usage = Fuse.fusage

    encfs = ENCFS(version="%prog " + fuse.__version__, usage = usage)
    encfs.parser.add_option(mountopt="root", metavar="PATH", default='/', help="asdf")
    encfs.parse(values=encfs, errex=1)
    encfs.main()

if __name__ == '__main__':
    main()
