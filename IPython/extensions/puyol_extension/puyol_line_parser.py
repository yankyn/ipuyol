from IPython.extensions.orm_extension.orm_line_parser import OrmLineParser

__author__ = 'USER'


class PuyolLikeLineParser(OrmLineParser):
    def _get_main_query_func_name(self):
        return 'get'

    @classmethod
    def _get_query_function_names(cls):
        return ['get', 'refine', 'join']

    def _get_base_class(self):
        return self.module.orm.base.Base