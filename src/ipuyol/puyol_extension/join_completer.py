import re
from sqlalchemy.orm import class_mapper, RelationshipProperty
from sqlalchemy.orm.properties import ColumnProperty
from ipuyol.orm_extension_base.orm_completer import OrmArgumentCompleterFactory
from ipuyol.orm_extension_base.utils import NotQueryException, get_module_name
from ipuyol.puyol_extension.parser import PuyolLikeModuleAnalyzer
from ipuyol.puyol_extension.query_analyzer import PuyolLikeQueryAnalyzer

__author__ = 'Nathaniel'


class AbstractJoinCompleter(object):
    def __init__(self, argument, query):
        self.argument = argument
        self.query_analyzer = PuyolLikeQueryAnalyzer(query=query)

    def suggest(self):
        raise NotImplementedError()


class RelationshipJoinCompleter(AbstractJoinCompleter):
    def __init__(self, argument, query, cls, module):
        AbstractJoinCompleter.__init__(self, argument, query)
        self.cls = cls
        self.module = module

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
        suggestions = []
        for rel in allowed:
            suggestion = '%s.%s.%s' % (get_module_name(self.module), self.cls.__name__, rel.key)
            if self.argument in suggestion:
                suggestions.append(suggestion)
        return suggestions


def class_relationships(cls):
    mapper = class_mapper(cls)
    targets = set()
    for attr in mapper.attrs:
        if isinstance(attr, RelationshipProperty):
            targets.add(attr.mapper.entity)
    return targets


def matching_module_classes(argument, module, base_meta_class, from_clause):
    module_name = get_module_name(module)
    suggestions = []
    for key, potential_join_class in module.__dict__.items():  # All public attributes.
        if argument.lower() in key.lower():  # The argument matches string wise
            if isinstance(potential_join_class, base_meta_class):  # All suggestions that are tables.
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


class ClassJoinCompleter(AbstractJoinCompleter):
    def __init__(self, argument, query, base_meta_class, module):
        AbstractJoinCompleter.__init__(self, argument, query)
        self.base_meta_class = base_meta_class
        self.module = module

    def suggest(self):
        module_name = get_module_name(self.module)
        from_clause = self.query_analyzer.get_from_clause()
        if re.match('%s\..*' % module_name, self.argument):
            argument = self.argument.split('.')[-1]
        else:
            argument = self.argument
        return matching_module_classes(argument, self.module, self.base_meta_class, from_clause)


class CriterionJoinCompleter(AbstractJoinCompleter):
    def __init__(self, argument, query, cls, module, namespace):
        AbstractJoinCompleter.__init__(self, argument, query)
        self.cls = cls
        self.module = module
        self.namespace = namespace

    @staticmethod
    def primary_key(cls):
        mapper = class_mapper(cls)
        properties = mapper.attrs
        for attr in properties:
            if isinstance(attr, ColumnProperty):
                columns = attr.columns
                if len(columns) == 1 and columns[0].primary_key:
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
                return list(foreign_keys)[0]

    def _suggest_fk(self, argument, source_classes, target_classes):
        suggestions = []
        for source_class in source_classes:
            foreign_key_properties = self.foreign_keys(source_class)
            for foreign_key_property in foreign_key_properties:
                expression = foreign_key_property.expression
                foreign_key = self._get_fk_for_expression(expression)
                for target_class in target_classes:
                    if foreign_key.references(target_class.__table__):
                        suggestion = '%s.%s.%s' % (
                            get_module_name(self.module), source_class.__name__, foreign_key_property.key)
                        if argument.lower() in suggestion.lower():
                            suggestions.append(suggestion)
        return suggestions

    def _suggest_pk_for_cls(self, argument, cls):
        pk_attr = self.primary_key(cls)
        if pk_attr:
            key = pk_attr.key
        else:
            raise NotQueryException()
        suggestion = '%s.%s.%s' % (get_module_name(self.module), cls.__name__, key)
        if argument.lower() in suggestion.lower():
            return [suggestion]
        else:
            return []

    @staticmethod
    def _get_cls_for_fk(foreign_key, from_clause):
        for cls in from_clause:
            if foreign_key.references(cls.__table__):
                return cls

    def _suggest_right_side(self, from_clause):
        parts = self.argument.split('==')
        left = parts[0].strip()
        right = parts[1].strip()
        try:
            left_attribute = eval(left, self.namespace)
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
                return self._suggest_fk(argument=right, source_classes=from_clause, target_classes=[self.cls])
            else:
                # (a, b.id == a.b_id)
                return self._suggest_fk(argument=right, source_classes=[self.cls], target_classes=from_clause)
        else:
            # Either (a, a.b_id == b.id) or (a, b.a_id == a.id)
            foreign_key = self._get_fk_for_expression(expression)
            if not foreign_key:
                raise NotQueryException()

            if left_is_joinee:
                # (a, a.b_id == b.id)
                cls = self._get_cls_for_fk(foreign_key, from_clause + [self.cls])
            else:
                # (a, b.a_id == a.id)
                cls = self.cls

            if not cls:
                raise NotQueryException()

            return self._suggest_pk_for_cls(argument=right, cls=cls)

    def suggest(self):
        from_clause = self.query_analyzer.get_from_clause()
        if re.match('.+==.*', self.argument):
            return self._suggest_right_side(from_clause)
        else:
            return []


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
                                              namespace=self.namespace)
            else:
                raise NotQueryException()

        for cls in PuyolLikeQueryAnalyzer(query=query).get_from_clause():
            if arguments.lower() in ('%s.%s' % (get_module_name(self.module), cls.__name__)).lower():
                return RelationshipJoinCompleter(argument=arguments, query=query, cls=cls, module=self.module)

        parts = arguments.split('.')
        if len(parts) > 1:
            cls_name = '.'.join(parts[:-1])
            argument = parts[-1].strip()
            cls = self._get_cls(cls_name)
            if cls:
                return RelationshipJoinCompleter(argument=argument, query=query, cls=cls, module=self.module)

        return ClassJoinCompleter(argument=arguments, query=query,
                                  base_meta_class=self.module_analyzer.get_base_meta_class(self.module),
                                  module=self.module)