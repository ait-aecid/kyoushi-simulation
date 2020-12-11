from abc import ABCMeta
from abc import abstractmethod
from typing import Optional

from .model import Context
from .util import sleep


__all__ = ["Transition", "DelayedTransition"]


class Transition(metaclass=ABCMeta):
    """Abstract base Transition class describes a transition from one state into another"""

    @property
    def name(self) -> str:
        """The name of the transition"""
        return self._name

    @property
    def target(self) -> Optional[str]:
        """The target state of the transition"""
        return self._target

    def __init__(self, name: str, target: Optional[str] = None):
        """
        Args:
            name: The transition name
            target: The target state
        """
        self._name = name
        self._target = target

    def execute(self, current_state: str, context: Context) -> Optional[str]:
        """Transition execution function called by the state machine.

        The default behavior is to directly call `execute_transition(...)`

        !!! Info
            This function can be overridden or extended to change **how**
            transitions are executed. Actual transition implementations
            should be done via `execute_transition`.

        !!! Warning
            Don't forget to call `#!python super().execute(current_state, context)`
            or `#!python execute_transition(current_state, context)` and capture the
            return value, if you override this function.

        Args:
            current_state: The calling states name
            context: The state machine context

        Returns:
            The state the machine has moved to
        """
        return self.execute_transition(current_state, context)

    @abstractmethod
    def execute_transition(self, current_state: str, context: Context) -> Optional[str]:
        """Executes the transition functionality

        This must be implemented by concret transition classes.
        The function is called indirectly by `execution(...)`.

        Args:
            current_state: The calling states name
            context: The state machine context

        Returns:
            The state the machine has moved to
        """
        ...

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
        target: Optional[str] = None,
        delay_before: float = 0.0,
        delay_after: float = 0.0,
    ):
        """
        Args:
            name: The transition name
            target: The target state
            delay_before: The pre execution delay to configure
            delay_after: The post execution delay to configure
        """
        super().__init__(name, target)
        self._delay_before = delay_before
        self._delay_after = delay_after

    def execute(self, current_state, context) -> Optional[str]:
        """
        Delayed transition execution sleeps before and after executing the transition.

        Both delays can be configured during initialization.
        The delays use a special `sleep` function that registers a `SIGINT`
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
        """
        sleep(self.delay_before)
        next_state = super().execute(current_state, context)
        sleep(self.delay_after)
        return next_state
