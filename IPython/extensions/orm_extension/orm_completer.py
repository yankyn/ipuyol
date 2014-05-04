import re
import regex
from IPython.extensions.orm_extension.utils import NotQueryException

__author__ = 'Nathaniel'


class OrmQueryAnalyzer(object):
    def get_from_clause(self, query):
        raise NotImplementedError()


class OrmQueryCompleter(object):
    def __init__(self, module, namespace):
        self.module = module
        self.namespace = namespace

    def get_parser(self):
        raise NotImplementedError()

    def get_handler_for_function(self, function):
        raise NotImplementedError()

    def suggest(self, line):
        parser = self.get_parser()
        query, function, arguments = parser.parse(line)
        inner_completer = self.get_handler_for_function(function)
        if not inner_completer:
            raise NotQueryException()
        return inner_completer.suggest(query, arguments)


class NotSupportedYetError(Exception):
    pass


class OrmFunctionCompleter(object):
    def __init__(self, module, namespace):
        self.module = module
        self.namespace = namespace

    def get_criterion_functions(self):
        raise NotImplementedError()

    def get_binary_expression_mock(self):
        '''
        TODO explain this very fucking well. Maybe find a better fucking solution.
        '''
        raise NotImplementedError()

    def _get_call_split_regex(self):
        allowed_functions = self.get_criterion_functions()
        return '|'.join(map(lambda x: '\.' + x + '\(', allowed_functions))

    @staticmethod
    def has_kwarg(argument_string):
        return re.match('(.+, ?)?[a-zA-Z]+=[^=]+', argument_string)

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

    def argument_to_complete(self, arguments_string):
        split_regex = self._get_call_split_regex()
        calls = re.split(split_regex, arguments_string)
        open_calls = self.open_criterion_call_indices(calls)
        if not open_calls:
            if re.match('.*\) *,.*', calls[-1]):  # Last argument is not the last call
                # ignore any calls, simply pass the last argument.
                return arguments_string.split(',')[-1].strip()
            else:  # Last argument is the last call.
                # We cannot assemble the call here, but we do know that the call is a complete criterion.
                # We assume that the behavior for all criteria remians the same
                # Because different criteria having different methods seems weird.
                # TODO enforce this, make this class handle criteria completion.
                # TODO Or, move all this logic to the actual completer.
                return self.get_binary_expression_mock()
        else:
            # There is an open criterion call,
            # remove all junk and pass everything after the first call to the actual completer.
            first_call = calls[0]
            arguments_to_remove = first_call.count(',')
            return arguments_string.split(',', arguments_to_remove)[-1].strip()

    @classmethod
    def get_args_types(cls, arguments):
        parsing = 'args'
        kwargs = []
        args = []
        last_kwarg = False
        for argument in arguments:
            if last_kwarg:
                raise NotQueryException()
            if re.match('[a-zA-Z]+=.+', argument):
                # Is a kwarg
                parsing = 'kwargs'
                kwargs.append(argument)
            elif parsing == 'args':
                if not cls.validate_argument(argument):
                    raise NotQueryException()
                args.append(argument)
            else:
                if not last_kwarg:
                    last_kwarg = argument
        return args, kwargs

    def suggest(self, query, arguments):
        arguments = arguments.split(arguments)
        #arguments = regex.split(r'(?<!any(?!\(.*\))[^,]*),', arguments)
        args, kwargs = self.get_args_types(arguments)
        return self._suggest(query, args, has_kwargs=self.has_kwarg(arguments))

    def _suggest(self, query, last_arg, has_kwargs):
        # TODO implement different handlers for different function groups.
        # example: join should allow only kwargs that are actually legitimate join arguments.
        raise NotImplementedError()

    @classmethod
    def validate_argument(cls, argument):
        # TODO validate more
        if argument.count('"') % 2 or argument.count('\'') % 2:
            return False
        if re.match('.*\([^\)]*', argument):
            return False
