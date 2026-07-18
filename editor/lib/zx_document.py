import yaml
import numpy
from .zx_screen import ZXScreen
from .zx_glyph import ZXGlyph
from .zx_font import ZXFont

class ZXDocument:
    UNDEFINED = -1
    DEFAULT_ATTRIBUTE = ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLACK)
    DEFAULT_FONT_PATH = 'font_default.bin'
    DEFAULT_GLYPH_PATH = 'font_glyphs.bin'

    def __init__(self):
        self.zx_screen = ZXScreen()
        self.clear(attribute=self.DEFAULT_ATTRIBUTE)

    def clear(self, attribute):
        self.current_attribute = attribute
        self.zx_screen.clear_memory(set_attribute=attribute)
        self.__clear_background()
        self.__clear_cells()
        self.__clear_fonts()
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
        self.set_selected_font(self.DEFAULT_FONT_PATH)
        self.set_selected_glyph(self.DEFAULT_GLYPH_PATH)

    def export_to_scr(self, scr_path):
        with open(scr_path, 'wb') as file:
            file.write(self.zx_screen.to_scr())

    def export_to_specscii(self, specscii_path):
        SpecsciiFormat.write_document(self, specscii_path)

    def debug_cell(self, char_x, char_y):
        self.cells[char_y][char_x].debug(self)

    def get_attribute(self, char_x, char_y):
        cell = self.cells[char_y][char_x]
        return cell.get_attribute(self)

    def get_description(self):
        parts = ['*'] if self.has_changes() else []
        if self.is_blank():
            parts.append('Untitled')
        else:
            parts.append(self.document_path)
        return ''.join(parts)

    def has_background(self):
        if self.background is not None and self.background_data is not None:
            return True
        return False

    def has_changes(self):
        return self.changes

    def is_blank(self):
        if self.document_path == None:
            return True
        return False

    def load(self, document_path):
        data = self.__json_defaults()
        with open(document_path, 'r') as file:
            data.update(yaml.safe_load(file))
            if self.__class__.__name__ not in data:
                raise ValueError("does not look like a telezx file")
        root = data[self.__class__.__name__]

        # Clear and set as current file
        self.clear(root['attribute'])
        self.set_document(document_path)

        if root['background']:
            self.set_background(root['background'])
        self.set_selected_font(root['font'])
        self.set_selected_glyph(root['glyph'])
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.cells[char_y][char_x].from_dict(root['cells'][char_y][char_x])
        self.__render_cells()
        self.changes = False
    
    def __json_defaults(self):
        return {
            self.__class__.__name__: {
                'attribute': ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLACK),
                'background': None,
                'font': self.DEFAULT_FONT_PATH,
                'glyph': self.DEFAULT_GLYPH_PATH,
                'cells': {
                    char_y: {
                        char_x: { 'attribute': ZXDocument.UNDEFINED, 'char_code': ZXDocument.UNDEFINED } 
                        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS)} for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS)
                }
            }
        }
    
    def __render_cells(self):
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.cells[char_y][char_x].render_cell(self)

    def set_attribute(self, char_x, char_y, attribute=UNDEFINED):
        result = self.cells[char_y][char_x].set_attribute(self, attribute)
        if result:
            self.changes = True
        return result

    def set_background(self, background_path):
        self.background_data = numpy.fromfile(background_path, dtype='uint8')
        self.background = background_path
        self.zx_screen.flip_memory(self.background_data)
        self.__render_cells()
        self.changes = True

    def set_character(self, char_x, char_y, char_code=UNDEFINED):
        result = self.cells[char_y][char_x].set_character(self, char_code)
        if result:
            self.changes = True
        return result

    def set_document(self, document_path):
        self.document_path = document_path

    def set_selected_font(self, font_path):
        self.font_path = font_path
        self.font = ZXFont.from_file(self.font_path)

    def set_selected_glyph(self, glyph_path):
        self.glyph_path = glyph_path
        self.glyph = ZXGlyph.from_file(self.glyph_path)

    def save(self):
        if self.document_path:
            with open(self.document_path, 'w') as file:
                yaml.dump(
                    self.to_dict(), 
                    file, 
                    indent=4, 
                    default_flow_style=False, 
                    sort_keys=True
                )
            self.changes = False
            return
        raise Exception('No document set')
        
    def to_dict(self):
        result = self.__json_defaults()
        root = result[self.__class__.__name__]
        root['attribute'] = self.current_attribute
        root['background'] = self.background
        root['font'] = self.font_path
        root['glyph'] = self.glyph_path
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            root['cells'][char_y] = {}
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                root['cells'][char_y][char_x] = self.cells[char_y][char_x].to_dict()
        return result

    def to_rgb(self):
        return self.zx_screen.to_rgb()


