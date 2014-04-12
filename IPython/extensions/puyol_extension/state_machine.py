import re


NESTED_FUNCS = ['has', 'any']  # Functions that go inside an expression and allow nesting of each other.
QUERY_FUNCS = ['refine', 'order_by']  # PuyolQuery functions
SOURCE_FUNCS = ['get']  # Functions that generate a query
PUYOL_FUNCS = set(
    NESTED_FUNCS + QUERY_FUNCS + SOURCE_FUNCS)  # All functions that require special treatment in a puyol query.
# This allows us to find out when the query is ended.
QUERY_REGEX = re.compile(r'''[\(\)\w+\.('.*?(?<!\\)')(".*?(?<!\\)")]''')


class PuyolLineParserState(object):

    RESULT_NAME = None

    def __init__(self, result='', log=None):
        self.result = result
        self.log = log
        self.next_state = self
        self.repeat_tokens = []

    def handle_token(self, token):
        raise NotImplementedError()

    def is_done(self):
        return self.next_state != self

    def get_result(self):
        if not self.RESULT_NAME:
            raise NotImplementedError()
        return {self.RESULT_NAME: self.result}

    def _add_token(self, token):
        self.result = token + self.result


class PuyolLineParserQueryState(PuyolLineParserState):

    RESULT_NAME = 'query'

    def __init__(self, remove_last_query_token, *args, **kwargs):
        super(PuyolLineParserQueryState, self).__init__(*args, **kwargs)
        self.remove_last_query_token = remove_last_query_token
        self.open_par = 0

    def handle_token(self, token):
        end_query = False
        if token == ')':
            self.open_par -= 1
        elif token == '(':
            self.open_par += 1
        elif not QUERY_REGEX.match(token) and not self.open_par:
            end_query = True
        if self.open_par > 0:
            end_query = True

        if end_query:
            print 'prior query ended with token %s' % token
            if self.remove_last_query_token:
                self.result = self.result[:-1]
            self.next_state = None
        else:
            self.result = token + self.result


class PuyolLineParserEvaluationFunctionState(PuyolLineParserState):

    RESULT_NAME = 'evaluation_func'

    def handle_token(self, token):
        if self.result:
            self.next_state = PuyolLineParserQueryState(remove_last_query_token=False)
        else:
            self._add_token(token)


class PuyolLineParserExpressionState(PuyolLineParserState):

    RESULT_NAME = 'expression'

    def handle_token(self, token):
        if token in PUYOL_FUNCS and token not in NESTED_FUNCS:
            print 'last expression starts with %s' % token
            self.next_state = PuyolLineParserEvaluationFunctionState()
            self.repeat_tokens = [token]
            self.result = self.result[1:]
        else:
            self._add_token(token)
            if token in NESTED_FUNCS:
                print 'found nested func %s' % token


class PuyolLineParserArgumentsState(PuyolLineParserState):

    RESULT_NAME = 'arguments'

    def handle_token(self, token):
        if token == '(':
            print 'arguments ended with (, looking for containing expression'
            self.next_state = PuyolLineParserExpressionState()
        elif token == ')':
            print 'arguments ended with ), looking for prior query'
            self.next_state = PuyolLineParserQueryState(remove_last_query_token=False, result=token)
        else:
            self._add_token(token)


class PuyolLineParser(object):

    def __init__(self):
        self.state = PuyolLineParserArgumentsState()
        self.all_states = set()

    @staticmethod
    def _get_tokenizer_regex():
        return re.compile(r'''
            '.*?(?<!\\)' | # single quoted strings or
            ".*?(?<!\\)" | # double quoted strings or
            \w+ | # identifier
            \S | # other characters
            \
            ''', re.VERBOSE | re.DOTALL)

    @staticmethod
    def _get_tokens(regex, text):
        tokens = regex.findall(text)
        tokens.reverse()
        return tokens

    def parse_line(self, text):
        regex = self.get_tokenizer_regex()
        tokens = self._get_tokens(regex, text)
        self.state = None

        while tokens:
            token = tokens.pop(0)
            if self.state:
                self.state.handle_token(token)
                if self.state.is_done():
                    tokens = self.state.repeat_tokens + tokens
                    self.all_states.add(self.state)
                    self.state = self.state.next_state

    def get_result(self):
        result = {}
        for state in self.all_states:
            result.update(state.get_result())

#l = regexp.findall('[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses).refine(puyol.Cource.university.has(puyol.university.countries.any(name=5, ')
#l = regexp.findall('[a for a in func(puyol.Student.get(pedro.Student.something.has())).join(puyol.Student.courses).refine(puyol.Cource.university.has(puyol.university.countries.any(name=5, ')
#l = regexp.findall('[a for a in func(puyol.Student.get(pedro.Student.something.has())).join(puyol.Student.courses).refine(puyo l.Cource.u niversity.h as(puyol .university.countries.any(name=5, ') # this is ok, should only fail on eval
#l = regexp.findall('[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses).refine(')
#l = regexp.findall('[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)')# does not work, no arguments state
#l = regexp.findall('puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)') # does not work, no arguments state
#l = regexp.findall('[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses).order_by(')
#l = regexp.findall("[a for a in func(puyol.Student.get(pedro.Student.something.has(name='hello')).join(puyol.Student.courses).order_by(")
#tokens = regexp.findall('[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses).refine(puyol.Cource.university.has(puyol.university.name == "NAME"  | puyol.university.countries.any(name=5, ')
