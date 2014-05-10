import re
from sqlalchemy.orm import class_mapper, ColumnProperty, RelationshipProperty
from sqlalchemy.orm.interfaces import StrategizedProperty
from sqlalchemy.sql import ClauseElement
from IPython.extensions.orm_extension_base.orm_completer import OrmQueryAnalyzer
from IPython.extensions.orm_extension_base.utils import get_module_name, NotQueryException

__author__ = 'USER'


class PuyolLikeQueryAnalyzer(OrmQueryAnalyzer):
    def get_from_clause(self):
        inner_query = self.query._q
        all_mappers = list(inner_query._join_entities) + [inner_query._entity_zero().entity_zero]
        all_classes = map(lambda x: x.entity, all_mappers)
        return all_classes

    def get_last_table(self):
        """
        ~`rtype`: mapper
        """
        return self.query._q._joinpoint_zero()


class PuyolLikeExistsCriteriaAnalyzer(PuyolLikeQueryAnalyzer):
    def __init__(self, query, open_calls, module, namespace):
        PuyolLikeQueryAnalyzer.__init__(self, query)
        self.open_calls = open_calls
        self.module = module
        self.namespace = namespace

    def get_property_string_from_call(self, call):
        if re.match('.*%s\.[a-zA-Z]+\.[a-zA-Z]+$' % get_module_name(self.module), call):
            string = re.findall('%s\.[a-zA-Z]+\.[a-zA-Z]+$' % get_module_name(self.module), call)[0]
            return string
        elif re.match('.*[a-zA-Z]+\.[a-zA-Z]+$', call):
            string = re.findall('[a-zA-Z]+\.[a-zA-Z]+$', call)[0]
            return string
        else:
            raise NotQueryException()

    def get_property_from_property_string(self, property_string):
        try:
            relationship_property = eval(property_string, self.namespace)
        except Exception:
            raise NotQueryException()
        if hasattr(relationship_property, 'property') and isinstance(relationship_property.property,
                                                                     RelationshipProperty):
            return relationship_property.property.mapper.entity
        else:
            raise NotQueryException()

    def get_from_clause(self):
        join_classes = PuyolLikeQueryAnalyzer.get_from_clause(self)
        exists_classes = []
        legitimate_strings = []

        for call in self.open_calls:
            string = self.get_property_string_from_call(call)
            legitimate_strings.append(string)

        for string in legitimate_strings:
            entity = self.get_property_from_property_string(string)
            exists_classes.append(entity)
        return join_classes + exists_classes

    def get_last_table(self):
        if not self.open_calls:
            raise NotQueryException()
        last_call = self.open_calls[-1]
        return class_mapper(self.get_property_from_property_string(self.get_property_string_from_call(last_call)))


def get_criteria_suggestions_for_class(cls, module):
    mapper = class_mapper(cls)
    attributes = mapper.attrs
    return ['%s.%s.%s' % (get_module_name(module), cls.__name__, attr.key) for attr in attributes]


class AbstractCriterionCompleter(object):
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
            argument = self.argument.split(',')[-1]
            if '=' in argument:
                raise NotQueryException()
            suggestions = filter(lambda x: x.startswith(argument.lstrip()), suggestions)
        return suggestions

    def _get_working_operators(self):
        argument = self.argument.split(',')[-1]
        example_operators = [r'== ', r'!= ', r'>= ', r'> ']
        if argument[-1] == ' ':
            return example_operators
        return [argument + ' ' + x for x in example_operators]

    def suggest_criteria(self):
        if self.argument and self.argument[-1] == '.':
            # Looks like a column/relationship.
            argument = self.argument[:-1].split(',')[-1].lstrip()
            mapped_property = self.get_mapped_property(argument)
            if not mapped_property:
                raise NotQueryException()
            suggestions = self._mapped_property_functions(mapped_property, argument)
        elif self.argument and self.get_mapped_property(self.argument.split(',')[-1].lstrip()):
            # We want to remind the user how to use criteria.
            return self._get_working_operators()
        elif self._is_boolean_expression():
            return RedundantCriterionCompleter.suggest()
        else:
            from_clause = self.get_query_analyzer().get_from_clause()
            if re.match('.*[a-zA-Z]+ ?= ?$', self.argument):
                raise NotQueryException()
            else:
                suggestions = self._get_normal_suggestions(from_clause, self.argument)
        return suggestions  # + self.get_criterion_suggestion_variants(suggestions)

    def suggest(self):
        if self._has_kwarg(self.argument):
            return self.suggest_kwarg()
        else:
            self.argument = self.argument.split(',')[-1].lstrip()
            return self.suggest_criteria()

    @staticmethod
    def _has_kwarg(argument_string):
        return re.match('(.+, ?)?[a-zA-Z]+=[^=]+', argument_string)

    def _get_attributes_for_kwarg(self, query):
        mapper = self.get_query_analyzer().get_last_table()
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

    def _get_normal_suggestions(self, from_clause, last_arg):
        all_suggestions = reduce(lambda x, y: x + y,
                                 [get_criteria_suggestions_for_class(cls, self.module) for cls in from_clause])
        results = filter(lambda x: last_arg in x, all_suggestions)
        return results

    @staticmethod
    def get_criterion_suggestion_variants(suggestions):
        return map(lambda x: '~' + x, suggestions)

    @staticmethod
    def _mapped_property_functions(mapped_property, string):
        suggestions = []
        if isinstance(mapped_property, ColumnProperty):
            suggestions = ['in_', 'like', 'ilike']  # TODO make a puyol function for getting these.
        elif isinstance(mapped_property, RelationshipProperty):
            if mapped_property.uselist:
                suggestions = ['any']
            else:
                suggestions = ['has']
        else:
            raise NotQueryException()
        return ['%s.%s(' % (string, suggestion) for suggestion in suggestions]


class QuerySimpleCriterionCompleter(AbstractCriterionCompleter):
    def get_query_analyzer(self):
        return PuyolLikeQueryAnalyzer(self.query)


class ComplexCriterionCompleter(AbstractCriterionCompleter):
    def __init__(self, argument, query, module, namespace, open_calls):
        AbstractCriterionCompleter.__init__(self, argument, query, module, namespace)
        self.open_calls = open_calls

    def get_query_analyzer(self):
        return PuyolLikeExistsCriteriaAnalyzer(query=self.query, open_calls=self.open_calls, module=self.module,
                                               namespace=self.namespace)


class RedundantCriterionCompleter(object):
    @staticmethod
    def suggest():
        return [' | (', ' & (']