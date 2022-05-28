#!/usr/bin/env python3

import argparse
import sys

import Driver

import unfuck

def parse_args():
    parser = argparse.ArgumentParser()

    # order of positional parameters is important in python but is not guaranteed by clang
    unfuck.argv()

    # for i in range(len(sys.argv)):
    #     print(f'argv[{i}]: {sys.argv[i]}')

    # Unused arguments
    parser.add_argument('-demangle', dest='demangle',
                        help='This option is unused', action='store_true')
    parser.add_argument('-no_deduplicate', dest='no_deduplicate',
                        help='This option is unused', action='store_true')
    parser.add_argument('-lto_library', dest='lto_library', nargs=1,
                        help='This option is unused')
    parser.add_argument('-dynamic', dest='dynamic',
                        help='This option is unused', action='store_true')
    parser.add_argument('-arch', dest='arch', metavar='ARCH',
                        help='This option is unused')
    parser.add_argument('-platform_version', dest='platform_version', nargs=3,
                        help='This option is unused')

    # Used arguments
    parser.add_argument(
        '-T',
        '--script',
        dest='T',
        metavar='FILE',
        action='append',
        help='Use scriptfile as the linker script')
    parser.add_argument('-static', dest='static', metavar='PATH',
                        help='do not link against dynamic libraries')
    parser.add_argument('-syslibroot', dest='syslibroot', metavar='PATH',
                        help='macOS system library path')
    parser.add_argument('-o', dest='o', metavar='FILE', default='a.out',
                        help='Output filename (default is "a.out")')
    parser.add_argument('-L', dest='L', metavar='PATH', action='append',
                        help='Library search path')
    parser.add_argument('-l', dest='l', metavar='LIBRARY', action='append',
                        help='Linked dynamic libraries')
    parser.add_argument('input', metavar='INPUT', nargs=argparse.REMAINDER,
                        help='Object files or static libraries')

    args = parser.parse_args()

    return args


def main():
    # try:
    for i in range(1):
        args = parse_args()
        d = Driver.Driver(args)
        d.link()
        d.finish()
    # except BaseException as e:
    #     print(str(e))
    #     sys.exit(1)


if __name__ == '__main__':
    main()
