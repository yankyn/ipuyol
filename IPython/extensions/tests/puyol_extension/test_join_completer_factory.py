import mock
import pytest
from IPython.extensions.orm_extension_base.utils import NotQueryException
from IPython.extensions.puyol_extension.join_completer import PuyolLikeJoinCompleterFactory, CriterionJoinCompleter, ClassJoinCompleter, RelationshipJoinCompleter
from IPython.extensions.tests.orm_extension import mock_module
from fixtures.utils import namespace_with_direct_import
import puyol

__author__ = 'Nathaniel'


@pytest.fixture
def mock_query():
    return mock.Mock()


@pytest.fixture
def mock_join_completer_factory(namespace_with_direct_import):
    return PuyolLikeJoinCompleterFactory(module=mock_module, namespace=namespace_with_direct_import)


@pytest.mark.parametrize('name, cls', [('puyol.Student', puyol.Student), ('Country', puyol.Country)])
def test_get_cls(mock_join_completer_factory, name, cls):
    assert mock_join_completer_factory._get_cls(name) == cls


@pytest.mark.parametrize('name', ['puyol.Stud', 'Student', 'puyol.Studenta', '5', 'object'])
def test_get_raises_exception(mock_join_completer_factory, name):
    assert mock_join_completer_factory._get_cls(name) is None


def test_get_completer_several_arguments(mock_join_completer_factory, mock_query):
    with pytest.raises(NotQueryException):
        mock_join_completer_factory.get_completer('puyol.Student, puyol.University, a == 5', query=mock_query)


def test_get_completer_two_arguments_not_class(mock_join_completer_factory, mock_query):
    with pytest.raises(NotQueryException):
        mock_join_completer_factory.get_completer('NotAClass, a == 5', query=mock_query)


@pytest.mark.parametrize('arguments, expected_class', [('puyol.Student, a == 5', CriterionJoinCompleter),
                                                       (' puyol.Student ,', CriterionJoinCompleter),
                                                       (' puyol.Student', ClassJoinCompleter),
                                                       (' puyol.Student', ClassJoinCompleter),
                                                       (' puyol.Student.a', RelationshipJoinCompleter),
                                                       ('puyol.Stu', ClassJoinCompleter)])
def test_get_completer(mock_join_completer_factory, mock_query, arguments, expected_class):
    assert mock_join_completer_factory.get_completer(arguments, query=mock_query).__class__ == expected_class