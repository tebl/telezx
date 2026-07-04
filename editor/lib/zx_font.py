import numpy
from .zx_glyph import ZXGlyph

class ZXFont(ZXGlyph):
    def __init__(self, glyph_data):
        super().__init__(glyph_data)

    def get_ascii(self, character):
        data = self.get_offset(ord(character) - 32)
        return data
