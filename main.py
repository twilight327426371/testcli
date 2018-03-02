from __future__ import unicode_literals
import re
import sys
import os
import sqlite3
import subprocess
import logging
import click
import traceback
from collections import deque

from prompt_toolkit import prompt, AbortAction
from prompt_toolkit.history import FileHistory
from pygments.lexers import SqlLexer
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .sdscompleter import SDSCompleter
from .colors import red
from .sdscmd import Sds
from .key_bindings import mycli_bindings
from .clistyle import DocumentStyle
from .sdslexers import SdsLexer


_logger = logging.getLogger(__name__)
debug = False

def initalize_logging():
    handler = logging.FileHandler('test.log')
    formatter = logging.Formatter(
        '%(asctime)s %(name)s [line:%(lineno)d] %(levelname)s - %(message)s')
    handler.setFormatter(formatter)    
    root_logger = logging.getLogger('testcli')
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    root_logger.info('initializing test logging!')

def echo_usp():
    click.secho(" _   _ ___ _ __  " , fg="red")
    click.secho("| | | / __| '_ \ " , fg="yellow")
    click.secho("| |_| \__ \ |_) |" , fg="green")
    click.secho(" \__,_|___/ .__/ " , fg="blue")
    click.secho("          |_|    " , fg="magenta")

def echo_mos():
    click.secho(" _ __ ___   ___  ___  " , fg="red")
    click.secho("| '_ ` _ \ / _ \/ __| " , fg="yellow")
    click.secho("| | | | | | (_) \__ \ " , fg="green")
    click.secho("|_| |_| |_|\___/|___/ " , fg="blue")

class Cli(object):
    attrs = []
    @classmethod
    def register(cls, cmd_class):
        cmd = cmd_class()
        for attr in dir(cmd):
            m = getattr(cmd, attr)
            if callable(m):
                if not attr.startswith('__'):
                    cls.attrs.append(attr)
                    setattr(cls, attr, m)
    @staticmethod
    def parse_text(text):
        # bug fixed : "osd df" with some space, 
        # then get_methods return "osd_df" [" "]
        def get_methods(queue, ms=[]):
            _logger.info(queue)
            if queue:
                a = queue.popleft()
                ms.append(a)
                method = "_".join(ms)
                if method in Cli.attrs: 
                    _logger.info(method)
                    return method, list(queue)
                else: return get_methods(queue) 
            # bug fixed : the string method not in Cli.attrs
            else: return None, None
        _logger.info(red(text))
        infos = [ i for i in re.split("\s+", text) if i]
        _logger.info(infos)
        if infos:
            queues = deque(infos)
            return get_methods(queues)
        # bug fixed : some space can call traceback
        else: return None, None

    @classmethod 
    def enable_debug(cls):
        global debug
        debug = True

Cli.register(Sds)
sds_completer = SDSCompleter(ignore_case=True)
history = FileHistory(os.path.expanduser('~/.sdscli-history'))
auto = AutoSuggestFromHistory()
key_binding_manager = mycli_bindings()

def main(database):
    #def _deal_text(text):
    #    lst = re.split(r'\s+', text)
    #    if lst[-1]: return "_".join(lst)
    #    else: return "_".join(lst[0:-1])
    initalize_logging()
    echo_usp()
    echo_mos()
    while True:
        try:
            text = prompt('> ', lexer=SdsLexer, completer=sds_completer,
                          style=DocumentStyle, history=history, 
                          auto_suggest=auto, key_bindings_registry=key_binding_manager.registry,
                          on_abort=AbortAction.RETRY)
        except EOFError:
            break  # Control-D pressed.
        except Exception as e:
            raise e
            _logger.error("traceback: %r", traceback.format_exc())
        _logger.info(red(text))
        method, paras = Cli.parse_text(text)
        if method:
            try:
                m = getattr(Cli, method)
                print m(*paras)
            except Exception as e:
                print e.message

        elif method is None: pass
        else: print(red("not support the cmd"))
    print('GoodBye!')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]
    main(db)
    #print Cli.aitext("osd tree asdsgsds")

