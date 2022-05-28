import os
import sys

# python hasn't yet figured out argument parsing with argparse, so..
def argv():
    argv = []
    input = []

    for i in range(len(sys.argv)):
        a = sys.argv[i]

        # change '-Lpath' to ['-L', 'path']
        if a.startswith('-L') and len(a) > len('-L'):
            argv.append('-L')
            argv.append(a[2:])
            continue

        # change '-lfoo' to ['-l', 'foo']
        if a.startswith('-l') and len(a) > len('-l'):
            if a == '-lto_library':
                argv.append('-lto_library')
                argv.append(sys.argv[i + 1])
                i += 1
            else:
                argv.append('-l')
                argv.append(a[2:])
                continue
        
        if a.endswith('.a') or a.endswith('.o'):
            input.append(a)
            continue

        argv.append(a)
    
    # append positional parameters last
    for i in input:
        argv.append(i)

    sys.argv = argv
        

def apple_system_libs():
    url1 = 'https://lapcatsoftware.com/articles/bigsur.html'
    url2 = 'https://ladydebug.com/blog/2021/04/16/big-sur-and-built-in-dynamic-linker-cache/'

    msg = f"""
ATTENTION: please follow the instructions at the URL below to
extract System libraries from the System dyld cache.

{url1}

ATTENTION: Assuming you have extracted to DIR, please ensure
that you have added LDFLAGS="-LDIR/usr/lib -LDIR/usr/lib/system"

ATTENTION: Also ensure that libSystem.dylib is a symbolic link to libSystem.B.dylib

cd DIR/usr/lib
ln -sf libSystem.B.dylib libSystem.dylib

More information can be found at the URL below

{url2}

"""
    print(msg)
