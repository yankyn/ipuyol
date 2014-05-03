import re
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.elements import ColumnElement
from IPython.extensions.orm_extension.orm_completer import OrmQueryAnalyzer, OrmQueryCompleter, OrmFunctionCompleter
from IPython.extensions.orm_extension.orm_line_parser import NotQueryException
from IPython.extensions.puyol_extension.parser import PuyolLikeLineParser

__author__ = 'USER'


class PuyolLikeQueryAnalyzer(OrmQueryAnalyzer):
    def get_from_clause(self, query):
        inner_query = query._q
        all_mappers = list(inner_query._join_entities) + [inner_query._entity_zero.entity_zero]
        all_classes = map(lambda x: x.entity, all_mappers)
        return all_classes

    def get_last_join(self, query):
        return query._q._joinpoint_zero()


def get_criteria_suggestions_for_class(cls):
    mapper = class_mapper(cls)
    attributes = mapper.attrs
    return map(lambda x: x.class_attribute, attributes)


INNER_FUNCS = ['any', 'has']
INNER_FUNCS_REGEX = r'|'.join(map(lambda x: '.+\.%s' % x, INNER_FUNCS))


class PuyolLikeGetCompleter(OrmFunctionCompleter):
    def __init__(self, module, namespace):
        OrmFunctionCompleter.__init__(self, module=module, namespace=namespace)
        self.analyzer = PuyolLikeQueryAnalyzer()

    def _get_attributes_for_kwarg(self, query):
        mapper = self.analyzer.get_last_join(query)
        attributes = mapper.attrs
        return attributes

    @staticmethod
    def _get_properties(attributes, attribute_cls):
        return filter(lambda x: isinstance(x, attribute_cls), attributes)

    def suggest_kwarg(self, query, last_kwarg):

        try:
            attributes = self._get_attributes_for_kwarg(query)
        except AttributeError:
            raise NotQueryException()

        suggestions = []

        column_properties = self._get_properties(attributes, ColumnProperty)
        column_suggestions = map(lambda x: x.key + '=', column_properties)
        suggestions += column_suggestions

        relationship_properties = self._get_properties(attributes, RelationshipProperty)
        relationship_suggestions = map(lambda x: x.key + '=', filter(lambda x: not x.uselist, relationship_properties))
        suggestions += relationship_suggestions

        if last_kwarg:
            suggestions = filter(lambda x: x.startswith(last_kwarg), suggestions)

        return suggestions

    def get_actual_expression(self, argument):
        try:
            return eval(argument, self.namespace)
        except Exception:
            return

    def get_mapped_property(self, argument):
        result = None
        if re.match(r'%s\.[a-zA-Z]+\.[a-zA-Z]+' % self.module_name, argument) and self.is_actual_expression():
            result = self.get_actual_expression(argument)
        if re.match(r'[a-zA-Z]+\.[a-zA-Z]+', argument) and hasattr(self.module,
                                                                   argument.split('.')[
                                                                       0]) and self.is_actual_expression():
            result = self.get_actual_expression(argument)
        if result and (isinstance(result, ColumnProperty) or isinstance(result, RelationshipProperty)):
            return result

    def get_binary_expression(self, argument):
        expression = self.get_actual_expression(argument)
        if isinstance(argument, ColumnElement):
            return expression

    def suggest_criteria(self, query, last_arg):

        from_clause = self.analyzer.get_from_clause(query)
        normal_suggestions = reduce(lambda x, y: x + y, map(get_criteria_suggestions_for_class, from_clause))
        suggestions = []

        if last_arg:
            if re.match(INNER_FUNCS_REGEX, last_arg):
                suggestions = self.suggest_inner(query, last_arg)
            elif last_arg[:-1] == '.':
                mapped_property = self.get_mapped_property(last_arg[:-1])
                if mapped_property:
                    suggestions = self.suggest_mapped_property(mapped_property)
            elif self.get_binary_expression(last_arg):
                suggestions = self.suggest_logic_operator_for_mapped_property()
            else:
                suggestions = filter(lambda x: last_arg in normal_suggestions)

        return suggestions

    def _suggest(self, query, args, kwargs):
        if kwargs:
            # Only suggest kwargs
            last_kwarg = kwargs[-1]
            return self.suggest_kwarg(query, last_kwarg)
        else:
            if args:
                last_arg = args[-1]
            else:
                last_arg = ''
            return self.suggest_criteria(query, last_arg)

    def suggest_inner(self, query, last_arg):
        return []  # TODO implement

    @staticmethod
    def suggest_mapped_property(mapped_property):
        if isinstance(mapped_property, ColumnProperty):
            return ['in_']  # TODO make a puyol function for getting these.
        elif isinstance(mapped_property, RelationshipProperty):
            if mapped_property.uselist:
                return ['any']
            else:
                return ['has']
        else:
            raise NotQueryException()

    @staticmethod
    def suggest_logic_operator_for_mapped_property():
        return [' | ', ' & ']


class PuyolLikeJoinCompleter(OrmFunctionCompleter):
    pass


class PuyolLikeQueryCompleter(OrmQueryCompleter):
    _function_handlers = {'get': PuyolLikeGetCompleter, 'refine': PuyolLikeGetCompleter,
                          'join': PuyolLikeJoinCompleter}

    def get_parser(self):
        return PuyolLikeLineParser(module=self.module, namespace=self.namespace)

    def get_handler_for_function(self, function):
        return self._function_handlers.get(function)