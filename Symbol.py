from enum import Enum


class SymbolType(Enum):
    DEFINED = 0
    UNDEFINED = 1
    LAZY = 2


class Symbol(object):
    def __init__(self, name, path, type):
        self._name = name
        self._type = type
        self._path = path

        # absolute pathnames of object files or dylibs that refer to this symbol
        self._refs = set()

        if type == SymbolType.UNDEFINED:
            self._refs.add(path)
        else:
            self._path = path

    def add_ref(self, path):
        assert(path != None)
        self._refs.add(path)

    def get_refs(self):
        return self._refs

    def define(self, path):
        assert(self._type == SymbolType.UNDEFINED)
        self._type = SymbolType.DEFINED
        self._path = path

    def __repr__(self):
        return f'{{name: {self._name}, path: {self._path}, type: {self._type}}}'
