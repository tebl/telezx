from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from .repository_helper import RepositoryHelper
from .. import ZXScreen, ZXDocument, DocumentIdentifierIterator, ZXToken, ZXPage_Token, utilities

class TOCHelper(RepositoryHelper):
    TOC_TITLE = 'Table of contents'
    TOC_ABBREVIATION = 'TOC'

    enable_preview = True

    def __init__(self, repository: Path):
        super().__init__(repository)
        self.create_path_structure()
        self.open_registry()

    def create_toc(self, document_id_start=ZXDocument.DOCUMENT_ID_TOC):
        self.__create_toc_index(document_id_start)

        registry_toc = self.registry.generate_TOC_AZ()
        address = self.__get_address_iterator(document_id_start, ZXDocument.DOCUMENT_ID_MAX)
        for letter in self.registry.LETTERS_AZ:
            document_id = next(address)
            self.registry.set_ignored(document_id, True)
            target_directory = self.__create_path(document_id, f'TOC-{letter}')

            with self.__get_document(document_id, f'{self.TOC_TITLE} ({letter})', f'TOC-{letter}', target_directory) as document:
                document.link_a = document_id_start
                items = registry_toc[letter] if letter in registry_toc else []
                current_y = 4
                page_id = 0

                current_page = self.__get_titlepage(document, f'{self.TOC_TITLE} ({letter})')

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
                                current_page = self.__get_page(document)
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
                ZXPage_Token(parent=document, zxtoken_path=current_page.document_path, export_format='TKN')

                document.save()
                document.export(self.out_path, self.registry, sync_registry=False)

        self.registry.save()
        self.logger.info(f'Registry saved')

    def __get_address_iterator(self, start: int, maximum: int):
        return DocumentIdentifierIterator(start, maximum)

    def __pad_entry(self, string, max_length = 25):
        string = string[0:max_length]
        if len(string) < (max_length - 1):
            return (string + ' ').ljust(max_length, '.')
        return string

    def __create_toc_index(self, document_id_start: int):
        target_directory = self.__create_path(document_id_start, 'TOC-Index')
        self.logger.info('Creating', target_directory.name)

        address = self.__get_address_iterator(document_id_start, ZXDocument.DOCUMENT_ID_MAX)
        with self.__get_document(document_id_start, self.TOC_TITLE, self.TOC_ABBREVIATION, target_directory) as document:
            document.link_a = ZXDocument.DOCUMENT_ID_HOME

            with self.__get_titlepage(document, self.TOC_TITLE) as page:
                page.set_string(1, 5, 'The corresponding pages have  ')
                page.set_string(1, 6, 'been generated based on TeleZX')
                page.set_string(1, 7, 'registry.')

                start_y = 10
                current_x = 2
                current_y = start_y
                for number, letter in enumerate(self.registry.LETTERS_AZ):
                    document_id = next(address)
                    page.set_string(current_x, current_y, f'[{letter}]', ZXScreen.to_attribute(ink=ZXScreen.GREEN))
                    page.set_string(current_x + 4, current_y, utilities.format_padded_id(document_id), ZXScreen.to_attribute(ink=ZXScreen.CYAN))

                    current_y += 1
                    if current_y > (start_y + 8):
                        current_y = start_y
                        current_x += 10
                page.save()

            # Add reference to created token page
            ZXPage_Token(parent=document, zxtoken_path=page.document_path, export_format='TKN')

            # Save and export
            document.save()
            document.export(self.out_path, self.registry, sync_registry=True)

    def __get_document(self, document_id: int, description, abbreviation, target_directory: Path):
        return ZXDocument(
            self.repository,
            document_path=target_directory / ZXDocument.FILENAME_DEFAULT,
            document_id=document_id,
            description=description,
            abbreviation=abbreviation
        )

    def __get_page(self, document: ZXDocument) -> ZXToken:
        return self.from_frame(
            self.resolve_frame_path('frame_default'),
            self.__page_path(document)
        )

    def __get_titlepage(self, document: ZXDocument, page_title) -> ZXToken:
        page_title = page_title[0:(ZXScreen.SCREEN_WIDTH_CHARS-2)]
        zx_token = self.from_frame(
            self.resolve_frame_path('frame_default_title'),
            self.__page_path(document)
        )
        zx_token.set_string(self.__centered_position(page_title), 2, page_title)
        return zx_token

    def __centered_position(self, title):
        return (ZXScreen.SCREEN_WIDTH_CHARS - len(title)) // 2

    def __create_path(self, document_id: int, path_hint: str) -> Path:
        directory = self.src_path / utilities.suggest_document_directory(document_id, path_hint)
        if not directory.is_dir():
            directory.mkdir()
        else:
            self.__clear_directory(directory)
        return directory

    def __clear_directory(self, directory: Path, indent: int=0):
        self.logger.debug('Clearing existing assets', indent=indent)
        for page_id in range(ZXDocument.ASSET_ID_MIN, ZXDocument.ASSET_ID_MAX + 1):
            asset_path = Path(directory) / utilities.suggest_asset_path(page_id, ZXToken.FILE_EXTENSION)
            if asset_path.is_file():
                self.logger.debug('Removing', asset_path, indent=(indent+1))
                asset_path.unlink()
            else:
                return

    def __page_path(self, document: ZXDocument, path_hint: str=None) -> Path:
        return self.generate_asset_path(document, document.get_next_asset_id(), ZXToken.FILE_EXTENSION, path_hint)