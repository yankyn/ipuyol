from IPython.extensions.orm_extension.orm_line_parser import OrmLineParser

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


class OrmJoinCompleter(object):
    def suggest(self, from_clause, arguments):
        raise NotImplementedError()


class OrmRefineCompleter(object):
    def suggest(self, from_clause, arguments):
        raise NotImplementedError()

