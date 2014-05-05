import re
import regex
from IPython.extensions.orm_extension.utils import NotQueryException

__author__ = 'Nathaniel'


class OrmQueryAnalyzer(object):
    def __init__(self, query):
        self.query = query

    def get_from_clause(self):
        raise NotImplementedError()


class OrmQueryCompleter(object):
    def __init__(self, module, namespace):
        self.module = module
        self.namespace = namespace

    def get_parser(self):
        raise NotImplementedError()

    def get_handler_for_function(self, function, query):
        raise NotImplementedError()

    def suggest(self, line):
        parser = self.get_parser()
        query, function, arguments = parser.parse(line)
        inner_completer = self.get_handler_for_function(function, query)
        if not inner_completer:
            raise NotQueryException()
        return inner_completer.suggest(arguments)


class NotSupportedYetError(Exception):
    pass


class OrmFunctionCompleter(object):
    def __init__(self, module, namespace, query):
        self.module = module
        self.namespace = namespace
        self.query = query

    def get_criterion_functions(self):
        raise NotImplementedError()

    def suggest(self, arguments):
        raise NotImplementedError()

    @classmethod
    def validate_argument(cls, argument):
        # TODO validate more
        if argument.count('"') % 2 or argument.count('\'') % 2:
            return False
        if re.match('.*\([^\)]*', argument):
            return False
