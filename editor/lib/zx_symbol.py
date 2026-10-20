import numpy, string, typing
from pathlib import Path
from PIL import Image
from .utilities import format_padded_id, BinaryYAML
from .zx_screen import ZXScreen
type UDG = list[int, int, int, int, int, int, int, int]

class ZXSymbol:
    GLYPH_WIDTH = 8
    GLYPH_HEIGHT = 8

    _glyph_data: numpy.ndarray
    _mask_data: dict[int, numpy.ndarray]
    _rgb_fg: int
    _rgb_bg: int
    _generate_rgb: bool

    def __init__(self, glyph_data: numpy.array, char_code_offset: int, rgb_fg: int=255, rgb_bg: int=0, generate_rgb=False):
        self._char_code_offset = char_code_offset
        self._generate_rgb = generate_rgb
        self._rgb_fg = rgb_fg
        self._rgb_bg = rgb_bg
        self._set_glyph_data(glyph_data)

    # def __iter__(self):
    #     return iter(self.pages)

    def _set_glyph_data(self, glyph_data: numpy.array):
        self._glyph_data = glyph_data
        self._mask_data = {}
        if self._generate_rgb:
            self.__generate_rgb()

    def __generate_rgb(self):
        self.rgb_data = {}
        for glyph_idx in range(self.count_symbols()):
            self.rgb_data[glyph_idx] = self.__generate_symbol_rgb(glyph_idx)

    def add_symbol(self, values: UDG):
        '''
        Adds an 8x8 glyph to the underlying data structure
        '''
        if not len(values) == 8:
            raise ValueError('Not 8x8 UDG')
        self._set_glyph_data(numpy.insert(self._glyph_data, self._glyph_data.shape[0], values=values, axis=0))

    def count_symbols(self):
        '''
        Get the number of glyphs stored in the underlying data structure
        '''
        return self._glyph_data.shape[0]

    def update_symbol(self, offset: int, values: UDG):
        '''
        Update a symbols pixel data. When the symbol has been masked out we'll
        silently forget about that detail.
        '''
        self._validate_offset(offset)
        if not len(values) == 8:
            raise ValueError('Not 8x8 UDG')
        self._glyph_data[offset] = values

        if offset in self._mask_data:
            self.mask_symbol(offset, None)
        else:
            if self._generate_rgb:
                self.rgb_data[offset] = self.__generate_symbol_rgb(offset)

    def mask_symbol(self, offset: int, values: UDG|None):
        '''
        When dealing with the user definable symbols we'll need to selectively
        return that data instead of what's stored in the file, calling
        mask_symbol sets the data to use instead for a specific offset. Note
        that toggling it's state will also change RGB-version of the data.
        '''
        if values is None:
            if offset in self._mask_data:
                del self._mask_data[offset]
        else:
            self._mask_data[offset] = values
        if self._generate_rgb:
            self.rgb_data[offset] = self.__generate_symbol_rgb(offset)

    def generate_rgb(self, rgb_fg: int=255, rgb_bg: int=0, force: bool=False):
        if not self._generate_rgb or force:
            self._generate_rgb = True
            self._rgb_fg = rgb_fg
            self._rgb_bg = rgb_bg
            self.__generate_rgb()

    def symbols(self, translate_offset: bool=True) -> typing.Generator[tuple[int, numpy.ndarray]]:
        for idx in range(0, self.count_symbols()):
            yield (self.get_char_code_from_offset(idx) if translate_offset else idx,
                   self.get_offset(idx))

    def symbols_rgb(self) -> typing.Generator[tuple[int, numpy.ndarray]]:
        if not self._generate_rgb:
            raise ValueError('RGB not available')
        for idx in range(0, self.count_symbols()):
            yield (self.get_char_code_from_offset(idx), self.get_offset_rgb(idx))

    def __generate_symbol_rgb(self, offset: int):
        data = numpy.full(shape=(8, 8, 3), fill_value=self._rgb_bg, dtype=numpy.uint8)
        for row_idx, row_value in enumerate(self.get_offset(offset)):
            for bit_idx in range(8):
                value = self._rgb_fg if self.__check_bits(row_value, bit_idx) else self._rgb_bg
                data[row_idx, bit_idx] = value
        return data

    def __check_bits(self, value: int, bit_idx: int) -> int:
        mask = (1 << (7 - bit_idx))
        return (value & mask) != 0

    def get_offset(self, offset: int):
        self._validate_offset(offset)
        if offset in self._mask_data:
            return self._mask_data[offset]
        return self._glyph_data[offset]

    def _validate_offset(self, offset: int) -> bool:
        if offset < 0 or offset >= self.count_symbols():
            raise ValueError('Invalid offset')
        return True

    def get_offset_from(self, char_code: int):
        return self.get_offset(self.get_offset_from_char_code(char_code))

    def get_offset_transform(self, offset: int, mirror: bool=False, flip: bool=False):
        data = self.get_offset(offset)
        if flip:
            data = numpy.flip(data)
        if mirror:
            return numpy.array([ numpy.packbits(numpy.unpackbits(data[idx])[::-1])[0] for idx in range(self.GLYPH_HEIGHT) ], dtype=numpy.uint8)
        return data

    def get_offset_rgb(self, offset: int):
        self._validate_offset(offset)
        return self.rgb_data[offset]

    def get_char_code_from_offset(self, value: int=0) -> int:
        return self._char_code_offset + value

    def get_offset_from_char_code(self, char_code: int=0) -> int:
        return char_code - self._char_code_offset

    def is_blank(self, offset: int) -> bool:
        if offset == 0:
            return False
        return max(self.get_offset(offset)) == 0

    def print_preview(self, char_fill: str|None=None, char_empty: str|None=None):
        for idx in range(0, self.count_symbols()):
            print(f'{self.get_char_code_from_offset(idx)}:')
            self.print_offset_preview(idx, char_fill, char_empty)

    def print_offset_preview(self, offset: int, char_fill: str|None=None, char_empty: str|None=None):
        print("▄▄▄▄▄▄▄▄▄▄")
        for line in self.__get_offset_preview(offset, char_fill, char_empty):
            print(f'▌{''.join(line)}▐')
        print("▀▀▀▀▀▀▀▀▀▀")

    def __get_offset_preview(self, offset: int, char_fill: str|None=None, char_empty: str|None=None):
        data = self.get_offset(offset)
        return [ self.__preview_byte(value, char_fill, char_empty) for value in data ]

    def __preview_byte(self, value: int, char_fill: str|None=None, char_empty: str|None=None):
        if not char_fill:
            char_fill = '█'
        if not char_empty:
            char_empty = '░'
        return [ char_fill if self.__check_bits(value, bit_idx) else char_empty for bit_idx in range(8)]

    def write(self, path: Path):
        glyph_data = numpy.reshape(self._glyph_data, shape=(self.count_symbols()*8))
        with open(path, 'wb') as file:
            file.write(glyph_data)

    def export_js(self, path: Path, name: str|None=None) -> bool:
        with open(path, 'w') as file:
            self.export_js_file(file, name)
        return True

    def export_js_file(self, file, name: str|None=None):
        indent = ' '*4
        file.write(f'const {self._get_js_name(name)} = [\n')
        for glyph_idx in range(0, self.count_symbols()):
            file.write(f'{indent} ')
            for value in self.get_offset(glyph_idx):
                file.write(f'0x{format_padded_id(value, width=2).lower()}, ')

            char_code = self.get_char_code_from_offset(glyph_idx)
            if chr(char_code) in string.printable:
                file.write(f' /* {str(char_code).rjust(3) } = "{chr(char_code)}" */')
            else:
                file.write(f' /* {str(char_code).rjust(3) } */')
            file.write('\n')
        file.write('];\n')

    def _get_js_name(self, name: str) -> str:
        if not name:
            return f'FONT_SYMBOLS'
        return f'FONT_{name.upper()}'

    def export_png(self, path: Path) -> bool:
        zx_screen = ZXScreen()
        zx_screen.clear_memory(0, ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.WHITE))
        attribute = ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.WHITE, is_bright=True)

        char_y = 0
        char_x = 0
        for idx in range(0, self.count_symbols()):
            zx_screen.write_cell(
                char_x, 
                char_y, 
                self.get_offset(idx),
                attribute
            )

            char_x += 1
            if char_x > ZXScreen.SCREEN_WIDTH_CHARS - 1:
                char_x = 0
                char_y += 1

        image = Image.fromarray(zx_screen.to_rgb())
        image.save(path)

    @classmethod
    def generate_blank_glyph(cls):
        return [0x0]*8

    @classmethod
    def generate_placeholder_glyph(cls):
        return [
            0b11111111,
            0b10000001,
            0b10100101,
            0b10100101,
            0b10100101,
            0b10011001,
            0b10000001,
            0b11111111
        ]

    @classmethod
    def empty_file(cls, rgb_fg: int=255, rgb_bg: int=0, generate_rgb: bool=False):
        glyph_data = numpy.empty(shape=(0, 8), dtype=numpy.uint8)
        return cls(glyph_data, char_code_offset=cls.CHAR_CODE_OFFSET, rgb_fg=rgb_fg, rgb_bg=rgb_bg, generate_rgb=generate_rgb)
        
    @classmethod
    def from_file(cls, path: Path, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        glyph_data = numpy.fromfile(path, dtype=numpy.uint8)
        glyph_data = numpy.reshape(glyph_data, shape=((glyph_data.size // 8),8))
        return cls(glyph_data, char_code_offset=cls.CHAR_CODE_OFFSET, rgb_fg=rgb_fg, rgb_bg=rgb_bg, generate_rgb=generate_rgb)


class CustomCharacter:
    _data: UDG

    def __init__(self, data: UDG|None=None):
        self.data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data: UDG):
        if data is None:
            data = ZXSymbol.generate_blank_glyph()
        if not len(data) == 8:
            raise ValueError('Not 8x8 UDG')
        self._data = data

    def to_dict(self):
        return [ BinaryYAML(v) for v in self.data ]
