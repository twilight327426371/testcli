import re
import sys
import logging
import subprocess

_logger = logging.getLogger(__name__)

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str
else:
    string_types = basestring
cleanup_regex = {
        # This matches only alphanumerics and underscores.
        'alphanum_underscore': re.compile(r'(\w+)$'),
        # This matches everything except spaces, parens, colon, and comma
        'many_punctuations': re.compile(r'([^():,\s]+)$'),
        # This matches everything except spaces, parens, colon, comma, and period
        'most_punctuations': re.compile(r'([^\.():,\s]+)$'),
        # This matches everything except a space.
        'all_punctuations': re.compile('([^\s]+)$'),
        }

def last_word(text, include='alphanum_underscore'):
    """
    Find the last word in a sentence.

    >>> last_word('abc')
    'abc'
    >>> last_word(' abc')
    'abc'
    >>> last_word('')
    ''
    >>> last_word(' ')
    ''
    >>> last_word('abc ')
    ''
    >>> last_word('abc def')
    'def'
    >>> last_word('abc def ')
    ''
    >>> last_word('abc def;')
    ''
    >>> last_word('bac $def')
    'def'
    >>> last_word('bac $def', include='most_punctuations')
    '$def'
    >>> last_word('bac \def', include='most_punctuations')
    '\\\\def'
    >>> last_word('bac \def;', include='most_punctuations')
    '\\\\def;'
    >>> last_word('bac::def', include='most_punctuations')
    'def'
    """

    if not text:   # Empty string
        return ''

    if text[-1].isspace():
        return ''
    else:
        regex = cleanup_regex[include]
        matches = regex.search(text)
        if matches:
            return matches.group(0)
        else:
            return ''

def run(cmd):
    err = None
    out = ''
    # out_file = open('cmd_output.txt', 'a')
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError, e:
        err = e.output
    #logging.info('cmd: ' + cmd)
    # print 'CMD: ' + cmd
    if err:
        _logger.error(err)
        return err
    else:
        return out

def suggest_type(full_text, text_before_cursor):
    """Takes the full_text that is typed so far and also the text before the
    cursor to suggest completion type and scope.

    Returns a tuple with a type of entity ('table', 'column' etc) and a scope.
    A scope for a column category will be a list of tables.
    """

    word_before_cursor = last_word(text_before_cursor,
            include='many_punctuations')
    identifier = None
    _logger.debug(word_before_cursor)

    # here should be removed once sqlparse has been fixed
    try:
        # If we've partially typed a word then word_before_cursor won't be an empty
        # string. In that case we want to remove the partially typed string before
        # sending it to the sqlparser. Otherwise the last token will always be the
        # partially typed string which renders the smart completion useless because
        # it will always return the list of keywords as completion.
        if word_before_cursor:
            last_token = last_word(text_before_cursor)
            # word_before_cursor may include a schema qualification, like
            # "schema_name.partial_name" or "schema_name.", so parse it
            # separately
        else:
            _logger.debug(len(word_before_cursor))
            words = text_before_cursor.split(" ")
            if len(words) > 1:
                last_token = text_before_cursor.split(" ")[-2]
            else:
                last_token = last_word(text_before_cursor[:-len(word_before_cursor)])
    except (TypeError, AttributeError):
        return [{'type': 'keyword'}]

    return suggest_based_on_last_token(last_token, text_before_cursor,
                                       full_text)

def suggest_based_on_last_token(token, text_before_cursor, full_text):
    _logger.debug(token)
    _logger.debug(text_before_cursor)
    _logger.debug(full_text)
    if isinstance(token, string_types):
        token_v = token.lower()
    else:
        token_v = token.value.lower()

    is_operand = lambda x: x and any([x.endswith(op) for op in ['+', '-', '*', '/']])

    if not token:
        return [{'type': 'keyword'}]
    elif token_v == 'osd':
        return [{'type': 'osd'}]
    elif token_v == ('megacli'):
        return [{'type': 'megacli'}]
    else:
        return [{'type': 'keyword'}]


def identifies(id, schema, table, alias):
    return id == alias or id == table or (
        schema and (id == schema + '.' + table))
