import re
import yaml
import collections.abc

def format_padded_id(document_id, width=4):
    return str(document_id).rjust(width, '0')

def sanitize_filename(filename):
    return re.sub(r'[^\w_. -]', '', filename)

def suggest_document_name(document_id, path_hint):
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

class QuotedYAML(str):
    '''
    Wrapper class used in order to force yaml to use double-quotes within
    dumps. Must be wrapped around values before performing the dump.
    '''
    pass

def quoted_yaml_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(QuotedYAML, quoted_yaml_presenter)
