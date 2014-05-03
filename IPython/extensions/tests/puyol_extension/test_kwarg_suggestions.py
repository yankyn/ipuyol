import copy
import pytest
from IPython.core.magic_arguments import argument
from IPython.extensions.orm_extension.orm_line_parser import NotQueryException
from IPython.extensions.puyol_extension.completer import PuyolLikeGetCompleter
from puyol_tests.fixtures.db_fixtures import *

__author__ = 'USER'


@pytest.fixture
def get_completer():
    namespace = globals()
    namespace = copy.copy(namespace)
    namespace.update(locals())
    return PuyolLikeGetCompleter(module=puyol, namespace=namespace)


@pytest.mark.parametrize('query, arg, expected_suggestions', [('puyol.Country.get()', '', ['name=', 'id=']),
                                                              ('puyol.Country.get()', 'n', ['name=']),
                                                              ('puyol.Country.get().join(puyol.Country.universities)',
                                                               '', ['name=', 'id=', 'country=', 'country_id=']),
                                                              ('puyol.Country.get().join(puyol.Country.universities)',
                                                               'c', ['country=', 'country_id=']), ])
def test_suggest_kwarg(db, get_completer, query, arg, expected_suggestions):
    query = eval(query)
    suggestions = get_completer.suggest_kwarg(query, arg)
    assert len(suggestions) == len(expected_suggestions)
    assert set(suggestions) == set(expected_suggestions)


def test_kwarg_does_not_suggest_lists(db, get_completer):
    query = puyol.Country.get()
    argument = 'uni'
    suggestions = get_completer.suggest_kwarg(query, argument)
    assert not suggestions


def test_kwarg_query_is_not_puyol_query(db, get_completer):
    query = 'not a query'
    with pytest.raises(NotQueryException):
        get_completer.suggest_kwarg(query, '')
