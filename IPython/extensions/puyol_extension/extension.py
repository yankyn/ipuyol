import types
from IPython.core.completer import IPCompleter

__author__ = 'Nathaniel'


def puyol_matches(self, text):
    pass


def load_ipython_extension(ip):
    ip.Completer.puyol_matches = types.MethodType(puyol_matches,
                                                  ip.Completer)  # We need to bind the new method to the completer.
    ip.Completer.matchers.append(ip.Completer.puyol_matches)