import re
import yaml
import unicodedata
import collections.abc
from pathlib import Path
from argparse import ArgumentParser, ArgumentError, ArgumentTypeError

def format_padded_id(document_id, width=4):
    return str(document_id).rjust(width, '0')

def sanitize_filename(filename):
    filename = str(filename)
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s-]', '', filename)
    return re.sub(r'[-\s]+', '-', filename).strip('-_')

def suggest_document_name(document_id, path_hint=None):
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

def parse_document_id(value):
    value = int(value)
    if value < 0 or value > 9999:
        raise ValueError(f'Does not look like a valid document id')
    return value

def argument_is_id(value):
    '''
    Check that the supplied value appears to be an int between 0 and 9999
    '''
    try:
        return parse_document_id(value)
    except ValueError:
        raise ArgumentError(f'Does not look like a valid document id')

class QuotedYAML(str):
    '''
    Wrapper class used in order to force yaml to use double-quotes within
    dumps. Must be wrapped around values before performing the dump.
    '''
    pass

def quoted_yaml_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(QuotedYAML, quoted_yaml_presenter)
