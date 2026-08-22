from .zx_screen import ZXScreen, ZXScreenIterator
from .zx_token import ZXToken, ZXScreenIterator, ZXScreen

class ZXFrame(ZXToken):
    def __init__(self):
        super().__init__()

    def overlay_box(self, char_attribute, title_attribute):
        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.set_cell(char_x, 1, char_code=140, char_attribute=char_attribute)
            self.set_cell(char_x, 22, char_code=131, char_attribute=char_attribute)
        for char_y in range(2, ZXScreen.SCREEN_HEIGHT_CHARS - 2):
            self.set_cell(0, char_y, char_code=138, char_attribute=char_attribute)
            self.set_cell(31, char_y, char_code=133, char_attribute=char_attribute)

    def overlay_title_box(self, char_attribute, title_attribute):
        self.overlay_box(char_attribute, title_attribute)
        for char_x in range(ZXScreen.SCREEN_WIDTH_CHARS):
            self.set_cell(char_x, 2, char_code=32, char_attribute=title_attribute)

        for char_x in range(1, ZXScreen.SCREEN_WIDTH_CHARS - 1):
            self.set_cell(char_x, 3, char_code=131, char_attribute=char_attribute)
        self.set_cell(0, 3, char_code=139, char_attribute=char_attribute)
        self.set_cell(31, 3, char_code=135, char_attribute=char_attribute)

    def overlay_title(self, char_attribute, title_attribute):
        for char_x in range(1, ZXScreen.SCREEN_WIDTH_CHARS - 1):
            self.set_cell(char_x, 1, char_code=140, char_attribute=char_attribute)
            self.set_cell(char_x, 2, char_code=32, char_attribute=title_attribute)
            self.set_cell(char_x, 3, char_code=131, char_attribute=char_attribute)

    @classmethod
    def create_frame(cls, document_path):
        zx_frame = ZXFrame()
        zx_frame.set_document(document_path)
        return zx_frame

    @classmethod
    def frame_colours(cls):
        yield (
            'black', 
            ZXScreen.to_attribute(ink=ZXScreen.BLACK), 
            ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLACK)
        ) 
        yield (
            'blue', 
            ZXScreen.to_attribute(ink=ZXScreen.BLUE), 
            ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLUE)
        ) 
        yield (
            'red', 
            ZXScreen.to_attribute(ink=ZXScreen.RED), 
            ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.RED)
        ) 
        yield (
            'magenta', 
            ZXScreen.to_attribute(ink=ZXScreen.MAGENTA), 
            ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.MAGENTA)
        ) 
        yield (
            'green', 
            ZXScreen.to_attribute(ink=ZXScreen.GREEN), 
            ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.GREEN)
        ) 
        yield (
            'cyan', 
            ZXScreen.to_attribute(ink=ZXScreen.CYAN), 
            ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.CYAN)
        ) 
        yield (
            'yellow', 
            ZXScreen.to_attribute(ink=ZXScreen.YELLOW), 
            ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.YELLOW)
        ) 
        yield (
            'white', 
            ZXScreen.to_attribute(ink=ZXScreen.WHITE), 
            ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=ZXScreen.WHITE)
        )