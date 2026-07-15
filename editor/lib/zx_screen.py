import numpy

class ZXScreen:
    # Attributes
    BLACK   = 0b00000000
    BLUE    = 0b00000001
    RED     = 0b00000010
    MAGENTA = 0b00000011
    GREEN   = 0b00000100
    CYAN    = 0b00000101
    YELLOW  = 0b00000110
    WHITE   = 0b00000111
    FLASH   = 0b10000000
    BRIGHT  = 0b01000000

    # Screen dimensions
    SCREEN_WIDTH_CHARS = 32
    SCREEN_WIDTH_PIXELS = SCREEN_WIDTH_CHARS*8
    SCREEN_HEIGHT_CHARS = 24
    SCREEN_HEIGHT_PIXELS = SCREEN_HEIGHT_CHARS*8
    SIZE_DATA = 6144
    SIZE_ATTR = 768
    SIZE_MEMORY = SIZE_DATA + SIZE_ATTR

    def __init__(self):
        self.memory = numpy.zeros(shape=self.SIZE_MEMORY, dtype=numpy.uint8)
        self.cursor_x = 0
        self.cursor_y = 0
        self.__calculate_lookup()


    def __calculate_lookup(self):
        self.start_at = [[0]*self.SCREEN_HEIGHT_CHARS for x in range(self.SCREEN_WIDTH_CHARS)]
        for pos_x in range(0, self.SCREEN_WIDTH_CHARS):
            for pos_y in range(0, self.SCREEN_HEIGHT_CHARS):
                lot = pos_y // 8
                self.start_at[pos_x][pos_y] = (lot * 0x800) + (pos_y - lot*8)*self.SCREEN_WIDTH_CHARS + pos_x


    def clear_memory(self, byte=0, attribute=BLACK):
        self.memory[:self.SIZE_DATA] = byte
        self.memory[self.SIZE_DATA:] = attribute


    def cursor_next(self):
        self.cursor_x += 1
        if self.cursor_x >= self.SCREEN_WIDTH_CHARS:
            self.cursor_x = 0
            self.cursor_y += 1
            if self.cursor_y >= self.SCREEN_HEIGHT_CHARS:
                self.cursor_y = 0


    def cursor_move(self, pos_x, pos_y):
        self.cursor_x = (pos_x % self.SCREEN_WIDTH_CHARS)
        self.cursor_y = (pos_y % self.SCREEN_HEIGHT_CHARS)


    def cursor_write(self, values, attribute=-1):
        self.write_cell(self.cursor_x, self.cursor_y, values, attribute)
        self.cursor_next()
    
    def flip_memory(self, numpy_array):
        if not isinstance(numpy_array, numpy.ndarray) or numpy_array.size != self.SIZE_MEMORY:
            raise ValueError('does not look like a numpy array of expected size')
        self.memory[:] = numpy_array[:]
        print("flipped memory")

    def get_attribute_at(self, pos_x, pos_y):
        attr_idx = self.__get_attr_idx(pos_x, pos_y)
        return self.memory[attr_idx]

    def to_rgb(self):
        pixels = numpy.zeros(shape=(self.SCREEN_HEIGHT_PIXELS, self.SCREEN_WIDTH_PIXELS, 3), dtype=numpy.uint8)
        for pos_x in range(self.SCREEN_WIDTH_CHARS):
            for pos_y in range(self.SCREEN_HEIGHT_CHARS):
                attr_idx = self.__get_attr_idx(pos_x, pos_y)
                attr_value = self.to_parsed_attribute(self.memory[attr_idx])

                data_start = self.start_at[pos_x][pos_y]
                for line in range(8):
                    data_idx = data_start + (line * 0x100)
                    data_value = self.memory[data_idx]
                    for bit_idx in range(8):
                        pixels[pos_y*8 + line, pos_x*8 + bit_idx] = self.to_attribute_rgb(
                            self.__check_bits(data_value, bit_idx),
                            attr_value
                        )
        return pixels


    def __get_attr_idx(self, pos_x, pos_y):
        return self.SIZE_DATA + (self.SCREEN_WIDTH_CHARS*pos_y + pos_x)


    def __check_bits(self, value, bit_idx):
        mask = (1 << (7 - bit_idx))
        return (value & mask) != 0


    def read_cell(self, pos_x, pos_y):
        result = []
        index = self.start_at[pos_x][pos_y]
        for byte_idx in range(8):
            result.append(self.memory[index + byte_idx*0x100])
        return result


    def write_cell(self, pos_x, pos_y, values, attribute=-1):
        if values.size != 8:
            raise ValueError(f'values ({values}) not array of 8 bytes')
        index = self.start_at[pos_x][pos_y]
        for byte_idx, byte_value in enumerate(values):
            self.memory[index + byte_idx*0x100] = byte_value
        if attribute >= self.BLACK:
            self.write_attribute(pos_x, pos_y, attribute)


    def write_attribute(self, pos_x, pos_y, attribute=0):
        self.memory[(pos_y * self.SCREEN_WIDTH_CHARS) + pos_x] = attribute


    @classmethod
    def colour_to_rgb(cls, colour, bright):
        base_value = 255 if bright else 224
        return [
            ((colour >> 1) & 1)*base_value,  # red
            ((colour >> 2) & 1)*base_value,  # green
            (colour & 1)*base_value          # blue
        ]

    @classmethod
    def to_attribute(cls, is_flashing=False, is_bright=False, paper=BLACK, ink=WHITE):
        return (
            (cls.FLASH if is_flashing else 0x00) | 
            (cls.BRIGHT if is_bright else 0x00) | 
            (paper << 3) |
            ink
        )

    @classmethod
    def to_attribute_rgb(cls, is_on, parsed_attribute):
        colour = parsed_attribute['ink'] if is_on else parsed_attribute['paper']
        return cls.colour_to_rgb(colour, parsed_attribute['bright'])

    @classmethod
    def to_parsed_attribute(cls, attribute):
        return {
            'flash': bool((attribute & cls.FLASH) == cls.FLASH),
            'bright': bool((attribute & cls.BRIGHT) == cls.BRIGHT),
            'paper': (attribute & 0b00111000) >> 3,
            'ink': attribute & 0b00000111
        }