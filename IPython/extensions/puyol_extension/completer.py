import re
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.interfaces import StrategizedProperty
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.elements import ClauseElement
from IPython.extensions.orm_extension.orm_completer import OrmQueryAnalyzer, OrmQueryCompleter, OrmFunctionCompleter
from IPython.extensions.orm_extension.utils import NotQueryException, get_module_name
from IPython.extensions.puyol_extension.parser import PuyolLikeLineParser

__author__ = 'USER'


class PuyolLikeQueryAnalyzer(OrmQueryAnalyzer):
    def get_from_clause(self):
        inner_query = self.query._q
        all_mappers = list(inner_query._join_entities) + [inner_query._entity_zero().entity_zero]
        all_classes = map(lambda x: x.entity, all_mappers)
        return all_classes

    def get_last_join(self):
        return self.query._q._joinpoint_zero()


class CompleteCriterion(object):
    @staticmethod
    def suggest():
        return [' | ', ' & ']


class AbstractCriterion(object):
    def __init__(self, argument, query, module, namespace):
        self.argument = argument
        self.query = query
        self.module = module
        self.namespace = namespace

    def get_query_analyzer(self):
        raise NotImplementedError()

    def suggest_kwarg(self):
        try:
            attributes = self._get_attributes_for_kwarg(self.query)
        except AttributeError:
            raise NotQueryException()
        suggestions = []
        column_properties = self._get_properties(attributes, ColumnProperty)
        column_suggestions = map(lambda x: x.key + '=', column_properties)
        suggestions += column_suggestions
        relationship_properties = self._get_properties(attributes, RelationshipProperty)
        relationship_suggestions = map(lambda x: x.key + '=', filter(lambda x: not x.uselist, relationship_properties))
        suggestions += relationship_suggestions
        if self.argument:
            suggestions = filter(lambda x: x.startswith(self.argument), suggestions)
        return suggestions

    def suggest_criteria(self):
        # TODO suggest a proper criterion when a kwarg head is detected.
        suggestions = []
        if self.argument[-1] == '.' and self.get_mapped_property(self.argument[:-1]):
            # Looks like a column/relationship.
            mapped_property = self.get_mapped_property(self.argument[:-1])
            suggestions = self._mapped_property_functions(mapped_property)
        elif self._is_boolean_expression():
            return ComplexCriterion.suggest()
        else:
            from_clause = self.get_query_analyzer().get_from_clause(self.query)
            suggestions = self._get_normal_suggestions(from_clause, self.argument)
        return suggestions + self.get_criterion_suggestion_variants(suggestions)

    def suggest(self):
        if self._has_kwarg():
            return self.suggest_kwarg()
        else:
            self.suggest_criteria()


    @staticmethod
    def _has_kwarg(argument_string):
        return re.match('(.+, ?)?[a-zA-Z]+=[^=]+', argument_string)

    def _get_attributes_for_kwarg(self, query):
        mapper = self.get_query_analyzer().get_last_join(query)
        attributes = mapper.attrs
        return attributes

    @staticmethod
    def _get_properties(attributes, attribute_cls):
        return filter(lambda x: isinstance(x, attribute_cls), attributes)


    def evaluate_expression(self, argument):
        try:
            return eval(argument, self.namespace)
        except Exception:
            return

    def get_mapped_property(self, argument):
        result = None
        if re.match(r'%s\.[a-zA-Z]+\.[a-zA-Z]+' % get_module_name(self.module),
                    argument) and self.evaluate_expression(argument):
            result = self.evaluate_expression(argument)
        if re.match(r'[a-zA-Z]+\.[a-zA-Z]+', argument) and hasattr(self.module,
                                                                   argument.split('.')[
                                                                       0]) and self.evaluate_expression(argument):
            result = self.evaluate_expression(argument)
        if result and hasattr(result, 'property') and (isinstance(result.property, StrategizedProperty)):
            return result.property

    def _is_boolean_expression(self):
        expression = self.evaluate_expression(self.argument)
        if isinstance(expression, ClauseElement):
            return True
        return False

    @staticmethod
    def _get_normal_suggestions(from_clause, last_arg):
        all_suggestions = reduce(lambda x, y: x + y, map(get_criteria_suggestions_for_class,
                                                         from_clause))
        return filter(lambda x: last_arg in all_suggestions, all_suggestions)

    @staticmethod
    def get_criterion_suggestion_variants(suggestions):
        return map(lambda x: '~' + x, suggestions)

    @staticmethod
    def _mapped_property_functions(mapped_property):
        if isinstance(mapped_property, ColumnProperty):
            return ['in_']  # TODO make a puyol function for getting these.
        elif isinstance(mapped_property, RelationshipProperty):
            if mapped_property.uselist:
                return ['any']
            else:
                return ['has']
        else:
            raise NotQueryException()


