import yaml
import numpy
import os.path
from PIL import Image
from typing import Optional
from pathlib import Path
from .zx_screen import ZXScreen, ZXScreenIterator
from .zx_glyph import ZXGlyph
from .zx_font import ZXFont
from .utilities import update_tree

class ZXToken:
    UNDEFINED = -1
    UNSPECIFIED = -2
    DEFAULT_ATTRIBUTE = ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLACK)
    DEFAULT_FONT = 'font_default'
    DEFAULT_GLYPH = 'font_glyphs'
    FILE_EXTENSION = '.zxtoken'

    def __init__(self):
        self.zx_screen = ZXScreen()
        self.clear(attribute=self.DEFAULT_ATTRIBUTE)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.save()

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
                self.cells[char_y][char_x] = ZXTokenCell(char_x, char_y, self.UNDEFINED, self.UNDEFINED)

    def __clear_fonts(self):
        self.set_selected_font(self.DEFAULT_FONT)
        self.set_selected_glyph(self.DEFAULT_GLYPH)

    def debug_cell(self, char_x, char_y):
        self.__lookup_cell(char_x, char_y).debug(self)

    def export(self, document_path):
        with open(document_path, 'w') as file:
            yaml.dump(
                self.to_dict(), 
                file, 
                indent=4, 
                default_flow_style=False, 
                sort_keys=True
            )
        return True

    def export_screenshot(self, screenshot_path):
        image = Image.fromarray(self.to_rgb())
        image.save(screenshot_path)

    def export_to_scr(self, scr_path):
        with open(scr_path, 'wb') as file:
            file.write(self.zx_screen.to_scr())

    def export_to_specscii(self, specscii_path):
        SpecsciiFormat.write_document(self, specscii_path)

    def get_attribute(self, char_x, char_y):
        '''
        Note that this will always attempt to return a value used for display,
        either from a value set on a character cell or from ZXScreen.
        '''
        cell = self.__lookup_cell(char_x, char_y)
        return cell.get_attribute(self)

    def get_character(self, char_x, char_y):
        cell = self.__lookup_cell(char_x, char_y)
        return cell.char_code

    def get_inverted(self, char_x, char_y):
        cell = self.__lookup_cell(char_x, char_y)
        return cell.char_inverted

    def get_cell(self, char_x, char_y) -> CellCopy:
        return CellCopy.from_cell(self.__lookup_cell(char_x, char_y))

    def __lookup_cell(self, char_x, char_y) -> ZXTokenCell:
        return self.cells[char_y][char_x]

    def get_title(self):
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
    
    def is_defined(self, char_x, char_y):
        cell = self.__lookup_cell(char_x, char_y)
        return not cell.char_code == ZXToken.UNDEFINED

    def load(self, document_path):
        data = self.__yaml_defaults()
        with open(document_path, 'r') as file:
            data = update_tree(data, self.__load_zx_page(file))
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
        self.render_cells()
        self.changes = False
    
    def __yaml_defaults(self):
        return {
            self.__class__.__name__: {
                'attribute': ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLACK),
                'background': None,
                'font': self.DEFAULT_FONT,
                'glyph': self.DEFAULT_GLYPH,
                'cells': {
                    char_y: {
                        char_x: { 'attribute': ZXToken.UNDEFINED, 'char_code': ZXToken.UNDEFINED, 'inverted': ZXToken.UNDEFINED } 
                        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS)} for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS)
                }
            }
        }

    def __load_zx_page(self, file):
        data = yaml.safe_load(file)
        if self.__class__.__name__ not in data:
            raise ValueError("does not look like a {}-file".format(self.__class__.__name__))
        return data

    def render_cells(self):
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                self.__lookup_cell(char_x, char_y).sync_screen(self)

    def set_attribute(self, char_x, char_y, char_attribute=UNDEFINED) -> bool:
        result = self.__lookup_cell(char_x, char_y).set_attribute(self, char_attribute)
        if result:
            self.changes = True
        return result

    def set_background(self, background_path):
        self.background_data = numpy.fromfile(background_path, dtype='uint8')
        self.background = background_path
        self.zx_screen.flip_memory(self.background_data)
        self.render_cells()
        self.changes = True

    def set_cell(self, char_x, char_y, cell_copy: Optional[CellCopy]=None, char_code=UNDEFINED, char_attribute=UNDEFINED, char_inverted=UNDEFINED) -> bool:
        cell = self.__lookup_cell(char_x, char_y)
        if cell_copy:
            char_code = cell_copy.char_code
            char_attribute = cell_copy.char_attribute
            char_inverted = cell_copy.char_inverted
        result = False
        if not char_code == self.UNSPECIFIED:
            result = True if cell.set_character(self, char_code, sync_screen=False) else result
        if not char_attribute == self.UNSPECIFIED:
            result = True if cell.set_attribute(self, char_attribute, sync_screen=False) else result
        if not char_inverted == self.UNSPECIFIED:
            result = True if cell.set_inverted(self, char_inverted, sync_screen=False) else result
        if result:
            cell.sync_screen(self)
            self.changes = True
        return result

    def set_string(self, start_x, start_y, string, char_attribute=UNSPECIFIED, char_inverted=UNSPECIFIED) -> bool:
        position = ZXScreenIterator(start_x, start_y, allow_looping=True)
        for character in string:
            current_x, current_y = next(position)
            self.set_cell(current_x, current_y, char_code=ord(character), char_attribute=char_attribute, char_inverted=char_inverted)

    def set_character(self, char_x, char_y, char_code=UNDEFINED) -> bool:
        result = self.__lookup_cell(char_x, char_y).set_character(self, char_code)
        if result:
            self.changes = True
        return result

    def set_document(self, document_path):
        self.document_path = document_path

    def set_inverted(self, char_x, char_y, char_inverted=UNDEFINED) -> bool:
        result = self.__lookup_cell(char_x, char_y).set_inverted(self, char_inverted)
        if result:
            self.changes = True
        return result

    def set_selected_font(self, font_name):
        self.font_name = font_name
        self.font_path = self.get_font_path(font_name)
        self.font = ZXFont.from_file(self.font_path)

    def set_selected_glyph(self, glyph_name):
        self.glyph_name = glyph_name
        self.glyph_path = self.get_font_path(glyph_name)
        self.glyph = ZXGlyph.from_file(self.glyph_path)

    def get_font_path(self, font_name):
        return Path('.') / 'fonts' / f'{font_name}.bin'

    def save(self):
        if self.document_path:
            self.export(self.document_path)
            self.changes = False
            return
        raise Exception('No document set')

    def to_dict(self):
        result = self.__yaml_defaults()
        root = result[self.__class__.__name__]
        root['attribute'] = self.current_attribute
        root['background'] = self.__get_relative_path(self.background)
        root['font'] = self.font_name
        root['glyph'] = self.glyph_name
        for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
            for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                root['cells'][char_y][char_x] = self.__lookup_cell(char_x, char_y).to_dict()
        return result
    
    def __get_relative_path(self, path):
        return os.path.relpath(path, os.path.dirname(self.document_path)) if path else None

    def to_rgb(self, flash_value=False):
        return self.zx_screen.to_rgb(flash_value)


    @classmethod
    def from_file(cls, document_path):
        zx_token = ZXToken()
        zx_token.load(document_path)
        return zx_token


