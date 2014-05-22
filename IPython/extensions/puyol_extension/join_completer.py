import re
from sqlalchemy.orm import class_mapper, RelationshipProperty
from sqlalchemy.orm.properties import ColumnProperty
from IPython.extensions.orm_extension_base.orm_completer import OrmArgumentCompleterFactory
from IPython.extensions.orm_extension_base.utils import NotQueryException, get_module_name
from IPython.extensions.puyol_extension.parser import PuyolLikeModuleAnalyzer
from IPython.extensions.puyol_extension.query_analyzer import PuyolLikeQueryAnalyzer

__author__ = 'Nathaniel'


class AbstractJoinCompleter(object):
    def __init__(self, argument, query):
        self.argument = argument
        self.query_analyzer = PuyolLikeQueryAnalyzer(query=query)

    def suggest(self):
        raise NotImplementedError()


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


def class_relationships(cls):
    mapper = class_mapper(cls)
    targets = set()
    for attr in mapper.attrs:
        if isinstance(attr, RelationshipProperty):
            targets.add(attr.mapper.entity)
    return targets


class ClassJoinCompleter(AbstractJoinCompleter):
    def __init__(self, argument, query, base_meta_class, module):
        AbstractJoinCompleter.__init__(self, argument, query)
        self.base_meta_class = base_meta_class
        self.module = module

    def suggest(self):
        suggestions = []
        module_name = get_module_name(self.module)
        from_clause = self.query_analyzer.get_from_clause()
        if re.match('%s\..*' % module_name, self.argument):
            argument = self.argument.split(['.'])[:-1]
        else:
            argument = self.argument
        for key, potential_join_class in self.module.__dict__.items():  # All public attributes.
            if argument.lower() in key.lower():  # The argument matches string wise
                if isinstance(potential_join_class, self.base_meta_class):  # All suggestions that are tables.
                    if potential_join_class not in from_clause:  # Is not already joined.
                        # All possible combinations for relationships.
                        # Either the suggestion has a relationship to the from clause.
                        # Or the from clause has a relationship to the suggestion.
                        for cls in from_clause:
                            if (potential_join_class in class_relationships(cls)) or (
                                    cls in class_relationships(
                                        potential_join_class)):
                                suggestions.append('%s.%s' % (module_name, key))
        return suggestions


class CriterionJoinCompleter(AbstractJoinCompleter):
    class _ParameterKey(object):
        def __init__(self, cls=None, pk=None, fk=None, key=None):
            self.cls = cls
            self.pk = pk
            self.fk = fk
            self.key = key

    def __init__(self, argument, query, cls, module_analyzer, module):
        AbstractJoinCompleter.__init__(self, argument, query)
        self.cls = cls
        self.module_analyzer = module_analyzer
        self.module = module

    @staticmethod
    def primary_key(cls):
        mapper = class_mapper(cls)
        properties = mapper.attrs
        for attr in properties:
            if isinstance(attr, ColumnProperty):
                columns = attr.columns
                if len(columns) == 0 and columns[0].primary_key:
                    return attr

    @staticmethod
    def foreign_keys(cls):
        mapper = class_mapper(cls)
        properties = mapper.attrs
        fks = []
        for attr in properties:
            if isinstance(attr, ColumnProperty):
                if [a for a in attr.columns if a.foreign_keys]:
                    fks.append(attr)
        return fks

    @staticmethod
    def _attr_fks(attr):
        if isinstance(attr, ColumnProperty):
            return reduce(lambda x, y: x.union(y), [a.foreign_keys for a in attr.columns])

    def _get_key_for_part(self, part):
        pk = None
        fk = None

        parts = part.partition('.')

        key = parts[-1]
        class_string = reduce(lambda x, y: x + y, parts[-2])
        cls = self.module_analyzer.get_class(class_string)

        if not cls:
            return self._ParameterKey(key=part)

        class_primary_key = self.primary_key(cls)
        if class_primary_key.key == key:
            pk = class_primary_key

        class_foreign_keys = self.foreign_keys(cls)
        for class_fk in class_foreign_keys:
            if class_fk.key == key:
                fk = class_fk

        return self._ParameterKey(cls, fk, pk, key)

    def suggest(self):
        from_clause = self.query_analyzer.get_from_clause()
        if re.match('.+==.*', self.argument):
            parts = self.argument.split('==')
            left = parts[0]
            right = parts[1]

            left_key = self._get_key_for_part(left)
            right_key = self._get_key_for_part(right)

            suggestions = []
            if left_key.pk:
                if right_key.cls:
                    if right_key.fk:
                        raise NotQueryException()
                    for fk_prop in self.foreign_keys(right_key.cls):
                        for fk in self._attr_fks(fk_prop):
                            if fk.references(left_key.cls.__table__) and right_key.key in fk_prop.key:
                                suggestions.append(fk_prop.key)

                elif self.cls == left_key.cls:
                    if get_module_name(self.module) in right_key.key:
                        key = right_key.key.split(get_module_name(self.module))[-1]
                    else:
                        key = right_key.key
                    for cls in from_clause:
                        if key in cls.__name__.lower():
                            suggestions.append('%s.%s.' % (get_module_name(self.module), cls.__name__))
                else:
                    suggestions.append('%s.%s.' % (get_module_name(self.module), self.cls.__name__))
            elif left_key.fk:
                fks = self._attr_fks(left_key.fk)
                if right_key.cls:
                    for fk in fks:
                        if fk.references(right_key.cls.__table__):
                            suggestions.append('%s.%s.%s' % ())
            else:
                raise NotQueryException()

        else:
            pass


class PuyolLikeJoinCompleterFactory(OrmArgumentCompleterFactory):
    def __init__(self, *args, **kwargs):
        OrmArgumentCompleterFactory.__init__(self, *args, **kwargs)
        self.module_analyzer = PuyolLikeModuleAnalyzer()

    def _get_cls(self, cls_str):
        return self.module_analyzer.get_class(cls_str)

    @classmethod
    def get_allowed_inner_functions(cls):
        return []

    def get_completer(self, arguments, query):

        if not self.validate_argument(arguments):
            raise NotQueryException()

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

        return ClassJoinCompleter(argument=arguments, query=query,
                                  base_meta_class=self.module_analyzer.get_base_meta_class(self.module),
                                  module=self.module)