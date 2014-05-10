import copy
import pytest
from IPython.extensions.orm_extension_base.utils import NotQueryException
import puyol
from puyol_tests.fixtures.db_fixtures import db
from IPython import get_ipython
from IPython.extensions.puyol_extension.query_completer import PuyolLikeQueryCompleter

__author__ = 'Nathaniel'


@pytest.mark.parametrize('line, expected_results', [
    # Simple Queries
    ('puyol.Country.get(', ['puyol.Country.name', 'puyol.Country.id', 'puyol.Country.universities']),
    ('puyol.University.get(',
     ['puyol.University.id', 'puyol.University.name', 'puyol.University.country', 'puyol.University.country_id',
      'puyol.University.courses']),
    ('puyol.Country.get(na', ['puyol.Country.name']),
    ('puyol.Country.get(name="test", ', ['id=', 'name=']),
    ('puyol.University.get(name="test", ', ['id=', 'name=', 'country_id=', 'country=']),
    ('puyol.University.get(name="test", cou', ['country_id=', 'country=']),
    ('puyol.University.get(puyol.Country.name == "test"', [' & (', ' | (']),
    ('puyol.University.get((puyol.Country.name == "test") | (puyol.Country.id == 5)', [' & (', ' | (']),
    ('puyol.University.get(puyol.Country.name == "test" | puyol.Country.id == 5', []),
    ('puyol.University.get(puyol.University.country.', ['puyol.University.country.has(']),
    ('puyol.Country.get(puyol.Country.universities.', ['puyol.Country.universities.any(']),
    ('puyol.University.get(puyol.University.id.',
     ['puyol.University.id.in_(', 'puyol.University.id.like(', 'puyol.University.id.ilike(']),
    ('puyol.University.get(puyol.University.id == 5, puyol.University.country.', ['puyol.University.country.has(']),
    ('puyol.University.get(puyol.University.id',
     ['puyol.University.id == ', 'puyol.University.id != ', 'puyol.University.id >= ', 'puyol.University.id > ']),
    ('puyol.University.get(puyol.University.id  ', ['== ', '!= ', '>= ', '> ']),
    # Join queries
    ('puyol.Country.get().join(puyol.Country.universities).refine(na',
     ['puyol.Country.name', 'puyol.University.name']),
    ('puyol.Country.get().join(puyol.Country.universities).refine(',
     ['puyol.Country.name', 'puyol.Country.id', 'puyol.Country.universities', 'puyol.University.id',
      'puyol.University.name', 'puyol.University.country', 'puyol.University.country_id',
      'puyol.University.courses']),
    ('puyol.Country.get().join(puyol.Country.universities).refine(name="test", ',
     ['name=', 'id=', 'country=', 'country_id=']),
    # Exists queries
    ('puyol.Country.get(puyol.Country.universities.any(',
     ['puyol.Country.name', 'puyol.Country.id', 'puyol.Country.universities', 'puyol.University.id',
      'puyol.University.name', 'puyol.University.country', 'puyol.University.country_id',
      'puyol.University.courses']),
    ('puyol.Country.get(puyol.Country.universities.any(na',
     ['puyol.Country.name', 'puyol.University.name']),
    ('puyol.Country.get(puyol.Country.id == 5, puyol.Country.universities.any(na',
     ['puyol.Country.name', 'puyol.University.name']),
    ('puyol.Country.get(puyol.Country.id == 5 | puyol.Country.universities.any(na',
     ['puyol.Country.name', 'puyol.University.name']),
    ('puyol.Country.get(puyol.Country.id == 5 | puyol.Country.universities.any(), na',
     ['puyol.Country.name']),
    ('puyol.Country.get(puyol.Country.id == 5 | puyol.Country.universities.any(puyol.University.courses.any(na',
     ['puyol.Country.name', 'puyol.University.name', 'puyol.Course.name']),
    ('puyol.Country.get(puyol.Country.id == 5 | puyol.Country.universities.any(puyol.University.courses.any(), na',
     ['puyol.Country.name', 'puyol.University.name']),
    ('puyol.University.get(puyol.Country.universities.any()', [' & (', ' | (']),
    # Mixed queries
    ('puyol.Country.get().join(puyol.Country.universities).refine(puyol.University.courses.any(',
     ['puyol.Country.name', 'puyol.Country.id', 'puyol.Country.universities', 'puyol.University.id',
      'puyol.University.name', 'puyol.University.country', 'puyol.University.country_id',
      'puyol.University.courses', 'puyol.Course.name', 'puyol.Course.id', 'puyol.Course.university_id',
      'puyol.Course.university']),
    ('puyol.Country.get().join(puyol.Country.universities).refine(puyol.University.courses.any(), na',
     ['puyol.Country.name', 'puyol.University.name']),
])
def test_completion_queries(db, line, expected_results):
    namespace = copy.copy(locals())
    namespace.update(globals())
    completer = PuyolLikeQueryCompleter(module=puyol, namespace=namespace)
    results = completer.suggest(line)
    assert set(results) == set(expected_results)
    assert len(results) == len(expected_results)


@pytest.mark.parametrize('line',
                         ['puyol.University.get(puyol.University.name == "test", name=', 'puyol.University.get(name=',
                          'sgasfgasf', 'puyol.Country.get(some_shit.any(', 'puyol.Country.get(puyol.Random.shit.any(',
                          'puyol.Country.get(puyol.Country.foo.any(', 'puyol.Country.get(puyol.Country.foo.'])
def test_completion_not_queries(db, line):
    namespace = copy.copy(locals())
    namespace.update(globals())
    completer = PuyolLikeQueryCompleter(module=puyol, namespace=namespace)
    with pytest.raises(NotQueryException):
        completer.suggest(line)