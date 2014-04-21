import copy
import pytest
from IPython.extensions.puyol_extension.alt_state_machine import OrmLineParser, NotQueryException
import mock_module

__author__ = 'USER'

NOT_QUERIES = ['mock_module.SomeLie', 'mock_module.NotBaseMock']
NAME_ERRORS = ['BaseMock.get()']


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


@pytest.fixture(params=NOT_QUERIES)
def not_query_line(request):
    return request.param


@pytest.fixture(params=NAME_ERRORS)
def name_error_line(request):
    return request.param


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
    assert parser_with_direct_import.get_base('BaseMock.get()') == 15


def test_query_line_direct_module_no_member_get_base(parser, not_query_line):
    with pytest.raises(NotQueryException):
        parser.get_base(not_query_line)