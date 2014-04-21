import re

__author__ = 'USER'


class NotQueryException(Exception):
    pass


class OrmLineParser(object):
    def __init__(self, module, namespace):
        self.module = module
        self.namespace = namespace

    @property
    def module_name(self):
        return self.module.__name__.split('.')[-1]

    def get_module_full_path(self):
        return self.module.__name__

    @classmethod
    def get_funcs_regex(cls):
        regex = '|'.join(cls._get_query_function_names())
        return regex

    def _get_query_from_query_string(self, string):
        try:
            # TODO should maybe run in different thread? Should check how evaluation is done in IPython
            base = eval(string, self.namespace)
        except SyntaxError:
            # Not a full query. Probable a query inside a query. (And this works with union or minus and such)
            # TODO sometime in the future we may want to support this. Currently this is just annoying.
            raise NotQueryException()
        return base

    def get_base(self, string):
        '''
        Receives a string, and returns the query object to be used for extracting information about possible
        suggestions.
        '''
        base = None

        if re.match(r'%s\.[a-zA-Z]+' % self.module_name, string):
            if re.match(r'%s.[a-zA-Z]+\.%s*' % (self.module_name, self._get_main_query_func_name()), string):
                # Looks like a full query.
                base = self._get_query_from_query_string(string)
            else:
                # Looks like a class, called through the module.
                class_name = re.sub('%s\.' % self.module_name, '', string)
                if hasattr(self.module, class_name):
                    base = self._get_query_from_class_name(class_name)
                else:
                    raise NotQueryException()

        elif hasattr(self.module, string.split('.')[0]):
            # Looks like a class, separately imported.
            if re.match(r'[a-zA-Z]+\.%s*' % self._get_main_query_func_name(), string):
                base = self._get_query_from_query_string(string)
            else:
                if not issubclass(getattr(self.module, string), self._get_base_class()):
                    raise NotQueryException()
                else:
                    base = self._get_query_from_class_name(string)

        # TODO implement more cases.
        else:
            raise NotQueryException()

        return base

    def parse(self, line):
        regex = self.get_funcs_regex()
        non_funcs = re.split(regex, line)
        funcs = re.findall(regex, line)

        if not funcs or not non_funcs:
            raise NotQueryException()

        first_func = funcs[0]
        last_func = funcs[-1]

        base = self.get_base(non_funcs[0])

    # Private Functions

    def _get_query_from_class(self, cls):
        return getattr(cls, self._get_main_query_func_name())()

    def _get_query_from_class_name(self, class_name):
        return self._get_query_from_class(getattr(self.module, class_name))

    # Abstract Private Functions

    def _get_base_class(self):
        raise NotImplementedError()

    def _get_main_query_func_name(self):
        raise NotImplementedError()

    @classmethod
    def _get_query_function_names(cls):
        raise NotImplementedError()

