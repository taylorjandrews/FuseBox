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

    def getData(self, path):
        try:
            metadata = self.client.metadata(path)
            return metadata
        
        except dropbox.rest.ErrorResponse as e:
            # for fuse calls that are not in the users dropbox e.status will be 404
            if e.status == 404:
                return -1
            return -1

    def parsePath(self, path):
        name = path.split('/')
        name = name[len(name)-1]
        dirname = path.rsplit('/',1)[0]
        if not dirname:
            dirname = '/'

        return {"name" : name, "dirname" : dirname}

    def getSize(self, metadata):
        return int(metadata['bytes'])
        
    def getTime(self):
        pass
        #strip should be modified
        #try time.time()
        #t = datetime.strptime(str(self.files[f]['modified']).strip(" +0000"), "%a, %d %b %Y %H:%M:%S")
        #self.files[f]['time'] = t

class ENCFS(Fuse):

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.dropfuse = DropboxInit()
        self.t = time()
        self.metadata = {}
        self.temp_path = ""

    def getattr(self, path):
        self.metadata = self.dropfuse.getData(path)

        if self.metadata is not -1:
            st = fuse.Stat()

            st.st_mtime = self.t
            st.st_atime = st.st_mtime
            st.st_ctime = st.st_mtime
                
            
            if self.metadata['is_dir']:
                st.st_mode = S_IFDIR | 0755
                st.st_nlink = 1
                st.st_size = 4096
                return st

            st.st_mode = S_IFREG | 0664
            st.st_size = self.dropfuse.getSize(self.metadata)
            st.st_nlink = 1

            return st

        return -2
                        
    def readdir(self, path, offset):
        #fix error if folder etc. does not exist
        entries = [fuse.Direntry('.'),
                    fuse.Direntry('..')]

        if self.metadata is not -1:
            if 'contents' in self.metadata:
                for e in self.metadata['contents']:
                    path = self.dropfuse.parsePath(e['path'])
                    entries.append(fuse.Direntry(path['name'].encode('utf-8')))
            
        return entries

    def open(self, path, flags):
        metadata = self.dropfuse.getData(path)
        if metadata is -1:
            return -1

        if metadata['is_dir']:
            return -1

        if 'is_deleted' in metadata:
            return -1
        
        db_fd, self.temp_path = tempfile.mkstemp(prefix='drop_')
        fu_fd = os.dup(db_fd)

        data = self.dropfuse.client.get_file(path)
        
        db_fh = os.fdopen(db_fd, 'wb')
        for line in data:
            db_fh.write(line)
        db_fh.close()
          
        if (flags & 3) == os.O_WRONLY:
            fu_fh =  os.fdopen(fu_fd, 'w+b')
            return fu_fh
        elif (flags & 3) == os.O_RDONLY:
            fu_fh = os.fdopen(fu_fd, 'rb')
            return fu_fh

    def read(self, path, length, offset, fh):
        fh.seek(offset)
        return fh.read(length)

    def write(self, path, buf, offset, fh):
        fh.seek(offset, 0)
        fh.write(buf)

        return len(buf)

    def release(self, path, flags, fh):
        metadata = self.dropfuse.getData(path)
        print("Size: ", metadata['bytes'])
        fh.seek(0, os.SEEK_END)
        if fh.mode == 'w+b':
            fh.seek(0,0)
            response = self.dropfuse.client.put_file(path, fh, overwrite=True)
        os.remove(self.temp_path)
        fh.close()

    def access(self, path, mode):
        if not os.access(path, mode):
            #raise FuseOSError(errno EACCES)
            return 0 #should be -1 but I'm not setting permissions

    def create(self, path, mode, flags):
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
        f = open(temp_path, 'w+b')
        response = self.dropfuse.client.put_file(path, f, overwrite=True)
        f.close()
        os.close(fd)
        os.remove(temp_path)
    
    def unlink(self, path):
        print("unlink")

    def utimens(self, path, ts_acc, ts_mod):
        print("utimens")
        print(type(ts_acc))
        print(str(ts_acc))

    def flush(self, path, fh):
        fh.truncate()
        data = self.dropfuse.client.get_file(path)
        for line in data:
            fh.write(line)
        fh.seek(0)

        # pos = fh.tell()
        # fh.seek(0, 0)
        # response = self.dropfuse.client.put_file(path, fh, overwrite=True)
        # fh.seek(pos)

def main():
    encfs = ENCFS()
    encfs.parse(errex=1)
    encfs.main()

if __name__ == '__main__':
    main()
