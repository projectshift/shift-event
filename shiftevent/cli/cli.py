import click
from shiftevent.cli.colors import *


# -----------------------------------------------------------------------------
# Group setup
# -----------------------------------------------------------------------------


@click.group(help=yellow('Welcome to project console!'))
def cli():
    pass


# -----------------------------------------------------------------------------
# Commands
# -----------------------------------------------------------------------------


@cli.command(name='test',context_settings=dict(ignore_unknown_options=True))
@click.argument('nose_argsuments', nargs=-1, type=click.UNPROCESSED)
def test(nose_argsuments):
    """ Run application tests """
    from nose import run
    params = ['__main__', '-c', 'nose.ini']
    params.extend(nose_argsuments)
    run(argv=params)




