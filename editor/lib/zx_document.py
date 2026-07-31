import yaml
from pathlib import Path
from .utilities import update_tree, format_padded_id, QuotedYAML
from .zx_registry import ZXRegistry
from .zx_logger import ZXLogger
from .zx_token import ZXToken, ZXScreenIterator, ZXScreen

class ZXDocument:
    EXTENSION_INDEX = '.idx'
    EXTENSION_TOKEN = '.tkn'
    EXTENSION_SCR = '.scr'
    EXTENSION_ABOUT = '.about'

    def __init__(self, document_path, document_id=0, description=None, abbreviation=None, link_a=None, link_a_txt=None, link_b=None, link_b_txt=None, link_c=None, link_c_txt=None):
        self.logger = ZXLogger.get_instance()
        self.document_path = Path(document_path)
        self.working_path = self.document_path.parent.resolve()
        self.document_id = document_id
        self.description = description
        self.abbreviation = abbreviation
        self.link_a = link_a
        self.link_a_txt = link_a_txt
        self.link_b = link_b
        self.link_b_txt = link_b_txt
        self.link_c = link_c
        self.link_c_txt = link_c_txt
        self.pages = []

    def __iter__(self):
        return iter(self.pages)

    def add_page(self, page) -> int:
        if not isinstance(page, ZXPage):
            raise TypeError("{} does not appear to a page-type object".format(page))
        page_id = len(self.pages)
        self.pages.append(page)
        return page_id

    def check_file_exists(self, path, raise_exception=True) -> bool:
        if not self.get_asset_path(path).is_file():
            if raise_exception:
                raise FileNotFoundError(path)
            return False
        return True

    def clean(self, output_directory: Path, indent=0) -> True:
        path = self.get_output_base(output_directory)
        self.logger.info('cleaning', path, 'assets', indent=indent)
        for asset in self.__asset_list(directory=path.parent, basename=path.name):
            self.logger.debug('delete', asset, indent=(indent+1))
            asset.unlink()
        return True

    def __asset_list(self, directory: Path, basename):
        results = []
        results.extend(directory.glob(f'{basename}{self.EXTENSION_INDEX}'))
        results.extend(directory.glob(f'{basename}.*{self.EXTENSION_TOKEN}'))
        results.extend(directory.glob(f'{basename}.*{self.EXTENSION_SCR}'))
        results.extend(directory.glob(f'{basename}.*{self.EXTENSION_ABOUT}'))
        return sorted(
            results,
            key=lambda path: path.name
        )

    def export(self, output_directory: Path, registry: ZXRegistry, log_indent=0):
        '''
        Create index file from registered pages, using the data structure as
        listed below. Note that with room for 99 subpages we should leave
        roughly a space for 512 bytes in total to account for any future
        additions. Strings are terminated with an added \0.

        Index structure:
            ADDR Field              Bytes
            0x00 IDX                3
            0x03 Page count (hex)   2
            0x05 Link A             4
            0x09 Link A TXT (8+\0)  9
            0x12 Link B             4
            0x16 Link B TXT (8+\0)  9
            0x1f Link C             4
            0x23 Link C TXT (8+\0)  9
            0x2c <unused>           20
            0x40 Page 0 type (hex)  2
            0x42 Page 0 parameter   2
        '''
        self.logger.info('export', self.document_path, '->', self.get_output_path(output_directory), indent=log_indent)
        self.clean(output_directory, indent=(log_indent+1))
        with open(self.get_output_path(output_directory), 'w') as file:
            file.write('IDX')
            self.__export_digits(file, len(self.pages))
            self.__export_link(file, self.link_a, self.link_a_txt, registry)
            self.__export_link(file, self.link_b, self.link_b_txt, registry)
            self.__export_link(file, self.link_c, self.link_c_txt, registry)

            # Align byte boundary so that records start at position 64 (0x40),
            # giving us around 20 bytes of overhead that we can fill if we find
            # a need for them.
            file.write('\0'*(64 - file.tell()))

            page: ZXPage
            for page_idx, page in enumerate(self.pages):
                type, parameter = page.export(self.get_output_base(output_directory), page_idx, log_indent=(log_indent+1))
                self.__export_hex(file, type)
                self.__export_hex(file, parameter)

        registry.sync_record(self.document_id, self.description, self.abbreviation)

    def __export_record(self, file, value, pad_to_size, pad_chr):
        file.write(self.__pad_record(value, pad_to_size, pad_chr))

    def __export_digits(self, file, value):
        file.write(f'{value:02d}')

    def __export_hex(self, file, value):
        file.write(f'{value:02X}')

    def __export_link(self, file, link, link_txt, registry: ZXRegistry):
        if link is not None:
            file.write(f'{link:04d}')
            if link_txt is None:
                link_txt = registry.lookup_abbreviation(link)
            self.__export_record(file, link_txt, (ZXRegistry.ABBREVIATION_CHARS + 1), '\0')
        else:
            file.write('0000')
            file.write('\0'*(ZXRegistry.ABBREVIATION_CHARS + 1))

    def __pad_record(self, value, pad_to_size, pad_chr):
        return value.ljust(pad_to_size, pad_chr)[0:(pad_to_size + 1)]

    def get_output_path(self, output_directory: Path):
        return self.get_output_base(output_directory).with_suffix(self.EXTENSION_INDEX)

    def get_output_base(self, output_directory: Path):
        if isinstance(output_directory, str):
            output_directory = Path(output_directory)
        return output_directory / format_padded_id(self.document_id)

    def get_asset_path(self, path: Path) -> Path:
        return self.working_path.joinpath(path).resolve()

    def get_relative_path(self, path: Path) -> Path:
        return Path(path).relative_to(self.working_path, walk_up=True)

    def save(self) -> bool:
        with open(self.document_path, 'w') as file:
            yaml.dump(
                self.to_dict(), 
                file, 
                indent=4, 
                default_flow_style=False, 
                sort_keys=True
            )
        return True

    def to_dict(self) -> dict:
        result = self.__yaml_defaults()
        root = result[self.__class__.__name__]
        root['document_id'] = self.document_id
        root['description'] = self.description
        root['abbreviation'] = self.abbreviation
        root['link_a'] = self.link_a
        root['link_a_txt'] = self.link_a_txt
        root['link_b'] = self.link_b
        root['link_b_txt'] = self.link_b_txt
        root['link_c'] = self.link_c
        root['link_c_txt'] = self.link_c_txt
        for page_idx, page in enumerate(self.pages):
            root['pages'].append(page.to_dict(page_idx))
        return result

    @classmethod
    def from_dict(cls, document_path, data) -> ZXDocument:
        if not len(data) == 1:
            raise ValueError("expected one key specifying datatype, found {}".format(len(data)))
        if cls.__name__ not in data:
            raise ValueError("does not look like a {}-file".format(cls.__name__))
        root = data[cls.__name__]

        zx_document = ZXDocument(
            document_path, 
            document_id=root['document_id'],
            description=root['description'],
            abbreviation=root['abbreviation'],
            link_a=root['link_a'],
            link_a_txt=root['link_a_txt'],
            link_b=root['link_b'],
            link_b_txt=root['link_b_txt'],
            link_c=root['link_c'],
            link_c_txt=root['link_c_txt']
        )
        for page_data in root['pages']:
            ZXPage.from_dict(zx_document, page_data)

        return zx_document

    @classmethod
    def from_file(cls, document_path) -> ZXDocument:
        data = cls.__yaml_defaults()
        data = update_tree(data, cls.__get_yaml(document_path))
        return cls.from_dict(document_path, data)

    @classmethod
    def __yaml_defaults(cls) -> dict:
        return {
            cls.__name__: {
                'document_id':  0,
                'description':  None,   # Registry description (21 characters)
                'abbreviation': None,   # Link text (8 characters)
                'link_a':       None,   # Link A
                'link_a_txt':   None,   #  - Description (8 characters)
                'link_b':       None,   # Link B
                'link_b_txt':   None,   #  - Description (8 characters)
                'link_c':       None,   # Link C
                'link_c_txt':   None,   #  - Description (8 characters)
                'pages': []
            }
        }

    @classmethod
    def __get_yaml(cls, yaml_path) -> dict:
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            if cls.__name__ not in data:
                raise ValueError("does not look like a {}-file".format(cls.__name__))
            return data

