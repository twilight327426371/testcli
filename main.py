from __future__ import unicode_literals
import re
import sys
import os
import sqlite3
import subprocess
import logging
import click
import traceback

from prompt_toolkit import prompt, AbortAction
from prompt_toolkit.history import FileHistory
from pygments.lexers import SqlLexer
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .sdscompleter import SDSCompleter
from .colors import red
from .sdscmd import Sds
from .key_bindings import mycli_bindings
from .clistyle import DocumentStyle


_logger = logging.getLogger(__name__)

def initalize_logging():
    handler = logging.FileHandler('test.log')
    formatter = logging.Formatter(
        '%(asctime)s %(name)s [line:%(lineno)d] %(levelname)s - %(message)s')
    handler.setFormatter(formatter)    
    root_logger = logging.getLogger('testcli')
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    #logging.captureWarnings(True)
    root_logger.info('initializing test logging!')

class Cli(object):
    @classmethod
    def register(cls, cmd_class):
        cmd = cmd_class()
        for attr in dir(cmd):
            m = getattr(cmd, attr)
            if callable(m):
                setattr(cls, attr, m)

Cli.register(Sds)
sds_completer = SDSCompleter(ignore_case=True)
history = FileHistory(os.path.expanduser('~/.sdscli-history'))
auto = AutoSuggestFromHistory()
key_binding_manager = mycli_bindings()

def main(database):
    def _deal_text(text):
        lst = re.split(r'\s+', text)
        if lst[-1]:
            return "_".join(lst)
        else:
            return "_".join(lst[0:-1])
    initalize_logging()
    connection = sqlite3.connect(database)
    click.secho(" ________    ______     ______     __         __    ", fg="red")
    click.secho("/\ \___\ \  /\ \_\ \   /\  ___\   /\ \       /\ \   ", fg="yellow")
    click.secho("\ \ \___\ \ \ \_\___\  \ \ \____  \ \ \____  \ \ \  ", fg="green")
    click.secho(" \ \_____\ \ \ \_\      \ \_____\  \ \_____\  \ \_\ ", fg="blue")
    click.secho("  \/_____/_/  \/__\      \/_____/   \/_____/   \/_/ ", fg="magenta")
    while True:
        try:
            text = prompt('> ', lexer=SqlLexer, completer=sds_completer,
                          style=DocumentStyle, history=history, auto_suggest=auto,
                          key_bindings_registry=key_binding_manager.registry,
                          on_abort=AbortAction.RETRY)
        except EOFError:
            break  # Control-D pressed.
        except Exception as e:
            _logger.error("traceback: %r", traceback.format_exc())
        text = _deal_text(text)
        if not text:
            pass
        elif text in dir(Cli):
            m = getattr(Cli, text)
            print m()
        else:
            print(red("not support the cmd"))
    print('GoodBye!')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]
    main(db)

