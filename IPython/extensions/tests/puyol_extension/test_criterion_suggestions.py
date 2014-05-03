import pytest
from IPython.extensions.orm_extension.orm_line_parser import NotQueryException
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


def test_suggest_mapped_property_fails(get_completer):
    with pytest.raises(NotQueryException):
        get_completer.suggest_mapped_property('not a property')