# -*- coding: utf-8 -*-
"""State machine module

This module contains all class and function defintions for creating and defining
Cyber Range Kyoushi simulation machines.
"""
import logging

from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Type

from . import errors
from .model import ActivePeriod
from .model import Context
from .model import StatemachineConfig
from .states import State
from .transitions import Transition


class Statemachine:
    """The State machine implements state control and transition logic"""

    def __init__(
        self,
        initial_state: str,
        states: List[State],
        max_errors: int = 0,
    ):
        self.initial_state = initial_state
        self.current_state: Optional[str] = initial_state
        self.current_transition: Optional[Transition] = None
        self.states: Dict[str, State] = {state.name: state for state in states}
        self.context: Context = {}
        self.max_errors = max_errors
        self.errors = 0

    def setup_context(self) -> None:
        pass

    def destroy_context(self) -> None:
        pass

    def _execute_transition(self):
        assert self.current_state is not None
        assert self.current_transition is not None
        try:
            logging.info(
                "Executing transition %s -> %s",
                self.current_state,
                self.current_transition,
            )
            self.current_state = self.current_transition.execute(
                self.current_state, self.context
            )
            logging.info("Moved to new state %s", self.current_state)
        except errors.TransitionExecutionError as transition_error:
            logging.warning("Encountered a transition error: %s", transition_error)
            if transition_error.fallback_state:
                logging.warning(
                    "Recovering to state '%s'", transition_error.fallback_state
                )
            self.current_state = transition_error.fallback_state

    def _execute_step(self):
        assert self.current_state is not None
        try:
            self.current_transition = self.states[self.current_state].next(self.context)

            if self.current_transition:
                self._execute_transition()
            else:
                logging.info("Empty transition received state machine will end")
                self.current_state = None
        except Exception as err:
            logging.error(
                "State machine failed in state:'%s' and transition:%r",
                self.current_state,
                self.current_transition,
            )
            logging.error("Exception: %s", err)

            # try to recover from error by restarting state machine
            self.errors += 1
            if self.max_errors > self.errors:
                self.destroy_context()
                logging.warning(
                    "Trying to recover from exception in state:'%s' and transition:%r",
                    self.current_state,
                    self.current_transition,
                )
                self.setup_context()
                self.current_state = self.initial_state
            else:
                self.current_state = None

    def _execute_machine(self):
        # state machine run main loop
        while self.current_state:
            self._execute_step()

    def run(self) -> None:
        # prepare state machine before start
        logging.info("Starting state machine")
        self.setup_context()

        # execute the state machine
        logging.info("Entering state machine execution")
        self._execute_machine()

        # clean up state machine
        self.destroy_context()
        logging.info("State machine finished")


class HumanStatemachine(Statemachine):
    """
    A human state machine extends normal state machine behavior by introducting
    an active time period. Outside of the configured active time period
    the human state machine will idle its execution. Additionally upon leaving the
    active time period the state machine will reset to the initial state.
    This includes destrying and recreating the context.
    """

    def __init__(
        self,
        initial_state: str,
        states: List[State],
        active_period: ActivePeriod,
        max_errors: int = 0,
    ):
        super().__init__(initial_state, states, max_errors=max_errors)
        self.active_period = active_period


class StatemachineFactory(ABC, Generic[StatemachineConfig]):
    """Abstract class definition for factories generating state machines"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def config_class(self) -> Type[StatemachineConfig]:
        ...

    @abstractmethod
    def build(self, config: StatemachineConfig) -> Statemachine:
        ...
