import re
from IPython.extensions.orm_extension.orm_line_parser import NotQueryException

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


class OrmFunctionCompleter(object):

    def __init__(self, module, namespace):
        self.module = module
        self.namespace = namespace

    @staticmethod
    def get_args_types(arguments):
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
                args.append(argument)
            else:
                if not last_kwarg:
                    last_kwarg = argument
        return args, kwargs

    def suggest(self, query, arguments):
        arguments = arguments.split(',')  # TODO user regex split so any/has chains to get split.
        args, kwargs = self.get_args_types(arguments)
        return self._suggest(query, args, kwargs)

    def _suggest(self, query, args, kwargs):
        # TODO implement different handlers for different function groups.
        # example: join should allow only kwargs that are actually legitimate join arguments.
        raise NotImplementedError()