from __future__ import unicode_literals
import sys
import sqlite3

from prompt_toolkit import prompt, AbortAction
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit import CommandLineInterface, Application
from pygments.lexers import SqlLexer
from pygments.style import Styl
from pygments.token import Token
from pygments.styles.default import DefaultStyle
from sdscompleter import SDSCompleter
import subprocess
import logging
import click

#sql_completer = WordCompleter(["osd_df","bcache_quote",'create', 'select', 'insert', 'drop',
#                               'delete', 'from', 'where', 'table'], ignore_case=True)


class DocumentStyle(Style):
    styles = {
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton: 'bg:#003333',
        Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    }
    styles.update(DefaultStyle.styles)

def run(cmd):
    err = None
    out = ''
    # out_file = open('cmd_output.txt', 'a')
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError, e:
        err = e.output
    logging.info('cmd: ' + cmd)
    # print 'CMD: ' + cmd
    if err:
        logging.error(err)
        return err
    else:
        return out

def bcache_quote():
    cmd = "cat /sys/fs/bcache/$(/opt/sandstone/sbin/sdscache_ctl -q \
    /dev/sdb2 | grep cset.uuid | awk '{print $2}')/cache0/priority_stats"
    return run(cmd)

def osd_df():
    cmd = "/opt/sandstone/bin/sds osd df | sort -nk 6"
    return run(cmd)

def main(database):
    history = InMemoryHistory()
    connection = sqlite3.connect(database)

    click.secho(" ________    ______     ______     __         __    ", fg="red")
    click.secho("/\ \___\ \  /\ \_\ \   /\  ___\   /\ \       /\ \   ", fg="yellow")
    click.secho("\ \ \___\ \ \ \_\___\  \ \ \____  \ \ \____  \ \ \  ", fg="green")
    click.secho(" \ \_____\ \ \ \_\      \ \_____\  \ \_____\  \ \_\ ", fg="blue")
    click.secho("  \/_____/_/  \/__\      \/_____/   \/_____/   \/_/ ", fg="magenta")
    while True:
        try:
            text = prompt('> ', lexer=SqlLexer, completer=SDSCompleter,
                          style=DocumentStyle, history=history,
                          on_abort=AbortAction.RETRY)
        except EOFError:
            break  # Control-D pressed.
        if text.startswith('bcache'):
            print bcache_quote()
        elif text.startswith('osd_df'):
            print osd_df()
        else:
            print run(text)
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

    main(db)

