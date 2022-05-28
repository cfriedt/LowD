from Symbol import SymbolType
from InputFile import InputFileType


class SymbolTable(object):
    def __init__(self):
        self._defined = dict()
        self._undefined = dict()
        self._lazy = dict()

    def add_symbols(self, input_file):
        for sym in input_file.get_symbols():
            self.add_symbol(input_file, sym)

    def add_symbol(self, input_file, sym):
        if sym._type == SymbolType.UNDEFINED:
            if sym._name in self._defined.keys():
                return

            if sym._name in self._lazy.keys():
                self._defined[sym._name] = self._lazy[sym._name]
                del self._lazy[sym._name]
            else:
                if sym._name in self._undefined.keys():
                    self._undefined[sym._name]._refs = self._undefined[sym._name]._refs.union(
                        sym.get_refs())
                else:
                    self._undefined[sym._name] = sym
        elif sym._type == SymbolType.DEFINED:
            if sym._name in self._defined.keys():
                if input_file.get_type() in [InputFileType.OBJECT, InputFileType.ARCHIVE]:
                    # If the same symbol is defined in an object file or archive it is an error
                    raise ValueError(
                        f'ld: multiply-defined symbol {sym._name}')
                # Ignore already-defined symbols if they appear in shared libraries
                return

            self._defined[sym._name] = sym
            if sym._name in self._undefined.keys():
                for ref in self._undefined[sym._name].get_refs():
                    self._defined[sym._name].add_ref(ref)

        elif sym._type == SymbolType.LAZY:
            if sym._name in self._undefined.keys():
                self._defined[sym._name] = sym
                del self._undefined[sym._name]
            else:
                self._lazy[sym._name] = sym
        else:
            raise ValueError('invalid type')

    def get_symbols(self, type=SymbolType.DEFINED):
        if type == SymbolType.DEFINED:
            return self._defined
        elif type == SymbolType.UNDEFINED:
            return self._undefined
        elif type == SymbolType.LAZY:
            return self._lazy
        else:
            raise ValueError('invalid type')

    def get_undefined_symbols(self):
        return self.get_symbols(SymbolType.UNDEFINED)

    def get_lazy_symbols(self):
        return self.get_symbols(SymbolType.LAZY)

    def __repr__(self):
        s = '{\n'
        if self._defined:
            s += f'\tdefined: {len(self._defined)} symbols\n'
            # s += 'defined: {'
            # for sym in self._defined.values():
            #     s += f'\t\t{sym}'
            #     s += '\n'
            # s += '}\n'
        if self._undefined:
            s += '\tundefined: {'
            for sym in self._undefined.values():
                s += f'\t\t{sym}'
                s += '\n'
            s += '\t}'
        if self._lazy.values():
            s += 'lazy: {'
            for sym in self._lazy.values():
                s += f'\t\t{sym}'
                s += '\n'
            s += '\t}'
        s += '}'

        return s
