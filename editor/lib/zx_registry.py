import yaml
from pathlib import Path
from .utilities import format_padded_id, update_tree
from .zx_logger import ZXLogger

class ZXRegistry:
    FILE_EXTENSION = '.registry'
    ABBREVIATION_CHARS = 8
    register: dict[str, ZXRegistryEntry]

    def __init__(self, registry_path):
        self.registry_path = Path(registry_path)
        self.register = {}

    def generate_TOC_AZ(self):
        results = []
        cur_group = '#'
        cur_list = []
        results.append([cur_group, cur_list])
        for (document_id, data) in self.__sorted_description():
            if not data.description:
                continue
            group = data.description[0].upper() if data.description[0].isalpha() else '#'
            if not group == cur_group:
                cur_list = []
                cur_group = group
                results.append([cur_group, cur_list])
            cur_list.append([data.description, document_id])
        return results

    def __sorted_description(self):
        return sorted(
            self.register.items(),
            key = lambda entry: entry[1].description
        )

    def __sorted_id(self):
        return sorted(
            self.register.items(),
            key = lambda entry: entry[0]
        )

    def lookup(self, document_id):
        registry_key = format_padded_id(document_id, width=4)
        if registry_key in self.register:
            return self.register[registry_key]
        return None

    def lookup_abbreviation(self, document_id):
        record = self.lookup(document_id)
        if record and record.abbreviation:
            return record.abbreviation[0:self.ABBREVIATION_CHARS]
        return "[{}]".format(format_padded_id(document_id, width=4).ljust(self.ABBREVIATION_CHARS - 2))

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

    def sync_record(self, document_id, description=None, abbreviation=None) -> bool:
        registry_key = format_padded_id(document_id, width=4)
        record = self.__get_updated_record(registry_key, document_id, description, abbreviation)
        if record.is_valid():
            self.register[registry_key] = record
            return True
        self.__delete_record(registry_key)
        return False

    def __get_updated_record(self, registry_key, document_id, description=None, abbreviation=None) -> ZXRegistryEntry:
        if registry_key in self.register:
            record = self.register[registry_key]
            record.description = description
            record.abbreviation = abbreviation
            return record
        return ZXRegistryEntry(document_id, description, abbreviation)

    def __delete_record(self, registry_key) -> True:
        if registry_key in self.register:
            del self.register[registry_key]
        return True

    def to_dict(self):
        result = { self.__class__.__name__: { 'entries': {} } }
        entries = result[self.__class__.__name__]['entries']
        for index, (document_id, entry) in enumerate(self.register.items()):
            entries[entry.get_padded_id()] = entry.to_dict()
        return result

    @classmethod
    def from_dict(cls, registry_path, data) -> ZXRegistry:
        if not len(data) == 1:
            raise ValueError("expected one key specifying datatype, found {}".format(len(data)))
        if cls.__name__ not in data:
            raise ValueError("does not look like a {}-file".format(cls.__name__))
        root = data[cls.__name__]

        zx_registry = ZXRegistry(registry_path)
        for i, (registry_key, data) in enumerate(root['entries'].items()):
            zx_registry.sync_record(
                int(registry_key), 
                description=data['description'], 
                abbreviation=data['abbreviation'])
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
            logger.warning(f'Creating {cls.__name__} ({document_path})')
            return cls.create_file(document_path, allow_overwrite=False)
        data = cls.__yaml_defaults()
        data = update_tree(data, cls.__get_yaml(document_path))
        return cls.from_dict(document_path, data)

    @classmethod
    def __yaml_defaults(cls) -> dict:
        return {
            cls.__name__: {
                'entries':  {}
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
    def __init__(self, document_id, description=None, abbreviation=None):
        self.document_id = document_id
        self.description = description
        self.abbreviation = abbreviation

    def __str__(self):
        return self.description

    def get_padded_id(self):
        return format_padded_id(self.document_id, width=4)

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
            'abbreviation': self.abbreviation
        }