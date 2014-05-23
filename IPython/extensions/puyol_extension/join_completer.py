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
    def _get_fk_for_expression(expression):
        if expression.foreign_keys:
            foreign_keys = expression.foreign_keys
            if len(foreign_keys) == 1:
                return foreign_keys.pop()

    def _suggest_fk(self, argument, source_classes, target_classes):
        suggestions = []
        for source_class in source_classes:
            foreign_key_attributes = self.foreign_keys(source_class)
            for foreign_key_attribute in foreign_key_attributes:
                expression = foreign_key_attribute.property.expression
                foreign_key = self._get_fk_for_expression(expression)
                for target_class in target_classes:
                    if foreign_key.references(target_class.__table__):
                        suggestion = '%s.%s.%s' % (
                            get_module_name(self.module), self.cls.__name__, foreign_key_attribute.key)
                        if suggestion.startswith(argument):
                            suggestions.append(suggestion[len(argument):])
        return suggestions

    def _suggest_pk_for_cls(self, argument, cls):
        pk_attr = self.primary_key(cls)
        if pk_attr:
            key = pk_attr.key
        else:
            raise NotQueryException()
        suggestion = '%s.%s.%s' % (get_module_name(self.module), self.cls.__name__, key)
        if suggestion.startswith(argument):
            return suggestion[len(argument):]
        else:
            raise NotQueryException()

    @staticmethod
    def _get_cls_for_fk(foreign_key, from_clause):
        for cls in from_clause:
            if foreign_key.references(cls.__table__):
                return cls

    def suggest(self):
        from_clause = self.query_analyzer.get_from_clause()
        if re.match('.+==.*', self.argument):
            parts = self.argument.split('==')
            left = parts[0]
            right = parts[1]
            try:
                left_attribute = eval(left)
            except Exception:
                raise NotQueryException()

            if left_attribute.class_ in from_clause:
                left_is_joinee = False
            elif left_attribute.class_ == self.cls:
                left_is_joinee = True
            else:
                raise NotQueryException()

            expression = left_attribute.property.expression
            if expression.primary_key:
                # Either (a, a.id == b.a_id) or (a, b.id == a.b_id)
                if left_is_joinee:
                    # (a, a.id == b.a_id)
                    return self._suggest_fk(argument=right, source_classes=[self.cls], target_classes=from_clause)
                else:
                    # (a, b.id == a.b_id)
                    return self._suggest_fk(argument=right, source_classes=from_clause, target_classes=[self.cls])
            else:
                # Either (a, a.b_id == b.id) or (a, b.a_id == a.id)
                foreign_key = self._get_fk_for_expression(expression)
                if not foreign_key:
                    raise NotQueryException()

                if not left_is_joinee:
                    # (a, a.b_id == b.id)
                    cls = self.cls
                else:
                    # (a, b.a_id == a.id)
                    cls = self._get_cls_for_fk(foreign_key, from_clause + [self.cls])

                if not cls or not foreign_key.references(cls):
                    raise NotQueryException()

                return self._suggest_pk_for_cls(argument=right, cls=cls)


class PuyolLikeJoinCompleterFactory(OrmArgumentCompleterFactory):
    def __init__(self, *args, **kwargs):
        OrmArgumentCompleterFactory.__init__(self, *args, **kwargs)
        self.module_analyzer = PuyolLikeModuleAnalyzer(module=self.module, namespace=self.namespace)

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
                return CriterionJoinCompleter(argument=argument, query=query, cls=cls, module=self.module,
                                              module_analyzer=self.module_analyzer)
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