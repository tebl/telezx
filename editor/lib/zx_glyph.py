import numpy

class ZXGlyph:
    def __init__(self, glyph_data):
        self.glyph_data = glyph_data

    def get_offset(self, offset):
        return self.glyph_data[offset]

    @classmethod
    def from_file(cls, path):
        font_data = numpy.fromfile(path, dtype=numpy.uint8)
        font_data = numpy.reshape(font_data, shape=((font_data.size // 8),8))
        return cls(font_data)