class ComplexCriterion(AbstractCriterion):
    pass


class QuerySimpleCriterion(AbstractCriterion):
    def get_query_analyzer(self):
        return PuyolLikeQueryAnalyzer(self.query)


class InnerCriterionSimpleCriterion(AbstractCriterion):
    pass


def get_criteria_suggestions_for_class(cls):
    mapper = class_mapper(cls)
    attributes = mapper.attrs
    return map(lambda x: x.class_attribute, attributes)


class PuyolLikeGetCompleter(OrmFunctionCompleter):
    def __init__(self, module, namespace, query):
        OrmFunctionCompleter.__init__(self, module=module, namespace=namespace)
        self.query = query

    @staticmethod
    def open_criterion_call_indices(calls):
        closed_call_indices = set()
        count = 0
        for call in calls:
            for i in range(call.count(')')):
                closed_call_indices.add(count - i - 1)
            count += 1
        all_call_indices = set(range(len(calls) - 1))
        open_call_indices = all_call_indices.difference(closed_call_indices)
        return open_call_indices

    def parse_arguments(self, arguments_string):
        split_regex = self._get_call_split_regex()
        calls = re.split(split_regex, arguments_string)
        if not calls:
            return QuerySimpleCriterion(argument=arguments_string, query=self.query)
        open_calls = self.open_criterion_call_indices(calls)
        if not open_calls:
            if re.match('.*\) *,.*', calls[-1]):  # Last argument is not the last call
                # ignore any calls, simply pass the last argument.
                return QuerySimpleCriterion(argument=arguments_string.split(',')[-1].strip(), query=self.query)
            else:  # Last argument is the last call.
                return CompleteCriterion()
        else:
            # There is an open criterion call,
            # remove all junk and pass everything after the first call to the actual completer.
            first_call = calls[0]
            arguments_to_remove = first_call.count(',')
            return ComplexCriterion(module=self.module, namespace=self.namespace,
                                    argument=arguments_string.split(',', arguments_to_remove)[-1].strip(),
                                    query=self.query)

    def suggest(self, arguments_string):
        # TODO remember to suggest ~suggestions if argument is empty.
        criterion = self.parse_arguments(arguments_string)
        return criterion.suggest()

    def get_criterion_functions(self):
        return ['any', 'has']

    def _get_call_split_regex(self):
        allowed_functions = self.get_criterion_functions()
        return '|'.join(map(lambda x: '\.' + x + '\(', allowed_functions))


class PuyolLikeJoinCompleter(OrmFunctionCompleter):
    pass


class PuyolLikeQueryCompleter(OrmQueryCompleter):
    _function_handlers = {'get': PuyolLikeGetCompleter, 'refine': PuyolLikeGetCompleter,
                          'join': PuyolLikeJoinCompleter}

    def get_parser(self):
        return PuyolLikeLineParser(module=self.module, namespace=self.namespace)

    def get_handler_for_function(self, function, query):
        return self._function_handlers.get(function)(query=query, module=self.module, namespace=self.namespace)