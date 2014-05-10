import copy
import types
from IPython.extensions.orm_extension_base.utils import NotQueryException
from IPython.extensions.puyol_extension.query_completer import PuyolLikeQueryCompleter
import puyol

__author__ = 'Nathaniel'

original_merge_completions = None


def puyol_matches(self, text):
    full_text = self.text_until_cursor
    namespace = copy.copy(self.namespace)
    namespace.update(self.global_namespace)
    completer = PuyolLikeQueryCompleter(module=puyol, namespace=namespace)
    try:
        return completer.suggest(full_text)
    except NotQueryException:
        return []


def load_ipython_extension(ip):
    global original_merge_completions
    print 'Puyol IPython extension is loaded!'
    ip.Completer.puyol_matches = types.MethodType(puyol_matches,
                                                  ip.Completer)  # We need to bind the new method to the completer.
    ip.Completer.matchers.insert(0, ip.Completer.puyol_matches)
    original_merge_completions = ip.Completer.merge_completions
    ip.Completer.merge_completions = False


def unload_ipython_extension(ip):
    global original_merge_completions
    ip.Completer.matchers.remove(ip.Completer.puyol_matches)
    ip.Completer.merge_completions = original_merge_completions
