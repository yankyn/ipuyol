import re
from IPython.extensions.orm_extension_base.orm_completer import OrmArgumentCompleterFactory
from IPython.extensions.puyol_extension.criterion_completer import QuerySimpleCriterionCompleter, \
    RedundantCriterionCompleter, ComplexCriterionCompleter

__author__ = 'USER'


class PuyolLikeGetCompleterFactory(OrmArgumentCompleterFactory):
    def __init__(self, module, namespace):
        OrmArgumentCompleterFactory.__init__(self, module=module, namespace=namespace)

    @classmethod
    def open_criterion_call_indices(cls, calls):
        closed_call_indices = set()
        count = 0
        for call in calls:
            for i in range(call.count(')') - call.count('(')):
                closed_call_indices.add(count - i - 1)
            count += 1
        all_call_indices = set(range(len(calls) - 1))
        open_call_indices = all_call_indices.difference(closed_call_indices)
        return open_call_indices

    @classmethod
    def open_criterion_calls(cls, calls):
        indices = list(cls.open_criterion_call_indices(calls))
        indices.sort()
        return [calls[i] for i in indices]

    def parse_arguments(self, arguments_string, query):
        split_regex = self._get_call_split_regex()
        calls = re.split(split_regex, arguments_string)
        if len(calls) == 1:
            return QuerySimpleCriterionCompleter(argument=arguments_string, query=query, module=self.module,
                                                 namespace=self.namespace)
        open_calls = self.open_criterion_calls(calls)
        if not open_calls:
            if re.match('.*\) *,.*', calls[-1]):  # Last argument is not the last call
                # ignore any calls, simply pass the last argument.
                return QuerySimpleCriterionCompleter(argument=arguments_string.split(',')[-1].strip(), query=query,
                                                     module=self.module, namespace=self.namespace)
            else:  # Last argument is the last call.
                return RedundantCriterionCompleter()
        else:
            # There is an open criterion call,
            # remove all junk and pass everything after the first call to the actual completer.
            first_call = calls[0]
            arguments_to_remove = first_call.count(',')
            return ComplexCriterionCompleter(module=self.module, namespace=self.namespace,
                                             argument=arguments_string.split('(')[-1].strip(),
                                             query=query, open_calls=open_calls)

    def get_completer(self, arguments_string, query):
        completer = self.parse_arguments(arguments_string, query)
        return completer

    def get_criterion_functions(self):
        return ['any', 'has']

    def _get_call_split_regex(self):
        allowed_functions = self.get_criterion_functions()
        return '|'.join(map(lambda x: '\.' + x + '\(', allowed_functions))


class PuyolLikeJoinCompleterFactory(OrmArgumentCompleterFactory):
    pass