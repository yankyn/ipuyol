import copy
import pytest
from IPython.extensions.orm_extension.orm_line_parser import OrmLineParser, NotQueryException
import mock_module

__author__ = 'USER'

NOT_QUERY_BASES = ['mock_module.SomeLie', 'mock_module.NotBaseMock']
BASE_NAME_ERRORS = ['BaseMock.get()']

QUERIES = [('mock_module.BaseMock.get()', 'mock_module.BaseMock'), ()]


class MockOrmLineParser(OrmLineParser):
    def _get_base_class(self):
        return mock_module.BaseMock

    def _get_main_query_func_name(self):
        return 'get'

    @classmethod
    def _get_query_function_names(cls):
        return ['get', 'join', 'refine']


@pytest.fixture
def parser():
    return MockOrmLineParser(module=mock_module, namespace=globals())


@pytest.fixture
def parser_with_direct_import():
    from mock_module import BaseMock

    namespace = globals()
    namespace = copy.copy(namespace)
    namespace.update(locals())
    return MockOrmLineParser(module=mock_module, namespace=namespace)


@pytest.fixture(params=NOT_QUERY_BASES)
def not_query_line(request):
    return request.param


@pytest.fixture(params=BASE_NAME_ERRORS)
def name_error_line(request):
    return request.param


@pytest.mark.parametrize('line, expected', [('mock_module.BaseMock.get()', 'mock_module.BaseMock'),
                                            ('mock_module.BaseMock.get(', 'mock_module.BaseMock'),
                                            ('mock_module.BaseMock.get(a = 5', 'mock_module.BaseMock'),
                                            ('mock_module.BaseMock.get(a = 5)', 'mock_module.BaseMock'),
                                            ('mock_module.BaseMock.get().join(', 'mock_module.BaseMock.get()'),
                                            (
                                                'mock_module.BaseMock.get(a = 5).join(',
                                                'mock_module.BaseMock.get(a = 5)'),
                                            ('mock_module.BaseMock.get(a = 5.join(', 'mock_module.BaseMock.get(a = 5')])
def test_get_base_string(parser, line, expected):
    assert parser.get_base_string(line) == expected


@pytest.mark.parametrize('line', ['.get()', '.get(a=5,', 'get('])
def test_validate_func_and_args_passes(parser, line):
    parser.validate_func_and_args(line)


@pytest.mark.parametrize('line', ['.get().join(', 'get', 'get.join()'])
def test_validate_func_and_args_fails(parser, line):
    with pytest.raises(NotQueryException):
        parser.validate_func_and_args(line)


@pytest.mark.parametrize('line, expected_func, expected_args',
                         [('.get()', 'get', ')'), ('.get(a=5)', 'get', 'a=5)')])
def test_get_func_and_args(parser, line, expected_func, expected_args):
    func, args = parser.parse_func_and_args(line)
    assert func == expected_func
    assert args == expected_args


def test_class_line_get_base(parser):
    assert parser.get_base('mock_module.BaseMock') == mock_module.RETURN_VALUE


def test_class_imported_directly_line_get_base(parser):
    assert parser.get_base('BaseMock') == mock_module.RETURN_VALUE


def test_query_line_class_get_base(parser):
    assert parser.get_base('mock_module.BaseMock.get()') == mock_module.RETURN_VALUE


def test_query_line_no_module_get_base(parser, name_error_line):
    with pytest.raises(NameError):
        parser.get_base(name_error_line)


def test_query_imported_directly_line_get_base(parser_with_direct_import):
    assert parser_with_direct_import.get_base('BaseMock.get()') == mock_module.RETURN_VALUE


def test_query_line_direct_module_no_member_get_base(parser, not_query_line):
    with pytest.raises(NotQueryException):
        parser.get_base(not_query_line)


@pytest.mark.parametrize('line, expected_func, expected_args, expected_base',
                         [('mock_module.BaseMock.get(', 'get', '', mock_module.BaseMock.get()),
                          ('mock_module.BaseMock.get()', 'get', ')', mock_module.BaseMock.get()),
                          ('mock_module.BaseMock.get(a=5,', 'get', 'a=5,', mock_module.BaseMock.get()),
                          ('mock_module.BaseMock.get().join(', 'join', '', mock_module.BaseMock.get()),
                          ('mock_module.BaseMock.get(a=5).join(', 'join', '', mock_module.BaseMock.get(a=5))])
def test_parse_query(parser, line, expected_func, expected_args, expected_base):
    assert parser.parse(line) == (expected_base, expected_func, expected_args)
