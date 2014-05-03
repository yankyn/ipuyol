import copy
import pytest
from IPython.extensions.puyol_extension.completer import PuyolLikeGetCompleter
import puyol

__author__ = 'USER'

@pytest.fixture
def get_completer():
    namespace = globals()
    namespace = copy.copy(namespace)
    namespace.update(locals())
    return PuyolLikeGetCompleter(module=puyol, namespace=namespace)