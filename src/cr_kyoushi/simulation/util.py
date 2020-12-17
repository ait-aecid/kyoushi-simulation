# -*- coding: utf-8 -*-
"""Statemachine util module

This module contains some utility functions which can used for statemachines, state
and state transitions.
"""
from __future__ import annotations

# we must import datetime like this or we cannot mock it
import datetime
import logging
import signal
import time

from contextlib import contextmanager
from types import FrameType
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import List
from typing import Optional
from typing import Union

from .errors import SkipSectionError
from .model import ApproximateFloat


if TYPE_CHECKING:
    from .cli import Info


__all__ = ["version_info", "elements_unique", "skip_on_interrupt", "sleep"]

logger = logging.getLogger("cr_kyoushi.simulation")


def version_info(cli_info: Info) -> str:
    """Returns formatted version information about the `cr_kyoushi.simulation package`.

    Adapted from
    [Pydantic version.py](https://github.com/samuelcolvin/pydantic/blob/master/pydantic/version.py)
    """
    import platform
    import sys

    from pathlib import Path

    from . import __version__

    info = {
        "cr_kyoushi.simulation version": __version__,
        "config path": cli_info.config_path.absolute()
        if cli_info.config_path is not None
        else None,
        "install path": Path(__file__).resolve().parent,
        "python version": sys.version,
        "platform": platform.platform(),
    }
    return "\n".join(
        "{:>30} {}".format(k + ":", str(v).replace("\n", " ")) for k, v in info.items()
    )


def elements_unique(to_check: List[Any]) -> bool:
    """Utility function to check if elements in a list are uniq.

    Args:
        to_check: The list to check

    Returns:
        `True` if the list contains no duplicates `False` otherwise.
    """
    seen = set()
    return not any(i in seen or seen.add(i) for i in to_check)  # type: ignore


def skip_on_interrupt_sig_handler(signum: signal.Signals, frame: FrameType):
    """Simple signal handler that just raises a
    [`SkipSectionError`][cr_kyoushi.simulation.errors.SkipSectionError]
    when it receives a interrupt signal.

    Raises:
        SkipSectionError: To indicate the current section should be skipped
    """
    logger.debug("Received interrupt raising skip section error")
    raise SkipSectionError()


@contextmanager
def skip_on_interrupt(
    sig: signal.Signals = signal.SIGINT,
    sig_handler: Callable[
        [signal.Signals, FrameType], None
    ] = skip_on_interrupt_sig_handler,
):
    """Context manager for creating skipable code sections.

    Args:
        sig: The signal that should indicate a skip request.
        sig_handler: The skip on signal handler to use.

    Example:
        ```python
            # start of the skipable section
            with skip_on_interrupt():
                ...
                long_running_task()
                ...
            # after a skip we resume here
            ...
        ```
    """
    try:
        original_handler = signal.getsignal(sig)
        signal.signal(sig, sig_handler)
        yield
    except SkipSectionError:
        logger.debug("Skipped section")
        signal.signal(sig, original_handler)
        # clear original signal handler so we know not to
        # reset to it twice
        original_handler = None
        print("Press CTRL+C again to stop the program")
        time.sleep(0.5)
    finally:
        if original_handler is not None:
            signal.signal(sig, original_handler)


def sleep(sleep_time: Union[ApproximateFloat, float]) -> None:
    """Skipable sleep function

    This function utilizes the
    [`skip_on_interrupt`][cr_kyoushi.simulation.util.skip_on_interrupt]
    context manager to implement a skipable sleep.

    `SIGINT` is used used as skip signal. For CLI applications
    simply press ++ctrl+c++ to skip to interrupt the sleep.

    !!! Note
        If you wish to send the `SIGINT` signal to the main process press
         ++ctrl+c++ twice.
    """
    if isinstance(sleep_time, ApproximateFloat):
        sleep_time = sleep_time.value

    with skip_on_interrupt():
        logger.debug("Going to sleep for %f", sleep_time)
        time.sleep(sleep_time)
        logger.debug("Resuming execution after sleeping for %f", sleep_time)


def sleep_until(
    end_datetime: datetime.datetime,
    min_sleep_amount: float = 0.1,
    sleep_amount: Optional[Union[float, ApproximateFloat]] = None,
):
    """Sleep until specified datetime

    The default behavior is to basically binary search towards the target datetime.
    i.e., the sleep duration is always `time left/2` until min sleep amount is larger
    than the division result. Alternatively fixed sleep steps can be configured.

    !!! Hint
        You can interupt the current sleep and check if the desired datetime is already
        reached by pressing ++ctrl+c++ and sending a `SIGINT`.


    Args:
        end_datetime: The datetime to wait until
        min_sleep_amount: The minimum amount of time sleep in between checks.
        sleep_amount: Optionally use fixed amount of time sleep steps
    """

    while True:
        diff = (end_datetime - datetime.datetime.now()).total_seconds()

        # stop waiting once its the end time or later
        if diff <= 0:
            return

        # if we do not have a sleep interval sleep relative to
        # the time between now and the end time
        if sleep_amount is None:
            #  to avoid many extremely short sleeps
            #  fallback to the minimum sleep
            sleep(max(min_sleep_amount, diff / 2))
        else:
            sleep(sleep_amount)
