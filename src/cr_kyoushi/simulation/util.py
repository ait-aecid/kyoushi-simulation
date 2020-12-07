# -*- coding: utf-8 -*-
"""Statemachine util module

This module contains some utility functions which can used for statemachines, state
and state transitions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import List


if TYPE_CHECKING:
    from .cli import Info


__all__ = ["version_info", "elements_unique"]


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
