import pytest
from IPython.extensions.orm_extension_base.utils import NotQueryException
from IPython.extensions.puyol_extension.completer_factory import PuyolLikeGetCompleterFactory
from puyol_tests.fixtures.db_fixtures import db
from fixtures.parsers import *
import puyol


__author__ = 'USER'


@pytest.mark.parametrize('property, expected_suggestions', [(puyol.Country.universities, ['any']),
                                                            (puyol.University.country, ['has']),
                                                            (puyol.Country.id, ['in_'])])
def test_suggest_mapped_property(criterion_completer, property, expected_suggestions):
    suggestions = criterion_completer._mapped_property_functions(property.property)
    assert len(suggestions) == len(expected_suggestions)
    assert set(suggestions) == set(expected_suggestions)


def test_suggest_mapped_property_fails(criterion_completer):
    with pytest.raises(NotQueryException):
        criterion_completer._mapped_property_functions('not a property')


@pytest.mark.parametrize('argument, expected_result',
                         [('puyol.Country.universities', puyol.Country.universities.property),
                          ('Country.universities', puyol.Country.universities.property),
                          ('puyol.University.id', puyol.University.id.property)])
def test_get_mapped_property(criterion_completer_with_direct_import, argument, expected_result):
    assert criterion_completer_with_direct_import.get_mapped_property(argument) == expected_result


@pytest.mark.parametrize('argument',
                         ['puyol.Country.no', 'Country.no', 'University.id', 'aaaaaa', 'Country.name_and_id'])
def test_get_mapped_property_none(criterion_completer_with_direct_import, argument):
    assert criterion_completer_with_direct_import.get_mapped_property(argument) is None


@pytest.mark.parametrize('argument, expected_result', [('.any(', 0),
                                                       ('id', 0),
                                                       ('puyol.Country.universities.', 2),
                                                       ('Country.universities.', 2),
                                                       ('University.id.', 0),
                                                       ('id=', 3),
                                                       ('id = ', 3)])
def test_suggest_criteria_flow(db, criterion_completer_with_direct_import, monkeypatch, argument, expected_result):
    monkeypatch.setattr(criterion_completer_with_direct_import, '_mapped_property_functions', lambda x: 2)
    monkeypatch.setattr(criterion_completer_with_direct_import, '_get_normal_suggestions', lambda x, y: 0)
    monkeypatch.setattr(criterion_completer_with_direct_import, 'get_criterion_suggestion_variants',
                        lambda x: 0)  # So we ignore variant addition.
    monkeypatch.setattr(criterion_completer_with_direct_import, '_map_suggestions_to_initial_kwarg',
                        lambda x: 3)
    criterion_completer_with_direct_import.query = puyol.Country.get()
    criterion_completer_with_direct_import.argument = argument
    assert criterion_completer_with_direct_import.suggest_criteria() == expected_result


@pytest.mark.parametrize('from_clause, suggestions, argument',
                         [([puyol.Country], ['puyol.Country.id', 'puyol.Country.name', 'puyol.Country.universities'],
                           ''),
                          ([puyol.Country, puyol.University],
                           ['puyol.Country.id', 'puyol.Country.name', 'puyol.Country.universities',
                            'puyol.University.country', 'puyol.University.country_id', 'puyol.University.courses',
                            'puyol.University.id', 'puyol.University.name'],
                           ''),
                          ([puyol.Country], ['puyol.Country.name'],
                           'name'),
                          ([puyol.Country, puyol.University],
                           ['puyol.Country.id', 'puyol.University.country_id',
                            'puyol.University.id'],
                           'id')])
def test_default_criterion_suggestions(criterion_completer, from_clause, suggestions, argument):
    assert set(criterion_completer._get_normal_suggestions(from_clause, argument)) == set(suggestions)
    assert len(criterion_completer._get_normal_suggestions(from_clause, argument)) == len(suggestions)


@pytest.mark.parametrize('from_clause, suggestions, argument',
                         [([puyol.Country], ['puyol.Country.id == '], 'id = '),
                          ([puyol.Country, puyol.University],
                           ['puyol.Country.id == ', 'puyol.University.country_id == ', 'puyol.University.id == ', ],
                           'id='),
                          ([puyol.Country], ['puyol.Country.name == '],
                           'name')])
def test_suggest_criterion_for_kwarg(criterion_completer, from_clause, suggestions, argument):
    criterion_completer.argument = argument
    assert set(criterion_completer._suggest_criteria_for_kwarg(from_clause)) == set(suggestions)
    assert len(criterion_completer._suggest_criteria_for_kwarg(from_clause)) == len(suggestions)