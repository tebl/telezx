import numpy
from .zx_glyph import ZXGlyph

class ZXFont(ZXGlyph):
    ASCII_SPACE = 32

    def __init__(self, glyph_data, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        super().__init__(glyph_data, rgb_fg, rgb_bg, generate_rgb)

    def get_ascii(self, character):
        data = self.get_offset(ord(character) - self.ASCII_SPACE)
        return data
