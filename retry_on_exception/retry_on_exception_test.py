#!/usr/bin/env python3

# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement


import random

import click

try:
    from icecream import ic
except ImportError:
    import sys
    def eprint(*args, **kwargs):
        if 'file' in kwargs.keys():
            kwargs.pop('file')
        print(*args, file=sys.stderr, **kwargs)


from retry_on_exception import retry_on_exception, retry_on_exception_manual


def raise_valueerror():
    raise ValueError('try again')


@retry_on_exception(exceptions=(ValueError,),
                    retries=2,)
@retry_on_exception(exceptions=(TypeError,),
                    retries=3,)
def raise_multiple():
    choice = round(random.random())
    ic(choice)
    if choice == 0:
        raise ValueError
    if choice == 1:
        raise TypeError


@click.command()
@click.option('--verbose', is_flag=True)
@click.option('--ipython', is_flag=True)
@click.option('--debug', is_flag=True)
def cli(ipython,
        verbose,
        debug,):

    retry_on_exception_manual(function=raise_valueerror,
                              kwargs={},
                              args=(),
                              retries=1,
                              exceptions=(ValueError,),
                              errno=None,
                              verbose=verbose,)

    @retry_on_exception(exceptions=(TypeError,),
                        retries=2,)
    def raise_typeerror(thing):
        thing()

    raise_typeerror("1")

    raise_multiple()

    if ipython:
        import IPython; IPython.embed()


