import json
import numpy
from .zx_screen import ZXScreen
from .zx_font import ZXFont

class ZXDocument:
    UNSET = -1
    DEFAULT_FONT_PATH = 'font_default.bin'
    DEFAULT_GLYPH_PATH = 'font_glyphs.bin'

    def __init__(self, zx_screen):
        self.zx_screen = zx_screen
        self.font_path = self.DEFAULT_FONT_PATH
        self.glyph_path = self.DEFAULT_GLYPH_PATH
        self.document_path = None
        self.background = None
        self.changes = False
        self.cells = {}
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            self.cells[char_y] = {}
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.cells[char_y][char_x] = Element(self.UNSET, self.UNSET)

    def clear(self):
        self.zx_screen.clear_memory()
        self.clear_background()
        self.clear_fonts()
        self.set_document(None)
        self.changes = False

    def clear_background(self):
        self.background = None
        self.background_data = None

    def clear_fonts(self):
        self.font_path = self.DEFAULT_FONT_PATH
        self.glyph_path = self.DEFAULT_GLYPH_PATH

    def has_changes(self):
        return self.changes

    def is_blank(self):
        if self.document_path == None:
            return True
        return False

    def load(self, document_path):
        data = {
            'background': None,
            'font': self.font_path,
            'glyph': self.glyph_path,
            'cells': {}
        }
        with open(document_path, 'r') as file:
            data.update(json.load(file))
        self.zx_screen.clear_memory()

        if data['background']:
            self.set_background(data['background'])
        self.set_font(data['font'])
        self.set_glyph(data['glyph'])
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                if char_y in data['cells'] and char_x in data['cells'][char_y]:
                    element = self.cells[char_y][char_x]
                    element.from_dict(data['cells'][char_y][char_x])
        self.set_document(document_path)
        self.changes = False

    def set_document(self, document_path):
        self.document_path = document_path
    
    def set_background(self, background_path):
        self.background_data = numpy.fromfile(background_path, dtype='uint8')
        self.zx_screen.flip_memory(self.background_data)
        self.background = background_path
        self.changes = True

    def set_font(self, font_path):
        self.font_path = font_path

    def set_glyph(self, glyph_path):
        self.glyph_path = glyph_path

    def save(self):
        if self.document_path:
            with open(self.document_path, 'w') as file:
                json.dump(self.to_dict(), file, indent=4)
            self.changes = False
            return
        raise Exception('No document set')
        
    def to_dict(self):
        result = {
            'background': self.background,
            'font': self.font_path,
            'glyph': self.glyph_path,
            'cells': {}
        }
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            result['cells'][char_y] = {}
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                result['cells'][char_y][char_x] = self.cells[char_y][char_x].to_dict()
        return result

class Element:
    def __init__(self, char_code, attribute):
        self.char_code = char_code
        self.attribute = attribute

    def to_dict(self):
        return {
            'char_code': self.char_code,
            'attribute': self.attribute
        }
    
    def from_dict(self, data):
        self.char_code = data['char_code']
        self.attribute = data['attribute']