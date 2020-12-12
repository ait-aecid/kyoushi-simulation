from typing import Optional

from typing_extensions import Protocol

from .model import Context
from .util import sleep


__all__ = ["Transition", "DelayedTransition"]


class ContextFunction(Protocol):
    def __call__(self, current_state: str, context: Context):
        """

        Args:
            current_state: The calling states name
            context: The state machine context

        Raises:
            TransitionExecutionError: If a transition error occurs for which we can fallback into a valid state
        """


class Transition:
    """Abstract base Transition class describes a transition from one state into another"""

    @property
    def name(self) -> str:
        """The name of the transition"""
        return self._name

    @property
    def target(self) -> Optional[str]:
        """The target state of the transition"""
        return self._target

    @property
    def transition_function(self) -> ContextFunction:
        """The transition function"""
        return self._transition_function

    def __init__(
        self,
        name: str,
        transition_function: ContextFunction,
        target: Optional[str] = None,
    ):
        """
        Args:
            name: The transition name
            target: The target state
            transition_function: The transition function to call upon execution
        """
        self._name = name
        self._transition_function = transition_function
        self._target = target

    def execute(self, current_state: str, context: Context) -> Optional[str]:
        """Transition execution function called by the state machine.

        The default behavior is to directly call the configured
        [`transition_function`][cr_kyoushi.simulation.transitions.Transition.transition_function]


        !!! Info
            This function can be overridden or extended to change **how**
            transitions are executed. Actual transition implementations
            should be done via the supplied
            [`transition_function`][cr_kyoushi.simulation.transitions.Transition.transition_function].

        !!! Warning
            Don't forget to call `#!python super().execute(current_state, context)`
            or `#!python self.transition_function(current_state, context)`.

        Args:
            current_state: The calling states name
            context: The state machine context

        Returns:
            The state the machine has moved to

        Raises:
            TransitionExecutionError: If a transition error occurs for which we can fallback into a valid state
        """
        self.transition_function(current_state, context)
        return self.target

    def __str__(self):
        return f"name='{self.name}' -> target={self.target}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', target={self.target})"


class DelayedTransition(Transition):
    """
    Abstract DelayedTransition allows configuring skipable
    pre and post transition execution delays.
    """

    @property
    def delay_before(self) -> float:
        """The amount of time in seconds to delay before execution"""
        return self._delay_before

    @property
    def delay_after(self) -> float:
        """The amount of time in seconds to delay after execution"""
        return self._delay_after

    def __init__(
        self,
        name: str,
        transition_function: ContextFunction,
        target: Optional[str] = None,
        delay_before: float = 0.0,
        delay_after: float = 0.0,
    ):
        """
        Args:
            name: The transition name
            transition_function: The transition function to call upon execution
            target: The target state
            delay_before: The pre execution delay to configure
            delay_after: The post execution delay to configure
        """
        super().__init__(name, transition_function, target)
        self._delay_before = delay_before
        self._delay_after = delay_after

    def execute(self, current_state, context) -> Optional[str]:
        """
        Delayed transition execution sleeps before and after executing the transition.

        Both delays can be configured during initialization.
        The delays use a special [`sleep`][cr_kyoushi.simulation.util.sleep] function that registers a `SIGINT`
        signal handler to make it possible to interrupt and skip the sleep
        phase.

        !!! Note
            When running in a terminal press ++ctrl+c++ to
            *fast forward*.

        Args:
            current_state: The calling states name
            context: The state machine context

        Returns:
            The state the machine has moved to

        Raises:
            TransitionExecutionError: If a transition error occurs for which we can fallback into a valid state
        """
        sleep(self.delay_before)
        next_state = super().execute(current_state, context)
        sleep(self.delay_after)
        return next_state
