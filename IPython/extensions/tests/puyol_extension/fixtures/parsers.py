import copy
import mock
import pytest
from IPython.extensions.puyol_extension.completer_factory import PuyolLikeGetCompleterFactory
from IPython.extensions.puyol_extension.criterion_completer import AbstractCriterionCompleter, PuyolLikeQueryAnalyzer
import puyol

__author__ = 'USER'


class MockCriterionCompleter(AbstractCriterionCompleter):
    def get_query_analyzer(self):
        return PuyolLikeQueryAnalyzer(self.query)


@pytest.fixture
def criterion_completer():
    namespace = globals()
    namespace = copy.copy(namespace)
    namespace.update(locals())
    return MockCriterionCompleter(module=puyol, namespace=namespace, query=mock.Mock(), argument=None)


@pytest.fixture
def criterion_completer_with_direct_import():
    from puyol import Country

    namespace = globals()
    namespace = copy.copy(namespace)
    namespace.update(locals())
    return MockCriterionCompleter(module=puyol, namespace=namespace, query=mock.Mock(), argument=None)