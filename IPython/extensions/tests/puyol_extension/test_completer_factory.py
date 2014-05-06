import mock
import pytest
from IPython.extensions.puyol_extension.criterion_completer import QuerySimpleCriterionCompleter, ComplexCriterionCompleter, RedundantCriterionCompleter
from IPython.extensions.puyol_extension.completer_factory import PuyolLikeGetCompleterFactory
from IPython.extensions.tests.orm_extension import mock_module

__author__ = 'USER'


@pytest.fixture
def mock_completer_factory():
    return PuyolLikeGetCompleterFactory(module=mock_module, namespace={})


LINES = ['a==5, puyol.Country.universities.any(puyol.University.courses.any(puyol.Country.somethings.any(b=5, c=)',
         'a==5, puyol.Country.u.any(), puyol.University.courses.any(puyol.Country.somethings.any(b=5, c=)',
         'a==5, puyol.Country.u.any(), puyol.University.courses.any(), puyol.Country.somethings.any(b=5, c=)',
         'a==5, puyol.Country.u.any(), puyol.University.courses.any(), puyol.Country.somethings.any(b=5, c=), a',
         'a==5, a']


@pytest.mark.parametrize('calls, expected_indices',
                         [(['a==5, puyol.Country.universities', 'puyol.University.courses',
                            ')), puyol.Country.somethings', 'b=5, c='], set([2])),
                          (['a==5, puyol.Country.universities',
                            'puyol.University.courses',
                            ')), puyol.Country.somethings',
                            'b=5, c=)'], set([])),
                          (['a==5, puyol.Country.universities',
                            'puyol.University.courses',
                            '), puyol.Country.somethings',
                            'b=5, c=)'], set([0])),
                          (['a==5, puyol.Country.universities',
                            'foo(), puyol.University.courses',
                            'foo()), puyol.Country.somethings',
                            'foo(), b=5, c=)'], set([0]))])
def test_open_criterion_call_indices(calls, expected_indices):
    indices = PuyolLikeGetCompleterFactory.open_criterion_calls(calls)
    assert indices == expected_indices


@pytest.mark.parametrize('line, completer_type, open_indices',
                         [(LINES[0], ComplexCriterionCompleter, {0, 1}),
                          (LINES[1], ComplexCriterionCompleter, {1}),
                          (LINES[2], RedundantCriterionCompleter, {}),
                          (LINES[3], QuerySimpleCriterionCompleter, {}),
                          (LINES[4], QuerySimpleCriterionCompleter, {})])
def test_completer_factory_types(mock_completer_factory, monkeypatch, line, completer_type, open_indices):
    query = mock.Mock()
    monkeypatch.setattr(mock_completer_factory, 'open_criterion_call_indices', lambda x: open_indices)
    assert isinstance(mock_completer_factory.get_completer(line, query), completer_type)