class Cell:
    def __init__(self, char_x, char_y, char_code=ZXDocument.UNDEFINED, char_attribute=ZXDocument.UNDEFINED):
        self.char_x = char_x
        self.char_y = char_y
        self.char_code = char_code
        self.char_attribute = char_attribute

    def debug(self, zx_document):
        print(f'Cell X={self.char_x},Y={self.char_y}:')

        if self.char_code != ZXDocument.UNDEFINED:
            print(f'  char_code      = {self.char_code} ({chr(self.char_code)})')
        else:
            print(f'  char_code      = UNDEFINED')

        if self.char_attribute != ZXDocument.UNDEFINED:
            print("  char_attribute  = {0} (0x{1:04x})".format(self.char_attribute, self.char_attribute))
        else:
            print(f'  char_attribute = UNDEFINED')

        memory = zx_document.zx_screen.read_cell(self.char_x, self.char_y)
        for idx, value in enumerate(memory):
            s_value = "{:08b}".format(value)
            if idx == 0:
                print("  memory         = {0} (0x{1:04x})".format(s_value, ZXScreen.calculate_offset_data(self.char_x, self.char_y, row=idx)))
            else:
                print("                   {0} (0x{1:04x})".format(s_value, ZXScreen.calculate_offset_data(self.char_x, self.char_y, row=idx)))
        source = ZXScreen.__name__ if self.char_attribute == ZXDocument.UNDEFINED else ZXDocument.__name__
        s_value = "{:08b}".format(self.get_attribute(zx_document))
        print(        "  attribute      = {0} (0x{1:04x}) from {2}".format(
            s_value,
            ZXScreen.calculate_offset_attribute(self.char_x, self.char_y),
            source))
        print()

    def render_cell(self, zx_document):
        if self.char_code == ZXDocument.UNDEFINED:
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

    def get_attribute(self, zx_document):
        if self.char_attribute == ZXDocument.UNDEFINED:
            return zx_document.zx_screen.get_attribute_at(self.char_x, self.char_y)
        return self.char_attribute

    def set_attribute(self, zx_document, char_attribute=ZXDocument.UNDEFINED):
        changed = (self.char_attribute != char_attribute)
        if char_attribute == ZXDocument.UNDEFINED:
            if changed:
                if zx_document.has_background():
                    bg_index = ZXScreen.calculate_offset_attribute(self.char_x, self.char_y)
                    bg_attribute = zx_document.background_data[bg_index]
                    zx_document.zx_screen.write_attribute(
                        self.char_x, 
                        self.char_y, 
                        bg_attribute)
                else:
                    zx_document.zx_screen.write_attribute(
                        self.char_x, 
                        self.char_y, 
                        zx_document.default_attribute)
        else:
            zx_document.zx_screen.write_attribute(self.char_x, self.char_y, char_attribute)
        self.char_attribute = char_attribute
        return changed

    def set_character(self, zx_document, char_code=ZXDocument.UNDEFINED):
        changed = (self.char_code != char_code)
        if char_code == ZXDocument.UNDEFINED:
            if changed:
                if zx_document.has_background():
                    zx_document.zx_screen.write_cell(
                        self.char_x, 
                        self.char_y,
                        ZXScreen.exctract_cell(self.char_x, self.char_y, zx_document.background_data)
                    )
                else:
                    # overwrite with empty space
                    zx_document.zx_screen.write_cell(
                        self.char_x, 
                        self.char_y, 
                        zx_document.font.get_offset(0)
                    )
                self.char_code = char_code
        else:
            self.char_code = char_code
            self.render_cell(zx_document)
        self.char_code = char_code
        return changed

    def to_dict(self):
        return {
            'char_code': int(self.char_code),
            'attribute': int(self.char_attribute)
        }
    
    def from_dict(self, data):
        self.char_code = data['char_code']
        self.char_attribute = data['attribute']

