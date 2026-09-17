import string, yaml, typing
import yaml
from pathlib import Path
from .utilities import format_padded_id, update_tree, HexYAML, QuotedYAML
from .zx_logger import ZXLogger

class ZXRegistry:
    FILE_EXTENSION = '.registry'
    ABBREVIATION_CHARS = 8
    LETTERS_AZ = f'#{string.ascii_uppercase}'
    entries: dict[str, ZXRegistryEntry]
    tags: dict[str, ZXRegistryTag]
    ignored: list[int]

    def __init__(self, registry_path, tags, ignored_list):
        self.logger = ZXLogger.get_instance()
        self.registry_path = Path(registry_path)
        self.entries = {}
        self.tags = tags
        self.ignored = ignored_list

    def clear(self):
        self.entries.clear()

    def generate_TOC_AZ(self):
        results = {}
        for char in self.LETTERS_AZ:
            results[char] = []
        for (document_id, data) in self.__sorted_description(self.entries):
            if not data.description:
                continue
            letter = data.description[0].upper() if data.description[0].isalpha() else '#'
            results[letter].append([data.description, document_id])
        return results

    def generate_tag_AZ(self, tag_name):
        results = {}
        for char in self.LETTERS_AZ:
            results[char] = []
        tag = self.lookup_tag(tag_name)
        if tag:
            entry: ZXRegistryEntry
            for entry in sorted(tag.entries, key=lambda x: x.description):
                if not entry.description:
                    continue
                letter = entry.description[0].upper() if entry.description[0].isalpha() else '#'
                results[letter].append([entry.description, entry.document_id])
        return results

    def __sorted_description(self, entries_list):
        return sorted(
            entries_list.items(),
            key = lambda entry: entry[1].description
        )

    def __sorted_id(self):
        return sorted(
            self.entries.items(),
            key = lambda entry: entry[0]
        )

    def get_tags(self, only_exportable: bool=True):
        tag: ZXRegistryTag
        for i, (tag_name, tag) in enumerate(self.tags.items()):
            if only_exportable:
                if tag.is_exportable():
                    yield tag
            else:
                yield tag

    def lookup(self, document_id: int):
        if document_id in self.entries:
            return self.entries[document_id]
        return None

    def lookup_abbreviation(self, document_id: int):
        record = self.lookup(document_id)
        if record and record.abbreviation:
            return record.abbreviation[0:self.ABBREVIATION_CHARS]
        return "0x{}".format(format_padded_id(document_id, width=4).ljust(self.ABBREVIATION_CHARS - 2))

    def lookup_tag(self, name: str) -> ZXRegistryTag|None:
        name = self.__clean_tag_name(name)
        if name in self.tags:
            return self.tags[name]
        return None

    def save(self) -> bool:
        with open(self.registry_path, 'w') as file:
            yaml.dump(
                self.to_dict(), 
                file, 
                indent=4, 
                default_flow_style=False, 
                sort_keys=True
            )
        return True

    def set_ignored(self, document_id: int, value: bool):
        if value:
            if document_id not in self.ignored:
                self.ignored.append(document_id)
            self.__delete_record(document_id)
        else:
            while document_id in self.ignored:
                self.ignored.remove(document_id)


    def sync_record(self, document_id: int, description: str|None=None, abbreviation: str|None=None, tags:list[str]|None=None) -> bool:
        if document_id in self.ignored:
            return False
        
        record = self.__get_updated_record(document_id, description, abbreviation, tags)
        if record.is_valid():
            self.entries[document_id] = record
            return True
        self.__delete_record(document_id)
        return False

    def __get_updated_record(self, document_id: int, description: str|None=None, abbreviation: str|None=None, tags:list[str]|None=None) -> ZXRegistryEntry:
        if document_id in self.entries:
            record = self.entries[document_id]
            record.description = description
            record.abbreviation = abbreviation
        else:
            record = ZXRegistryEntry(document_id, description, abbreviation)

        # Sync tags
        tags_removed = [ tag_name for tag_name in record.tags ]
        for tag_name in self.__ensure_tags(tags):
            if tag_name in tags_removed:
                tags_removed.remove(tag_name)

            record.add_tag(tag_name)
            tag = self.lookup_tag(tag_name)
            tag.add_entry(record)

        # Any tags still in tags_removed are no longer referenced
        for tag_name in tags_removed:
            record.remove_tag(tag_name)
            self.lookup_tag(tag_name).remove_entry(record)
        
        return record

    def __ensure_tags(self, tags:list[str]|None=None) -> typing.Iterator[str]:
        '''
        Ensures that the referenced tag exists in some way, just not in a way
        that includes any interesting details (for later editing).
        '''
        if tags is None:
            return []
        for tag_name in tags:
            tag_name = self.__clean_tag_name(tag_name)
            if not tag_name in self.tags:
                self.sync_tag(name=tag_name)
            yield tag_name

    def __delete_record(self, document_id: str) -> True:
        if document_id in self.entries:
            del self.entries[document_id]
        return True

    def sync_tag(self, name: str, title: str|None=None, export_id: int|None=None) -> ZXRegistryTag:
        name = self.__clean_tag_name(name)
        self.tags[name] = self.__get_updated_tag(name, title, export_id)
        return self.tags[name]

    def __clean_tag_name(self, name: str) -> str:
        name = name.strip() if name else None
        if not name:
            raise ValueError('Encountered empty tag name')
        return name

    def __get_updated_tag(self, name: str, title: str|None=None, export_id: int|None=None) -> ZXRegistryTag:
        if name in self.tags:
            tag = self.tags[name]
            tag.title = title
            tag.export_id = export_id
            return tag
        return ZXRegistryTag(name, title, export_id)

    def to_dict(self):
        result = {
            self.__class__.__name__: {
                'entries': {}, 
                'ignored': [],
                'tags': {}
            }
        }

        node_tags = result[self.__class__.__name__]['tags']
        tag_entry: ZXRegistryTag
        for index, (tag_name, tag_entry) in enumerate(self.tags.items()):
            node_tags[tag_name] = tag_entry.to_dict()

        node_entries = result[self.__class__.__name__]['entries']
        for index, (document_id, entry) in enumerate(self.entries.items()):
            registry_key = entry.document_id
            if registry_key in self.ignored:
                continue
            node_entries[HexYAML(registry_key)] = entry.to_dict()

        node_ignored = result[self.__class__.__name__]['ignored']
        for value in self.ignored:
            node_ignored.append(HexYAML(value))
        return result

    @classmethod
    def from_dict(cls, registry_path, data) -> ZXRegistry:
        if not len(data) == 1:
            raise ValueError("expected one key specifying datatype, found {}".format(len(data)))
        if cls.__name__ not in data:
            raise ValueError("does not look like a {}-file".format(cls.__name__))
        root = data[cls.__name__]

        zx_registry = ZXRegistry(registry_path, 
                                 tags={} ,
                                 ignored_list=root['ignored'])

        for i, (tag_name, data) in enumerate(root['tags'].items()):
            zx_registry.sync_tag(
                tag_name,
                title=data['title'],
                export_id=data['export_id']
            )

        for i, (document_id, data) in enumerate(root['entries'].items()):
            zx_registry.sync_record(
                document_id, 
                description=data['description'], 
                abbreviation=data['abbreviation'],
                tags=data['tags'] if 'tags' in data else []
            )
        return zx_registry

    @classmethod
    def create_file(cls, document_path, allow_overwrite=False) -> ZXRegistry:
        if not allow_overwrite and Path(document_path).is_file():
            raise FileExistsError(document_path)
        return cls.from_dict(document_path, cls.__yaml_defaults())

    @classmethod
    def from_file(cls, document_path, allow_create=True) -> ZXRegistry:
        logger = ZXLogger.get_instance()
        if not Path(document_path).is_file() and allow_create:
            logger.warning(f'Empty registry {cls.__name__} ({document_path})')
            return cls.create_file(document_path, allow_overwrite=False)
        data = cls.__yaml_defaults()
        data = update_tree(data, cls.__get_yaml(document_path))
        return cls.from_dict(document_path, data)

    @classmethod
    def __yaml_defaults(cls) -> dict:
        return {
            cls.__name__: {
                'entries':  {},
                'ignored': [],
                'tags': {}
            }
        }

    @classmethod
    def __get_yaml(cls, yaml_path, check_exists=True) -> dict:
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            if cls.__name__ not in data:
                raise ValueError("does not look like a {}-file".format(cls.__name__))
            return data


