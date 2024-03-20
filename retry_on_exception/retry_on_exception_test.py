#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=global-statement      # [W0603]

from __future__ import annotations

import errno
import os
import time

import click

from retry_on_exception import retry_on_exception
from retry_on_exception.retry_on_exception import eprint

try_number = 0


def raise_valueerror():
    raise ValueError("try again")


@retry_on_exception(
    exception=ValueError,
    in_e_args="custom arg",
    retries=1,
)
@retry_on_exception(
    exception=ValueError,
    in_e_args="totally different",
    retries=1,
)
def raise_test_in_e_args_duplicate():
    global try_number
    try_number += 1
    eprint(f"raise_test_in_e_args_duplicate() {try_number=}")
    if try_number == 1:
        raise ValueError("custom arg")
    raise ValueError("totally different")


@retry_on_exception(
    exception=ValueError,
    in_e_args="custom arg",
    retries=2,
)
def raise_test_in_e_args():
    global try_number
    try_number += 1
    eprint(f"raise_test_in_e_args() {try_number=}")
    raise ValueError("custom arg")


@retry_on_exception(
    exception=OSError,
    errno=errno.ETXTBSY,
    retries=2,
)
def raise_testerrno_wrong_errno():
    global try_number
    try_number += 1
    eprint(f"raise_testerrno_wrong_errno() {try_number=}")
    raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC), "foodir")


@retry_on_exception(
    exception=OSError,
    errno=errno.ENOSPC,
    retries=2,
)
def raise_testerrno():
    global try_number
    try_number += 1
    eprint(f"raise_testerrno() {try_number=}")
    # cant use, will get converted to: FileNotFoundError: [Errno 2] No such file or directory: 'foodir'
    # raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), "foodir")
    raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC), "foodir")


@retry_on_exception(
    exception=ValueError,
    retries=3,
    initial_delay=1,
    delay_multiplier=2,
    max_delay=8,
)
def raise_valueerror_slowly():
    global try_number
    try_number += 1
    eprint(f"raise_valueerror_slowly() {try_number=}")
    raise ValueError("raise_valueerror_slowly()")


@retry_on_exception(
    exception=OSError,
    retries=3,
)
@retry_on_exception(
    exception=FileNotFoundError,
    retries=2,
)
def raise_filenotfounderror():
    global try_number
    try_number += 1
    eprint(f"raise_filenotfounderror() {try_number=}")
    raise FileNotFoundError("raise_filenotfounderror()")


@retry_on_exception(
    exception=ValueError,
    retries=2,
)
@retry_on_exception(
    exception=TypeError,
    retries=3,
)
def raise_multiple(choice: int):
    # choice = round(random.random())
    global try_number
    try_number += 1
    eprint(f"raise_multiple() {choice=}, {try_number=}")
    if choice == 0:
        raise ValueError(f"raise_multiple({choice=})")
    if choice == 1:
        raise TypeError(f"raise_multiple({choice=})")