class CellCopy():
    UNDEFINED = 'UNDEFINED'

    def __init__(self, char_code=ZXToken.UNDEFINED, char_attribute=ZXToken.UNDEFINED, char_inverted=ZXToken.UNDEFINED):
        self.char_code = char_code
        self.char_attribute = char_attribute
        self.char_inverted = char_inverted
    
    def __str__(self):
        return "{} ({})".format(
            self.__format_char(),
            ' '.join(self.__to_tokens())
        )

    def __format_char(self):
        if self.char_code == ZXToken.UNDEFINED:
            return self.UNDEFINED
        return "0x{0:02x}".format(self.char_code)

    def __to_tokens(self):
        tokens = []
        if not self.char_code == ZXToken.UNDEFINED:
            tokens += ZXScreen.to_tokens(self.char_attribute)
        if not self.char_inverted == ZXToken.UNDEFINED:
            tokens += [f"INVERTED={int(self.char_inverted)}"]
        if not tokens:
            return [self.UNDEFINED]
        return tokens

    @classmethod
    def from_values(cls, char_code=ZXToken.UNDEFINED, char_attribute=ZXToken.UNDEFINED, char_inverted=ZXToken.UNDEFINED) -> CellCopy:
        return cls(char_code, char_attribute, char_inverted)
    
    @classmethod
    def from_cell(cls, cell: ZXTokenCell) -> CellCopy:
        return cls(
            cell.char_code,
            cell.char_attribute,
            cell.char_inverted
        )


