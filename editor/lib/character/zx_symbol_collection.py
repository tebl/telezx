import numpy, yaml, typing, enum
from abc import ABC, abstractmethod
from pathlib import Path
from .. import BaseDocument, ZXLogger, ZXFont, ZXGlyph, UDG, CustomCharacter, utilities
type Symbols = list[ZXDefinitionCharacter]


class ZXSymbolType(enum.Enum):
    FONT = enum.auto()
    GLYPH = enum.auto()
    UDG = enum.auto()


class ZXSymbolCollection(BaseDocument):
    def __init__(self, char_code_offset: int=ZXFont.CHAR_CODE_OFFSET, symbols: Symbols|None=None, debug_enabled: bool=False):
        super().__init__(debug_enabled)
        self._char_code_offset = char_code_offset
        self.symbols: Symbols = [] if symbols is None else symbols
        self.__pad_symbols()
        self.__truncate_symbols()

    def __pad_symbols(self):
        'Pad out missing offsets to full size'
        for x in range(len(self.symbols), self.max_symbols()):
            self.symbols.append(ZXDefinitionCharacter())

    def __truncate_symbols(self):
        'Truncate symbols by chopping off any extras'
        self.symbols = self.symbols[0:self.max_symbols()]

    @property
    def char_code_offset(self):
        return self._char_code_offset

    def can_revert_offset(self, offset: int) -> bool:
        return self.get_offset(offset).revert is not None

    def revert_offset(self, offset: int):
        self.update_offset(offset, 
                           self.get_offset(offset).revert, 
                           create_undo=True)

    def can_undo_offset(self, offset: int) -> bool:
        return len(self.get_offset(offset).undo) > 0

    def undo_offset(self, offset: int):
        chr = self.get_offset(offset)
        if len(chr.undo):
            undo = chr.undo.pop()
            self.update_offset(offset, 
                            undo.data,
                            create_undo=False)

    def constrain_offset(self, offset: int|None) -> int|None:
        '''
        Constrain offset value to something that's within the currently defined
        data.
        '''
        if len(self.symbols) == 0:
            return None
        if len(self.symbols) < offset:
            return (len(self.symbols) - 1)
        return offset

    def get_offset(self, offset: int):
        if offset < 0 or offset >= len(self.symbols):
            raise ValueError('offset overflow')
        return self.symbols[offset]

    def update_offset(self, offset: int, data: UDG, create_undo: bool):
        if offset < 0 or offset >= len(self.symbols):
            raise ValueError('offset overflow')
        self._changes = True
        self.symbols[offset].update(data, create_undo)

    def get_symbols(self):
        for offset, symbol in enumerate(self.symbols):
            yield (offset, self.char_code_offset + offset, symbol)

    @classmethod
    @abstractmethod
    def get_type_description(cls):
        ...

    @classmethod
    def get_type(cls, symbol_type: ZXSymbolType) -> ZXSymbolCollection:
        match symbol_type:
            case ZXSymbolType.FONT:
                return ZXFontCollection
            case ZXSymbolType.GLYPH:
                return ZXGlyphCollection
            case _:
                raise ValueError(f'Unknown symbol type - {symbol_type}')

    def is_type(self, symbol_type: ZXSymbolType) -> bool:
        return isinstance(self, self.get_type(symbol_type))

    def is_font(self) -> bool:
        return False

    def is_glyphs(self) -> bool:
        return False

    def import_bin(self, file_path: Path):
        self.symbols = []
        loader = ZXFont if self.is_font() else ZXGlyph
        data = loader.from_file(path=file_path)
        for offset, data in data.symbols():
            self.symbols.append(ZXDefinitionCharacter(data))
        self.__pad_symbols()
        self.__truncate_symbols()
        self._changes = True

    def to_dict(self):
        result = self._yaml_defaults()
        root = result[self.__class__.__name__]
        root['symbols'] = [s.to_dict() for s in self.symbols]
        return result

    @classmethod
    def _yaml_defaults(cls):
        return {
            cls.__name__: {
                'symbols': []
            }
        }

    @classmethod
    @abstractmethod
    def get_char_code_offset(cls):
        ...

    @classmethod
    def from_binary(cls, file_path: Path, symbol_type: ZXSymbolType) -> typing.Self:
        ZXLogger.get_instance().debug('Importing data from', file_path)
        doc: ZXSymbolCollection = ZXSymbolCollection.create_from_type(symbol_type=symbol_type)
        doc.import_bin(file_path)
        return doc

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any], debug_enabled: bool=False) -> typing.Any:
        root = super().from_dict(data)
        return cls(
            symbols=[ZXDefinitionCharacter.from_dict(v) for v in root['symbols']],
            debug_enabled=debug_enabled
        )

    @classmethod
    def get_subclass_matching(cls, symbol_type: ZXSymbolType|None=None, type_string: str|None=None):
        if symbol_type is not None:
            return cls.get_subclass_matching_type(symbol_type)
        if type_string is not None:
            return cls.get_subclass_matching_str(type_string)
        raise ValueError(f'No identifier parameters specified!')

    @classmethod
    def get_subclass_matching_str(cls, type_string: str) -> typing.Type[ZXSymbolCollection]:
        match type_string:
            case ZXFontCollection.__name__:
                return ZXFontCollection
            case ZXGlyphCollection.__name__:
                return ZXGlyphCollection
            case _:
                raise ValueError(f'Unknown symbol type - {type_string}')

    @classmethod
    def get_subclass_matching_type(cls, symbol_type: ZXSymbolType) -> typing.Type[ZXSymbolCollection]:
        match symbol_type:
            case ZXFontCollection.__name__:
                return ZXFontCollection
            case ZXGlyphCollection.__name__:
                return ZXGlyphCollection
            case _:
                raise ValueError(f'Unknown symbol type - {symbol_type}')

    @classmethod
    def get_implementation_for(cls, document_path) -> ZXSymbolCollection:
        symbol_type_string = cls.peek_filetype(document_path)
        return cls.get_subclass_matching_str(type_string=symbol_type_string)

    @classmethod
    def create_from_type(cls, symbol_type: ZXSymbolType, symbols: Symbols|None=None, debug_enabled: bool=False) -> typing.Self:
        return cls.get_subclass_matching_type(symbol_type)(symbols=symbols, debug_enabled=debug_enabled)

    @classmethod
    def create_from_str(cls, symbol_type: str, symbols: Symbols|None=None, debug_enabled: bool=False) -> typing.Self:
        return cls.get_subclass_matching_str(type_string=symbol_type)(symbols=symbols, debug_enabled=debug_enabled)

    @abstractmethod
    def max_symbols(cls):
        ...

    @classmethod
    def max_offset(cls):
        return (cls.max_symbols - 1)
    

