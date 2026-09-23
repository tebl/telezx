from pathlib import Path
from .repository_helper import RepositoryHelper
from .. import ZXScreen, ZXDocument, DocumentIdentifierIterator, ZXToken, ZXPage_Token, utilities, ZXRegistry, ZXRegistryEntry, ZXRegistryTag

class RegistryHelper(RepositoryHelper):
    TOC_TITLE = 'Table of contents'
    TOC_ABBREVIATION = 'TOC'
    COLOUR_CATEGORY = ZXScreen.to_attribute(ink=ZXScreen.WHITE, paper=ZXScreen.BLUE)
    COLOUR_DESCRIPTION = ZXScreen.to_attribute(ink=ZXScreen.BLUE, paper=ZXScreen.WHITE)
    COLOUR_REFERENCE = ZXScreen.to_attribute(ink=ZXScreen.MAGENTA, paper=ZXScreen.WHITE)

    enable_preview = True

    def __init__(self, repository: Path):
        super().__init__(repository)
        self.create_path_structure()
        self.open_registry()

    def create_tag(self, name: str):
        if self.registry.lookup_tag(name) is not None:
            raise FileExistsError(f'TAG {name} already exists')
        return self.registry.sync_tag(name)

    def open_tag(self, name: str):
        tag = self.registry.lookup_tag(name)
        if not tag:
            raise FileNotFoundError(f'TAG {name} does not exist')
        return tag

    def delete_tag(self, name: str):
        self.registry.delete_tag(name)

    def create_toc_page(self, document_id_start=ZXDocument.DOCUMENT_ID_TOC):
        self.__create_toc_index(document_id_start)

        registry_toc = self.registry.generate_TOC_AZ()
        address = self.__get_address_iterator(document_id_start, ZXDocument.DOCUMENT_ID_MAX)
        for letter in self.registry.LETTERS_AZ:
            document_id = next(address)
            self.registry.set_ignored(document_id, True)
            target_directory = self._create_document_path(document_id, f'TOC-{letter}')

            with self._get_document(document_id, f'{self.TOC_TITLE} ({letter})', f'TOC-{letter}', target_directory) as document:
                document.link_a = document_id_start
                items = registry_toc[letter] if letter in registry_toc else []
                current_y = 4
                page_id = 0

                current_page = self._get_titlepage(document, f'{self.TOC_TITLE} ({letter})')

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
                                current_page = self._get_page(document)
                            else:
                                self.logger.error(f'Item count for letter {letter} was truncated')
                                break
                        else:
                            current_y += 1
                    else:
                        first_item = False

                    current_page.set_string(1, current_y, self.__pad_entry(description))
                    current_page.set_string(27, current_y, utilities.format_padded_id(link_id), char_attribute=self.COLOUR_REFERENCE)

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
        target_directory = self._create_document_path(document_id_start, 'TOC-Index')
        self.logger.info('Creating', target_directory.name)

        address = self.__get_address_iterator(document_id_start, ZXDocument.DOCUMENT_ID_MAX)
        with self._get_document(document_id_start, self.TOC_TITLE, self.TOC_ABBREVIATION, target_directory) as document:
            document.link_a = ZXDocument.DOCUMENT_ID_HOME

            with self._get_titlepage(document, self.TOC_TITLE) as page:
                page.set_string(1, 5, 'The corresponding pages have  ')
                page.set_string(1, 6, 'been generated based on TeleZX')
                page.set_string(1, 7, 'registry.')

                start_y = 10
                current_x = 2
                current_y = start_y
                for number, letter in enumerate(self.registry.LETTERS_AZ):
                    document_id = next(address)
                    page.set_string(current_x, current_y, f'[{letter}]', self.COLOUR_DESCRIPTION)
                    page.set_string(current_x + 4, current_y, utilities.format_padded_id(document_id), self.COLOUR_REFERENCE)

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

    def create_tag_page(self, tag_name, log_indent: int=0):
        tag: ZXRegistryTag = self.registry.lookup_tag(tag_name)
        if not tag:
            raise ValueError(f'No such tag: {tag_name}')
        self.logger.info('Creating', tag.export_description, 'on', utilities.format_padded_id(tag.export_id))
        entries = self.registry.generate_tag_AZ(tag_name)

        target_directory = self._create_document_path(tag.export_id, path_hint=f'TAG {tag_name}', log_indent=(log_indent+1))
        with self._get_document(tag.export_id, tag.export_description, tag.export_abbreviation, target_directory) as document:
            document.tags = tag.get_export_tags()
            if tag.export_link_a is not None:
                document.link_a = tag.export_link_a
                document.link_a_txt = tag.export_link_a_txt
            if tag.export_link_b is not None:
                document.link_b = tag.export_link_b
                document.link_b_txt = tag.export_link_b_txt
            if tag.export_link_c is not None:
                document.link_c = tag.export_link_c
                document.link_c_txt = tag.export_link_c_txt
            document.include_toc = tag.export_include_toc

            current_y = 3
            page_id = 0

            current_page = self._get_titlepage(document, tag.export_description)
            current_letter = None
            for letter in self.registry.LETTERS_AZ:
                items = entries[letter] if letter in entries else []
                if not items:
                    continue

                for (description, link_id) in items:
                    if current_y >= 20:
                        if page_id < 99:
                            current_page.save()
                            ZXPage_Token(parent=document, zxtoken_path=current_page.document_path.name, export_format='TKN')

                            page_id += 1
                            current_page = self._get_page(document)
                        else:
                            self.logger.error(f'Item count for letter {letter} was truncated')
                            break
                        current_y = 3
                    else:
                        current_y += 1

                    if not current_letter == letter:
                        current_letter = letter
                        current_page.set_string(1, current_y, f' {letter} ', char_attribute=self.COLOUR_CATEGORY)

                    current_page.set_string(5, current_y, self.__pad_entry(description, max_length=21))
                    current_page.set_string(27, current_y, utilities.format_padded_id(link_id), char_attribute=self.COLOUR_REFERENCE)

            current_page.save()
            ZXPage_Token(parent=document, zxtoken_path=current_page.document_path, export_format='TKN')

            document.save(log_indent=(log_indent+1))
            document.export(self.out_path, self.registry, sync_registry=True, log_indent=(log_indent+1))

        self.registry.save()
        self.logger.info(f'Registry saved', indent=(log_indent+1))

    def get_tags(self):
        return self.registry.get_tags()

    def get_exportable_tags(self):
        '''
        Get a list of exportable tags, the contents of which should be sorted
        so that created subcategories will get added to main categories.
        '''
        return self.registry.get_tag_dependency_tree()

    def set_ignored(self, document_id: int, is_ignored: bool):
        self.registry.set_ignored(document_id, is_ignored)

    def save(self):
        self.registry.save()