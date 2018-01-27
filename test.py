from __future__ import unicode_literals
import re
import sys
import sqlite3

from prompt_toolkit import prompt, AbortAction
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit import CommandLineInterface
from pygments.lexers import SqlLexer
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle
from prompt_toolkit.completion import Completer, Completion
import subprocess
import logging
import click
from .new_sdscompleter import SDSCompleter
from .colors import red
import traceback
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.manager import KeyBindingManager
from .sdscmd import Sds

_logger = logging.getLogger(__name__)

class DocumentStyle(Style):
    styles = {
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton: 'bg:#003333',
        Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    }
    styles.update(DefaultStyle.styles)


def mycli_bindings():

    key_binding_manager = KeyBindingManager(
        enable_open_in_editor=True,
        enable_system_bindings=True,
        enable_auto_suggest_bindings=True,
        enable_search=True,
        enable_abort_and_exit_bindings=True)

    @key_binding_manager.registry.add_binding(Keys.Tab)
    def _(event):
        """
        Force autocompletion at cursor.
        """
        #print('Detected <Tab> key.')
        b = event.cli.current_buffer
        #print b.complete_state
        if b.complete_state:
            b.complete_next()
        else:
            event.cli.start_completion(select_first=True)
    return key_binding_manager



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
print type(Cli.osd_df)
#sql_completer = SDSCompleter(["osd","bcache_quote",'create', 'select', 'insert', 'drop',
#                               'delete', 'from', 'where', 'table','megacli'], ignore_case=True, )
sds_completer = SDSCompleter(ignore_case=True)

def main(database):
    initalize_logging()
    _logger.info("test")
    history = InMemoryHistory()
    connection = sqlite3.connect(database)
    key_binding_manager = mycli_bindings()
    click.secho(" ________    ______     ______     __         __    ", fg="red")
    click.secho("/\ \___\ \  /\ \_\ \   /\  ___\   /\ \       /\ \   ", fg="yellow")
    click.secho("\ \ \___\ \ \ \_\___\  \ \ \____  \ \ \____  \ \ \  ", fg="green")
    click.secho(" \ \_____\ \ \ \_\      \ \_____\  \ \_____\  \ \_\ ", fg="blue")
    click.secho("  \/_____/_/  \/__\      \/_____/   \/_____/   \/_/ ", fg="magenta")
    while True:
        try:
            text = prompt('> ', lexer=SqlLexer, completer=sds_completer,
                          style=DocumentStyle, history=history,
                          key_bindings_registry=key_binding_manager.registry,
                          on_abort=AbortAction.RETRY)
        except EOFError:
            break  # Control-D pressed.
        except Exception as e:
            _logger.error("traceback: %r", traceback.format_exc())

        text = re.sub(" ", "_", text)
        if text in dir(Cli):
            m = getattr(Cli, text)
            print m()
        else:
            print(red("not support the cmd"))
        #if text.startswith('bcache'):
        #    print "bcache"
        #elif text.startswith('osd_df'):
        #    print "osd df"
        #else:
        #    print run(text)
        #with connection:
        #    messages = connection.execute(text)
        #    for message in messages:
        #        print(message)
    print('GoodBye!')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]
    print db
    main(db)

