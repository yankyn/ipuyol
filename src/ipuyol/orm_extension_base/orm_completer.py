import re
from ipuyol.orm_extension_base.utils import NotQueryException

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

    def get_factory_for_function(self, function):
        raise NotImplementedError()

    def suggest(self, line):
        parser = self.get_parser()
        query, function, arguments = parser.parse(line)
        completer_factory = self.get_factory_for_function(function)
        if not completer_factory:
            raise NotQueryException()
        completer = completer_factory.get_completer(arguments, query)
        return completer.suggest()


class OrmArgumentCompleterFactory(object):
    def __init__(self, module, namespace):
        self.module = module
        self.namespace = namespace

    def get_completer(self, arguments, query):
        raise NotImplementedError()

    @classmethod
    def get_allowed_inner_functions(cls):
        raise NotImplementedError

    @classmethod
    def validate_argument(cls, argument):
        # TODO validate more
        if argument.count('"') % 2 or argument.count('\'') % 2:
            return False

        # Regexp for open parenthesis after a function that is not allowed.
        if re.match('.*[^(' + '|'.join(cls.get_allowed_inner_functions()) + ')]\([^\)]*', argument):
            return False

        return True
