import pytest
from IPython.extensions.orm_extension_base.utils import NotQueryException
import puyol
from IPython.extensions.puyol_extension.join_completer import RelationshipJoinCompleter, ClassJoinCompleter

__author__ = 'Nathaniel'

puyol.connect()


@pytest.mark.parametrize('argument, query, cls, expected',
                         [('', puyol.Country.get(), puyol.Country, ['universities']),
                          ('hello', puyol.Country.get(), puyol.Country, []),
                          ('uni', puyol.Country.get(), puyol.Country, ['universities']),
                          ('', puyol.Country.get().join(puyol.Country.universities), puyol.Country,
                           []),
                          ('', puyol.Country.get().join(puyol.Country.universities), puyol.University,
                           ['courses'])])
def test_relationship_join_completer(argument, query, cls, expected):
    completer = RelationshipJoinCompleter(argument=argument, query=query, cls=cls)
    assert set(completer.suggest()) == set(expected)
    assert len(completer.suggest()) == len(expected)


@pytest.mark.parametrize('query, cls', [(puyol.Country.get(), puyol.University)])
def test_relationship_join_completer_exceptions(query, cls):
    with pytest.raises(NotQueryException):
        RelationshipJoinCompleter(argument='', query=query, cls=cls).suggest()


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