class ZXPage:
    INDEX_TYPE_SCR = 0x55
    INDEX_TYPE_TKN = 0xAA
    BLANK_PARAMETER = 0x00

    logger: ZXLogger
    parent: ZXDocument

    def __init__(self, parent: ZXDocument):
        self.logger = ZXLogger.get_instance()
        self.parent = parent
        self.parent.add_page(self)

    def __str__(self):
        return self.__class__.__name__

    def export(self, output_base, page_idx, log_indent=0):
        raise NotImplementedError()

    def get_export_path(self, output_base: Path, page_idx: int, file_extension):
        return output_base.with_suffix('.{}{}'.format(format_padded_id(page_idx, width=2), file_extension))

    def to_dict(self, page_idx) -> dict:
        return { self.__class__.__name__: {} }

    @classmethod
    def from_dict(cls, parent, data) -> ZXPage:
        for subclass in cls.__subclasses__():
            if subclass.__name__ in data:
                return subclass.from_dataset(parent, data)
        raise ValueError("failed to find suitable implementation of page type")


class ZXPage_SCR(ZXPage):
    parent: ZXDocument
    scr_path: Path
    scr_about: dict

    def __init__(self, parent: ZXDocument, scr_path: Path, scr_about):
        super().__init__(parent)
        self.scr_path = scr_path
        self.parent.check_file_exists(self.scr_path)
        self.scr_about = scr_about

    def __str__(self):
        return f'{self.__class__.__name__} (input={self.scr_path.name})'

    def export(self, output_base, page_idx, log_indent=0) -> tuple[int, int]:
        self.logger.info(format_padded_id(page_idx, width=2), str(self), indent=log_indent)
        self.__copy_scr(self.get_export_path(output_base, page_idx, ZXDocument.EXTENSION_SCR), log_indent=log_indent+1)
        self.__export_about(self.get_export_path(output_base, page_idx, ZXDocument.EXTENSION_SCR + ZXDocument.EXTENSION_ABOUT), log_indent=log_indent+1)
        return (self.INDEX_TYPE_SCR, self.BLANK_PARAMETER)

    def __copy_scr(self, target_path: Path, log_indent=0):
        self.logger.debug('copy', self.scr_path, '->', target_path, indent=log_indent)
        self.scr_path.copy(target=target_path)

    def __export_about(self, file_path: Path, log_indent=0):
        self.logger.debug('create', file_path, indent=log_indent)
        with open(file_path, 'w') as file:
            self.__export_about_field(file, 'title')
            self.__export_about_field(file, 'author')
            self.__export_about_field(file, 'source')
            self.__export_about_field(file, 'license')

    def __export_about_field(self, file, key: str):
        title = f'{key.capitalize()}:'
        file.write(title.ljust(10))
        file.write(self.scr_about[key])
        file.write('\n')

    def to_dict(self, page_idx):
        result = super().to_dict(page_idx)
        root = result[self.__class__.__name__]
        root['scr_path'] = str(self.parent.get_relative_path(self.scr_path))
        root['scr_about'] = self.scr_about
        return result

    @classmethod
    def from_dataset(cls, parent: ZXDocument, data):
        '''
        Reconstructs object from a dictionary structure. Could quite possibly
        have named it from_dict as it serves the same structure, but didn't
        want to have it recursively call itself when I forgot to add the
        function.
        '''
        result = cls.__yaml_defaults()
        result = update_tree(result, data)
        root = result[cls.__name__]
        return ZXPage_SCR(
            parent, 
            parent.get_asset_path(root['scr_path']), 
            root['scr_about'])

    @classmethod
    def __yaml_defaults(cls) -> dict:
        return {
            cls.__name__: {
                'scr_path': None,
                'scr_about': {
                    'title': '',
                    'author': '',
                    'source': '',
                    'license': ''
                }
            }
        }


