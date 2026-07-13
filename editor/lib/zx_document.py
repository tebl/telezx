import json
import numpy
from .zx_screen import ZXScreen
from .zx_font import ZXFont

class ZXDocument:
    UNSET = -1

    def __init__(self, zx_screen):
        self.zx_screen = zx_screen
        self.background = None
        self.changes = False
        self.cells = {}
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            self.cells[char_y] = {}
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.cells[char_y][char_x] = Element(self.UNSET, self.UNSET)

    def clear(self):
        self.zx_screen.clear_memory()
        self.background = None
        self.changes = False

    def load(self, document_path):
        data = { 'background': None, 'cells': {} }
        with open(document_path, 'r') as file:
            data.update(json.load(file))
        self.zx_screen.clear_memory()

        if data['background']:
            self.set_background(data['background'])
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                if char_y in data['cells'] and char_x in data['cells'][char_y]:
                    self.cells[char_y][char_x].from_dict(data['cells'][char_y][char_x])
                    
        self.changes = False

    def set_background(self, path):
        self.zx_screen.flip_memory(numpy.fromfile(path, dtype='uint8'))
        self.background = path
        self.changes = True

    def save_as(self, document_path):
        with open(document_path, 'w') as file:
            json.dump(self.to_dict(), file, indent=4)
        self.changes = False

    def to_dict(self):
        result = { 'background': self.background, 'cells': {} }
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