#!/usr/bin/env python

import fuse

fuse.fuse_python_api = ( 0, 2 )

class ExampleFS( fuse.Fuse ):
    def __init__( self, *args, **kw ):
        fuse.Fuse.__init__( self, *args, **kw )

if __name__ == '__main__':
    examplefs = ExampleFS()
    args = examplefs.parse( errex = 1 )
    examplefs.main()
