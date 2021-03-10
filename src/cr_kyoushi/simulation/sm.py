# -*- coding: utf-8 -*-
"""State machine module

This module contains all class and function defintions for creating and defining
Cyber Range Kyoushi simulation machines.
"""
from abc import (
    ABC,
    abstractmethod,
)
from datetime import datetime
from typing import (
    Dict,
    Generic,
    List,
    Optional,
    Type,
)
from uuid import (
    UUID,
    uuid4,
)

from structlog.stdlib import BoundLogger

from . import errors
from .config import get_seed
from .logging import get_logger
from .model import (
    Context,
    StatemachineConfig,
    WorkSchedule,
)
from .states import State
from .transitions import Transition
from .util import (
    now,
    sleep_until,
)


__all__ = ["Statemachine", "StatemachineFactory"]


class Statemachine:
    """
    Implements state control and transition logic

    This class implements basic state machine execution, i.e., execution
    starts at the configured initial state and continues until a end state
    (i.e., a state without outgoing transitions) is reached. A state machine
    can be started by calling the [`run()`][cr_kyoushi.simulation.sm.Statemachine.run] function.

    !!! Note
        You can also execute a state machine step wise using `execute_step()`
        function manually. If you choose to do so be care full to remember to call
        `setup_context()` before you start execution and `destroy_context()`
        after the state machine is finished.

    Default state machine behavior can be extended or modified by creating
    a sub class and overriding the state machine functions
    [`execute_machine()`][cr_kyoushi.simulation.sm.Statemachine.execute_machine],
    [`execute_step()`][cr_kyoushi.simulation.sm.Statemachine.execute_step],
    [`execute_transition()`][cr_kyoushi.simulation.sm.Statemachine.execute_transition], etc.
    """

    @property
    def context(self) -> Context:
        """The state machine execution context object."""
        return self._context

    @context.setter
    def context(self, new_value: Context):
        self._context = new_value

    @property
    def log(self) -> BoundLogger:
        """Bound logger initialize with context information for this state machine."""
        return self.__log

    @property
    def uuid(self) -> UUID:
        """UUID for this state machine execution.

        For example used as unique run ID during when logging.
        """
        return self.__uuid

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
        self.__uuid = uuid4()
        self.__log: BoundLogger = get_logger().bind(run=self.uuid)
        self.log.info("Created state machine", seed=get_seed())

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

    def execute_transition(self, log: BoundLogger):
        """Execute the current transition.

        The current transition is executed and the current state is
        updated on successful executions. This function also handles
        [`TransitionExecutionErrors`][cr_kyoushi.simulation.errors.TransitionExecutionError]
        and sets the state machines current state to the errors fallback state.

        Args:
            log: The bound logger initialized with transition specific information

        ??? Note
            Override or extend this if you want to change how transitions are executed
            or how [`TransitionExecutionErrors`][cr_kyoushi.simulation.errors.TransitionExecutionError]
            are handled.
        """
        assert self.current_state is not None
        assert self.current_transition is not None
        try:
            log.info(
                "Executing transition %s -> %s",
                self.current_state,
                self.current_transition,
            )
            self.current_state = self.current_transition.execute(
                log, self.current_state, self.context
            )
            log.info("Moved to new state", new_state=self.current_state)
        except errors.TransitionExecutionError as transition_error:
            log.warning("Encountered a transition error: %s", transition_error)
            if transition_error.fallback_state:
                log.warning(
                    "Recovering to fallback state",
                    fallback=transition_error.fallback_state,
                )

            self.current_state = transition_error.fallback_state

    def execute_step(self):
        """Execute a single state machine step.

        This function delegates transition execution to `execute_transition()`.
        All pre and post execution tasks such as retrieving the transition
        from the current state before the transition and handeling unexpected
        errors encountered during transition execution.

        ??? Note
            Override or extend this function if you whish to change pre-, post-execution
            and handling of all unexpected errors.
        """
        assert self.current_state is not None

        # bind upcoming transition context to logger
        log: BoundLogger = self.log.bind(
            current_state=self.current_state,
            transition=None,
            transition_id=uuid4(),
            target=None,
        )

        try:
            self.current_transition = self.states[self.current_state].next(
                log, self.context
            )

            if self.current_transition:
                # bind selected transition and target to logger
                log = log.bind(
                    transition=self.current_transition.name,
                    target=self.current_transition.target,
                )

                # execute transition
                self.execute_transition(log)
            else:
                log.info("Empty transition received state machine will end")
                self.current_state = None
        except Exception:
            log.exception("State machine execution failure")

            # try to recover from error by restarting state machine
            self.errors += 1
            if self.max_errors > self.errors:
                self.destroy_context()
                log.warning("Trying to recover statemachine from exception ")
                self.setup_context()
                self.current_state = self.initial_state
            else:
                self.current_state = None

    def execute_machine(self):
        """State machine main execution loop.

        This function executes state machine steps in a loop
        until a end state is reached (i.e., current state is `None`).

        ??? Note
            Override or extends this if you whish to change how your
            state machine does continues execution.
        """
        # state machine run main loop
        while self.current_state:
            self.execute_step()

    def run(self) -> None:
        """Starts the state machine execution.

        The state machine execution context is setup before
        executing the state machine main loop and destroyed again
        after the main loop ends.
        """
        # prepare state machine before start
        self.log.info("Starting state machine")
        self.setup_context()

        # execute the state machine
        self.log.info("Entering state machine execution")
        self.execute_machine()

        # clean up state machine
        self.destroy_context()
        self.log.info("State machine finished")


