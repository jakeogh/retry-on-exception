#!/usr/bin/env python3
# tab-width:4

import sys
from collections.abc import Callable
from functools import wraps
from math import inf

from delay_timer import DelayTimer
from globalverbose import gvd


def _eprint(*args) -> None:
    print(*args, file=sys.stderr)


def retry_on_exception(
    *,
    exception: type[Exception],
    retries: float = inf,
    initial_delay: float = 0.0,
    max_delay: float = 100.0,
    delay_multiplier: float = 1.5,
    errno: int | None = None,
    in_e_args: str | None = None,
    in_e_args_isinstance: type | None = None,
    cancel_retry_function: Callable | None = None,
    call_function_once: Callable | None = None,
    call_function_once_args: tuple = (),
    call_function_once_kwargs: dict | None = None,
):
    """Retry a call while it raises exactly `exception` and the filters match.

    Nothing is printed on a call that does not raise. The decorator wraps every
    call site of whatever it decorates, so unconditional output scales with
    call volume rather than with anything going wrong: a clean run of a caller
    doing one LMDB transaction per record produced 2469 lines of it. Retry
    activity is reported under gvd, and a give-up always reports.
    """
    if not issubclass(exception, Exception):
        raise ValueError(f"exception must subclass Exception, not {exception!r}")
    if retries < 1:
        raise ValueError(f"retries must be >= 1, not {retries!r}")

    once_kwargs = call_function_once_kwargs or {}

    def retry_on_exception_decorator(function):
        @wraps(function)
        def retry_on_exception_wrapper(*args, **kwargs):
            # per-call: backoff state must not leak between calls
            delay_timer = (
                DelayTimer(
                    start=initial_delay,
                    multiplier=delay_multiplier,
                    end=max_delay,
                )
                if initial_delay > 0
                else None
            )
            retry_number = 0

            while True:
                try:
                    return function(*args, **kwargs)
                except exception as e:
                    # `except` catches subclasses; the contract is this exact type
                    if type(e) is not exception:
                        raise
                    if errno is not None:
                        if getattr(e, "errno", None) != errno:
                            raise
                    if in_e_args is not None:
                        if not any(in_e_args in repr(arg) for arg in e.args):
                            raise
                    if in_e_args_isinstance is not None:
                        if not any(
                            isinstance(arg, in_e_args_isinstance) for arg in e.args
                        ):
                            raise
                    if retry_number >= retries:
                        _eprint(
                            f"retry_on_exception: {function.__qualname__} gave up "
                            f"after {retry_number} retries on {e!r}"
                        )
                        raise
                    if cancel_retry_function and cancel_retry_function():
                        _eprint(
                            f"retry_on_exception: {function.__qualname__} cancelled "
                            f"on {e!r}"
                        )
                        raise

                    retry_number += 1
                    if gvd:
                        _eprint(
                            f"retry_on_exception: {function.__qualname__} "
                            f"retry {retry_number} after {e!r}"
                        )

                    if call_function_once and retry_number == 1:
                        call_function_once(*call_function_once_args, **once_kwargs)

                if delay_timer:
                    delay_timer.sleep()

        return retry_on_exception_wrapper

    return retry_on_exception_decorator
