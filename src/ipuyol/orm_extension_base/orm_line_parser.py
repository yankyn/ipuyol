import re
from ipuyol.orm_extension_base.utils import NotQueryException, get_module_name, get_module_full_path

__author__ = 'USER'


class OrmLineParser(object):
    def __init__(self, module, namespace):
        self.module = module
        self.namespace = namespace

    @property
    def module_name(self):
        return get_module_name(self.module)

    def get_module_full_path(self):
        return get_module_full_path(self.module)

    @classmethod
    def get_funcs_regex(cls):
        regex = '|'.join(cls._get_query_function_names())
        return regex

    @classmethod
    def get_funcs_wit_parenthesis_regex(cls):
        regex = '|'.join([x + '\(' for x in cls._get_query_function_names()])
        return regex

    @classmethod
    def get_base_regex(cls):
        regex = '.*(?=' + '|'.join(['\.' + x + '\(' for x in cls._get_query_function_names()]) + ')'
        return regex

    def _get_query_from_query_string(self, string):
        try:
            # TODO should maybe run in different thread? Should check how evaluation is done in IPython
            base = eval(string, self.namespace)
        except SyntaxError:
            # Not a full query. Probably a query inside a query. (And this works with union or minus and such)
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
            if re.match(r'%s\.[a-zA-Z]+\.%s.*' % (self.module_name, self._get_main_query_func_name()), string):
                # Looks like a full query.
                base = self._get_query_from_query_string(string)
            else:
                # Looks like a class, called through the module.
                class_name = re.sub('%s\.' % self.module_name, '', string)
                if hasattr(self.module, class_name) and isinstance(getattr(self.module, class_name),
                                                                   self._get_base_meta_class()):
                    base = self._get_query_from_class_name(class_name)
                else:
                    raise NotQueryException()

        elif hasattr(self.module, string.split('.')[0]):
            # Looks like a class, separately imported.
            if re.match(r'[a-zA-Z]+\.%s.*' % self._get_main_query_func_name(), string):
                base = self._get_query_from_query_string(string)
            else:
                if not isinstance(getattr(self.module, string), self._get_base_meta_class()):
                    raise NotQueryException()
                else:
                    base = self._get_query_from_class_name(string)

        # TODO implement more cases.
        else:
            raise NotQueryException()

        return base

    def get_base_string(self, line):
        # TODO support parsing of lines not starting with the query.
        regex = self.get_base_regex()
        base_string_parts = re.findall(regex, line)
        if not base_string_parts:
            raise NotQueryException()
        return base_string_parts[0]

    def validate_func_and_args(self, func_and_args):
        if len(re.findall(self.get_funcs_regex(), func_and_args)) != 1:
            raise NotQueryException()
        if len(re.findall(self.get_funcs_wit_parenthesis_regex(), func_and_args)) != 1:
            raise NotQueryException()
            # TODO: validate more.

    def parse_func_and_args(self, func_and_args):
        func = re.findall(self.get_funcs_regex(), func_and_args)[0]
        parts = func_and_args.split(func + '(')
        return func, parts[-1]

    def parse(self, line):
        base_string = self.get_base_string(line)
        func_and_args = line[len(base_string):]
        self.validate_func_and_args(func_and_args)
        func_str, args = self.parse_func_and_args(func_and_args)
        base = self.get_base(base_string)
        return base, func_str, args

    # Private Functions

    def _get_query_from_class(self, cls):
        return getattr(cls, self._get_main_query_func_name())()

    def _get_query_from_class_name(self, class_name):
        return self._get_query_from_class(getattr(self.module, class_name))

    # Abstract Private Functions

    def _get_base_meta_class(self):
        raise NotImplementedError()

    def _get_main_query_func_name(self):
        raise NotImplementedError()

    @classmethod
    def _get_query_function_names(cls):
        raise NotImplementedError()

