from IPython.extensions.puyol_extension.state_machine import QUERY

__author__ = 'Nathaniel'
import puyol


class PuyolQueryCompleter(object):

    def complete_statement(self, parsed_statement):
        query_text = parsed_statement.get(QUERY)
        query = eval(query_text)




        pass


'''{QUERY: 'puyol.Student.get(pedro.Student.something.has()).join(puyol.Student.courses)',
                   EVAL_FUNC: 'refine',
                   EXPRESSION: 'puyol.Course.university.has(puyol.university.countries.any',
                   ARGUMENTS: 'name=5, '})'''