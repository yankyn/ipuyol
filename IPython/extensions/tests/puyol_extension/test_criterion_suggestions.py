import pytest
from fixtures.parsers import get_completer
import puyol


__author__ = 'USER'


@pytest.mark.parametrize('property, expected_suggestions', [(puyol.Country.universities, ['any']),
                                                            (puyol.University.country, ['has']),
                                                            (puyol.Country.id, ['in_'])])
def test_suggest_mapped_property(get_completer, property, expected_suggestions):
    suggestions = get_completer.suggest_mapped_property(property.property)
    assert len(suggestions) == len(expected_suggestions)
    assert set(suggestions) == set(expected_suggestions)