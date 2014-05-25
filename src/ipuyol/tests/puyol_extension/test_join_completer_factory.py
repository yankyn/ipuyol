import pytest
from fixtures.utils import namespace_with_direct_import
from ipuyol.orm_extension_base.utils import NotQueryException
from ipuyol.puyol_extension.join_completer import PuyolLikeJoinCompleterFactory, CriterionJoinCompleter, ClassJoinCompleter, RelationshipJoinCompleter
from ipuyol.tests.orm_extension import mock_module
from puyol_tests.fixtures.db_fixtures import db
import puyol

__author__ = 'Nathaniel'


@pytest.fixture
def mock_join_completer_factory(namespace_with_direct_import):
    return PuyolLikeJoinCompleterFactory(module=puyol, namespace=namespace_with_direct_import)


@pytest.mark.parametrize('name, cls', [('puyol.Student', puyol.Student), ('Country', puyol.Country)])
def test_get_cls(mock_join_completer_factory, name, cls):
    assert mock_join_completer_factory._get_cls(name) == cls


@pytest.mark.parametrize('name', ['puyol.Stud', 'Student', 'puyol.Studenta', '5', 'object'])
def test_get_raises_exception(mock_join_completer_factory, name):
    assert mock_join_completer_factory._get_cls(name) is None


def test_get_completer_several_arguments(db, mock_join_completer_factory):
    with pytest.raises(NotQueryException):
        mock_join_completer_factory.get_completer('puyol.Student, puyol.University, a == 5', query=puyol.Country.get())


def test_get_completer_two_arguments_not_class(db, mock_join_completer_factory):
    with pytest.raises(NotQueryException):
        mock_join_completer_factory.get_completer('NotAClass, a == 5', query=puyol.Country.get())


@pytest.mark.parametrize('arguments, expected_class', [('puyol.Student, a == 5', CriterionJoinCompleter),
                                                       (' puyol.Student ,', CriterionJoinCompleter),
                                                       (' puyol.Student', ClassJoinCompleter),
                                                       (' puyol.Student', ClassJoinCompleter),
                                                       (' puyol.Student.a', RelationshipJoinCompleter),
                                                       ('puyol.Stu', ClassJoinCompleter),
                                                       ('puyol.Cou', RelationshipJoinCompleter),
                                                       ('puyol.cou', RelationshipJoinCompleter),
                                                       ('puy', RelationshipJoinCompleter),
                                                       ('puyol.', RelationshipJoinCompleter)])
def test_get_completer(db, mock_join_completer_factory, arguments, expected_class):
    assert mock_join_completer_factory.get_completer(arguments, query=puyol.Country.get()).__class__ == expected_class