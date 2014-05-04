import pytest
from IPython.extensions.orm_extension.orm_completer import OrmFunctionCompleter
from IPython.extensions.tests.orm_extension import mock_module

__author__ = 'USER'


@pytest.fixture
def mock_completer():
    class MockOrmFunctionCompleter(OrmFunctionCompleter):
        def get_binary_expression_mock(self):
            return 'mock!'

        def get_criterion_functions(self):
            return ['any', 'has']

    return MockOrmFunctionCompleter(module=mock_module, namespace={})


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
                            'b=5, c=)'], set([0]))])
def test_open_criterion_call_indices(calls, expected_indices):
    indices = OrmFunctionCompleter.open_criterion_call_indices(calls)
    assert indices == expected_indices


LINES = [
    dict(
        line='a==5, puyol.Country.universities.any(puyol.University.courses.any(puyol.Country.somethings.any(b=5, c=)',
        argument='puyol.Country.universities.any(puyol.University.courses.any(puyol.Country.somethings.any(b=5, c=)'),
    dict(
        line='a==5, puyol.Country.u.any(), puyol.University.courses.any(puyol.Country.somethings.any(b=5, c=)',
        argument='puyol.Country.u.any(), puyol.University.courses.any(puyol.Country.somethings.any(b=5, c=)'),
    dict(
        line='a==5, puyol.Country.u.any(), puyol.University.courses.any(), puyol.Country.somethings.any(b=5, c=)',
        argument='mock!'),
    dict(
        line='a==5, puyol.Country.u.any(), puyol.University.courses.any(), puyol.Country.somethings.any(b=5, c=), a',
        argument='a')]


@pytest.mark.parametrize('line, expected_argument, open_indices',
                         [(LINES[0]['line'], LINES[0]['argument'], {0, 1}),
                          (LINES[1]['line'], LINES[1]['argument'], {1}),
                          (LINES[2]['line'], LINES[2]['argument'], {}),
                          (LINES[3]['line'], LINES[3]['argument'], {})])
def test_get_last_argument(mock_completer, monkeypatch, line, expected_argument, open_indices):
    monkeypatch.setattr(mock_completer, 'open_criterion_call_indices', lambda x: open_indices)
    assert mock_completer.argument_to_complete(line) == expected_argument