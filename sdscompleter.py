from re import escape
from prompt_toolkit.completion import Completer, Completion
from utils import last_word


class SDSCompleter(Completer):

    @staticmethod
    def find_matches(text, collection, start_only=False, fuzzy=True, casing=None):
        """Find completion matches for the given text.

        Given the user's input text and a collection of available
        completions, find completions matching the last word of the
        text.

        If `start_only` is True, the text will match an available
        completion only at the beginning. Otherwise, a completion is
        considered a match if the text appears anywhere within it.

        yields prompt_toolkit Completion instances for any matches found
        in the collection of available completions.
        """
        last = last_word(text, include='most_punctuations')
        text = last.lower()

        completions = []

        if fuzzy:
            regex = '.*?'.join(map(escape, text))
            pat = compile('(%s)' % regex)
            for item in sorted(collection):
                r = pat.search(item.lower())
                if r:
                    completions.append((len(r.group()), r.start(), item))
        else:
            match_end_limit = len(text) if start_only else None
            for item in sorted(collection):
                match_point = item.lower().find(text, 0, match_end_limit)
                if match_point >= 0:
                    completions.append((len(text), match_point, item))

        if casing == 'auto':
            casing = 'lower' if last and last[-1].islower() else 'upper'

        def apply_case(kw):
            if casing == 'upper':
                return kw.upper()
            return kw.lower()

        return (Completion(z if casing is None else apply_case(z), -len(text))
                for x, y, z in sorted(completions))

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        completions = []
        if word_before_cursor.startswith("osd"):
            o = ["tree", "df", "test"]
            osds = self.find_matches(word_before_cursor,)
            completions.extend(osds)




