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


import time
from functools import wraps  # todo
from math import inf

from delay_timer import DelayTimer

#import errno as error_number

try:
    from icecream import ic
except ImportError:
    import sys

    def eprint(*args, **kwargs):
        if 'file' in kwargs.keys():
            kwargs.pop('file')
        print(*args, file=sys.stderr, **kwargs)


def retry_on_exception(*,
                       exception,
                       errno=None,
                       in_e_args=None,
                       kwargs={},
                       args=(),
                       delay=1,
                       max_delay=360,
                       retries=inf,
                       call_function_once=None,
                       call_function_once_args=(),
                       call_function_once_kwargs={},
                       verbose=False,
                       delay_multiplier=0.5,):

    delay_timer = DelayTimer(start=delay,
                             multiplier=delay_multiplier,
                             end=max_delay,
                             verbose=verbose,)

    def retry_on_exception_decorator(function):
        @wraps(function)
        def retry_on_exception_wrapper(*args, **kwargs):
            nonlocal delay
            if not issubclass(exception, Exception):
                raise ValueError('exception must be a subclass of Exception, not:', type(exception))
            tries = 0
            if retries < 1:
                raise ValueError('retries must be >= 1: retries:', retries)
            while True:
                if tries > retries:
                    ic(tries, '>', retries, 'breaking')
                    break
                try:
                    if verbose:
                        ic('calling:', function.__name__)
                        ic(args)
                        ic(kwargs)
                    tries += 1
                    return function(*args, **kwargs)
                except exception as e:
                    if errno:
                        if not e.errno == errno:  # gonna throw an AttributeError if errno was passed and e does not have it, this is by design
                            raise e
                    if in_e_args:
                        if in_e_args not in e.args:
                            raise e
                    ic(function)
                    if verbose:
                        ic(exception)
                    if hasattr(e, 'errno'):
                        ic(e, e.errno)
                    else:
                        ic(e)
                    for index, arg in enumerate(e.args):
                        ic(index, arg)
                    if call_function_once:
                        call_function_once_result = call_function_once(*call_function_once_args, **call_function_once_kwargs)
                        ic(call_function_once_result)
                    delay_timer.sleep()
        return retry_on_exception_wrapper
    return retry_on_exception_decorator


def retry_on_exception_manual(function,
                              *,
                              exceptions,
                              errno=None,
                              kwargs={},
                              args=(),
                              delay=1,
                              retries=inf,
                              verbose=False,
                              delay_multiplier=0.5,):

    if not isinstance(exceptions, tuple):
        raise ValueError('exceptions must be a tuple, not:', type(exceptions))
    tries = 0
    while True:
        if tries > retries:
            ic(tries, '>', retries, 'breaking')
            break
        try:
            if verbose:
                ic('calling:', function.__name__)
                ic(args)
                ic(kwargs)
            tries += 1
            return function(*args, **kwargs)
        except exceptions as e:
            ic(e)  # need this to see what exception is being retried
            if errno:
                if not e.errno == errno:  # gonna throw an AttributeError if errno was passed and e does not have it, this is by design
                    raise e
            ic(function)
            ic(exceptions)
            if hasattr(e, 'errno'):
                ic(e, e.errno)
            else:
                ic(e)
            delay = delay + (delay * delay_multiplier)
            ic(delay)
            time.sleep(delay)

