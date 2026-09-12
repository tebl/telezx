from .zx_screen import ZXScreen, ZXScreenIterator
from .zx_token import ZXToken, ZXScreenIterator, ZXScreen

class ZXFrame(ZXToken):
    DEFAULT_ATTRIBUTE = ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.WHITE)
    HEADER_ATTRIBUTE = ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.BLACK)

    def __init__(self, init_attribute: int|None=None):
        super().__init__(init_attribute)

    def overlay_box(self, foreground, background, text_attribute):
        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.set_cell(char_x, 1, char_code=140, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=ZXScreen.BLACK))
            self.set_cell(char_x, 22, char_code=131, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=ZXScreen.BLACK))
        for char_y in range(2, ZXScreen.SCREEN_HEIGHT_CHARS - 2):
            self.set_cell(0, char_y, char_code=138, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=background))
            self.set_cell(31, char_y, char_code=133, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=background))

    def overlay_title_box(self, foreground, background, text_attribute):
        self.overlay_box(foreground, background, text_attribute)
        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.set_cell(char_x, 2, char_code=32, char_attribute=ZXScreen.to_attribute(ink=text_attribute, paper=foreground))

        for char_x in range(1, ZXScreen.SCREEN_WIDTH_CHARS - 1):
            self.set_cell(char_x, 3, char_code=131, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=background))
        self.set_cell(0, 3, char_code=139, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=background))
        self.set_cell(31, 3, char_code=135, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=background))

    def overlay_title(self, foreground, background, text_attribute):
        for char_x in range(1, ZXScreen.SCREEN_WIDTH_CHARS - 1):
            self.set_cell(char_x, 1, char_code=140, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=background))
            self.set_cell(char_x, 2, char_code=32, char_attribute=ZXScreen.to_attribute(ink=text_attribute, paper=foreground))
            self.set_cell(char_x, 3, char_code=131, char_attribute=ZXScreen.to_attribute(ink=foreground, paper=background))

    @classmethod
    def create_frame(cls, document_path):
        zx_frame = ZXFrame(init_attribute=ZXFrame.DEFAULT_ATTRIBUTE)
        zx_frame.set_document(document_path)

        # Black out areas expected to contain headers
        zx_frame.set_string(0, 0, ' '*ZXScreen.SCREEN_WIDTH_CHARS, char_attribute=cls.HEADER_ATTRIBUTE)
        zx_frame.set_string(0, ZXScreen.SCREEN_HEIGHT_CHARS - 1, ' '*ZXScreen.SCREEN_WIDTH_CHARS, char_attribute=cls.HEADER_ATTRIBUTE)
        return zx_frame

    @classmethod
    def frame_colours(cls):
        yield (
            'black',        # Name
            ZXScreen.BLACK, # Foreground
            ZXScreen.WHITE, # Background
            ZXScreen.WHITE  # Title colour
        ) 
        yield (
            'blue',
            ZXScreen.BLUE,
            ZXScreen.WHITE,
            ZXScreen.WHITE,
        ) 
        yield (
            'red', 
            ZXScreen.RED,
            ZXScreen.WHITE,
            ZXScreen.WHITE
        ) 
        yield (
            'magenta', 
            ZXScreen.MAGENTA,
            ZXScreen.WHITE,
            ZXScreen.WHITE
        ) 
        yield (
            'green', 
            ZXScreen.GREEN,
            ZXScreen.WHITE,
            ZXScreen.BLACK
        ) 
        yield (
            'cyan', 
            ZXScreen.CYAN,
            ZXScreen.WHITE,
            ZXScreen.BLACK
        ) 
        yield (
            'yellow', 
            ZXScreen.YELLOW,
            ZXScreen.WHITE,
            ZXScreen.BLACK
        ) 