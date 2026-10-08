import numpy
from .utilities import get_project_root
from .zx_glyph import ZXGlyph

class ZXFont(ZXGlyph):
    ASCII_SPACE = 0x20
    ASCII_COPYRIGHT = 0x7f
    FONT_OFFSET = ASCII_SPACE

    def __init__(self, glyph_data, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        super().__init__(glyph_data, rgb_fg, rgb_bg, generate_rgb)

    def get_ascii(self, character: str, rgb: bool=False):
        offset = ord(character) - self.ASCII_SPACE
        if rgb:
            return self.get_offset_rgb(offset)
        return self.get_offset(offset)

    def get_charcode_from_offset(self, value: int=0):
        return self.FONT_OFFSET + value

    def _get_js_name(self, name):
        if not name:
            return 'FONT_DEFAULT'
        return super()._get_js_name(name)

    @classmethod
    def get_default(cls, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        return ZXFont.from_file(get_project_root() / 'fonts'/ 'font_default.bin', 
                                rgb_fg, 
                                rgb_bg, 
                                generate_rgb)

    @classmethod
    def get_alternate(cls, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        return ZXFont.from_file(get_project_root() / 'fonts'/ 'font_cp850.bin', 
                                rgb_fg, 
                                rgb_bg, 
                                generate_rgb)

    @classmethod
    def validate_ascii(cls, char_code):
        return char_code >= cls.ASCII_SPACE and char_code <= cls.ASCII_COPYRIGHT

    @classmethod
    def is_whitespace(cls, char_code):
        match char_code:
            case cls.ASCII_SPACE:
                return True
        return False 