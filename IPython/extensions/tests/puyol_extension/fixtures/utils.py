import copy
import pytest

__author__ = 'Nathaniel'


@pytest.fixture
def namespace_with_direct_import():
    from puyol import Country
    import puyol
    namespace = globals()
    namespace = copy.copy(namespace)
    namespace.update(locals())
    return namespace
