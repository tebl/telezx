from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .. import ZXScreen, ZXDocument, ZXToken, ZXFrame, ZXPage_Overlay, ZXPage_Token, ZXPage_ClearText, ZXRegistry, ZXLogger, utilities

class TOCGenerator:
    registry_path: Path
    documents_path: Path
    output_path: Path

    TOC_TITLE = 'Table of contents'
    TOC_ABBREVIATION = 'TOC'

    enable_preview = True

    def __init__(self, repository: Path):
        self.logger = ZXLogger.get_instance()
        self.repository = Path(repository)
        self.documents_path = self.repository / 'src'
        self.documents_path.mkdir(exist_ok=True)
        self.output_path = self.repository / 'out'
        self.output_path.mkdir(exist_ok=True)

        self.registry_path = self.repository / 'src' / f'telezx{ZXRegistry.FILE_EXTENSION}'
        self.registry = ZXRegistry.from_file(self.registry_path, allow_create=True)

    def create_toc(self, document_id_start = 9900):
        document_id = document_id_start
        self.__create_toc_index(document_id)

        registry_toc = self.registry.generate_TOC_AZ()
        for letter in self.registry.LETTERS_AZ:
            document_id += 1
            self.registry.set_ignored(document_id, True)
            target_directory = self.__create_path(document_id, f'TOC-{letter}')

            with self.__get_document(document_id, f'{self.TOC_TITLE} ({letter})', f'TOC-{letter}', target_directory) as document:
                document.link_a = document_id_start
                items = registry_toc[letter] if letter in registry_toc else []
                current_y = 4
                page_id = 0

                current_page = self.__get_titlepage(document_id, page_id, f'{self.TOC_TITLE} ({letter})', target_directory)

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
                document.export(self.output_path, self.registry, sync_registry=False)

        self.registry.save()
        print('Registry saved.')

    def __pad_entry(self, string, max_length = 25):
        string = string[0:max_length]
        if len(string) < (max_length - 1):
            return (string + ' ').ljust(max_length, '.')
        return string

    def __create_toc_index(self, document_id):
        target_directory = self.__create_path(document_id, 'TOC-Index')

        with self.__get_document(document_id, self.TOC_TITLE, self.TOC_ABBREVIATION, target_directory) as document:
            document.link_a = 1000

            with self.__get_titlepage(document_id, 0, self.TOC_TITLE, target_directory) as page:
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
            document.export(self.output_path, self.registry, sync_registry=True)

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
            'frame_default',
            self.__page_path(document_id, page_id, target_directory)
        )

    def __get_titlepage(self, document_id, page_id, page_title, target_directory) -> ZXToken:
        page_title = page_title[0:(ZXScreen.SCREEN_WIDTH_CHARS-2)]
        zx_token = self.__load_frame(
            'frame_default_title',
            self.__page_path(document_id, page_id, target_directory)
        )
        zx_token.set_string(self.__centered_position(page_title), 2, page_title)
        return zx_token

    def __centered_position(self, title):
        return (ZXScreen.SCREEN_WIDTH_CHARS - len(title)) // 2

    def __create_path(self, document_id, path_hint):
        directory = self.documents_path / utilities.suggest_document_name(document_id, path_hint)
        directory.mkdir(exist_ok=True)
        return directory

    def __page_path(self, document_id, page_id, target_directory):
        return target_directory / "{}.{}{}".format(
            utilities.format_padded_id(document_id),
            utilities.format_padded_id(page_id, width=2),
            ZXToken.FILE_EXTENSION
        )

    def __load_frame(self, frame_name, page_path: Path):
        frame_path = Path(self.documents_path) / 'assets' / f'{frame_name}{ZXToken.FILE_EXTENSION}'
        if not frame_path.is_file():
            frame_path = Path('.') / 'assets' / f'{frame_name}{ZXToken.FILE_EXTENSION}'
        zx_token = ZXToken.from_file(frame_path)
        zx_token.set_document(page_path)
        return zx_token
