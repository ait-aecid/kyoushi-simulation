# -*- coding: utf-8 -*-
"""State machine module

This module contains all class and function defintions for creating and defining
Cyber Range Kyoushi simulation machines.
"""
import datetime  # need import datetime like this so we can mock it
import logging

from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Type

from . import errors
from .model import Context
from .model import StatemachineConfig
from .states import State
from .transitions import Transition
from .util import sleep_until


__all__ = ["Statemachine", "StatemachineFactory"]

logger = logging.getLogger("cr_kyoushi.simulation")


class Statemachine:
    """
    Implements state control and transition logic

    This class implements basic state machine execution, i.e., execution
    starts at the configured initial state and continues until a end state
    (i.e., a state without outgoing transitions) is reached. A state machine
    can be started by calling the [`run()`][cr_kyoushi.simulation.sm.Statemachine.run] function.

    !!! Note
        You can also execute a state machine step wise using `_execute_step()`
        function manually. If you choose to do so be care full to remember to call
        `setup_context()` before you start execution and `destroy_context()`
        after the state machine is finished.

    Default state machine behavior can be extended or modified by creating
    a sub class and overriding the state machine functions
    [`_execute_machine()`][cr_kyoushi.simulation.sm.Statemachine._execute_machine],
    [`_execute_step()`][cr_kyoushi.simulation.sm.Statemachine._execute_step],
    [`_execute_transition()`][cr_kyoushi.simulation.sm.Statemachine._execute_transition], etc.
    """

    @property
    def context(self) -> Context:
        """The state machine execution context object."""
        return self._context

    @context.setter
    def context(self, new_value: Context):
        self._context = new_value

    def __init__(
        self,
        initial_state: str,
        states: List[State],
        max_errors: int = 0,
    ):
        """
        Args:
            initial_state: The name of the initial state
            states: List of all states the state machine can enter
            max_errors: Maximum amount of errors the state machine is allowed to encounter
                        before it stops trying to recover by reseting to the initial state.

        """
        self.initial_state = initial_state
        self.current_state: Optional[str] = initial_state
        self.current_transition: Optional[Transition] = None
        self.states: Dict[str, State] = {state.name: state for state in states}
        self.context: Context = {}
        self.max_errors = max_errors
        self.errors = 0

    def setup_context(self) -> None:
        """Initialize and setup the state machine execution context

        ??? Note
            Override this function if your state machine needs run some
            logic or set `Context` information before it can be executed.
        """

    def destroy_context(self) -> None:
        """Destroy and clean up the state machine execution context

        ??? Note
            Override or extend this function if your state machine needs run some
            logic or free `Context` information after it has finished executing.
        """

    def _execute_transition(self):
        """Execute the current transition.

        The current transition is executed and the current state is
        updated on successful executions. This function also handles
        [`TransitionExecutionErrors`][cr_kyoushi.simulation.errors.TransitionExecutionError]
        and sets the state machines current state to the errors fallback state.

        ??? Note
            Override or extend this if you want to change how transitions are executed
            or how [`TransitionExecutionErrors`][cr_kyoushi.simulation.errors.TransitionExecutionError]
            are handled.
        """
        assert self.current_state is not None
        assert self.current_transition is not None
        try:
            logger.info(
                "Executing transition %s -> %s",
                self.current_state,
                self.current_transition,
            )
            self.current_state = self.current_transition.execute(
                self.current_state, self.context
            )
            logger.info("Moved to new state %s", self.current_state)
        except errors.TransitionExecutionError as transition_error:
            logger.warning("Encountered a transition error: %s", transition_error)
            if transition_error.fallback_state:
                logger.warning(
                    "Recovering to state '%s'", transition_error.fallback_state
                )
            self.current_state = transition_error.fallback_state

    def _execute_step(self):
        """Execute a single state machine step.

        This function delegates transition execution to `_execute_transition()`.
        All pre and post execution tasks such as retrieving the transition
        from the current state before the transition and handeling unexpected
        errors encountered during transition execution.

        ??? Note
            Override or extend this function if you whish to change pre-, post-execution
            and handling of all unexpected errors.
        """
        assert self.current_state is not None
        try:
            self.current_transition = self.states[self.current_state].next(self.context)

            if self.current_transition:
                self._execute_transition()
            else:
                logger.info("Empty transition received state machine will end")
                self.current_state = None
        except Exception as err:
            logger.error(
                "State machine failed in state:'%s' and transition:%r",
                self.current_state,
                self.current_transition,
            )
            logger.error("Exception: %s", err)

            # try to recover from error by restarting state machine
            self.errors += 1
            if self.max_errors > self.errors:
                self.destroy_context()
                logger.warning(
                    "Trying to recover from exception in state:'%s' and transition:%r",
                    self.current_state,
                    self.current_transition,
                )
                self.setup_context()
                self.current_state = self.initial_state
            else:
                self.current_state = None

    def _execute_machine(self):
        """State machine main execution loop.

        This function executes state machine steps in a loop
        until a end state is reached (i.e., current state is `None`).

        ??? Note
            Override or extends this if you whish to change how your
            state machine does continues execution.
        """
        # state machine run main loop
        while self.current_state:
            self._execute_step()

    def run(self) -> None:
        """Starts the state machine execution.

        The state machine execution context is setup before
        executing the state machine main loop and destroyed again
        after the main loop ends.
        """
        # prepare state machine before start
        logger.info("Starting state machine")
        self.setup_context()

        # execute the state machine
        logger.info("Entering state machine execution")
        self._execute_machine()

        # clean up state machine
        self.destroy_context()
        logger.info("State machine finished")


