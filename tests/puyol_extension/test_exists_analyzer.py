import copy
import mock
import pytest
from IPython.extensions.orm_extension_base.utils import NotQueryException
from IPython.extensions.puyol_extension.query_analyzer import PuyolLikeQueryAnalyzer
import puyol
from fixtures.utils import namespace_with_direct_import
from IPython.extensions.puyol_extension.criterion_completer import PuyolLikeExistsCriteriaAnalyzer

__author__ = 'Nathaniel'


@pytest.fixture
def analyzer():
    namespace = globals()
    namespace = copy.copy(namespace)
    namespace.update(locals())
    return PuyolLikeExistsCriteriaAnalyzer(module=puyol, namespace=namespace, open_calls=[], query=None)


@pytest.mark.parametrize('call, string', [('a==5, puyol.Country.universities', 'puyol.Country.universities'),
                                          ('foo(), puyol.University.courses', 'puyol.University.courses'),
                                          ('Puyol.University.country==x, puyol.University.courses',
                                           'puyol.University.courses'),
                                          ('a==5, Country.universities', 'Country.universities'),
                                          ('foo(), University.courses', 'University.courses'),
                                          ('University.country==x, University.courses',
                                           'University.courses'),
                                          ('puyol.Country', 'puyol.Country')])
def test_get_property_string_from_call_full(analyzer, call, string):
    assert analyzer.get_property_string_from_call(call) == string


@pytest.mark.parametrize('call', ['a==5, puyol.Country.universities, a==3'])
def test_get_property_string_from_call_no_query(analyzer, call):
    with pytest.raises(NotQueryException):
        analyzer.get_property_string_from_call(call)


@pytest.mark.parametrize('string, expected', [('puyol.Country.universities', puyol.University),
                                              ('puyol.University.courses', puyol.Course)])
def test_get_property_from_property_string_regular(analyzer, string, expected):
    prop = analyzer.get_property_from_property_string(string)
    assert prop == expected


@pytest.mark.parametrize('string, expected', [('Country.universities', puyol.University)])
def test_get_property_from_property_string_direct(analyzer, namespace_with_direct_import, string, expected):
    analyzer.namespace = namespace_with_direct_import
    prop = analyzer.get_property_from_property_string(string)
    assert prop == expected


@pytest.mark.parametrize('string', ['Country.universities', 'w00t', 'puyol.NoTable.no_column'])
def test_get_property_from_property_no_eval(analyzer, string):
    with pytest.raises(NotQueryException):
        analyzer.get_property_from_property_string(string)


@pytest.mark.parametrize('string', ['puyol.Country.foo', 'puyol.Country.id'])
def test_get_property_from_property_no_property(analyzer, string):
    with pytest.raises(NotQueryException):
        analyzer.get_property_from_property_string(string)


@pytest.mark.parametrize('calls, join', [(['a==5, puyol.Country.universities'], [puyol.University]),
                                         (['a==5, puyol.Country.universities', 'puyol.University.courses'],
                                          [puyol.University, puyol.Course])])
def test_join_clause(analyzer, calls, join, monkeypatch):
    monkeypatch.setattr(PuyolLikeQueryAnalyzer, 'get_from_clause', lambda self: [puyol.Student])
    query = mock.Mock()
    analyzer.open_calls = calls
    analyzer.query = query
    assert set(analyzer.get_from_clause()) == set(join + [puyol.Student])