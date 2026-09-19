from .zx_screen import ZXScreen

class Coordinate:
    '''
    Representing a character cell on the ZX Spectrums screen, ensuring that
    values are always within defined limits by doing a modulo-operation. 
    '''
    char_x: int
    char_y: int

    def __init__(self, char_x: int, char_y: int):
        self.char_x = self.__filter_x(char_x)
        self.char_y = self.__filter_y(char_y)

    def __str__(self):
        return f'(X={self.char_x}, Y={self.char_y})'

    def __eq__(self, value):
        return (self.char_x == value.x and self.char_y == value.y)

    def get(self):
        return (self.char_x, self.char_y)

    def set(self, char_x, char_y) -> bool:
        prev_x, prev_y = self.get()
        self.char_x = self.__filter_x(char_x)
        self.char_y = self.__filter_y(char_y)
        return not (self.char_x == prev_x and self.char_y == prev_y)

    @classmethod
    def get_box(self, coord_a: Coordinate, coord_b: Coordinate):
        return (Coordinate(min(coord_a.char_x, coord_b.char_x), min(coord_a.char_y, coord_b.char_y)),
                Coordinate(max(coord_a.char_x, coord_b.char_x), max(coord_a.char_y, coord_b.char_y)))

    @classmethod
    def __filter_x(cls, char_x):
        return (char_x % ZXScreen.SCREEN_WIDTH_CHARS)

    @classmethod
    def __filter_y(cls, char_y):
        return (char_y % ZXScreen.SCREEN_HEIGHT_CHARS)
