import yaml
from pathlib import Path
from .utilities import update_tree, format_padded_id
from .zx_registry import ZXRegistry

class ZXDocument:
    FILE_EXTENSION = '.idx'

    def __init__(self, document_path, document_id=0, description=None, abbreviation=None, link_a=None, link_a_txt=None, link_b=None, link_b_txt=None, link_c=None, link_c_txt=None):
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

    def export(self, output_directory: Path, registry: ZXRegistry=None):
        print('export', self.get_output_path(output_directory))
        for page_idx, page in enumerate(self.pages):
            page.export(self.get_output_base(output_directory), page_idx)
        if registry:
            registry.sync_record(self.document_id, self.description, self.abbreviation)

    def get_output_path(self, output_directory: Path):
        return self.get_output_base(output_directory).with_suffix(self.FILE_EXTENSION)

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
    def __init__(self, parent: ZXDocument):
        self.parent = parent
        self.parent.add_page(self)

    def export(self, output_base, page_idx):
        raise NotImplementedError()

    def to_dict(self, page_idx) -> dict:
        return { self.__class__.__name__: {} }

    @classmethod
    def from_dict(cls, parent, data) -> ZXPage:
        for subclass in cls.__subclasses__():
            if subclass.__name__ in data:
                return subclass.from_dataset(parent, data)
        raise ValueError("failed to find suitable implementation of page type")


class ZXPageSCR(ZXPage):
    SCR_EXTENSION = '.scr'
    ABOUT_EXTENSION = '.about'

    def __init__(self, parent: ZXDocument, scr_path, scr_about):
        super().__init__(parent)
        self.scr_path = scr_path
        self.parent.check_file_exists(self.scr_path)
        self.scr_about = scr_about

    def export(self, output_base, page_idx):
        # looses page_idx as with_suffix overrides it :-()
        print('export', self.get_output_base(output_base, page_idx).with_suffix(self.SCR_EXTENSION))
        print('export', self.get_output_base(output_base, page_idx).with_suffix(self.ABOUT_EXTENSION))

    def get_output_base(self, output_base: Path, page_idx):
        return output_base.with_suffix('.' + format_padded_id(page_idx, width=2)) #.with_suffix(self.FILE_EXTENSION)

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
        return cls(
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