@click.command()
@click.option("--verbose", is_flag=True)
@click.option("--ipython", is_flag=True)
def cli(
    ipython: bool,
    verbose: bool = False,
):
    global try_number

    @retry_on_exception(
        exception=TypeError,
        retries=2,
    )
    def raise_typeerror(thing):
        global try_number
        try_number += 1
        print(f"raise_typeerror(): global {try_number=}")
        thing()

    # test 1, simple retry test
    eprint()
    eprint("\ncli() Starting Test 1")
    try_number = 0
    try:
        raise_typeerror("1")
    except TypeError as e:
        eprint(f"cli() test 1: TypeError {try_number=} need 3")
        if try_number != 3:  # 2 retries, TypeError gets raised on the 3rd
            raise e

    # test 2, check wrapping twice ValueError
    eprint()
    eprint("\ncli() Starting Test 2")
    try_number = 0
    try:
        raise_multiple(0)
    except ValueError as e:
        eprint(f"cli() test 2 ValueError: {try_number=} need 3")
        if try_number != 3:  # 2 retries, ValueError gets raised on the 3rd
            raise e

    # test 3, check wrapping twice ValueError
    eprint()
    eprint("\ncli() Starting Test 3")
    try_number = 0
    try:
        raise_multiple(1)
    except TypeError as e:
        eprint(f"cli() test 3 TypeError: {try_number=} need 4")
        if try_number != 4:  # 3 retries, TypeError gets raised on the 4th
            raise e

    # test 4, check explicit catching of exceptions, not their parents
    eprint()
    eprint("\ncli() Starting Test 4")
    try_number = 0
    try:
        raise_filenotfounderror()
    except FileNotFoundError as e:
        eprint(f"cli() test 4 FileNotFoundError: {try_number=} need 3")
        if try_number != 3:  # 2 retries, FileNotFoundError gets raised on the 3th
            raise e

    # test 5, check delay
    # retry 1           1s
    # retry 2 1+(2*1) = 3s
    # retry 3 3+(2*3) = 9s (clipped to 8)
    # 1+3+8 = 12
    # max is 8, so total time should be 12s
    eprint()
    eprint("\ncli() Starting Test 5")
    try_number = 0
    start_time = time.time()
    try:
        raise_valueerror_slowly()
    except ValueError as e:
        eprint(f"cli() test 5 ValueError: {try_number=} need 4")
        end_time = time.time()
        elapsed_time = end_time - start_time
        eprint(f"{elapsed_time=}")
        if try_number != 4:  # 3 retries, ValueError gets raised on the 4th
            raise e
        if elapsed_time < 12:
            raise e
        if elapsed_time > 12.1:
            raise e

    # test 6, check errno
    eprint()
    eprint("\ncli() Starting Test 6")
    try_number = 0
    try:
        raise_testerrno()
    except OSError as e:
        eprint(f"cli() test 6 OSError: {try_number=} need 3")
        if try_number != 3:  # 2 retries, OSError gets raised on the 3th
            raise e

    # check incorrect errno
    test_number = 7
    eprint()
    eprint(f"\ncli() Starting Test {test_number}")
    try_number = 0
    try:
        raise_testerrno_wrong_errno()
    except OSError as e:
        eprint(f"cli() test {test_number} OSError: {try_number=} need 1")
        if try_number != 1:  # 0 retries, OSError gets raised on the 1th
            raise e
        if e.errno != errno.ENOSPC:
            raise e

    # check in_e_args
    test_number = 8
    eprint()
    eprint(f"\ncli() Starting Test {test_number}")
    try_number = 0
    try:
        raise_test_in_e_args()
    except ValueError as e:
        eprint(f"cli() test {test_number} ValueError: {try_number=} need 2")
        if try_number != 3:  # 2 retries, ValueError gets raised on the 3th
            raise e
        if e.args[0] != "custom arg":
            raise e

    # check in_e_args duplicate exception, different e.args
    test_number = 9
    eprint()
    eprint(f"\ncli() Starting Test {test_number}")
    try_number = 0
    try:
        raise_test_in_e_args_duplicate()
    except ValueError as e:
        eprint(f"cli() test {test_number} ValueError: {try_number=} need 3 {e=}")
        if try_number != 3:  # 2x1 retries, ValueError gets raised on the 3rd
            raise e
        # if e.args[0] != "custom arg":
        #    raise e

    ## check in_e_args_isinstance
    # test_number = 9
    # eprint()
    # eprint(f"\ncli() Starting Test {test_number}")
    # try_number = 0
    # try:
    #    raise_test_in_e_args_isinstance()
    # except ValueError as e:
    #    eprint(f"cli() test {test_number} ValueError: {try_number=} need 2")
    #    if try_number != 3:  # 2 retries, ValueError gets raised on the 3th
    #        raise e
    #    if e.args[0] != "custom arg":
    #        raise e

    if ipython:
        import IPython

        IPython.embed()
