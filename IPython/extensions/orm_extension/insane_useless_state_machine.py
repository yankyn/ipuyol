import re


NESTED_FUNCS = ['has', 'any']  # Functions that go inside an expression and allow nesting of each other.
QUERY_FUNCS = ['refine', 'order_by']  # PuyolQuery functions
SOURCE_FUNCS = ['get']  # Functions that generate a query
OTHER_FUNCS = ['join']
PUYOL_FUNCS = set(
    NESTED_FUNCS + QUERY_FUNCS + SOURCE_FUNCS + OTHER_FUNCS)  # All functions that require special treatment in a puyol query.
# This allows us to find out when the query is ended.
QUERY_REGEX = re.compile(r'''[\(\)\w+\.('.*?(?<!\\)')(".*?(?<!\\)")]''')

QUERY = 'query'
EVAL_FUNC = 'evaluation_function'
EXPRESSION = 'expression'
ARGUMENTS = 'arguments'


class PuyolLineParserState(object):
    '''
    Abstract class for a state in the parser's state machine.
    :
    '''

    RESULT_NAME = None

    def __init__(self, result='', log=None):
        '''

        '''
        self.result = result
        self.log = log
        self.next_state = self
        self.repeat_tokens = []

    def handle_token(self, token):
        '''
        Receives a token and changes the
        '''
        raise NotImplementedError()

    def is_done(self):
        return self.next_state != self or self.next_state is None

    def get_result(self):
        if not self.RESULT_NAME:
            raise NotImplementedError()
        return {self.RESULT_NAME: self.result}

    def _add_token(self, token):
        self.result = token + self.result


class PuyolLineParserQueryState(PuyolLineParserState):
    RESULT_NAME = QUERY

    def __init__(self, *args, **kwargs):
        super(PuyolLineParserQueryState, self).__init__(*args, **kwargs)
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
            self.next_state = None
        else:
            self._add_token(token)


class PuyolLineParserEvaluationFunctionState(PuyolLineParserState):
    RESULT_NAME = EVAL_FUNC

    def handle_token(self, token):
        if self.result:
            self.next_state = PuyolLineParserQueryState()
        else:
            self._add_token(token)


class PuyolLineParserExpressionState(PuyolLineParserState):
    RESULT_NAME = EXPRESSION

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
    RESULT_NAME = ARGUMENTS

    def __init__(self, *args, **kwargs):
        super(PuyolLineParserArgumentsState, self).__init__(*args, **kwargs)
        self._func_nest = 0
        self._allow_query = True

    def handle_token(self, token):
        if self._func_nest == 0:
            # All functions have been closed, it is either a query, a syntax error or a criterion with a function.
            if token in PUYOL_FUNCS:
                # it is a query, repeat everything.
                self.repeat_tokens.append(token)
                if self._allow_query:
                    print 'arguments ended with ), looking for prior query'
                    self.next_state = PuyolLineParserQueryState()
                    self.result = ''
                else:
                    raise Exception('Only a query is allowed and its not a query')
            else:
                # The last set of parenthesis proved to be part of a criterion. No need to repeat anything so far.
                self.repeat_tokens = []
                self._add_token(token)

        if self._func_nest < 0:
            # There's an open function.
            if token in PUYOL_FUNCS:
                # It's an expression, so we need to repeat the last token.
                print 'arguments ended with (, looking for containing expression'
                self.next_state = PuyolLineParserExpressionState()
                self.repeat_tokens.append(token)
                self.result = self.result[1:]
            else:
                # otherwise its a criterion function, there's still no need to repeat anything.
                self.repeat_tokens = []
                self._add_token(token)

        if self._func_nest > 0:
            # we're in a closed function, everything is allowed, repeat everything.
            self.repeat_tokens.append(token)
            self._add_token(token)

        if token == '(':
            self._func_nest -= 1
        elif token == ')':
            if not self._func_nest:
                self.repeat_tokens.append(token)
            self._func_nest += 1
        elif not self._func_nest:
            self._allow_query = False


class PuyolLineParser(object):

    def __init__(self):
        self.state = PuyolLineParserArgumentsState()
        self.all_states = set()
        self.tokens = []

    @staticmethod
    def _get_tokenizer_regex():
        return re.compile(r'''
        '.*?(?<!\\)' | # single quoted strings or
        ".*?(?<!\\)" | # double quoted strings or
        \w+ | # identifier
        \S | # other characters
        \s
        ''', re.VERBOSE | re.DOTALL)

    @staticmethod
    def _get_tokens(regex, text):
        tokens = regex.findall(text)
        tokens.reverse()
        return tokens

    @staticmethod
    def sanitize(text):
        text = text.replace('\n', '')
        text = text.replace('\r', '')
        return text

    def _get_info_from_state(self, token):
        if self.state:
            self.state.handle_token(token)
            if self.state.is_done():
                self.tokens = self.state.repeat_tokens + self.tokens
                self.all_states.add(self.state)
                self.state = self.state.next_state

    def parse_line(self, text):
        text = self.sanitize(text)
        regex = self._get_tokenizer_regex()
        self.tokens = self._get_tokens(regex, text)

        while self.tokens:
            token = self.tokens.pop(0)
            self._get_info_from_state(token)
        if self.state:
            self.all_states.add(self.state)
            self.state = None

    def get_result(self):
        result = {}
        for state in self.all_states:
            result.update(state.get_result())
        return result