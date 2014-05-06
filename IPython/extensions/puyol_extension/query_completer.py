from IPython.extensions.orm_extension.orm_completer import OrmQueryAnalyzer, OrmQueryCompleter
from IPython.extensions.puyol_extension.completer_factory import PuyolLikeGetCompleterFactory, \
    PuyolLikeJoinCompleterFactory
from IPython.extensions.puyol_extension.parser import PuyolLikeLineParser

__author__ = 'USER'


class PuyolLikeQueryCompleter(OrmQueryCompleter):
    _function_handlers = {'get': PuyolLikeGetCompleterFactory, 'refine': PuyolLikeGetCompleterFactory,
                          'join': PuyolLikeJoinCompleterFactory}

    def get_parser(self):
        return PuyolLikeLineParser(module=self.module, namespace=self.namespace)

    def get_handler_for_function(self, function):
        return self._function_handlers.get(function)(module=self.module, namespace=self.namespace)