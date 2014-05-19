from IPython.extensions.orm_extension_base.orm_line_parser import OrmLineParser

__author__ = 'USER'


class PuyolLikeModuleAnalyzer(object):
    @staticmethod
    def get_base_class(module):
        return module.orm.base.Base


class PuyolLikeLineParser(OrmLineParser):
    def __init__(self, *args, **kwargs):
        OrmLineParser.__init__(self, *args, **kwargs)
        self.module_analyzer = PuyolLikeModuleAnalyzer()

    def _get_main_query_func_name(self):
        return 'get'

    @classmethod
    def _get_query_function_names(cls):
        return ['get', 'refine', 'join']

    def _get_base_class(self):
        return self.module_analyzer.get_base_class(self.module)