from pathlib import Path
from .. import BaseDocument, ZXFont, ZXGlyph, CustomCharacter, utilities

class ZXFontDefinition(BaseDocument):
    def __init__(self, char_code_offset: int=ZXFont.CHAR_CODE_OFFSET, debug_enabled: bool=False):
        super().__init__(debug_enabled=debug_enabled)
        self._char_code_offset = char_code_offset
        self.symbols: list[CustomCharacter] = [ CustomCharacter() ]

        self.load_binary(utilities.get_project_root() / 'fonts'/ 'font_default.bin')

    @property
    def char_code_offset(self):
        return self._char_code_offset

    def get_offset(self, offset: int):
        if offset < 0 or offset >= len(self.symbols):
            raise ValueError('offset overflow')
        return self.symbols[offset]

    def update_offset(self, offset: int, data):
        if offset < 0 or offset >= len(self.symbols):
            raise ValueError('offset overflow')
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

    def load(self, document_path) -> bool:
        # return super().load()
        return True

    def load_binary(self, bin_path: Path):
        self.symbols = []
        loader = ZXFont if self.is_font() else ZXGlyph
        data = loader.from_file(path=bin_path)
        for offset, data in data.symbols():
            self.symbols.append(CustomCharacter(data))
        self._changes = True

    @classmethod
    def create(cls, document_path: Path):
        return super().create(document_path)