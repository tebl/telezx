import json
import numpy
from .zx_screen import ZXScreen
from .zx_glyph import ZXGlyph
from .zx_font import ZXFont

class ZXDocument:
    UNDEFINED = -1
    DEFAULT_FONT_PATH = 'font_default.bin'
    DEFAULT_GLYPH_PATH = 'font_glyphs.bin'

    def __init__(self):
        self.zx_screen = ZXScreen()
        self.clear()

    def clear(self):
        self.default_attribute = ZXScreen.to_attribute(
            paper=ZXScreen.BLACK, 
            ink=ZXScreen.WHITE
        )
        self.zx_screen.clear_memory(attribute=self.default_attribute)
        self.__clear_background()
        self.__clear_fonts()
        self.__clear_cells()
        self.set_document(None)
        self.changes = False

    def __clear_background(self):
        self.background = None
        self.background_data = None

    def __clear_cells(self):
        self.cells = {}
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            self.cells[char_y] = {}
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.cells[char_y][char_x] = Cell(char_x, char_y, self.UNDEFINED, self.UNDEFINED)

    def __clear_fonts(self):
        self.set_font(self.DEFAULT_FONT_PATH)
        self.set_glyph(self.DEFAULT_GLYPH_PATH)

    def debug_cell(self, char_x, char_y):
        self.cells[char_y][char_x].debug(self)

    def has_changes(self):
        return self.changes

    def is_blank(self):
        if self.document_path == None:
            return True
        return False

    def load(self, document_path):
        data = self.__json_defaults()
        with open(document_path, 'r') as file:
            data.update(json.load(file))
        self.set_document(document_path)
        self.zx_screen.clear_memory()

        if data['background']:
            self.set_background(data['background'])
        self.set_font(data['font'])
        self.set_glyph(data['glyph'])
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            s_char_y = str(char_y)
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                s_char_x = str(char_x)
                cell = self.cells[char_y][char_x]
                if s_char_y in data['cells'] and s_char_x in data['cells'][s_char_y]:
                    cell.from_dict(data['cells'][s_char_y][s_char_x])
                else:
                    cell.set(self.UNDEFINED, self.UNDEFINED)
        self.__render_cells()
        self.changes = False
    
    def __json_defaults(self):
        return {
            'attribute': self.default_attribute,
            'background': self.background,
            'font': self.font_path,
            'glyph': self.glyph_path,
            'cells': {}
        }
    
    def to_rgb(self):
        return self.zx_screen.to_rgb()

    def __render_cells(self):
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.__render_cell(char_x, char_y)

    def __render_cell(self, char_x, char_y):
        cell = self.cells[char_y][char_x]
        cell.render_screen(self)

    def set_document(self, document_path):
        self.document_path = document_path
    
    def set_background(self, background_path):
        self.background_data = numpy.fromfile(background_path, dtype='uint8')
        self.background = background_path
        self.zx_screen.flip_memory(self.background_data)
        self.__render_cells()
        self.changes = True

    def set_character(self, char_x, char_y, char_code=UNDEFINED):
        result = self.cells[char_y][char_x].set_character(char_code)
        if result:
            # unsaved document changes
            self.changes = True
        # Render into ZXScreen instance
        self.__render_cell(char_x, char_y)
        return result

    def get_attribute(self, char_x, char_y):
        cell = self.cells[char_y][char_x]
        return cell.get_attribute(self)

    def set_attribute(self, char_x, char_y, attribute=UNDEFINED):
        result = self.cells[char_y][char_x].set_attribute(attribute)
        if result:
            # unsaved document changes
            self.changes = True
        # Render into ZXScreen instance
        self.__render_cell(char_x, char_y)
        return result

    def set_font(self, font_path):
        self.font_path = font_path
        self.font = ZXFont.from_file(self.font_path)

    def set_glyph(self, glyph_path):
        self.glyph_path = glyph_path
        self.glyph = ZXGlyph.from_file(self.glyph_path)

    def save(self):
        if self.document_path:
            with open(self.document_path, 'w') as file:
                json.dump(self.to_dict(), file, indent=4)
            self.changes = False
            return
        raise Exception('No document set')
        
    def to_dict(self):
        result = self.__json_defaults()
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            result['cells'][char_y] = {}
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                result['cells'][char_y][char_x] = self.cells[char_y][char_x].to_dict()
        return result

class Cell:
    def __init__(self, char_x, char_y, char_code, char_attribute):
        self.char_code = ZXDocument.UNDEFINED
        self.char_attribute = ZXDocument.UNDEFINED
        self.char_x = char_x
        self.char_y = char_y
        self.set_character(char_code)
        self.set_attribute(char_attribute)

    def debug(self, zx_document):
        print(f'Cell X={self.char_x},Y={self.char_y}:')
        source = ZXScreen.__name__ if self.char_attribute == ZXDocument.UNDEFINED else ZXDocument.__name__
        print(f'  attribute = {self.get_attribute(zx_document)} from {source}')

        if self.char_code != ZXDocument.UNDEFINED:
            source = ZXDocument.__name__
            print(f'  char_code = {self.char_code} ({chr(self.char_code)}) from {source}')
        else:
            print(f'  char_code = UNDEFINED')
        memory = zx_document.zx_screen.read_cell(self.char_x, self.char_y)
        for idx, value in enumerate(memory):
            s_value = "{:08b}".format(value)
            if idx == 0:
                print(f'  memory = {s_value}')
            else:
                print(f'           {s_value}')
        print()

    def render_screen(self, zx_document):
        #
        # need to fix so we can delete value
        #
        if self.char_code == ZXDocument.UNDEFINED:
            self.__apply_attribute(zx_document)
            return
        if self.char_code >= ZXFont.ASCII_SPACE and self.char_code <= ZXFont.ASCII_COPYRIGHT:
            zx_document.zx_screen.write_cell(
                self.char_x, 
                self.char_y, 
                zx_document.font.get_offset(self.char_code - ZXFont.ASCII_SPACE),
                self.char_attribute
            )
        if self.char_code >= ZXGlyph.GLYPH_OFFSET:
            zx_document.zx_screen.write_cell(
                self.char_x, 
                self.char_y, 
                zx_document.glyph.get_offset(self.char_code - ZXGlyph.GLYPH_OFFSET),
                self.char_attribute
            )

    def __apply_attribute(self, zx_document):
        if self.char_attribute == ZXDocument.UNDEFINED:
            return
        zx_document.zx_screen.write_attribute(self.char_x, self.char_y, self.char_attribute)

    def get_attribute(self, zx_document):
        if self.char_attribute == ZXDocument.UNDEFINED:
            return zx_document.zx_screen.get_attribute_at(self.char_x, self.char_y)
        return self.char_attribute

    def set_attribute(self, char_attribute=ZXDocument.UNDEFINED):
        changed = (self.char_attribute != char_attribute)
        self.char_attribute = char_attribute
        return changed

    def set_character(self, char_code=ZXDocument.UNDEFINED):
        changed = (self.char_code != char_code)
        self.char_code = char_code
        return changed

    def to_dict(self):
        return {
            'char_code': self.char_code,
            'attribute': self.char_attribute
        }
    
    def from_dict(self, data):
        self.char_code = data['char_code']
        self.char_attribute = data['attribute']