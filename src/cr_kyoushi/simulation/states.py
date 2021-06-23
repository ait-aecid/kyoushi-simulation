from abc import (
    ABCMeta,
    abstractmethod,
)
from itertools import cycle
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
)

import numpy as np

from structlog.stdlib import BoundLogger

from .model import Context
from .transitions import Transition
from .util import calculate_propabilities


__all__ = [
    "State",
    "SequentialState",
    "FinalState",
    "RoundRobinState",
    "ProbabilisticState",
    "EquallyRandomState",
]


class State(metaclass=ABCMeta):
    """A State contains various transitions to other states"""

    @property
    def name(self) -> str:
        """The name (including the prefix) of the state instance

        Names must be unique within a state machine.
        """
        if self._name_prefix is not None:
            return f"{self._name_prefix}_{self._name}"
        return self._name

    @property
    def name_only(self) -> str:
        """The name of the state instance (names must be uniq within a state machine)."""
        return self._name

    @property
    def name_prefix(self) -> Optional[str]:
        """The name prefix of the state instance."""
        return self._name_prefix

    @property
    def transitions(self) -> List[Transition]:
        """
        List of all possible [`transitions`][cr_kyoushi.simulation.transitions.Transition]
        originating from this state
        """
        return list(self._transitions.values())

    @property
    def transitions_map(self) -> Dict[str, Transition]:
        """
        List of all possible [`transitions`][cr_kyoushi.simulation.transitions.Transition]
        originating from this state
        """
        return self._transitions

    def __init__(
        self,
        name: str,
        transitions: List[Transition],
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The state name
            transitions: List of possible transitions
            name_prefix: A prefix for the state name

        Raises:
            ValueError: If there are transitions with duplicate names
        """
        self._name = name
        self._transitions = {t.name: t for t in transitions}
        self._name_prefix: Optional[str] = name_prefix

        if len(self._transitions) < len(transitions):
            raise ValueError("Transition names must be unique")

    @abstractmethod
    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        """Selects the next state transition.

           The selection logic depends on the state implementation. It might
           rely on the [`state machine context`][cr_kyoushi.simulation.sm.Statemachine.context]
           and/or execution environment information to select transitions based on complex conditions.

        Args:
            log: The bound logger initialized with transition specific information
            context (Context): State machine context which can be used for complex selection logic

        Returns:
            The selected [`Transition`][cr_kyoushi.simulation.transitions.Transition]
            or None if no transition is available.

        """
        ...

    def __str__(self):
        return f"name='{self.name}' transitions={self.transitions}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', transitions={self.transitions})"


class SequentialState(State):
    """Simple sequential state only having one possible transition"""

    def __init__(
        self,
        name: str,
        transition: Transition,
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The state name
            transition: The target transition
            name_prefix: A prefix for the state name

        Raises:
            ValueError: If transition is None
        """
        if transition is None:
            raise ValueError("Transition must not be None")

        super().__init__(name, [transition], name_prefix)
        self.__transition = transition

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        return self.__transition


class ChoiceState(State):
    """Simple boolean choice state decides between two transitions"""

    @property
    def yes(self) -> Transition:
        """The transition that is returned when the decision function returns `True`"""
        return self.transitions[0]

    @property
    def no(self) -> Transition:
        """The transition that is returned when the decision function returns `False`"""
        return self.transitions[1]

    def __init__(
        self,
        name: str,
        decision_function: Callable[[BoundLogger, Context], bool],
        yes: Transition,
        no: Transition,
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The state name
            decision_function: Context function that decides a yes/no question.
            yes: The transition to return when the decision function returns `True`
            no: The transition to return when the decision function returns `False`
            name_prefix: A prefix for the state name
        """
        super().__init__(name, [yes, no], name_prefix)
        self.__decision_function: Callable[
            [BoundLogger, Context], bool
        ] = decision_function

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        return self.yes if self.__decision_function(log, context) else self.no


class FinalState(State):
    """State with not further transitions which can be used as final state of a state machine"""

    def __init__(self, name: str, name_prefix: Optional[str] = None):
        """
        Args:
            name: The state name
            name_prefix: A prefix for the state name
        """
        super().__init__(name, [], name_prefix)

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        return None


class RoundRobinState(State):
    def __init__(
        self,
        name: str,
        transitions: List[Transition],
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name (str): The state name
            transitions (List[Transition]): List of transitions to cycle through
            name_prefix: A prefix for the state name

        Raises:
            ValueError: If there are transitions with duplicate names
        """
        super().__init__(name, transitions, name_prefix)
        self.transition_cycle = cycle(transitions)

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        try:
            return next(self.transition_cycle)
        except StopIteration:
            return None


class ProbabilisticState(State):
    """A state that uses a propability table to select its successor"""

    @property
    def weights(self) -> Sequence[float]:
        """The weight assigned to the transitions."""
        return self.__weights

    def __init__(
        self,
        name: str,
        transitions: List[Transition],
        weights: Sequence[float],
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The state name
            transitions: The list of transitions
            weights: The list of weights to assign to the transitions in probability notation.
            name_prefix: A prefix for the state name

        Raises:
            ValueError: If there are transitions with duplicate names
            ValueError: If the weights and transitions list lengths do not match
            ValueError: If the given weights do not sum up to 1
        """
        # initial base properties
        super().__init__(name, transitions, name_prefix)

        # convert weights to cumulative weights
        self.__weights = weights

        # verify that given weights and transitions are sound
        self.__verify_weights()

    def __verify_weights(self) -> None:
        # check that lengths match
        if len(self.transitions) != len(self.weights):
            raise ValueError(
                f"Size of transitions and weights do not match, \
                got transitions={len(self.transitions)} and weights={len(self.weights)}"
            )
        # if we were given an empty transition list
        # then there is nothing more to check
        if len(self.weights) > 0:
            # check that all probs are positive values
            if any(p < 0 for p in self.weights):
                raise ValueError("Probabilities cannot be negative!")
            # probabilities must always sum to 1
            if abs(1.0 - sum(self.weights)) > 1e-8:
                raise ValueError(
                    "Probabilities are uneven, sum of weights must be 1,"
                    f" but got {self.weights[-1]}!"
                )

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        if len(self.transitions) > 0:
            return np.random.choice(a=np.array(self.transitions), p=self.weights)
        return None


class AdaptiveProbabilisticState(ProbabilisticState):
    """Special probabilistic state that allows modifaction of weights."""

    _modifiers: Dict[Transition, float]

    @property
    def modifiers(self) -> List[float]:
        """The weight modifiers assigned to the transitions."""
        return list(self._modifiers.values())

    @property
    def probabilities(self) -> List[float]:
        """The propabilities based on the weights and modifiers"""
        return calculate_propabilities(self.weights, self.modifiers)

    def __init__(
        self,
        name: str,
        transitions: List[Transition],
        weights: Sequence[float],
        modifiers: Optional[Sequence[float]] = None,
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The name of the state
            transitions: The list of transitions
            weights: The list of weights to assign to the transitions in propability notation
            modifiers: List of multiplicative modifiers for each weight.
                       Will default to all 1 if not set.
            name_prefix: A prefix for the state name
        """
        super().__init__(name, transitions, weights, name_prefix)
        if modifiers is None:
            modifiers = [1.0] * len(self.weights)

        self._modifiers = dict(zip(transitions, list(modifiers)))

        self.__modifiers_org: Tuple[float, ...] = tuple(self.modifiers)

    def adapt_before(self, log: BoundLogger, context: Context):
        """Hook to update the weight modifiers before the transition selection.

        Args:
            log: The logger for the sm context
            context: The state machine context
        """

    def adapt_after(
        self,
        log: BoundLogger,
        context: Context,
        selected: Optional[Transition],
    ):
        """Hook to update the weight modifiers after the transition selection.

        Args:
            log: The logger for the sm context
            context: The state machine context
            selected: The transition selected in this next call
        """

    def reset(self):
        """Resets the modifiers to their original state"""
        self._modifiers = dict(zip(self.transitions, self.__modifiers_org))

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        if len(self.transitions) > 0:
            self.adapt_before(log, context)
            selected = np.random.choice(
                a=np.array(self.transitions), p=self.probabilities
            )
            self.adapt_after(log, context, selected)
            return selected
        return None


class EquallyRandomState(ProbabilisticState):
    """Special type of probabilistic state using an equal random distribution for all transitions"""

    def __init__(
        self,
        name: str,
        transitions: List[Transition],
        name_prefix: Optional[str] = None,
    ):
        """
        Args:
            name: The state name
            transitions: The list of transitions
            name_prefix: A prefix for the state name

        Raises:
            ValueError: If there are transitions with duplicate names
        """
        # create even random distribution
        probability = 1.0 / len(transitions)
        weights = [probability for i in range(0, len(transitions))]
        # initialize using super
        super().__init__(name, transitions, weights, name_prefix)
