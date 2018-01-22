from re import escape
from prompt_toolkit.completion import Completer, Completion
from utils import last_word, suggest_type
from six import string_types
import logging


_logger = logging.getLogger(__name__)



class SDSCompleter(Completer):
    """
    Simple autocompletion on a list of words.
    :param words: List of words.
    :param ignore_case: If True, case-insensitive completion.
    :param meta_dict: Optional dict mapping words to their meta-information.
    :param WORD: When True, use WORD characters.
    :param sentence: When True, don't complete by comparing the word before the
        cursor, but by comparing all the text before the cursor. In this case,
        the list of words is just a list of strings, where each string can
        contain spaces. (Can not be used together with the WORD option.)
    :param match_middle: When True, match not only the start, but also in the
                         middle of the word.
    """
    osd     = ["df", "tree"]
    megacli = ["pdlist", "ldlist"]
    keyword = ["osd", "bcache_quote", 'create', 'select', 'insert', 'drop',
                'delete', 'from', 'where', 'table', "megacli"] 


    
    def __init__(self, words, ignore_case=False, meta_dict=None, WORD=False,
                 sentence=False, match_middle=False):
        assert not (WORD and sentence)
        self.words = list(words)
        self.ignore_case = ignore_case
        self.meta_dict = meta_dict or {}
        self.WORD = WORD
        self.sentence = sentence
        self.match_middle = match_middle
        assert all(isinstance(w, string_types) for w in self.words)
    
    @staticmethod
    def find_matches(text, collections):
        last = last_word(text, include='most_punctuations')
        text = last.lower()
        completions = []
        for item in sorted(collections):
            match_end_limit = len(text) 
            match_point = item.lower().find(text, 0, match_end_limit)
            if match_point >= 0:
                completions.append((len(text), match_point, item))
        return (Completion(z, -len(text)) for x, y, z in sorted(completions))

    def get_completions(self, document, complete_event):
        # Get word/text before cursor.
        if self.sentence:
            word_before_cursor = document.text_before_cursor
        else:
            word_before_cursor = document.get_word_before_cursor(WORD=self.WORD)

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()
        text = document.text_before_cursor
        #print "word_before_cursor:", word_before_cursor
        _logger.info(text)
        def word_matches(word):
            """ True when the word before the cursor matches. """
            if self.ignore_case:
                word = word.lower()

            if self.match_middle:
                return word_before_cursor in word
            else:
                return word.startswith(word_before_cursor)
        
        def not_support(word):
            """ True when word before the cursor not match in all words"""
            return any([ True for i in self.words if i.startswith(word)])
        
        
        _logger.debug(word_before_cursor)
        completions = []
        suggestions = suggest_type(document.text, document.text_before_cursor)
        for suggestion in suggestions:
            _logger.debug("Suggestion type: %r", suggestion["type"])
            if suggestion['type'] == "osd":
                osd_cli = self.find_matches(word_before_cursor, self.osd)
                completions.extend(osd_cli)
                _logger.debug(completions)
            if suggestion['type'] == "megacli":
                megaclis = self.find_matches(word_before_cursor, self.megacli)
                completions.extend(megaclis)
            if suggestion['type'] == "keyword":
                keywords = self.find_matches(word_before_cursor, self.keyword)
                completions.extend(keywords)
        return completions

        #if not_support(word_before_cursor):
            #if text.startswith("osd"):
                #return [Completion("df", -len(word_before_cursor) ), 
                        #Completion("tree", -len(word_before_cursor))]
            #if text.startswith("megacli"):
                #return [Completion("pdlist", -len(word_before_cursor) ), 
                        #Completion("ldlist", -len(word_before_cursor))]

            #lists = self.find_matches(word_before_cursor,self.words)
            #_logger.info(lists)
            #completions.extend(lists)
            #_logger.info(completions)
            #return completions
        #else:
            #_logger.info(word_before_cursor)
            #return completions
        