class ZXRegistryEntry:
    def __init__(self, document_id: int, description: str|None=None, abbreviation: str|None=None):
        self.document_id = document_id
        self.description = description
        self.abbreviation = abbreviation
        self.tags = []

    def __str__(self):
        return self.description

    def add_tag(self, tag_name: str):
        if tag_name not in self.tags:
            self.tags.append(tag_name)

    def remove_tag(self, tag_name: str):
        if tag_name in self.tags:
            self.tags.remove(tag_name)

    def is_valid(self):
        '''
        Registry entries will be ignored if it does not have a description set.
        '''
        if self.document_id > 0 and self.description:
            return True
        return False

    def to_dict(self):
        return {
            'description': self.description,
            'abbreviation': self.abbreviation,
            'tags': self.tags
        }


class ZXRegistryTag:
    name: str
    title: str
    export_id: int
    entries: list[ZXRegistryEntry]

    def __init__(self, name: str, title: str|None=None, export_id: int|None=None):
        self.name = name
        self.title = title
        self.export_id = export_id
        self.entries = []

    def is_exportable(self):
        if not self.name:
            return False
        if not self.title:
            return False
        if not self.export_id:
            return False
        return True

    def add_entry(self, entry: ZXRegistryEntry):
        if not entry in self.entries:
            self.entries.append(entry)

    def remove_entry(self, entry: ZXRegistryEntry):
        if entry in self.entries:
            self.entries.remove(entry)

    def to_dict(self):
        return {
            'export_id': HexYAML(self.export_id) if self.export_id is not None else None,
            'name': self.name,
            'title': QuotedYAML(self.title) if self.title else None
        }