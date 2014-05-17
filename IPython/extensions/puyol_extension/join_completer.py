from IPython.extensions.orm_extension_base.orm_completer import OrmArgumentCompleterFactory
from IPython.extensions.orm_extension_base.utils import NotQueryException
from IPython.extensions.puyol_extension.parser import get_base_class_for_module
from IPython.extensions.puyol_extension.query_analyzer import PuyolLikeQueryAnalyzer

__author__ = 'Nathaniel'


class AbstractJoinCompleter(object):

    def __init__(self, argument, query):
        self.argument = argument
        self.query_analyzer = PuyolLikeQueryAnalyzer(query=query)


class RelationshipJoinCompleter(AbstractJoinCompleter):

    def __init__(self, argument, query, cls):
        AbstractJoinCompleter.__init__(self, argument, query)
        self.cls = cls


class ClassJoinCompleter(AbstractJoinCompleter):
    pass


class CriterionJoinCompleter(AbstractJoinCompleter):
    pass


class PuyolLikeJoinCompleterFactory(OrmArgumentCompleterFactory):

    def _get_cls(self, cls_str):
        try:
            cls = eval(cls_str, self.namespace)
            base = get_base_class_for_module(self.module)
            if issubclass(cls, base):
                return cls
        except Exception:
            return

    def get_completer(self, arguments, query):

        if ',' in arguments:
            if arguments.count(',') > 1:
                raise NotQueryException()
            parts = arguments.split(',')
            cls_name = parts[0].strip()
            argument = parts[1].strip()
            cls = self._get_cls(cls_name)
            if cls:
                return CriterionJoinCompleter(argument=argument, query=query, cls=cls)
            else:
                raise NotQueryException()

        parts = arguments.split('.')
        if len(parts) > 1:
            cls_name = '.'.join(parts[:-1])
            argument = parts[-1]
            cls = self._get_cls(cls_name)
            if cls:
                return RelationshipJoinCompleter(argument=argument, query=query, cls=cls)

        return ClassJoinCompleter(argument=arguments, query=query)