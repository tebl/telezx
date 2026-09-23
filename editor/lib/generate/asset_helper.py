from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .repository_helper import RepositoryHelper
from .. import ZXDocument, ZXPage_Token, ZXGlyph, ZXFont, ZXFrame, ZXScreen, ZXToken, utilities

class AssetHelper(RepositoryHelper):
    DEFAULT_DESCRIPTION = 'default'
    TEST_TITLE = 'Test page'
    TEST_ABBREVIATION = 'Test'

    TEST_COLOUR_BARS = 'Colour bars'
    TEST_FONT = 'Characters'
    TEST_GLYPHS = 'Glyphs'

    def __init__(self, repository: Path):
        super().__init__(repository)
        self.create_path_structure()
        self.open_registry()

    def create_frames(self, indent: int=0):
        frame_path = self.asset_path / self.get_filename()
        frame = ZXFrame.create_frame(frame_path)
        frame.overlay_skirt(ZXToken.DEFAULT_PAPER)
        frame.save()
        frame.set_string(1, 2, 'Example text')
        frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
        self.logger.info(f'{frame_path.name} created.', indent=indent)

        for description, using_ink, using_paper, text_attribute in ZXFrame.frame_colours():
            frame_path = self.asset_path / self.get_filename(description, has_frame=True)
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_box(using_ink, using_paper, text_attribute)
            frame.save()
            frame.set_string(1, 2, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.info(f'{frame_path.name} created.', indent=indent)

            frame_path = self.asset_path / self.get_filename(description, has_frame=True, has_title=True)
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_title_box(using_ink, using_paper, text_attribute)
            frame.save()
            frame.set_string(1, 2, 'Title here')
            frame.set_string(1, 4, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.info(f'{frame_path.name} created.', indent=indent)

            frame_path = self.asset_path / self.get_filename(description, has_title=True)
            frame = ZXFrame.create_frame(frame_path)
            frame.overlay_title(using_ink, using_paper, text_attribute)
            frame.overlay_skirt(using_paper)
            frame.save()
            frame.set_string(2, 2, 'Title here')
            frame.set_string(0, 4, 'Example text')
            frame.export_screenshot(f'{frame_path}{ZXDocument.EXTENSION_SCREENSHOT}')
            self.logger.info(f'{frame_path.name} created.', indent=indent)

    def create_test_pages(self, document_id: int=ZXDocument.DOCUMENT_ID_TEST):
        target_directory = self._create_document_path(document_id, 'Test page')
        self.logger.info('Creating', target_directory.name)

        with self._get_document(document_id, self.TEST_TITLE, self.TEST_ABBREVIATION, target_directory) as document:
            self.__create_index_page(document)
            self.__create_colour_bars(document)
            self.__create_symbol_page(document, self.TEST_FONT, details_func=self.__get_font_details)
            self.__create_symbol_page(document, self.TEST_GLYPHS, details_func=self.__get_glyph_details)

            # Save and export
            document.save()
            document.export(self.out_path, self.registry, sync_registry=True)

    def __create_index_page(self, document: ZXDocument):
        with self._get_titlepage(document, self.TEST_TITLE, add_frame=False) as page:
            items = [('01', self.TEST_COLOUR_BARS),
                     ('02', self.TEST_FONT),
                     ('03', self.TEST_GLYPHS)]
            x_offset = 8
            y_offset = 10

            page.set_string(x_offset, y_offset, 'Page overview:')
            x_offset += 1
            y_offset += 1
            for i, (number, description) in enumerate(items):
                page.set_string(x_offset, y_offset + i, number, char_attribute=ZXScreen.to_attribute(ink=ZXScreen.MAGENTA, paper=ZXScreen.WHITE))
                page.set_string(x_offset + 3, y_offset + i, description, char_attribute=ZXScreen.to_attribute(ink=ZXScreen.BLUE, paper=ZXScreen.WHITE))
            page.save()

        # Add reference to created token page
        ZXPage_Token(parent=document, zxtoken_path=page.document_path, export_format='TKN')

    def __create_colour_bars(self, document: ZXDocument):
        page: ZXToken
        with self._get_titlepage(document, self.TEST_COLOUR_BARS, add_frame=False) as page:
            colours = sorted(ZXScreen.COLOURS.items(), key=lambda x: x[1])

            char_x = 0
            char_y = 4

            for i in range(5):
                for bg_colour, bg_value in colours:
                    page.set_string(char_x, char_y, '  ', char_attribute=ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=bg_value))
                    char_x += 2
                    page.set_string(char_x, char_y, '  ', char_attribute=ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=bg_value, is_bright=True))
                    char_x += 2
                char_x = 0
                char_y += 1
            for fg_colour, fg_value in colours:
                for bg_colour, bg_value in colours:
                    page.set_string(char_x, char_y, '20', char_attribute=ZXScreen.to_attribute(ink=fg_value, paper=bg_value))
                    char_x += 2
                    page.set_string(char_x, char_y, '26', char_attribute=ZXScreen.to_attribute(ink=fg_value, paper=bg_value, is_bright=True))
                    char_x += 2
                char_x = 0
                char_y += 1
            for i in range(6):
                for bg_colour, bg_value in colours:
                    page.set_string(char_x, char_y, '  ', char_attribute=ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=bg_value))
                    char_x += 2
                    page.set_string(char_x, char_y, '  ', char_attribute=ZXScreen.to_attribute(ink=ZXScreen.BLACK, paper=bg_value, is_bright=True))
                    char_x += 2
                char_x = 0
                char_y += 1
            page.save()

        # Add reference to created token page
        ZXPage_Token(parent=document, zxtoken_path=page.document_path, export_format='TKN')

    def __create_symbol_page(self, document: ZXDocument, title, details_func):
        page: ZXToken
        with self._get_titlepage(document, title, add_frame=False) as page:
            char_y = 4
            char_x = 1
            offset, char_start, char_end = details_func(page)
            for i, char in enumerate(range(char_start, char_end)):
                char_code = offset + char
                page.set_cell(char_x, char_y, char_code=char_code, char_attribute=ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLACK, is_bright=True))
                char_x += 2
                if char_x >= ZXScreen.SCREEN_WIDTH_CHARS - 1:
                    char_x = 1
                    char_y += 2
            page.save()

        # Add reference to created token page
        ZXPage_Token(parent=document, zxtoken_path=page.document_path, export_format='TKN')

    def __get_font_details(self, page: ZXToken):
        return (0, page.font.ASCII_SPACE, page.font.ASCII_COPYRIGHT + 1)

    def __get_glyph_details(self, page: ZXToken):
        return (page.glyph.GLYPH_OFFSET, 0, page.glyph.get_glyph_count())

    def copy_default_frame(self, colour_name: str, global_asset: bool):
        base_path = utilities.get_project_root() / 'assets' if global_asset else self.asset_path
        self.__copy_default(base_path)
        self.__copy_default(base_path, colour_name, has_frame=True)
        self.__copy_default(base_path, colour_name, has_frame=True, has_title=True)
        self.__copy_default(base_path, colour_name, has_title=True)

    def __copy_default(self, base_path: Path, has_description: str|None=None, has_frame: bool=False, has_title: bool=False):
        path_src = self.asset_path / self.get_filename(has_description, has_frame, has_title)
        path_out = base_path / self.get_filename(self.DEFAULT_DESCRIPTION, has_frame, has_title)
        self.__copy_file(path_src, path_out)

        path_src = path_src.with_suffix(path_src.suffix + ZXDocument.EXTENSION_SCREENSHOT)
        path_out = path_out.with_suffix(path_out.suffix + ZXDocument.EXTENSION_SCREENSHOT)
        if path_src.is_file():
            self.__copy_file(path_src, path_out)
        elif path_out.is_file():
            self.logger.warning('Removing', path_out)
            path_out.unlink()

    def __copy_file(self, path_src, path_out):
        root = utilities.get_project_root()
        self.logger.info('Copy', path_src.relative_to(root), 
                          '->', path_out.relative_to(root))
        path_src.copy(path_out)

    def get_filename(self, has_description: str|None=None, has_frame: bool=False, has_title: bool=False):
        parts = []
        if has_description:
            parts.append(utilities.sanitize_filename(has_description))
        if has_frame:
            parts.append('frame')
        if has_title:
            parts.append('title')
        if not len(parts):
            parts.append('page')
        return '_'.join(parts) + ZXToken.FILE_EXTENSION