import collections.abc

def format_padded_id(document_id, width=4):
    return str(document_id).rjust(width, '0')

def singleton(cls):
    """
    Decorator that converts a class into a singleton
    """
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

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