class ZXPage_TeleZX(ZXPage):
    parent: ZXDocument
    telezx_path: Path
    export_as: str

    def __init__(self, parent: ZXDocument, telezx_path: Path, export_as):
        super().__init__(parent)
        self.telezx_path = telezx_path
        self.parent.check_file_exists(self.telezx_path)
        self.export_as = export_as
        if self.export_as not in [ 'SCR', 'TKN' ]:
            raise ValueError(f"{self.export_as} not recognized")

    def __str__(self):
        return f'{self.__class__.__name__} (input={self.telezx_path.name}, export_as={self.export_as})'

    def export(self, output_base, page_idx, log_indent=0):
        self.logger.info(format_padded_id(page_idx, width=2), str(self), indent=log_indent)
        zx_token = ZXToken.from_file(self.telezx_path)
        match self.export_as:
            case 'TKN':
                target_path = self.get_export_path(output_base, page_idx, ZXDocument.EXTENSION_TOKEN)
                self.logger.debug('create', self.telezx_path, '->', target_path, indent=(log_indent+1))
                zx_token.export_to_specscii(target_path)
                return (self.INDEX_TYPE_TKN, zx_token.current_attribute)
            case _:
                target_path = self.get_export_path(output_base, page_idx, ZXDocument.EXTENSION_SCR)
                self.logger.debug('create', self.telezx_path, '->', target_path, indent=(log_indent+1))
                zx_token.export_to_scr(target_path)
                return (self.INDEX_TYPE_SCR, self.BLANK_PARAMETER)

    def to_dict(self, page_idx):
        result = super().to_dict(page_idx)
        root = result[self.__class__.__name__]
        root['telezx_path'] = str(self.parent.get_relative_path(self.telezx_path))
        root['export_as'] = self.export_as
        return result

    @classmethod
    def from_dataset(cls, parent: ZXDocument, data):
        '''
        Reconstructs object from a dictionary structure. Could quite possibly
        have named it from_dict as it serves the same structure, but didn't
        want to have it recursively call itself when I forgot to add the
        function.
        '''
        result = cls.__yaml_defaults()
        result = update_tree(result, data)
        root = result[cls.__name__]
        return ZXPage_TeleZX(
            parent, 
            parent.get_asset_path(root['telezx_path']),
            root['export_as'])

    @classmethod
    def __yaml_defaults(cls) -> dict:
        return {
            cls.__name__: {
                'telezx_path': None,
                'export_as': 'SCR'
            }
        }

