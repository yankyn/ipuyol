import pytest
from IPython.extensions.orm_extension.utils import NotQueryException
from fixtures.parsers import get_completer, get_completer_with_direct_import
from puyol_tests.fixtures.db_fixtures import db
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


@pytest.mark.parametrize('argument, expected_result',
                         [('puyol.Country.universities', puyol.Country.universities.property),
                          ('Country.universities', puyol.Country.universities.property),
                          ('puyol.University.id', puyol.University.id.property)])
def test_get_mapped_property(get_completer_with_direct_import, argument, expected_result):
    assert get_completer_with_direct_import.get_mapped_property(argument) == expected_result


@pytest.mark.parametrize('argument',
                         ['puyol.Country.no', 'Country.no', 'University.id', 'aaaaaa', 'Country.name_and_id'])
def test_get_mapped_property_none(get_completer_with_direct_import, argument):
    assert get_completer_with_direct_import.get_mapped_property(argument) is None


@pytest.mark.parametrize('argument, expected_result', [('puyol.Country.universities.any(', 1),
                                                       ('puyol.Country.universities.any(puyol.University.country.has(',
                                                        1),
                                                       ('.any(', 0),
                                                       ('id', 0),
                                                       ('puyol.Country.universities.', 2),
                                                       ('Country.universities.', 2),
                                                       ('University.id.', 0),
                                                       ('Country.id == 1', 3),
                                                       ('puyol.Country.id.in_([1])', 3)])
def test_suggest_criteria_flow(db, get_completer_with_direct_import, monkeypatch, argument, expected_result):
    monkeypatch.setattr(get_completer_with_direct_import, 'suggest_inner', lambda x, y: 1)
    monkeypatch.setattr(get_completer_with_direct_import, 'suggest_mapped_property', lambda x: 2)
    monkeypatch.setattr(get_completer_with_direct_import, 'suggest_logic_operator_for_mapped_property', lambda: 3)
    monkeypatch.setattr(get_completer_with_direct_import, '_get_normal_suggestions', lambda x, y: 0)
    assert get_completer_with_direct_import.suggest_criteria(puyol.Country.get(), argument) == expected_result
