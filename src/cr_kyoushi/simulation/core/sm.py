# -*- coding: utf-8 -*-
"""Statemachine core module

This module contains all core class and function defintions for creating and defining
Cyber Range Kyoushi simulation machines.
"""
import logging

from abc import ABCMeta
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


Config = Dict[str, Any]
Context = Dict[str, Any]


class Transition(metaclass=ABCMeta):
    """The Transition class describes a transition from one state into another"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def target(self) -> Optional[str]:
        ...

    @abstractmethod
    def execute(self, current_state: str, context: Context) -> Optional[str]:
        ...

    def __str__(self):
        return f"name='{self.name}' -> target={self.target}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', target={self.target})"


class State(metaclass=ABCMeta):
    """A State contains various transitions to other states"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def transitions(self) -> List[Transition]:
        ...

    @abstractmethod
    def next(self, context: Context) -> Optional[Transition]:
        ...

    def __str__(self):
        return f"name='{self.name}' transitions={self.transitions}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', transitions={self.transitions})"


class TransitionExecutionError(Exception):
    """Base class for errors that occur during state transitions"""

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        fallback_state: Optional[str] = None,
    ):
        super().__init__(message)
        self.cause = cause
        self.fallback_state = fallback_state

    def __str__(self):
        ret = f"message: '{super().__str__()}'"
        if self.cause:
            ret += f" cause: {self.cause}"
        return ret


class Statemachine:
    """The Statemachine implements state control and transition logic"""

    def __init__(
        self,
        initial_state: str,
        states: List[State],
        config: Config = {},
        max_errors: int = 0,
    ):
        self.initial_state = initial_state
        self.current_state: Optional[str] = initial_state
        self.current_transition: Optional[Transition] = None
        self.states: Dict[str, State] = {state.name: state for state in states}
        self.config = config
        self.context: Context = {}
        self.max_errors = max_errors
        self.errors = 0

    def setup_context(self) -> None:
        ...

    def destroy_context(self) -> None:
        ...

    def _execute_transition(self):
        assert self.current_state is not None
        assert self.current_transition is not None
        try:
            logging.info(
                f"Executing transition {self.current_state} -> {self.current_transition}"
            )
            self.current_state = self.current_transition.execute(
                self.current_state, self.context
            )
            logging.info(f"Moved to new state {self.current_state}")
        except TransitionExecutionError as te:
            logging.warning(f"Encountered a transition error: {te}")
            if te.fallback_state:
                logging.warning(f"Recovering to state '{te.fallback_state}'")
            self.current_state = te.fallback_state

    def _execute_step(self):
        assert self.current_state is not None
        try:
            self.current_transition = self.states[self.current_state].next(self.context)

            if self.current_transition:
                self._execute_transition()
            else:
                logging.info("Empty transition received state machine will end")
                self.current_state = None
        except Exception as e:
            logging.error(
                f"Statemachine failed in state:'{self.current_state}' and transition:{self.current_transition!r}"
            )
            logging.error(f"Exception: {e}")

            # try to recover from error by restarting state machine
            self.errors += 1
            if self.max_errors > self.errors:
                self.destroy_context()
                logging.warning(
                    f"Trying to recover from exception in state:'{self.current_state}' and transition:{self.current_transition!r}"
                )
                self.setup_context()
                self.current_state = self.initial_state
            else:
                self.current_state = None

    def run(self) -> None:
        # prepare state machine before start
        logging.info("Starting statemachine")
        self.setup_context()

        # state machine run main loop
        while self.current_state:
            self._execute_step()

        # clean up state machine
        self.destroy_context()
        logging.info("Statemachine finished")


class StatemachineFactory(metaclass=ABCMeta):
    """Abstract class definition for factories generating state machines"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def get_statemachine(self, config: Config) -> Statemachine:
        ...
