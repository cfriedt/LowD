import os
import platform
import stat
import magic
import tempfile
import glob
import time
from enum import Enum

from machotools.machofile import MachOFile
from machotools.enums import *

from Symbol import SymbolType
from Symbol import Symbol

class InputFileType(Enum):
    OBJECT=0
    ARCHIVE=1
    DYLIB=2

class InputFile(object):
    def __init__(self, path, explicit=True):
        self._type = None
        self._path = path
        # 'explicit' is mainly for dyld's that are explicitly added with '-lfoo' or '/usr/lib/libfoo.dylib'
        # if a dyld is pulled in as a dependency of another dyld, explicit
        # should be false
        self._explicit = explicit

        self._symbols = []

    def get_type(self):
        return self._type

    def get_path(self):
        return self._path

    def get_symbols(self):
        if not self._symbols:
            symbols = []
            mf = MachOFile(self._path)
            for offset, msym in mf.get_symtab().items():
                if not set([NLType.N_UNDF, NLTypeMask.N_EXT]).intersection(msym._n_type):
                    # only count undefined symbols and global symbols
                    continue
                type = SymbolType.UNDEFINED if NLType.N_UNDF in msym._n_type else SymbolType.DEFINED
                symbols.append(Symbol(msym._n_name, self._path, type))

            self._symbols = symbols
        return self._symbols

    def __repr__(self):
        return self._path

class ObjectInputFile(InputFile):
    def __init__(self, path):
        InputFile.__init__(self, path)
        self._type = InputFileType.OBJECT

# def link_archive(self, input):
#     # print(f'would link archive "{input}"')
#     td = tempfile.TemporaryDirectory()
#     self._tempdirs.append(td)
#     td = td.name
#     for f in Driver.arx(input, td):
#         self.link_object(f)


class ArchiveInputFile(InputFile):
    def __init__(self, path):
        InputFile.__init__(self, path)
        self._type = InputFileType.ARCHIVE


class DyldInputFile(InputFile):
    def __init__(self, path, explicit):
        InputFile.__init__(self, path, explicit)
        self._type = InputFileType.DYLIB

def create(path, explicit=True):
    mach = platform.machine()
    filetype = magic.from_file(path)

    if 'Mach-O' in filetype:
        if 'universal binary' in filetype and mach not in filetype:
            return None

        elif 'executable' in filetype:
            return None

        elif 'object' in filetype:
            return ObjectInputFile(path)

        elif 'dynamically linked shared library' in filetype:
            return DyldInputFile(path, explicit)

    elif 'current ar archive random library' in filetype:
        return ArchiveInputFile(path)

    return None