class ZXTokenCell:
    def __init__(self, char_x, char_y, char_code=ZXToken.UNDEFINED, char_attribute=ZXToken.UNDEFINED, char_inverted=ZXToken.UNDEFINED):
        self.char_x = char_x
        self.char_y = char_y
        self.char_code = char_code
        self.char_attribute = char_attribute
        self.char_inverted = char_inverted

    def debug(self, zx_token: ZXToken):
        print(f'Cell X={self.char_x},Y={self.char_y}:')

        if not self.char_code == ZXToken.UNDEFINED:
            print(f'  char_code      = {self.char_code} ({chr(self.char_code)})')
        else:
            print(f'  char_code      = UNDEFINED')

        if not self.char_attribute == ZXToken.UNDEFINED:
            print("  char_attribute = {0} (0x{1:02x})".format(self.char_attribute, self.char_attribute))
        else:
            print(f'  char_attribute = UNDEFINED')
        if not self.char_inverted == ZXToken.UNDEFINED:
            print(f'  char_inverted  = {self.char_inverted}')
        else:
            print(f'  char_inverted  = UNDEFINED')

        memory = zx_token.zx_screen.read_cell(self.char_x, self.char_y)
        for idx, value in enumerate(memory):
            s_value = "{:08b}".format(value)
            if idx == 0:
                print("  memory         = {0} (0x{1:04x})".format(s_value, ZXScreen.calculate_offset_data(self.char_x, self.char_y, row=idx)))
            else:
                print("                   {0} (0x{1:04x})".format(s_value, ZXScreen.calculate_offset_data(self.char_x, self.char_y, row=idx)))
        source = ZXScreen.__name__ if self.char_attribute == ZXToken.UNDEFINED else ZXToken.__name__
        s_value = "{:08b}".format(self.get_attribute(zx_token))
        print(        "  attribute      = {0} (0x{1:04x}) from {2}".format(
            s_value,
            ZXScreen.calculate_offset_attribute(self.char_x, self.char_y),
            source))
        print()

    def render_character(self, zx_token: ZXToken):
        if self.char_code == ZXToken.UNDEFINED:
            return

        if self.char_code >= ZXFont.ASCII_SPACE and self.char_code <= ZXFont.ASCII_COPYRIGHT:
            zx_token.zx_screen.write_cell(
                self.char_x, 
                self.char_y, 
                zx_token.font.get_offset(self.char_code - ZXFont.ASCII_SPACE),
                self.__select_attribute(self.char_attribute)
            )
        if self.char_code >= ZXGlyph.GLYPH_OFFSET:
            zx_token.zx_screen.write_cell(
                self.char_x, 
                self.char_y, 
                zx_token.glyph.get_offset(self.char_code - ZXGlyph.GLYPH_OFFSET),
                self.__select_attribute(self.char_attribute)
            )

    def get_attribute(self, zx_token: ZXToken):
        if self.char_attribute == ZXToken.UNDEFINED:
            return zx_token.zx_screen.get_attribute_at(self.char_x, self.char_y)
        return self.char_attribute

    def sync_screen(self, zx_token: ZXToken):
        # Pixels are either rendered from a specified character, or we attempt
        # to recover the original pixels from the background image.
        if self.char_code == ZXToken.UNDEFINED:
            if zx_token.has_background():
                zx_token.zx_screen.write_cell(
                    self.char_x, 
                    self.char_y,
                    ZXScreen.exctract_cell(self.char_x, self.char_y, zx_token.background_data)
                )
            else:
                # no character, overwrite screen memory with empty space
                zx_token.zx_screen.write_cell(
                    self.char_x, 
                    self.char_y, 
                    zx_token.font.get_offset(0)
                )
        else:
            if self.char_code >= ZXFont.ASCII_SPACE and self.char_code <= ZXFont.ASCII_COPYRIGHT:
                zx_token.zx_screen.write_cell(
                    self.char_x, 
                    self.char_y, 
                    zx_token.font.get_offset(self.char_code - ZXFont.ASCII_SPACE)
                )
            if self.char_code >= ZXGlyph.GLYPH_OFFSET:
                zx_token.zx_screen.write_cell(
                    self.char_x, 
                    self.char_y, 
                    zx_token.glyph.get_offset(self.char_code - ZXGlyph.GLYPH_OFFSET)
                )

        # Sync attribute information. Note that without a character present, we
        # will effectively ignore the value set (giving priority to original
        # value).
        if self.char_code == ZXToken.UNDEFINED:
            if zx_token.has_background():
                # We don't have a character, but a background so we restore it
                # from there.
                bg_index = ZXScreen.calculate_offset_attribute(self.char_x, self.char_y)
                bg_attribute = zx_token.background_data[bg_index]
                zx_token.zx_screen.write_attribute(
                    self.char_x, 
                    self.char_y, 
                    self.__select_attribute(bg_attribute))                
            else:
                # There was no background so we'll use value from the document.
                zx_token.zx_screen.write_attribute(
                    self.char_x, 
                    self.char_y, 
                    zx_token.current_attribute)
        else:
            # character included

            if self.char_attribute == ZXToken.UNDEFINED:
                # No attribute

                if zx_token.has_background():
                    # restore from background
                    bg_index = ZXScreen.calculate_offset_attribute(self.char_x, self.char_y)
                    bg_attribute = zx_token.background_data[bg_index]
                    zx_token.zx_screen.write_attribute(
                        self.char_x, 
                        self.char_y, 
                        self.__select_attribute(bg_attribute))                
                else:
                    # restore default attribute
                    zx_token.zx_screen.write_attribute(
                        self.char_x, 
                        self.char_y, 
                        zx_token.current_attribute)
            else:
                zx_token.zx_screen.write_attribute(
                    self.char_x, 
                    self.char_y, 
                    self.__select_attribute(self.char_attribute))

    def set_attribute(self, zx_token: ZXToken, char_attribute=ZXToken.UNDEFINED, sync_screen=True):
        changed = (not self.char_attribute == char_attribute)
        self.char_attribute = char_attribute
        if sync_screen:
            self.sync_screen(zx_token)
        return changed

    def set_inverted(self, zx_token: ZXToken, char_inverted=ZXToken.UNDEFINED, sync_screen=True):
        changed = (not self.char_inverted == char_inverted)
        self.char_inverted = char_inverted
        if sync_screen:
            self.sync_screen(zx_token)
        return changed
    
    def __select_attribute(self, attribute):
        if self.char_inverted == ZXToken.UNDEFINED or not self.char_inverted:
            return attribute
        parsed = ZXScreen.to_parsed_attribute(attribute)
        return ZXScreen.to_attribute(
            is_flashing=parsed['flash'],
            is_bright=parsed['bright'],
            ink=parsed['paper'],
            paper=parsed['ink']
        )

    def set_character(self, zx_token: ZXToken, char_code=ZXToken.UNDEFINED, sync_screen=True):
        changed = (not self.char_code == char_code)
        self.char_code = char_code
        if sync_screen:
            self.sync_screen(zx_token)
        return changed

    def to_dict(self):
        return {
            'char_code': int(self.char_code),
            'attribute': int(self.char_attribute),
            'inverted': int(self.char_inverted)
        }
    
    def from_dict(self, data):
        self.char_code = data['char_code']
        self.char_attribute = data['attribute']
        self.char_inverted = int(data['inverted'])


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

    def __init__(self, zx_token: ZXToken):
        self.zx_token = zx_token
        self.current_attribute = zx_token.current_attribute

        parsed = ZXScreen.to_parsed_attribute(self.current_attribute)
        self.last_ink = parsed['ink']
        self.last_paper = parsed['paper']
        self.last_bright = parsed['bright']
        self.last_flash = parsed['flash']
        self.last_xor = False
        self.last_inverted = False
        self.last_xor = False
        self.cursor_x = 0
        self.cursor_y = 0

    def write_formatted(self, specscii_path):
        with open(specscii_path, 'wb') as file:
            for char_y in range(ZXScreen.SCREEN_HEIGHT_CHARS):
                for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
                    cell = self.zx_token.cells[char_y][char_x]

                    # Skip if there's no content
                    if cell.char_code == ZXToken.UNDEFINED:
                        continue

                    # Move cursor to match
                    self.__write_cursor(file, char_x, char_y)

                    # Update attribute at location
                    if not cell.char_attribute == ZXToken.UNDEFINED:
                        self.__set_attribute(file, cell.char_attribute)

                    self.__write_inverted(file, self.__get_inverted(cell.char_inverted))

                    # Output a character
                    if not cell.char_code == ZXToken.UNDEFINED:
                        self.__write_character(file, cell.char_code)
    
    def __get_inverted(self, value):
        if value == ZXToken.UNDEFINED:
            return False
        return bool(value)

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

    def __write_inverted(self, file, is_inverted):
        '''
        Remove client should set a variable to swap ink/paper upon printing
        data to the screen. This allows a file to highlight text without
        knowing the colour scheme used on the other end.
        '''
        assert is_inverted == True or is_inverted == False
        if self.last_inverted == is_inverted:
            return
        self.last_inverted = is_inverted
        self.__write_bytes(
            file, 
            (self.SET_INVERSE, 1 if is_inverted else 0)
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
    def write_document(cls, zx_token: ZXToken, specscii_path):
        SpecsciiFormat(zx_token).write_formatted(specscii_path)
