import pytest
from IPython.extensions.puyol_extension.state_machine import QUERY, EVAL_FUNC, ARGUMENTS, EXPRESSION, PuyolLineParser

__author__ = 'USER'


def get_dict(line, result):
    return dict(line=line, expected_result=result)


LINES = [get_dict('a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)'
                  + '.refine(puyol.Course.university.has(puyol.university.countries.any(name=5, ',
                  {QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                   EVAL_FUNC: 'refine',
                   EXPRESSION: 'puyol.Course.university.has(puyol.university.countries.any',
                   ARGUMENTS: 'name=5, '}),
         get_dict('[a for a in func(puyol.Student.get(pedro.Student.something.has())).join(puyol.Student.courses)'
                  + '.refine(puyol.Course.university.has(puyol.university.countries.any(name=5, ',
                  {QUERY: 'func(puyol.Student.get(pedro.Student.something.has())).join(puyol.Student.courses)',
                   EVAL_FUNC: 'refine',
                   EXPRESSION: 'puyol.Course.university.has(puyol.university.countries.any',
                   ARGUMENTS: 'name=5, '}),
         get_dict(
             '[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses).refine(',
             {QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
              EVAL_FUNC: 'refine',
              EXPRESSION: '',
              ARGUMENTS: ''}),
         get_dict('[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                  {QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                   ARGUMENTS: ''}),
         get_dict('puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                  {QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                   ARGUMENTS: ''}),
         get_dict(
             '[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses).order_by(',
             {QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
              EVAL_FUNC: 'order_by',
              EXPRESSION: '',
              ARGUMENTS: ''}),
         get_dict(
             '[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)'
             + '.refine(puyol.Cource.university.has(puyol.university.name == "NAME"'
             + '  | puyol.university.countries.any(name=5, ',
             {QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
              EVAL_FUNC: 'refine',
              EXPRESSION: 'puyol.Cource.university.has(puyol.university.name == "NAME"'
                          + '  | puyol.university.countries.any',
              ARGUMENTS: 'name=5, '}),
         get_dict('[a for a in func(puyol.Student.get(pedro.Student.something.has()).refine(name="hello")',
                  {QUERY: 'puyol.Student.get(pedro.Student.something.has()).refine(name="hello")',
                   ARGUMENTS: ''}),
         get_dict('puyol.Student.get(pedro.Student.something.has())',
                  {QUERY: 'puyol.Student.get(pedro.Student.something.has())',
                   ARGUMENTS: ''}),
         get_dict('puyol.Student.get(pedro.Student.',
                  {QUERY: 'puyol.Student',
                   EVAL_FUNC: 'get',
                   EXPRESSION: '',
                   ARGUMENTS: 'pedro.Student.'}),
         get_dict('puyol.Student', {ARGUMENTS: 'puyol.Student'}),
         get_dict('puyol.Student.get(puyol.Student.university.has(name=',
                  {QUERY: 'puyol.Student',
                   EVAL_FUNC: 'get',
                   EXPRESSION: 'puyol.Student.university.has',
                   ARGUMENTS: 'name='}),
         get_dict('puyol.University.get(puyol.University.students.count() > ',
                  {QUERY: 'puyol.University',
                   EVAL_FUNC: 'get',
                   EXPRESSION: '',
                   ARGUMENTS: 'puyol.University.students.count() > '}),
         get_dict('puyol.University.get(puyol.University.students.count() > 5)'
                  + '.join(puyol.Student, puyol.Student.university_id == puyol.University.id)',
                  {QUERY: 'puyol.University.get(puyol.University.students.count() > 5)'
                          + '.join(puyol.Student, puyol.Student.university_id == puyol.University.id)',
                   ARGUMENTS: ''}),
         get_dict('puyol.Student.get(',
                  {QUERY: 'puyol.Student',
                   EVAL_FUNC: 'get',
                   EXPRESSION: '',
                   ARGUMENTS: ''}),
         get_dict('puyol.Student.get().',
                  {QUERY: 'puyol.Student.get()',
                   ARGUMENTS: '.'}),
         get_dict('puyol.Student.get().something',
                  {QUERY: 'puyol.Student.get()',
                   ARGUMENTS: '.something'}),
         ####### syntax errors ########
         # we don't want to raise exceptions here because it is much simpler to do so on evaluation
         get_dict('puyol.Student.get(any()',
                  {QUERY: 'puyol.Student',
                   EVAL_FUNC: 'get',
                   EXPRESSION: '',
                   ARGUMENTS: 'any()'}),
         get_dict('puyol.Student.get() == 5',
                  {QUERY: 'puyol.Student.get()',
                   ARGUMENTS: ' == 5'})]

EXCEPTION_LINES = ['puyol.Student.get(refine(']
'''
LINES = [get_dict('[a for a in func(puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                  {QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                   ARGUMENTS: ''})]'''


@pytest.fixture
def parser():
    return PuyolLineParser()


@pytest.fixture(params=range(len(LINES)))
def line(request):
    return LINES[request.param]


@pytest.fixture(params=range(len(EXCEPTION_LINES)))
def exception_line(request):
    return EXCEPTION_LINES[request.param]


def test_simple_parsing(parser, line):
    parser.parse_line(line.get('line'))
    assert parser.all_states
    assert parser.get_result() == line.get('expected_result')


def test_exception_parsing(parser, exception_line):
    with pytest.raises(Exception):
        parser.parse_line(exception_line)

