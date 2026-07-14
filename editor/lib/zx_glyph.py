import numpy

class ZXGlyph:
    GLYPH_OFFSET = 0x80

    def __init__(self, glyph_data, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        self.glyph_data = glyph_data
        if generate_rgb:
            self.__generate_rgb(foreground=rgb_fg, background=rgb_bg)

    def __generate_rgb(self, foreground, background):
        self.rgb_data = {}
        for glyph_idx in range(self.get_glyph_count()):
            self.rgb_data[glyph_idx] = self.__generate_glyph_rgb(glyph_idx, foreground, background)

    def __generate_glyph_rgb(self, offset, foreground, background):
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
        return self.glyph_data[offset]
    
    def get_offset_rgb(self, offset):
        return self.rgb_data[offset]

    def get_glyph_count(self):
        return self.glyph_data.shape[0]

    @classmethod
    def from_file(cls, path, rgb_fg=255, rgb_bg=0, generate_rgb=False):
        glyph_data = numpy.fromfile(path, dtype=numpy.uint8)
        glyph_data = numpy.reshape(glyph_data, shape=((glyph_data.size // 8),8))
        return cls(glyph_data, rgb_fg, rgb_bg, generate_rgb)