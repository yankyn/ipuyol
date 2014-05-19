from sqlalchemy.orm import class_mapper, RelationshipProperty
from IPython.extensions.orm_extension_base.orm_completer import OrmArgumentCompleterFactory
from IPython.extensions.orm_extension_base.utils import NotQueryException
from IPython.extensions.puyol_extension.parser import PuyolLikeModuleAnalyzer
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

    def suggest(self):
        mapper = class_mapper(self.cls)
        from_clause = self.query_analyzer.get_from_clause()
        if not self.cls in from_clause:
            raise NotQueryException()
        # All relationship properties.
        relationships = [attr for attr in mapper.attrs if isinstance(attr, RelationshipProperty)]
        # All relationship properties that are not already joined.
        allowed = [rel for rel in relationships if rel.mapper.entity not in from_clause]
        # And start with the argument.
        return [rel.key for rel in allowed if rel.key.startswith(self.argument)]


class ClassJoinCompleter(AbstractJoinCompleter):
    pass


class CriterionJoinCompleter(AbstractJoinCompleter):
    def __init__(self, argument, query, cls):
        AbstractJoinCompleter.__init__(self, argument, query)
        self.cls = cls


class PuyolLikeJoinCompleterFactory(OrmArgumentCompleterFactory):
    def __init__(self, *args, **kwargs):
        OrmArgumentCompleterFactory.__init__(self, *args, **kwargs)
        self.module_analyzer = PuyolLikeModuleAnalyzer()

    def _get_cls(self, cls_str):
        try:
            cls = eval(cls_str, self.namespace)
            if isinstance(cls, self.module_analyzer.get_base_meta_class(self.module)):
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
            argument = parts[-1].strip()
            cls = self._get_cls(cls_name)
            if cls:
                return RelationshipJoinCompleter(argument=argument, query=query, cls=cls)

        return ClassJoinCompleter(argument=arguments, query=query)