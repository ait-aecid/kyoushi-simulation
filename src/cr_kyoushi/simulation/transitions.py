import sys

from types import FunctionType
from typing import (
    Callable,
    Optional,
    Union,
)

from structlog.stdlib import BoundLogger


if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from .model import (
    ApproximateFloat,
    Context,
)
from .util import sleep


__all__ = [
    "Transition",
    "DelayedTransition",
    "transition",
    "delayed_transition",
    "NoopTransition",
    "noop",
]


class TransitionFunction(Protocol):
    def __call__(
        self,
        log: BoundLogger,
        current_state: str,
        context: Context,
        target: Optional[str],
    ):
        """

        Args:
            log: The bound logger initialized with transition specific information
            current_state: The calling states name
            context: The state machine context
            target: The target state

        Raises:
            TransitionExecutionError: If a transition error occurs for which we can fallback into a valid state
        """


class Transition:
    """Abstract base Transition class describes a transition from one state into another"""

    @property
    def name(self) -> str:
        """The name of the transition (including the prefix)"""
        if self._name_prefix is not None:
            return f"{self._name_prefix}_{self._name}"
        return self._name

    @property
    def name_only(self) -> str:
        """The name of the transition"""
        return self._name

    @property
    def name_prefix(self) -> Optional[str]:
        """The name prefix of the transition instance."""
        return self._name_prefix

    @property
    def target(self) -> Optional[str]:
        """The target state of the transition"""
        return self._target

    @property
    def transition_function(self) -> TransitionFunction:
        """The transition function"""
        return self._transition_function

    def __init__(
        self,
        transition_function: TransitionFunction,
        name: Optional[str] = None,
        target: Optional[str] = None,
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            transition_function: The transition function to call upon execution
            name: The transition name
            target: The target state
            name_prefix: A prefix for the transition name
        """
        if name is None:
            if isinstance(transition_function, FunctionType):
                name = transition_function.__name__.lower()
            else:
                name = transition_function.__class__.__name__.lower()

        self._transition_function: TransitionFunction = transition_function
        self._name: str = name
        self._name_prefix: Optional[str] = name_prefix
        self._target: Optional[str] = target

    def execute(
        self,
        log: BoundLogger,
        current_state: str,
        context: Context,
    ) -> Optional[str]:
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
            log: The bound logger initialized with transition specific information
            current_state: The calling states name
            context: The state machine context

        Returns:
            The state the machine has moved to

        Raises:
            TransitionExecutionError: If a transition error occurs for which we can fallback into a valid state
        """
        self.transition_function(log, current_state, context, self.target)
        return self.target

    def __str__(self):
        return f"name='{self.name}' -> target={self.target}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', target={self.target})"


def transition(
    name: Optional[str] = None,
    target: Optional[str] = None,
    name_prefix: Optional[str] = None,
) -> Callable[[TransitionFunction], Transition]:
    """Transition decorator that can be used to turn a
    [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction] into a
    [`Transition`][cr_kyoushi.simulation.transitions.Transition].

    Args:
        name: The name of the transition
        target: The target states name
        name_prefix: A prefix for the transition name


    Example:
        ```python
            @transition(name="example", target="next")
            def example(current_state, context, target):
                ...

            # the above is equivalent to
            def example_func(current_state, context, target):
                ...

            example = Transition(example_func, name="example", target="next")
        ```

    Returns:
        A decorator that turns a [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction]
        into a Transition initialized with the given args.
    """

    def decorator(func: TransitionFunction) -> Transition:
        return Transition(
            transition_function=func, target=target, name=name, name_prefix=name_prefix
        )

    return decorator


class DelayedTransition(Transition):
    """
    Abstract DelayedTransition allows configuring skipable
    pre and post transition execution delays.
    """

    @property
    def delay_before(self) -> ApproximateFloat:
        """The amount of time in seconds to delay before execution"""
        return self._delay_before

    @property
    def delay_after(self) -> ApproximateFloat:
        """The amount of time in seconds to delay after execution"""
        return self._delay_after

    def __init__(
        self,
        transition_function: TransitionFunction,
        name: Optional[str] = None,
        target: Optional[str] = None,
        delay_before: Union[ApproximateFloat, float] = 0.0,
        delay_after: Union[ApproximateFloat, float] = 0.0,
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The transition name
            transition_function: The transition function to call upon execution
            target: The target state
            delay_before: The pre execution delay to configure
            delay_after: The post execution delay to configure
            name_prefix: A prefix for the transition name
        """
        super().__init__(transition_function, name, target, name_prefix)

        if isinstance(delay_before, float):
            delay_before = ApproximateFloat.convert(delay_before)

        if isinstance(delay_after, float):
            delay_after = ApproximateFloat.convert(delay_after)

        self._delay_before = delay_before
        self._delay_after = delay_after

    def execute(
        self,
        log: BoundLogger,
        current_state: str,
        context: Context,
    ) -> Optional[str]:
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
            log: The bound logger initialized with transition specific information
            current_state: The calling states name
            context: The state machine context

        Returns:
            The state the machine has moved to

        Raises:
            TransitionExecutionError: If a transition error occurs for which we can fallback into a valid state
        """
        sleep(self.delay_before)
        next_state = super().execute(log, current_state, context)
        sleep(self.delay_after)
        return next_state


def delayed_transition(
    name: Optional[str] = None,
    target: Optional[str] = None,
    delay_before: Union[ApproximateFloat, float] = 0.0,
    delay_after: Union[ApproximateFloat, float] = 0.0,
    name_prefix: Optional[str] = None,
) -> Callable[[TransitionFunction], DelayedTransition]:
    """Transition decorator that can be used to turn a
    [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction] into a
    [`DelayedTransition`][cr_kyoushi.simulation.transitions.DelayedTransition].

    Args:
        name: The name of the transition
        target: The target states name
        delay_before: The pre execution delay to configure
        delay_after: The post execution delay to configure
        name_prefix: A prefix for the transition name

    Example:
        ```python
            @delayed_transition(name="example", target="next", delay_before=1.5)
            def example(current_state, context, target):
                ...

            # the above is equivalent to
            def example_func(current_state, context, target):
                ...

            example = DelayedTransition(example_func, name="example", target="next", delay_before=1.5)
        ```

    Returns:
        A decorator that turns a [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction]
        into a DelayedTransition initialized with the given args.
    """

    def decorator(func: TransitionFunction) -> DelayedTransition:
        return DelayedTransition(
            transition_function=func,
            target=target,
            name=name,
            delay_before=delay_before,
            delay_after=delay_after,
            name_prefix=name_prefix,
        )

    return decorator


def noop(log: BoundLogger, current_state: str, context: Context, target: Optional[str]):
    """No operation transition function"""


class NoopTransition(Transition):
    """No noperation transition that only changes the current state."""

    def __init__(
        self,
        name: str = "noop",
        target: Optional[str] = None,
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The name of the transition
            target: The name of the target state
            name_prefix: A prefix for the transition name
        """
        super().__init__(noop, name=name, target=target, name_prefix=name_prefix)
