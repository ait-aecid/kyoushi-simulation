# -*- coding: utf-8 -*-
"""Statemachine util module

This module contains some utility functions which can used for statemachines, state
and state transitions.
"""

from typing import Any
from typing import List


def elements_unique(to_check: List[Any]) -> bool:
    seen = set()
    return not any(i in seen or seen.add(i) for i in to_check)  # type: ignore
