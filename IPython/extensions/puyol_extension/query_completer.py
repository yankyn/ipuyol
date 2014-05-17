from IPython.extensions.orm_extension_base.orm_completer import OrmQueryCompleter
from IPython.extensions.puyol_extension.completer_factory import PuyolLikeGetCompleterFactory
from IPython.extensions.puyol_extension.join_completer import PuyolLikeJoinCompleterFactory
from IPython.extensions.puyol_extension.parser import PuyolLikeLineParser

__author__ = 'USER'


class PuyolLikeQueryCompleter(OrmQueryCompleter):
    _function_handlers = {'get': PuyolLikeGetCompleterFactory, 'refine': PuyolLikeGetCompleterFactory,
                          'join': PuyolLikeJoinCompleterFactory}

    def get_parser(self):
        return PuyolLikeLineParser(module=self.module, namespace=self.namespace)

    def get_factory_for_function(self, function):
        return self._function_handlers.get(function)(module=self.module, namespace=self.namespace)