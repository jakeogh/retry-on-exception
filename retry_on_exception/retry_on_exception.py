#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=useless-suppression             # [I0021]
# pylint: disable=missing-docstring               # [C0111] docstrings are always outdated and wrong
# pylint: disable=fixme                           # [W0511] todo is encouraged
# pylint: disable=line-too-long                   # [C0301]
# pylint: disable=too-many-instance-attributes    # [R0902]
# pylint: disable=too-many-lines                  # [C0302] too many lines in module
# pylint: disable=invalid-name                    # [C0103] single letter var names, name too descriptive
# pylint: disable=too-many-return-statements      # [R0911]
# pylint: disable=too-many-branches               # [R0912]
# pylint: disable=too-many-statements             # [R0915]
# pylint: disable=too-many-arguments              # [R0913]
# pylint: disable=too-many-nested-blocks          # [R1702]
# pylint: disable=too-many-locals                 # [R0914]
# pylint: disable=too-few-public-methods          # [R0903]
# pylint: disable=no-member                       # [E1101] no member for base
# pylint: disable=attribute-defined-outside-init  # [W0201]
# pylint: disable=too-many-boolean-expressions    # [R0916] in if statement
from __future__ import annotations

import traceback
from functools import wraps  # todo
from math import inf
from typing import Type
from typing import cast

from asserttool import ic
from delay_timer import DelayTimer
from eprint import eprint

# import errno as error_number


def retry_on_exception(
    *,
    exception: Type[Exception],
    errno=None,
    in_e_args=None,
    in_e_args_isinstance=None,
    kwargs: dict = {},
    args: tuple = (),
    kwargs_add_on_retry={},
    args_add_on_retry: tuple = (),
    kwargs_extract_from_exception=(),
    delay: float = 1.0,
    max_delay: float = 60.0,
    retries: float = inf,
    call_function_once=None,  # this could block, like wait_for_ping_default_gateway()
    call_function_once_args=(),
    call_function_once_kwargs={},
    verbose: bool | int | float = False,
    delay_multiplier: float = 1.5,
):

    delay_timer = DelayTimer(
        start=delay,
        multiplier=delay_multiplier,
        end=max_delay,
        verbose=verbose,
    )

    def retry_on_exception_decorator(function):
        @wraps(function)
        def retry_on_exception_wrapper(*args, **kwargs):
            nonlocal delay
            if not issubclass(exception, Exception):
                raise ValueError(
                    "exception must be a subclass of Exception, not:", type(exception)
                )
            tries = 0
            if retries < 1:
                raise ValueError("retries must be >= 1: retries:", retries)
            if verbose == inf:
                ic(exception)
                ic(type(exception))
                ic(errno)
                ic(in_e_args)
                ic(in_e_args_isinstance)
                ic(kwargs)
                ic(args)
                ic(delay)
                ic(max_delay)
                ic(retries)
                ic(kwargs_add_on_retry)
                ic(args_add_on_retry)
                ic(kwargs_extract_from_exception)
                ic(call_function_once)
                ic(call_function_once_args)
                ic(call_function_once_kwargs)
                ic(delay_multiplier)

            raise_next = False
            kwargs_extracted_from_exception = {}
            # ic(raise_next)
            while True:
                if tries > (retries - 1):
                    ic(
                        tries,
                        ">",
                        retries - 1,
                        "raising next matching exception:",
                        exception,
                    )
                    raise_next = True
                    # ic(raise_next)
                try:
                    if verbose:
                        ic("calling:", function.__name__)
                        ic(args)
                        ic(kwargs)
                    tries += 1
                    if kwargs_extracted_from_exception:
                        return function(
                            *args, **kwargs, **kwargs_extracted_from_exception
                        )
                    else:
                        return function(*args, **kwargs)
                except exception as e:
                    if verbose == inf:
                        ic(e)

                    # deliberately about to raise an AttributeError if errno was passed and e does not have it, this is by design
                    # seemingly, not actually raising AttributeError yet though... TODO
                    # if errno:  # mypy not happy
                    # if isinstance(e, OSError):  # mypy is fine with this, but it's using isinstance()
                    #    if not e.errno == errno:
                    #        raise e
                    if errno:
                        if not cast(OSError, e).errno == errno:  # best way?
                            raise e

                    if in_e_args:
                        if verbose == inf:
                            ic(e.args)
                        found = False
                        for arg in e.args:
                            if verbose == inf:
                                ic(arg)
                            try:
                                if in_e_args in repr(arg):  # hacky, should recurse
                                    found = True
                            except TypeError:  # TODO check for: TypeError: argument of type 'MaxRetryError' is not iterable
                                pass
                        if not found:
                            raise e

                    if in_e_args_isinstance:
                        if verbose == inf:
                            ic(e.args)
                        found = False
                        for arg in e.args:
                            try:
                                if isinstance(arg, in_e_args_isinstance):
                                    found = True
                                    if verbose == inf:
                                        ic("found:", arg, in_e_args_isinstance)
                            except TypeError:  # TODO check for: TypeError: argument of type 'MaxRetryError' is not iterable
                                pass
                        if not found:
                            raise e

                    if kwargs_extract_from_exception:
                        for arg in e.args:
                            if isinstance(arg, dict):
                                for kw in kwargs_extract_from_exception:
                                    if kw in arg.keys():
                                        kwargs_extracted_from_exception[kw] = arg[kw]
                        for kw in kwargs_extract_from_exception:
                            if kw not in kwargs_extracted_from_exception.keys():
                                ic(
                                    kw,
                                    "not found in",
                                    e.args,
                                    "exception does not match, raising:",
                                    e,
                                )
                                raise e
                    # by here, the exception is valid to be caught

                    if raise_next:
                        # ic(raise_next)
                        ic(raise_next, "raising:", e)
                        raise e
                    ic(function)
                    if verbose:
                        ic(exception)

                    if hasattr(e, "errno"):
                        # if cast(OSError, e).errno:  # need typing.Protocol?
                        ic(
                            e, e.errno
                        )  # mypy: "Exception" has no attribute "errno"  [attr-defined]

                    else:
                        ic(e)
                    for index, arg in enumerate(e.args):
                        ic(index, arg)
                        traceback.print_exc()
                    if call_function_once:
                        if tries == 1:
                            call_function_once_result = call_function_once(
                                *call_function_once_args, **call_function_once_kwargs
                            )
                            ic(call_function_once_result)
                    delay_timer.sleep()
                except Exception as e:
                    if verbose == inf:
                        ic(e)
                        ic(type(e))
                    raise e

        return retry_on_exception_wrapper

    return retry_on_exception_decorator
