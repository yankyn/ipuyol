from IPython.extensions.orm_extension_base.orm_line_parser import OrmLineParser

__author__ = 'USER'


def get_base_class_for_module(module):
    return module.orm.base.Base


class PuyolLikeLineParser(OrmLineParser):
    def _get_main_query_func_name(self):
        return 'get'

    @classmethod
    def _get_query_function_names(cls):
        return ['get', 'refine', 'join']

    def _get_base_class(self):
        return get_base_class_for_module(self.module)