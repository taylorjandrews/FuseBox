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
from time import time
from datetime import datetime

fuse.fuse_python_api = (0, 2)

class DropboxInit():
    def __init__(self):
        config = ConfigParser.SafeConfigParser()
        config.read('./dropfuse.ini')
        access_token = config.get('oauth', 'token')

        self.client = dropbox.client.DropboxClient(access_token)

    def getData(self, path):
        try:
            metadata = self.client.metadata(path)
            #print(metadata)
            if 'is_deleted' in metadata:
                if metadata['is_deleted']:
                    return -1
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
            fh = os.fdopen(fd, 'w+')
            return fh
        else:
            db_fd, temp_path = tempfile.mkstemp(prefix='drop_')
            fu_fd = os.dup(db_fd)
            os.remove(temp_path)
            
            data = self.dropfuse.client.get_file(path)
            
            db_fh = os.fdopen(db_fd, 'w+')
            for line in data:
                db_fh.write(line)
            db_fh.close()

            fh = os.fdopen(fu_fd, 'w+')
            return fh

    def read(self, path, length, offset, fh):
        fh.seek(offset)
        return fh.read(length)

    def write(self, path, buf, offset, fh):
        fh.seek(offset, 0)
        fh.write(buf)

        return len(buf)

    def release(self, path, flags, fh):
        metadata = self.dropfuse.getData(path)
        fh.seek(0)

        if fh.mode == 'w+':
            fh.seek(0,0)
            response = self.dropfuse.client.put_file(path, fh, overwrite=True)
        
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
        f = open(temp_path, 'w+')
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
