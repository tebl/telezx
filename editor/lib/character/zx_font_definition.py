import numpy, yaml, typing
from pathlib import Path
from .. import BaseDocument, ZXLogger, ZXFont, ZXGlyph, UDG, CustomCharacter, utilities
type Symbols = list[ZXDefinitionCharacter]

class ZXFontDefinition(BaseDocument):
    def __init__(self, char_code_offset: int=ZXFont.CHAR_CODE_OFFSET, symbols: Symbols|None=None, debug_enabled: bool=False):
        super().__init__(debug_enabled)
        self._char_code_offset = char_code_offset
        self.symbols: Symbols = [ ZXDefinitionCharacter() ] if symbols is None else symbols

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
            return 0
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

    def get_type(self):
        if self.is_font():
            return 'Characters'
        return 'Glyphs'

    def is_font(self) -> bool:
        return self.char_code_offset == ZXFont.CHAR_CODE_OFFSET

    def is_glyphs(self) -> bool:
        return not self.is_font()

    def import_bin(self, file_path: Path):
        self.symbols = []
        loader = ZXFont if self.is_font() else ZXGlyph
        data = loader.from_file(path=file_path)
        for offset, data in data.symbols():
            self.symbols.append(ZXDefinitionCharacter(data))
        self._changes = True

    def to_dict(self):
        result = self._yaml_defaults()
        root = result[self.__class__.__name__]
        root['char_code_offset'] = self.char_code_offset
        root['symbols'] = [s.to_dict() for s in self.symbols]
        return result

    @classmethod
    def _yaml_defaults(cls):
        return {
            cls.__name__: {
                'char_code_offset': ZXFont.CHAR_CODE_OFFSET,
                'symbols': []
            }
        }

    @classmethod
    def from_binary(cls, file_path: Path, char_code_offset: int=ZXFont.CHAR_CODE_OFFSET) -> typing.Self:
        ZXLogger.get_instance().debug('Importing data from', file_path)
        doc: ZXFontDefinition = ZXFontDefinition(char_code_offset)
        doc.import_bin(file_path)
        return doc

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> typing.Any:
        root = super().from_dict(data)
        return ZXFontDefinition(
            char_code_offset=root['char_code_offset'],
            symbols=[ZXDefinitionCharacter.from_dict(v) for v in root['symbols']]
        )

class ZXDefinitionCharacter(CustomCharacter):
    def __init__(self, data: UDG|None=None):
        self.revert = self.sanitize_data(data) if data is not None else None
        self.undo: list[UndoData] = []
        super().__init__(self.sanitize_data(data) if data is not None else None)

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