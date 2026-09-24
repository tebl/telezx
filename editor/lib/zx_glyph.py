import numpy, string, typing
from pathlib import Path
from .utilities import format_padded_id, format_padded_int

class ZXGlyph:
    GLYPH_OFFSET = 0x80
    'Offset added to index to get character code'

    _glyph_data: numpy.ndarray
    _rgb_fg: int
    _rgb_bg: int
    _generate_rgb: bool

    def __init__(self, glyph_data: numpy.array, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        self._generate_rgb = generate_rgb
        self._rgb_fg = rgb_fg
        self._rgb_bg = rgb_bg
        self._set_glyph_data(glyph_data)

    def _set_glyph_data(self, glyph_data: numpy.array):
        self._glyph_data = glyph_data
        if self._generate_rgb:
            self.__generate_rgb(foreground=self._rgb_fg, background=self._rgb_bg)

    def __generate_rgb(self, foreground, background):
        self.rgb_data = {}
        for glyph_idx in range(self.get_glyph_count()):
            self.rgb_data[glyph_idx] = self.generate_glyph_rgb(glyph_idx, foreground, background)

    def glyphs(self) -> typing.Generator[tuple[int, numpy.ndarray]]:
        for idx in range(0, self.get_glyph_count()):
            yield (self.get_charcode_offset(idx), self.get_offset(idx))

    def glyphs_rgb(self) -> typing.Generator[tuple[int, numpy.ndarray]]:
        if not self._generate_rgb:
            raise ValueError('RGB not available')
        for idx in range(0, self.get_glyph_count()):
            yield (self.get_charcode_offset(idx), self.get_offset_rgb(idx))

    def generate_glyph_rgb(self, offset, foreground, background):
        data = numpy.full(shape=(8, 8, 3), fill_value=background, dtype=numpy.uint8)
        for row_idx, row_value in enumerate(self.get_offset(offset)):
            for bit_idx in range(8):
                value = foreground if self.__check_bits(row_value, bit_idx) else background
                data[row_idx, bit_idx] = value
        return data

    def __check_bits(self, value, bit_idx):
        mask = (1 << (7 - bit_idx))
        return (value & mask) != 0

    def get_offset(self, offset):
        return self._glyph_data[offset]
    
    def get_offset_rgb(self, offset):
        return self.rgb_data[offset]

    def get_charcode_offset(self, value: int=0) -> int:
        return self.GLYPH_OFFSET + value

    def get_glyph_count(self):
        '''
        Get the number of glyphs stored in the underlying data structure
        '''
        return self._glyph_data.shape[0]

    def add_glyph(self, values: list[int, int, int, int, int, int, int, int]):
        '''
        Adds an 8x8 glyph to the underlying data structure
        '''
        if not len(values) == 8:
            raise ValueError('Not 8x8 UDG')
        self._set_glyph_data(numpy.insert(self._glyph_data, self._glyph_data.shape[0], values=values, axis=0))

    def write(self, path: Path):
        glyph_data = numpy.reshape(self._glyph_data, shape=(self.get_glyph_count()*8))
        with open(path, 'wb') as file:
            file.write(glyph_data)

    def export_js(self, path: Path, name: str|None=None) -> bool:
        indent = ' '*4
        with open(path, 'w') as file:
            file.write(f'const {self._get_js_name(name)} = [\n')
            for glyph_idx in range(0, self.get_glyph_count()):
                file.write(f'{indent} ')
                for value in self.get_offset(glyph_idx):
                    file.write(f'0x{format_padded_id(value, width=2).lower()}, ')

                char_code = self.get_charcode_offset(glyph_idx)
                if chr(char_code) in string.printable:
                    file.write(f' /* {str(char_code).rjust(3) } = "{chr(char_code)}" */')
                else:
                    file.write(f' /* {str(char_code).rjust(3) } */')
                file.write('\n')
            file.write('];\n')
        return True

    def _get_js_name(self, name: str) -> str:
        if not name:
            return f'FONT_GLYPHS'
        return f'FONT_{name.upper()}'

    @classmethod
    def generate_blank_glyph(cls):
        return [0x0]*8

    @classmethod
    def empty_file(cls, rgb_fg: int=255, rgb_bg: int=0, generate_rgb: bool=False):
        glyph_data = numpy.empty(shape=(0, 8), dtype=numpy.uint8)
        return cls(glyph_data, rgb_fg, rgb_bg, generate_rgb)
    
    @classmethod
    def from_file(cls, path: Path, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        glyph_data = numpy.fromfile(path, dtype=numpy.uint8)
        glyph_data = numpy.reshape(glyph_data, shape=((glyph_data.size // 8),8))
        return cls(glyph_data, rgb_fg, rgb_bg, generate_rgb)