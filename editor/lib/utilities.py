import re
import yaml
import unicodedata
import collections.abc
from pathlib import Path
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError

def argument_is_dir(path):
    '''
    Check the supplied path value to ensure that it is is actually a directory
    '''
    path = Path(path)
    if not path.is_dir():
        raise ArgumentError(f'is not a valid directory')
    return path

def argument_is_file(path):
    '''
    Check the supplied path value to ensure that it is is actually a file
    '''
    path = Path(path)
    if not path.is_file():
        raise ArgumentError(f'is not an existing file')
    return path

def argument_is_document_id(value):
    '''
    Check that the supplied value appears to be an int between 0 and 9999
    '''
    try:
        return parse_document_id(value)
    except ValueError:
        raise ArgumentError(f'Does not look like a valid document id')

def argument_is_page_id(value):
    '''
    Check that the supplied value appears to be an int between 0 and 9999
    '''
    try:
        return parse_page_id(value)
    except ValueError:
        raise ArgumentError(f'Does not look like a valid document id')

def format_padded_id(document_id, width=4):
    return str(document_id).rjust(width, '0')

def get_project_root() -> Path:
    '''
    Returns Path pointing to the base of the editor, allowing us to determine
    the location of assets stored with the code files. This matters when we
    run any of the scripts from a different working directory from where they
    are stored.
    '''
    return Path(__file__).parent.parent

def parse_asset_id(value):
    return ensure_int(value, 0, 99)

def parse_document_id(value):
    return ensure_int(value, 0, 9999)

def parse_page_id(value):
    return ensure_int(value, 0, 99)

def ensure_int(value, value_min, value_max):
    '''
    Ensure that we get an integer between the supplied value range, both ends
    included in the comparison.
    '''
    value = int(value)
    if value < value_min or value > value_max:
        raise ValueError(f'Value not between {value_min} and {value_max}')
    return value

def sanitize_filename(filename):
    filename = str(filename)
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s-]', '', filename)
    return re.sub(r'[-\s]+', '-', filename).strip('-_')

def suggest_document_directory(document_id: int, path_hint=None):
    '''
    Just generates a string with a predictable format, doesn't actually
    create or check if anything already exist.
    '''
    if not path_hint:
        return format_padded_id(document_id)
    return "{}-{}".format(
        format_padded_id(document_id),
        sanitize_filename(path_hint)
    )

def suggest_asset_path(asset_id: int, extension: str, path_hint: str=None):
    '''
    Generates asset path, no attempts made at checking if that would overlap
    any such existing file as that is assumed to be intentional. 
    '''
    if path_hint and str(path_hint).endswith(extension):
        path_hint = path_hint[:len(extension)]
    if not path_hint:
        return "{}{}".format(
            format_padded_id(asset_id, width=2),
            extension
        )
    return "{}-{}{}".format(
        format_padded_id(asset_id, width=2),
        sanitize_filename(path_hint),
        extension
    )    

def update_tree(data, update):
    '''
    Recursively update dictionary structure, allowing us to ensure that
    default values exist after loading data that may or may not be
    complete.
    '''
    for key, value in update.items():
        if isinstance(value, collections.abc.Mapping):
            data[key] = update_tree(data.get(key, {}), value)
        else:
            data[key] = value
    return data

class QuotedYAML(str):
    '''
    Wrapper class used in order to force yaml to use double-quotes within
    dumps. Must be wrapped around values before performing the dump.
    '''
    pass

def quoted_yaml_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(QuotedYAML, quoted_yaml_presenter)
