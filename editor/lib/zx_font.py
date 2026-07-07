import numpy
from .zx_glyph import ZXGlyph

class ZXFont(ZXGlyph):
    def __init__(self, glyph_data, rgb_fg=255, rgb_bg=0):
        super().__init__(glyph_data, rgb_fg, rgb_bg)

    def get_ascii(self, character):
        data = self.get_offset(ord(character) - 32)
        return data