class ZXPage_ClearText(ZXPage):
    parent: ZXDocument
    frame_path: Path
    lines: list[str]

    def __init__(self, parent: ZXDocument, frame_path: Path, lines):
        super().__init__(parent)
        self.frame_path = frame_path
        if self.frame_path:
            self.parent.check_file_exists(self.frame_path)
        self.lines = lines

    def __str__(self):
        return f'{self.__class__.__name__} (frame={self.frame_path.name if self.frame_path else None})'

    def export(self, output_base, page_idx, log_indent=0):
        self.logger.info(format_padded_id(page_idx, width=2), str(self), indent=log_indent)
        target_path = self.get_export_path(output_base, page_idx, ZXDocument.EXTENSION_TOKEN)
        self.logger.debug('create', target_path, indent=(log_indent+1))

        zx_token = self.__get_zx_token()
        for char_y, line in enumerate(self.lines):
            char_x = len(line) - len(line.lstrip())
            if char_x == ZXScreen.SCREEN_WIDTH_CHARS:
                continue
            zx_token.set_string(char_x, char_y, line.strip())
        zx_token.export_to_specscii(target_path)
        return (self.INDEX_TYPE_TKN, zx_token.current_attribute)

    def __get_zx_token(self) -> ZXToken:
        if self.frame_path:
            return ZXToken.from_file(self.frame_path)
        return ZXToken()

    def to_dict(self, page_idx):
        result = super().to_dict(page_idx)
        root = result[self.__class__.__name__]
        root['frame_path'] = str(self.parent.get_relative_path(self.frame_path)) if self.frame_path else None
        root['lines'] = self.__get_lines()
        return result

    def __get_lines(self):
        '''
        Ensures that we have lines of characters corresponding to a full ZX
        Spectrum screen. Missing blank lines will be added, any overflow will
        be violently thrown into logger and promptly forgotten about.
        '''
        # Add missing lines
        if len(self.lines) < ZXScreen.SCREEN_HEIGHT_CHARS:
            lines_added = ZXScreen.SCREEN_HEIGHT_CHARS - len(self.lines)
            if lines_added:
                for n in range(lines_added):
                    self.lines.append(' ' * ZXScreen.SCREEN_WIDTH_CHARS)
                self.logger.warning(f'{lines_added} blank lines added to', str(self))

        # Chop off any extras
        if len(self.lines) > ZXScreen.SCREEN_HEIGHT_CHARS:
            for line in self.lines[ZXScreen.SCREEN_HEIGHT_CHARS:]:
                self.logger.warning('Line', f'"{line}"', 'removed from', str(self), 'due to length')
        self.lines = self.lines[0:ZXScreen.SCREEN_HEIGHT_CHARS]

        return [ self.__get_quoted_line(line) for line in self.lines ]

    def __get_quoted_line(self, original_line):
        # Chop off longer strings, pad out with spaces if characters missing
        result = original_line[0:ZXScreen.SCREEN_WIDTH_CHARS]
        result = result.ljust(ZXScreen.SCREEN_WIDTH_CHARS, ' ')
        if not original_line == result:
            self.logger.warning('Line', f'"{original_line}"', 'changed to', f'"{result}"')
        return QuotedYAML(result)

    @classmethod
    def from_dataset(cls, parent: ZXDocument, data):
        '''
        Reconstructs object from a dictionary structure. Could quite possibly
        have named it from_dict as it serves the same structure, but didn't
        want to have it recursively call itself when I forgot to add the
        function.
        '''
        result = cls.__yaml_defaults()
        result = update_tree(result, data)
        root = result[cls.__name__]
        return ZXPage_ClearText(
            parent, 
            parent.get_asset_path(root['frame_path']) if root['frame_path'] else None,
            root['lines'])

    @classmethod
    def __yaml_defaults(cls) -> dict:
        return {
            cls.__name__: {
                'frame_path': None,
                'lines': cls.blank_lines()
            }
        }

    @classmethod
    def blank_lines(cls):
        return [ QuotedYAML(' ' * ZXScreen.SCREEN_WIDTH_CHARS) ] * ZXScreen.SCREEN_HEIGHT_CHARS