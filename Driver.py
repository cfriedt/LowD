#!/usr/bin/env python3

"""L03D2 - experimental replacement for ld on macOS
"""

import os
import platform
import stat
import magic
import tempfile
import glob
import time
from Symbol import Symbol

from machotools.machofile import MachOFile
from machotools.enums import *

import unfuck

import InputFile
from InputFile import InputFileType
import SymbolTable

DEFAULT_LIBRARY_PATH = ['/usr/local/lib', '/usr/lib', '/lib']


class Driver(object):
    def __init__(self, args):
        # https://www.linuxjournal.com/article/6463
        # ^^ old school
        #
        # https://lld.llvm.org/NewLLD.html
        # ^^ new school
        #
        # new school sounds better, imho

        self._args = args
        # append default search dirs
        if not self._args.L:
            self._args.L = []
        for d in DEFAULT_LIBRARY_PATH:
            if d not in self._args.L:
                self._args.L.append(d)

        # recursively add libSystem.dylib by default and all
        # of its dependencies
        if not self._args.l:
            self._args.l = []
        if 'System' not in self._args.l:
            self._args.l.append('System')

        # unordered_map<path,InputFile>
        self._objects = dict()
        self._archives = dict()
        self._dylibs = dict()

        # for marking -lname as resolved
        # unordered_set<name>
        self._resolved = set()

        # defined, undefined, and lazy symbol table
        self._symbol_table = SymbolTable.SymbolTable()

    def link(self):
        # for each input file, put all symbols within into the symbol table
        self.collect_input_files()
        self.populate_symbol_table()

        # check if there are no remaining undefined symbols
        self.check_for_undefined_symbols()

        print(self._symbol_table)

    def collect_input_file(self, input):
        input_file = InputFile.create(input)

        if not input_file:
            # raise an immediate error for explicitly named inputs
            raise ValueError(f'ld: invalid input file "{input}"')

        if input_file.get_type() == InputFileType.OBJECT:
            self._objects[input_file.get_path()] = input_file
        elif input_file.get_type() == InputFileType.ARCHIVE:
            self._archives[input_file.get_path()] = input_file
        elif input_file.get_type() == InputFileType.DYLIB:
            self._dylibs[input_file.get_path()] = input_file

    def resolve_and_collect_input_file(self, name):
        # skip already-resolved libraries
        if name in self._resolved:
            return

        # find lib[name].a or lib[name].dylib
        possible_inputs = self.resolve(name)

        input_file = None
        for input in possible_inputs:
            input_file = InputFile.create(input)
            if input_file:
                break

        if not input_file:
            if name == 'System':
                # XXX: annoyance. should not be required to unfuck Apple's system libs
                unfuck.apple_system_libs()
            # error when no candidate exists for an explicitly linked library
            raise ValueError(f'ld: library not found for -l{name}')

        if input_file.get_type() == InputFileType.ARCHIVE:
            self._archives[input_file.get_path()] = input_file
        elif input_file.get_type() == InputFileType.DYLIB:
            exports = Driver.get_reexported_dylibs(input_file.get_path())
            for x in exports:
                print(f'checking for -l{x}')
                self.resolve_and_collect_input_file(x)
            print(f'added dylib {input_file}')
            self._dylibs[input_file.get_path()] = input_file
        else:
            # objects are not allowed to be linked with -l
            raise ValueError(f'ld: not a library: {input_file._path}')

        self._resolved.add(name)

    def collect_input_files(self):
        # iterate through input files
        for input in self._args.input:
            self.collect_input_file(input)

        # iterate through linked libraries
        for name in self._args.l:
            self.resolve_and_collect_input_file(name)

    def resolve(self, name):
        possible_inputs = []
        for dir in self._args.L:
            # first, try to link against a .dylib, then a .a
            for ext in ['.dylib', '.a']:

                # if the '-static' argument is passed, do not use any .dylibs
                # EXCEPT if it is libSystem.dylib!!
                if ext == '.dylib' and self._args.static and name != 'System':
                    continue

                path = dir + '/lib' + name + ext

                if os.path.islink(path):
                    path = os.path.realpath(path)

                if os.path.isfile(path):
                    possible_inputs.append(path)

        return possible_inputs

    def populate_symbol_table(self):
        for f in self._objects.values():
            self._symbol_table.add_symbols(f)

        for f in self._archives.values():
            self._symbol_table.add_symbols(f)

        for f in self._dylibs.values():
            self._symbol_table.add_symbols(f)

    def check_for_undefined_symbols(self):

        # FIXME: look at args to see if undefined should be ignored, cause warning, error..

        err_msg = None
        for (name, sym) in self._symbol_table.get_undefined_symbols().items():
            if not err_msg:
                err_msg = f'Undefined symbols for architecture {platform.machine()}:\n'
            err_msg += f'  "{name}", referenced from:\n'
            paths = sorted(sym.get_refs())
            for path in paths:
                funcs = ['(fixme)', ]
                for func in funcs:
                    err_msg += f'      {func} in {os.path.basename(path)}\n'
        if err_msg:
            print(err_msg)
            raise ValueError(
                f'ld: symbol(s) not found for architecture {platform.machine()}')

    def finish(self):
        self.write_output_file()

    def process_linker_script(self):
        pass

    def write_output_file(self):
        try:
            os.remove(self._args.o)
        except BaseException:
            pass

        with open(self._args.o, 'w') as f:
            pass

        st = os.stat(self._args.o)
        os.chmod(self._args.o, st.st_mode | stat.S_IEXEC)

    @staticmethod
    def arx(archive, path):
        objs = []
        archive_path = os.path.abspath(archive)
        origdir = os.getcwd()

        os.chdir(path)

        os.system(f'ar x {archive_path}')
        time.sleep(1)
        for fn in glob.glob('*.o'):
            objs.append(f'{path}/{fn}')

        os.chdir(origdir)

        return objs

    @staticmethod
    def get_reexported_dylibs(input):
        mf = MachOFile(input)
        deps = []
        verb = False
        if input == '/Users/cfriedt/Desktop/libraries/usr/lib/system/libxpc.dylib':
            verb = True
        for offset, lc in mf.get_load_commands().items():
            if verb:
                print(lc)
            cmd = lc.get_cmd()
            if cmd == LCCommand.LC_REEXPORT_DYLIB or cmd == LCCommand.LC_LOAD_UPWARD_DYLIB:
                # these come in full paths that are not even necessarily present or correct
                # just use the 'resolve' machinery for now
                name = lc.get_dylib_name(input)
                name = (str(os.path.basename(name))[3:]).replace('.dylib', '')
                deps.append(name)
        return deps
