import yaml, typing
from pathlib import Path
from .. import BaseDocument, ZXFont, ZXGlyph, CustomCharacter, utilities
type Symbols = list[CustomCharacter]

class ZXFontDefinition(BaseDocument):
    def __init__(self, char_code_offset: int=ZXFont.CHAR_CODE_OFFSET, symbols: Symbols|None=None, debug_enabled: bool=False):
        super().__init__(debug_enabled)
        self._char_code_offset = char_code_offset
        self.symbols: Symbols = [ CustomCharacter() ] if symbols is None else symbols

    @property
    def char_code_offset(self):
        return self._char_code_offset

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

    def update_offset(self, offset: int, data):
        if offset < 0 or offset >= len(self.symbols):
            raise ValueError('offset overflow')
        self._changes = True
        self.symbols[offset].data = data

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

    def import_bin(self, bin_path: Path):
        self.symbols = []
        loader = ZXFont if self.is_font() else ZXGlyph
        data = loader.from_file(path=bin_path)
        for offset, data in data.symbols():
            self.symbols.append(CustomCharacter(data))
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
    def from_dict(cls, data: dict[str, typing.Any]) -> typing.Any:
        root = super().from_dict(data)
        return ZXFontDefinition(
            char_code_offset=root['char_code_offset'],
            symbols=[CustomCharacter.from_dict(v) for v in root['symbols']]
        )