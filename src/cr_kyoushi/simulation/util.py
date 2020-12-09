# -*- coding: utf-8 -*-
"""Statemachine util module

This module contains some utility functions which can used for statemachines, state
and state transitions.
"""
from __future__ import annotations

import logging
import signal
import time

from contextlib import contextmanager
from typing import TYPE_CHECKING
from typing import Any
from typing import List

from .errors import SkipSectionError


if TYPE_CHECKING:
    from .cli import Info


__all__ = ["version_info", "elements_unique", "skip_on_interrupt", "sleep"]

logger = logging.getLogger("cr_kyoushi.simulation")


def version_info(cli_info: Info) -> str:
    """Returns formatted version information about the package.

    Adapted from Pydantic see:
    https://github.com/samuelcolvin/pydantic/blob/master/pydantic/version.py
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
    seen = set()
    return not any(i in seen or seen.add(i) for i in to_check)  # type: ignore


def skip_on_interrupt_sig_handler(signum, frame):
    logger.debug("Received interrupt raising skip section error")
    raise SkipSectionError()


@contextmanager
def skip_on_interrupt(sig=signal.SIGINT, sig_handler=skip_on_interrupt_sig_handler):
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


def sleep(sleep_time: float) -> None:
    with skip_on_interrupt():
        logger.debug("Going to sleep for %d", sleep_time)
        time.sleep(sleep_time)
        logger.debug("Resuming execution after sleeping for %d", sleep_time)
