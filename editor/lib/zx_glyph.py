import numpy
from .utilities import get_project_root
from .zx_symbol import ZXSymbol

class ZXGlyph(ZXSymbol):
    CHAR_CODE_OFFSET = 0x80
    'Offset added to index to get character code'
    GLYPH_OFFSET_UDG = 0xf0
    'Start of user definable graphics'
    GLYPH_LAST_SYMBOL = 0xff
    
    def __init__(self, glyph_data, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        super().__init__(glyph_data, rgb_fg, rgb_bg, generate_rgb)

    def _get_js_name(self, name):
        if not name:
            return 'FONT_GLYPHS'
        return super()._get_js_name(name)

    @classmethod
    def get_default(cls, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        return ZXGlyph.from_file(get_project_root() / 'fonts'/ 'font_glyphs.bin', 
                                 rgb_fg, 
                                 rgb_bg, 
                                 generate_rgb)