class StartEndTimeStatemachine(Statemachine):
    """Special type of state machine that allows configuring a start and end time.

    The main stat machine execution loop will only start execution once it is
    the configured start time (starts immediately if none is configured). Similarly
    the state machine will stop once the current time is the end time even if there
    are still transitions left to execute. This is for example useful when you wish to
    configure a state machine to only run for the duration of an experiment.

    !!! Note
        A state machine might end before its end time if it enters a final state.
    """

    @property
    def start_time(self) -> Optional[datetime]:
        """The `datetime` this state machine will start execution"""
        return self.__start_time

    @property
    def end_time(self) -> Optional[datetime]:
        """The `datetime` this state machine will end"""
        return self.__end_time

    def __init__(
        self,
        initial_state: str,
        states: List[State],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_errors: int = 0,
    ):
        """
        Args:
            initial_state: The name of the initial state
            states: List of all states the state machine can enter
            start_time: The `datetime` this state machine should start execution
            end_time: The `datetime` this state machine should end execution
            max_errors: Maximum amount of errors the state machine is allowed to encounter
                        before it stops trying to recover by reseting to the initial state.

        !!! Note
            If `state_time` or `end_time` are `None` then the state machine will
            start or end execution normally.
        """
        super().__init__(initial_state, states, max_errors=max_errors)
        self.__start_time = start_time
        self.__end_time = end_time

    def _is_end_time(self) -> bool:
        # if no end time was set then this is always false
        if self.end_time is None:
            return False
        return self.end_time <= now()

    def execute_machine(self):
        """State machine main execution loop.

        This function executes state machine steps in a loop until either
         - a end state is reached (i.e., current state is `None`)
         - or the current time is >= `end_time`

        """
        # state machine run main loop
        while self.current_state and not self._is_end_time():
            self.execute_step()

    def run(self):
        """Starts the state machine execution.

        This will only start the state machine execution
        once the given start time is reached.
        """
        # wait for start time before actually starting the machine
        if self.start_time is not None:
            sleep_until(self.start_time)
        return super().run()


class WorkHoursStatemachine(StartEndTimeStatemachine):
    """State machine optionally allows the configuration of work hours.

    !!! Note
        This state machine extends
        [`StartEndTimeStatemachine`][cr_kyoushi.simulation.sm.StartEndTimeStatemachine]
        and as such has all its features.

    Work hours are defined through the configuration of a [`ActivePeriod`][cr_kyoushi.simulation.model.ActivePeriod].
    Outside of its work hours this state machine will simply idle and do nothing. You can also configure
    """

    @property
    def work_schedule(self) -> Optional[WorkSchedule]:
        """The work schedules for this state machine"""
        return self.__work_schedule

    def __init__(
        self,
        initial_state: str,
        states: List[State],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        work_schedule: Optional[WorkSchedule] = None,
        max_errors: int = 0,
    ):
        """
        Args:
            initial_state: The name of the initial state
            states: List of all states the state machine can enter
            start_time: The `datetime` this state machine should start execution
            end_time: The `datetime` this state machine should end execution
            work_schedule: The state machines work schedule (days and times to work)
            max_errors: Maximum amount of errors the state machine is allowed to encounter
                        before it stops trying to recover by reseting to the initial state.

        !!! Note
            If `state_time` or `end_time` are `None` then the state machine will
            start or end execution normally.
        """
        super().__init__(
            initial_state,
            states,
            start_time=start_time,
            end_time=end_time,
            max_errors=max_errors,
        )
        self.__work_schedule = work_schedule

    def _in_work_hours(self) -> bool:
        # if we do not have work hours we work 24/7
        if self.work_schedule is None:
            return True

        # if we have work hours we have to check them
        return self.work_schedule.is_work_time(now())

    def _pause_work(self):
        """The pause work metho will be called before pausing the SM until the next work time.

        Use this method to destroy any resources that should not be active outside
        the work hours (e.g., the selenium browser). Also see `_resume_work`

        !!! Hint
            You could simply destroy your context and set the SM to the initial state:
            ```python
            self.current_state = self.initial_state
            # reset context
            self.destroy_context()
            ```
        """

    def _resume_work(self):
        """The resume work method will be called before resuming work after sleeping.

        Use this method to prepare the state machine to resume after a potentially long
        pause. By default this method does nothing. Also see `_pause_work`.

        !!! Hint
            You could for example configure your state machine to recreate from the initial
            state before resuming work:

            ```python
            self.setup_context()
            ```
        """

    def _wait_for_work(self):
        """Idle until it is time to work again.

        Before returning to the normal state machine flow this
        will also call [`_resume_work`][cr_kyoushi.simulation.sm.WorkHoursStatemachine._resume_work].

        !!! Note
            If the next potential work time is after the machines end time
            it will not sleep, but instead set the current state to `None`
            and let the state machine flow end execution.
        """
        # immediately return if there is no work schedule
        if self.work_schedule is None:
            return

        next_work = self.work_schedule.next_work_start(now())

        # if there is no next work time or the machine will end
        # before the next work we stop immediately
        if next_work is None or (
            self.end_time is not None and self.end_time <= next_work
        ):
            self.current_state = None
        else:
            self.log.info("Pausing state machine")
            self._pause_work()
            self.log.info("Paused state machine")
            # wait til we have work again
            sleep_until(next_work)
            # and then pre-pare to resume work
            self.log.info("Resuming state machine")
            self._resume_work()
            self.log.info("Resumed state machine")

    def execute_step(self):
        """Execute a single state machine step.

        This will only execute a step if the current time is within
        our work schedule. Outside the work time the state machine will
        [wait until work][cr_kyoushi.simulation.sm.WorkHoursStatemachine._wait_for_work] begins again.
        """
        # when we are in work hours business as usual
        if self._in_work_hours():
            super().execute_step()
        # outside of work hours we idle
        else:
            self._wait_for_work()


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
