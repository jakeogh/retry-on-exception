#!/usr/bin/env python3
# -*- coding: utf8 -*-
# tab-width:4

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from functools import wraps  # todo
from math import inf
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal
from typing import Type

from asserttool import icp
from delay_timer import DelayTimer

# import traceback

logging.basicConfig(level=logging.INFO)
# import errno as error_number

# this should be earlier in the imports, but isort stops working
signal(SIGPIPE, SIG_DFL)


def _eprint(*args, **kwargs) -> None:
    try:
        kwargs.pop("file")
    except KeyError:
        pass
    print(*args, file=sys.stderr, **kwargs)


# comment out return to enable debug output
def eprint(*args, **kwargs) -> None:
    return
    _eprint(*args, **kwargs)


def retry_on_exception(
    *,
    exception: Type[Exception],
    kwargs: dict = {},
    args: tuple = (),
    retries: float = inf,
    initial_delay: float = 0.0,
    max_delay: float = 0.0,
    delay_multiplier: float = 0.0,
    errno: int | None = None,
    in_e_args: str | None = None,
    in_e_args_isinstance: type | None = None,
    cancel_retry_function: Callable | None = None,
    call_function_once=None,  # this could block, like wait_for_ping_default_gateway()
    call_function_once_args=(),
    call_function_once_kwargs={},
):
    delay_timer: DelayTimer | None = None
    if initial_delay > 0:
        delay_timer = DelayTimer(
            start=initial_delay,
            multiplier=delay_multiplier,
            end=max_delay,
        )

    def retry_on_exception_decorator(function):
        @wraps(function)
        def retry_on_exception_wrapper(*args, **kwargs):
            if not issubclass(exception, Exception):
                raise ValueError(
                    "exception must be a subclass of Exception, not:", type(exception)
                )
            retry_number = 0
            if retries < 1:
                raise ValueError("retries must be >= 1: retries:", retries)
            eprint(
                f"retry_on_exception() {function=}",
                f"{exception=}",
                f"{type(exception)=}",
                f"{kwargs=}",
                f"{args=}",
                f"{retry_number=}",
                f"{retries=}",
                f"{errno=}",
                f"{in_e_args=}",
                f"{in_e_args_isinstance=}",
                f"{cancel_retry_function=}",
            )

            while True:
                eprint(f"while True: {retry_number=}, {retries=}")
                try:
                    eprint(
                        f"while True: calling and returning: {function.__name__=}",
                        f"{args=}",
                        f"{kwargs=}",
                    )
                    _result = function(*args, **kwargs)
                    # icp(_result)
                    # icp(type(_result))
                    # return function(*args, **kwargs)
                    return _result
                # except exception as e:  # FileNotFoundError gets caught by OSError
                # oldbug, was not checking against decorated exception (fixed below)
                # if exception is OSError, and e is FileNotFoundError, this will still catch, so a second check is needed
                except exception as e:
                    eprint(
                        f"while True: caught {e=} with {exception=}, checking if its a keeper"
                    )
                    if retry_number >= retries:
                        raise e
                    # make sure it's the exact exception requested
                    if not type(e) is exception:
                        eprint(
                            f"while True: about to raise e because the exception matched, but its not the exact exception requested: {type(e)} {e=} {exception=}"
                        )
                        raise e
                    if errno:
                        eprint(f"while True: looking for {errno=} in {e=}")
                        if hasattr(e, "errno"):
                            if e.errno != errno:
                                eprint(
                                    f"while True: errno check failed {errno=}, {e.errno=}, raising e"
                                )
                                raise e
                        else:  # exception does not match, raise it
                            eprint(
                                f"while True: errno check failed {errno=} was specified, but {e=} has no errno attribute"
                            )
                            raise e

                    if in_e_args:
                        eprint(f"while True: looking for {in_e_args=} in {e.args=}")
                        found = False
                        for arg in e.args:
                            try:
                                if in_e_args in repr(arg):
                                    found = True
                            except TypeError:
                                pass
                        if not found:
                            eprint(
                                f"while True: in_e_args check failed {in_e_args=} {e.args=}, raising e"
                            )
                            raise e

                    if in_e_args_isinstance:
                        eprint(
                            f"while True: looking for {in_e_args_isinstance=} in {e.args=}"
                        )
                        found = False
                        for arg in e.args:
                            try:
                                if isinstance(arg, in_e_args_isinstance):
                                    found = True
                                    # icp("found:", arg, in_e_args_isinstance)
                            # T O D O check for: TypeError: argument of type 'MaxRetryError' is not iterable
                            except TypeError as ee:
                                icp(ee)
                                pass
                        if not found:
                            eprint(
                                f"while True: in_e_args_isinstance check failed {in_e_args_isinstance=} {e.args=}, raising e"
                            )
                            raise e

                    eprint(
                        f"while True: caught: {e=}, and it passed all checks, not re-raising",
                        f"{retry_number=}\n",
                    )

                    retry_number += 1
                    # for index, arg in enumerate(e.args):
                    #    eprint(f"while True: {index=}", f"{arg=}")
                    #    # traceback.print_exc()

                    # by here, a matching exception, e exists
                    # if cancel_retry_function() returns True, then raise e (so do not retry the function call again)
                    if cancel_retry_function:
                        _result = cancel_retry_function()
                        if _result:
                            eprint(
                                f"cancel_retry_function() returned {_result=}, raising {e=}"
                            )
                            raise e

                    if call_function_once:
                        if retry_number == 1:
                            call_function_once_result = call_function_once(
                                *call_function_once_args, **call_function_once_kwargs
                            )
                            eprint(f"{call_function_once_result=}")

                except Exception as e:
                    eprint(f"while True: (uncaught exception) {e=} {type(e)}")
                    raise e

                if delay_timer:
                    _eprint(
                        f"{function=}", f"{exception=}", f"{errno=}", f"{in_e_args=}"
                    )
                    delay_timer.sleep()

        return retry_on_exception_wrapper

    return retry_on_exception_decorator
