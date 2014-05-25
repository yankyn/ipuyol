import pytest
from ipuyol.orm_extension_base.utils import NotQueryException
from ipuyol.puyol_extension.join_completer import RelationshipJoinCompleter, ClassJoinCompleter, CriterionJoinCompleter
import puyol
from puyol_tests.fixtures.db_fixtures import db
from fixtures.utils import namespace_with_direct_import

__author__ = 'Nathaniel'

puyol.connect()


@pytest.mark.parametrize('argument, query, cls, expected',
                         [('', puyol.Country.get(), puyol.Country, ['puyol.Country.universities']),
                          ('hello', puyol.Country.get(), puyol.Country, []),
                          ('uni', puyol.Country.get(), puyol.Country, ['puyol.Country.universities']),
                          ('', puyol.Country.get().join(puyol.Country.universities), puyol.Country,
                           []),
                          ('', puyol.Country.get().join(puyol.Country.universities), puyol.University,
                           ['puyol.University.courses']),
                          ('puyol.Coun', puyol.Country.get(), puyol.Country,
                           ['puyol.Country.universities'])])
def test_relationship_join_completer(db, argument, query, cls, expected):
    completer = RelationshipJoinCompleter(argument=argument, query=query, cls=cls, module=puyol)
    assert set(completer.suggest()) == set(expected)
    assert len(completer.suggest()) == len(expected)


@pytest.mark.parametrize('query, cls', [(puyol.Country.get(), puyol.University)])
def test_relationship_join_completer_exceptions(db, query, cls):
    with pytest.raises(NotQueryException):
        RelationshipJoinCompleter(argument='', query=query, cls=cls, module=puyol).suggest()


@pytest.mark.parametrize('argument, query, expected',
                         [('', puyol.Country.get(), ['puyol.University']),
                          ('hello', puyol.Country.get(), []),
                          ('uni', puyol.Country.get(), ['puyol.University']),
                          ('', puyol.Country.get().join(puyol.Country.universities),
                           ['puyol.Course'])])
def test_class_join_completer(argument, query, expected):
    completer = ClassJoinCompleter(argument=argument, query=query, base_meta_class=puyol.orm.orm.Base.__class__,
                                   module=puyol)
    assert set(completer.suggest()) == set(expected)
    assert len(completer.suggest()) == len(expected)


@pytest.mark.parametrize('argument, cls, query, expected',
                         [('puyol.University.country_id == ', puyol.University, puyol.Country.get(),
                           ['puyol.Country.id']),
                          ('puyol.University.country_id == a', puyol.University, puyol.Country.get(),
                           []),
                          ('puyol.University.country_id == puyol.Country', puyol.University, puyol.Country.get(),
                           ['puyol.Country.id']),
                          ('puyol.University.country_id == ', puyol.Country, puyol.University.get(),
                           ['puyol.Country.id']),
                          ('puyol.University.country_id == a', puyol.Country, puyol.University.get(),
                           []),
                          ('puyol.University.country_id == puyol.Country', puyol.Country, puyol.University.get(),
                           ['puyol.Country.id']),
                          ('puyol.Country.id == ', puyol.Country, puyol.University.get(),
                           ['puyol.University.country_id']),
                          ('puyol.Country.id == a', puyol.Country, puyol.University.get(),
                           []),
                          ('puyol.Country.id == puyol.Uni', puyol.Country, puyol.University.get(),
                           ['puyol.University.country_id']),
                          ('puyol.Country.id == ', puyol.University, puyol.Country.get(),
                           ['puyol.University.country_id']),
                          ('puyol.Country.id == a', puyol.University, puyol.Country.get(),
                           []),
                          ('puyol.Country.id == puy', puyol.University, puyol.Country.get(),
                           ['puyol.University.country_id'])])
def test_criterion_join_completer_right(argument, cls, query, expected, namespace_with_direct_import):
    completer = CriterionJoinCompleter(argument=argument, query=query, cls=cls, module=puyol,
                                       namespace=namespace_with_direct_import)
    assert set(completer.suggest()) == set(expected)
    assert len(completer.suggest()) == len(expected)


@pytest.mark.parametrize('argument, cls, query',
                         [('bahhh == ', puyol.University, puyol.Country.get()),
                          ('puyol.Student.id == ', puyol.University, puyol.Country.get()),
                          ('puyol.University.name == ', puyol.University, puyol.Country.get())])
def test_criterion_join_completer_right_exception(argument, cls, query, namespace_with_direct_import):
    completer = CriterionJoinCompleter(argument=argument, query=query, cls=cls, module=puyol,
                                       namespace=namespace_with_direct_import)
    with pytest.raises(NotQueryException):
        completer.suggest()