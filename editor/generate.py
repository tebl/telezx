from pathlib import Path
from lib import ZXScreen, ZXDocument, ZXToken, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities
ZXLogger.get_instance().set_log_level(ZXLogger.LOG_DEBUG)

class TOCGenerator:
    registry_path: Path
    pages_path: Path
    output_path: Path

    enable_preview = True

    def __init__(self, registry_path: Path, pages_path: Path, output_path: Path):
        self.logger = ZXLogger.get_instance()
        self.registry = ZXRegistry.from_file(registry_path, allow_create=True)
        self.pages_path = pages_path
        self.output_path = output_path

    def create_toc(self, document_id_start = 9900):
        document_id = document_id_start
        self.__create_toc_index(document_id)

        registry_toc = self.registry.generate_TOC_AZ()
        for letter in self.registry.LETTERS_AZ:
            document_id += 1
            target_directory = self.__create_path(document_id, f'TOC-{letter}')

            with self.__get_document(document_id, f'A-Z ({letter})', f'TOC-{letter}', target_directory) as document:
                document.link_a = document_id_start
                items = registry_toc[letter] if letter in registry_toc else []
                current_y = 4
                page_id = 0

                current_page = self.__get_titlepage(document_id, page_id, f'A-Z ({letter})', target_directory)

                first_item = True
                for description, link_id in items:
                    if not first_item:
                        # traverse pages, adding as needed
                        if current_y >= 20:
                            current_y = 3
                            if page_id < 99:
                                current_page.save()
                                ZXPage_Token(parent=document, zxtoken_path=current_page.document_path.name, export_format='TKN')

                                page_id += 1
                                current_page = self.__get_page(document_id, page_id, target_directory)
                            else:
                                self.logger.error(f'Item count for letter {letter} was truncated')
                                break
                        else:
                            current_y += 1
                    else:
                        first_item = False

                    current_page.set_string(1, current_y, self.__pad_entry(description))
                    current_page.set_string(27, current_y, link_id, char_attribute=ZXScreen.to_attribute(ink=ZXScreen.CYAN))

                current_page.save()
                ZXPage_Token(parent=document, zxtoken_path=current_page.document_path.name, export_format='TKN')

                document.save()
                document.export(self.output_path, self.registry)

    def __pad_entry(self, string, max_length = 25):
        string = string[0:max_length]
        if len(string) < (max_length - 1):
            return (string + ' ').ljust(max_length, '.')
        return string

    def __create_toc_index(self, document_id):
        page_title = 'Table of contents'
        page_abbreviation = 'TOC'
        target_directory = self.__create_path(document_id, 'TOC-Index')

        with self.__get_document(document_id, page_title, page_abbreviation, target_directory) as document:
            document.link_a = 1000

            with self.__get_titlepage(document_id, 0, page_title, target_directory) as page:
                page.set_string(1, 5, 'The corresponding pages have  ')
                page.set_string(1, 6, 'been generated based on TeleZX')
                page.set_string(1, 7, 'registry.')

                start_y = 10
                current_x = 2
                current_y = start_y
                for number, letter in enumerate(self.registry.LETTERS_AZ):
                    page.set_string(current_x, current_y, f'[{letter}]', ZXScreen.to_attribute(ink=ZXScreen.GREEN))
                    page.set_string(current_x + 4, current_y, utilities.format_padded_id(document_id + number + 1), ZXScreen.to_attribute(ink=ZXScreen.CYAN))

                    current_y += 1
                    if current_y > (start_y + 8):
                        current_y = start_y
                        current_x += 10
                page.save()

            # Add reference to created token page
            ZXPage_Token(parent=document, zxtoken_path=page.document_path.name, export_format='TKN')

            # Save and export
            document.save()
            document.export(self.output_path, self.registry)

    def __get_document(self, document_id, description, abbreviation, target_directory):
        return ZXDocument(
            document_path=target_directory / "{}{}".format(
                utilities.format_padded_id(document_id),
                ZXDocument.EXTENSION_DOCUMENT
            ),
            document_id=document_id,
            description=description,
            abbreviation=abbreviation
        )

    def __get_page(self, document_id, page_id, target_directory) -> ZXToken:
        return self.__load_frame(
            'frame_blue',
            self.__page_path(document_id, page_id, target_directory)
        )

    def __get_titlepage(self, document_id, page_id, page_title, target_directory) -> ZXToken:
        page_title = page_title[0:(ZXScreen.SCREEN_WIDTH_CHARS-2)]
        zx_token = self.__load_frame(
            'frame_blue_title',
            self.__page_path(document_id, page_id, target_directory)
        )
        zx_token.set_string(self.__centered_position(page_title), 2, page_title)
        return zx_token

    def __centered_position(self, title):
        return (ZXScreen.SCREEN_WIDTH_CHARS - len(title)) // 2

    def __create_path(self, document_id, path_hint):
        directory = self.pages_path / utilities.suggest_document_name(document_id, path_hint)
        directory.mkdir(exist_ok=True)
        return directory

    def __page_path(self, document_id, page_id, target_directory):
        return target_directory / "{}.{}{}".format(
            utilities.format_padded_id(document_id),
            utilities.format_padded_id(page_id, width=2),
            ZXToken.FILE_EXTENSION
        )

    def __load_frame(self, frame_name, page_path: Path):
        zx_token = ZXToken.from_file(Path(self.pages_path) / 'assets' / f'{frame_name}{ZXToken.FILE_EXTENSION}')
        zx_token.set_document(page_path)
        return zx_token

TOCGenerator(
    registry_path='pages/telezx.registry', 
    pages_path=Path('.') / 'pages',
    output_path=Path('.') / 'output'
).create_toc()