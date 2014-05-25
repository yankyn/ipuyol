import pytest
from ipuyol.orm_extension_base.utils import NotQueryException
from puyol_tests.fixtures.db_fixtures import *
from fixtures.parsers import *

__author__ = 'USER'


@pytest.mark.parametrize('query, arg, expected_suggestions', [('puyol.Country.get()', '', ['name=', 'id=']),
                                                              ('puyol.Country.get()', 'n', ['name=']),
                                                              ('puyol.Country.get().join(puyol.Country.universities)',
                                                               '', ['name=', 'id=', 'country=', 'country_id=']),
                                                              ('puyol.Country.get().join(puyol.Country.universities)',
                                                               'c', ['country=', 'country_id=']), ])
def test_suggest_kwarg(db, criterion_completer, query, arg, expected_suggestions):
    query = eval(query)
    criterion_completer.query = query
    criterion_completer.argument = arg
    suggestions = criterion_completer.suggest_kwarg()
    assert len(suggestions) == len(expected_suggestions)
    assert set(suggestions) == set(expected_suggestions)


def test_kwarg_does_not_suggest_lists(db, criterion_completer):
    query = puyol.Country.get()
    criterion_completer.query = query
    criterion_completer.argument = 'uni'
    suggestions = criterion_completer.suggest_kwarg()
    assert not suggestions


def test_kwarg_query_is_not_puyol_query(db, criterion_completer):
    query = 'not a query'
    criterion_completer.query = query
    criterion_completer.argument = ''
    with pytest.raises(NotQueryException):
        criterion_completer.suggest_kwarg()
