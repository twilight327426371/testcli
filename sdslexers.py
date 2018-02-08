from pygments.lexers.python import PythonLexer
from pygments.token import Name, Keyword


__all__ = ( "SdsLexer")
class SdsLexer(PythonLexer):
    EXTRA_KEYWORDS = set(('foo', 'bar', 'foobar', 'barfoo', 'spam', 'eggs', "osd"))

    def get_tokens_unprocessed(self, text):
        for index, token, value in PythonLexer.get_tokens_unprocessed(self, text):
            if token is Name and value in self.EXTRA_KEYWORDS:
                yield index, Keyword.Pseudo, value
            else:
                yield index, token, value