__author__ = 'USER'


def get_module_full_path(module):
    return module.__name__


class NotQueryException(Exception):
    pass


def get_module_name(module):
    # TODO move these to utils module.
    return module.__name__.split('.')[-1]