class SpecsciiFormat:
    SET_INK = 0x10
    SET_PAPER = 0x11
    SET_FLASH = 0x12
    SET_BRIGHT = 0x13
    SET_INVERSE = 0x14
    SET_XOR = 0x15
    SET_CURSOR = 0x16
    SET_COLUMN = 0x17
    ASCII_START = ZXFont.ASCII_SPACE
    ASCII_LAST = ZXFont.ASCII_COPYRIGHT
    GLYPH_START = ZXGlyph.GLYPH_OFFSET
    GLYPH_LAST = 0xff

    def __init__(self, zx_document: ZXDocument):
        self.zx_document = zx_document
        self.current_attribute = zx_document.current_attribute

        parsed = ZXScreen.to_parsed_attribute(self.current_attribute)
        self.last_ink = parsed['ink']
        self.last_paper = parsed['paper']
        self.last_bright = parsed['bright']
        self.last_flash = parsed['flash']
        self.last_xor = False
        self.last_inverse = False
        self.last_xor = False
        self.cursor_x = 0
        self.cursor_y = 0

    def write_formatted(self, specscii_path):
        with open(specscii_path, 'wb') as file:
            for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
                for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                    cell = self.zx_document.cells[char_y][char_x]

                    # Skip if there's no content
                    if cell.char_code == ZXDocument.UNDEFINED:
                        continue

                    # Move cursor to match
                    self.__write_cursor(file, char_x, char_y)

                    # Update attribute at location
                    if not cell.char_attribute == ZXDocument.UNDEFINED:
                        self.__set_attribute(file, cell.char_attribute)

                    # Output a character
                    if not cell.char_code == ZXDocument.UNDEFINED:
                        self.__write_character(file, cell.char_code)
    
    def __set_attribute(self, file, attribute):
        parsed = ZXScreen.to_parsed_attribute(attribute)
        self.__write_ink(file, parsed['ink'])
        self.__write_paper(file, parsed['paper'])
        self.__write_flash(file, parsed['flash'])
        self.__write_bright(file, parsed['bright'])

    def __write_ink(self, file, ink):
        assert ink >= ZXScreen.BLACK and ink <= ZXScreen.WHITE
        if self.last_ink == ink:
            return
        self.last_ink = ink
        self.__write_bytes(file, (self.SET_INK, ink))

    def __write_paper(self, file, paper):
        assert paper >= ZXScreen.BLACK and paper <= ZXScreen.WHITE
        if self.last_paper == paper:
            return
        self.last_paper = paper
        self.__write_bytes(file, (self.SET_PAPER, paper))

    def __write_flash(self, file, is_flashing):
        assert is_flashing == True or is_flashing == False
        if self.last_flash == is_flashing:
            return
        self.last_flash = is_flashing
        self.__write_bytes(file, (self.SET_FLASH, 1 if is_flashing else 0))

    def __write_bright(self, file, is_bright):
        assert is_bright == True or is_bright == False
        if self.last_bright == is_bright:
            return
        self.last_bright = is_bright
        self.__write_bytes(file, (self.SET_BRIGHT, 1 if is_bright else 0))

    def __write_inverse(self, file, is_inverse):
        '''
        Remove client should set a variable to swap ink/paper upon printing
        data to the screen. This allows a file to highlight text without
        knowing the colour scheme used on the other end.
        '''
        assert is_inverse == True or is_inverse == False
        if self.last_inverse == is_inverse:
            return
        self.__write_bytes(
            file, 
            (self.SET_INVERSE, 1 if is_inverse else 0)
        )

    def __write_xor(self, file, is_xor):
        '''
        WARNING: Absolutely no idea what this does.
        '''
        assert is_xor == True or is_xor == False
        if self.last_xor == is_xor:
            return
        self.__write_bytes(
            file, 
            (self.SET_XOR, 1 if is_xor else 0)
        )

    def __write_cursor(self, file, char_x, char_y):
        assert char_x >= 0 and char_x < ZXScreen.SCREEN_WIDTH_CHARS
        assert char_y >= 0 and char_y < ZXScreen.SCREEN_HEIGHT_CHARS
        if self.cursor_x == char_x and self.cursor_y == char_y:
            return
        self.cursor_x = char_x
        self.cursor_y = char_y
        self.__write_bytes(
            file, 
            (self.SET_CURSOR, char_y, char_x)
        )

    def __write_column(self, file, char_x):
        '''
        WARNING: Not sure what this is used for, so I'm assuming that the
                 purpose is to move cursor within the same screen row.
        '''
        assert char_x >= 0 and char_x < ZXScreen.SCREEN_WIDTH_CHARS
        if self.cursor_x == char_x:
            return
        self.cursor_x = char_x
        self.__write_bytes(
            file, 
            (self.SET_COLUMN, char_x)
        )

    def __write_bytes(self, file, bytes):
        for b in bytes:
            file.write(b.to_bytes(1))
    
    def __write_character(self, file, char_code):
        assert char_code >= self.ASCII_START and char_code <= self.GLYPH_LAST
        file.write(char_code.to_bytes(1))
        self.__increment_cursor()

    def __increment_cursor(self):
        if self.cursor_x < (ZXScreen.SCREEN_WIDTH_CHARS - 1):
            self.cursor_x = (self.cursor_x + 1 % ZXScreen.SCREEN_WIDTH_CHARS)
            self.cursor_y = (self.cursor_y % ZXScreen.SCREEN_HEIGHT_CHARS)
            return
        if self.cursor_y < (ZXScreen.SCREEN_HEIGHT_CHARS - 1):
            self.cursor_x = 0
            self.cursor_y = (self.cursor_y + 1 % ZXScreen.SCREEN_HEIGHT_CHARS)
            return
        self.cursor_x = 0
        self.cursor_y = 0

    @classmethod
    def write_document(cls, zx_document, specscii_path):
        SpecsciiFormat(zx_document).write_formatted(specscii_path)