class ZXFontCollection(ZXSymbolCollection):
    def __init__(self, symbols=None, debug_enabled=False):
        super().__init__(ZXFont.CHAR_CODE_OFFSET, symbols, debug_enabled)

    def is_font(self):
        return True

    @classmethod
    def get_char_code_offset(cls):
        return ZXFont.CHAR_CODE_OFFSET

    @classmethod
    def get_type_description(cls):
        return 'Characters'

    @classmethod
    def max_symbols(cls):
        return (ZXGlyph.CHAR_CODE_OFFSET - ZXFont.CHAR_CODE_OFFSET)


class ZXGlyphCollection(ZXSymbolCollection):
    def __init__(self, symbols=None, debug_enabled=False):
        super().__init__(ZXGlyph.CHAR_CODE_OFFSET, symbols, debug_enabled)

    def is_glyphs(self):
        return True

    @classmethod
    def get_char_code_offset(cls):
        return ZXGlyph.CHAR_CODE_OFFSET

    @classmethod
    def get_type_description(self):
        return 'Glyphs'

    @classmethod
    def max_symbols(cls):
        return 128


class ZXDefinitionCharacter(CustomCharacter):
    def __init__(self, data: UDG|None=None):
        self.revert = self.sanitize_data(data) if data is not None else None
        self.undo: list[UndoData] = []
        data = self.sanitize_data(self.generate_blank_glyph()) if data is None else data
        super().__init__(self.sanitize_data(data))

    def update(self, data: UDG, create_undo: bool):
        data = self.sanitize_data(data)
        if create_undo:
            self.__create_undo(self.data)
        self.data = data

    def __create_undo(self, data: UDG):
        if len(self.undo) and self.undo[-1].matches(data):
            return
        self.undo.append(UndoData(data))

    @classmethod
    def sanitize_data(cls, data: UDG):
        return [int(v) for v in data]

class UndoData:
    def __init__(self, data: UDG):
        self.data = data

    def matches(self, new_data):
        return self.data == new_data