class LimitedActiveStatemachine(Statemachine):
    @property
    def start_time(self) -> Optional[datetime.datetime]:
        return self.__start_time

    @property
    def end_time(self) -> Optional[datetime.datetime]:
        return self.__end_time

    def __init__(
        self,
        initial_state: str,
        states: List[State],
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        max_errors: int = 0,
    ):
        super().__init__(initial_state, states, max_errors=max_errors)
        self.__start_time = start_time
        self.__end_time = end_time

    def _is_end_time(self) -> bool:
        # if no end time was set then this is always false
        if self.end_time is None:
            return False
        return self.end_time <= datetime.datetime.now()

    def _execute_machine(self):
        """State machine main execution loop.

        This function executes state machine steps in a loop until either
         - a end state is reached (i.e., current state is `None`)
         - or the current time is >= `end_time`

        """
        # state machine run main loop
        while self.current_state and not self._is_end_time():
            self._execute_step()

    def run(self):
        # wait for start time before actually starting the machine
        if self.start_time is not None:
            sleep_until(self.start_time)
        return super().run()


class StatemachineFactory(ABC, Generic[StatemachineConfig]):
    """Abstract class definition for factories generating state machines

    State machine factories are used by the CLI system to load dynamically load
    state machines from [entrypoints](https://packaging.python.org/specifications/entry-points/)
    or python files.

    A state machine factory must have a **name** and a **config class**.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the state machine factory."""

    @property
    @abstractmethod
    def config_class(self) -> Type[StatemachineConfig]:
        """The config class to use for the state machine.

        You can use the configuration class to define all required
        and optional configuration options for your state machine.
        e.g., to make it possible for users of your state machine to configure
        the probabilities for [`ProbabilisticStates`][cr_kyoushi.simulation.states.ProbabilisticState].

        The CLI system dynamically loads and validates configuration for your
        state machine based on the config class.
        [Pydantic](https://pydantic-docs.helpmanual.io/) is used for this so it is
        recommended to define your config class must be a pydantic model or any other field type
        pydantic can handle.
        """

    @abstractmethod
    def build(self, config: StatemachineConfig) -> Statemachine:
        """Builds the state machine instance.

        The build function must also create and initialize all states and transitions
        required by the state machine. This is called by the CLI system to create
        the state machine before executing it.

        Args:
            config: Configuration for your state machine.

        Returns:
            Statemachine: Statemachine instances created based on the given configuration.
        """
