import re
from IPython.extensions.orm_extension.orm_line_parser import NotQueryException

__author__ = 'Nathaniel'


class OrmQueryAnalyzer(object):
    def get_from_clause(self, query):
        raise NotImplementedError()


class OrmQueryCompleter(object):
    def get_parser(self):
        raise NotImplementedError()

    def get_query_analyzer(self):
        raise NotImplementedError()

    def _get_function_completer(self):
        raise NotImplementedError()

    def suggest(self, line):
        parser = self.get_parser()
        query, function, arguments = parser.parse(line)
        from_clause = self.get_query_analyzer().get_from_clause(query)
        inner_completer = self._get_function_completer()
        return inner_completer.suggest(from_clause, arguments)


class OrmInnerCompleter(object):
    @staticmethod
    def get_args_types(arguments):
        parsing = 'args'
        kwargs = []
        args = []
        for argument in arguments:
            if re.match('[a-zA-Z]+=.*', argument):
                # Is a kwarg
                parsing = 'kwargs'
                kwargs.append(argument)
            elif parsing == 'args':
                args.append(argument)
            else:
                raise NotQueryException()
        return args, kwargs

    def suggest(self, from_clause, arguments):
        arguments = arguments.split(',')
        args, kwargs = self.get_args_types(arguments)
        return self._suggest(from_clause, args, kwargs)

    def _suggest(self, from_clause, args, kwargs):
        # TODO implement different handlers for different function groups.
        # example: join should allow only kwargs that are actually legitimate join arguments.
        raise NotImplementedError()


