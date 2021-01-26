from abc import ABCMeta
from abc import abstractmethod
from itertools import cycle
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence

import numpy as np

from structlog.stdlib import BoundLogger

from .model import Context
from .transitions import Transition


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
        """The name of the state instance (names must be uniq within a state machine)."""
        return self._name

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

    def __init__(self, name: str, transitions: List[Transition]):
        """
        Args:
            name (str): The state name
            transitions (List[Transition]): List of possible transitions

        Raises:
            ValueError: If there are transitions with duplicate names
        """
        self._name = name
        self._transitions = {t.name: t for t in transitions}

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

    def __init__(self, name: str, transition: Transition):
        """
        Args:
            name: The state name
            transition: The target transition

        Raises:
            ValueError: If transition is None
        """
        if transition is None:
            raise ValueError("Transition must not be None")

        super().__init__(name, [transition])
        self.__transition = transition

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        return self.__transition


class FinalState(State):
    """State with not further transitions which can be used as final state of a state machine"""

    def __init__(self, name: str):
        """
        Args:
            name: The state name
        """
        super().__init__(name, [])

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        return None


class RoundRobinState(State):
    def __init__(self, name: str, transitions: List[Transition]):
        """
        Args:
            name (str): The state name
            transitions (List[Transition]): List of transitions to cycle through

        Raises:
            ValueError: If there are transitions with duplicate names
        """
        super().__init__(name, transitions)
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
        """The cumulative weights assigned to the transitions."""
        return self.__weights

    def __init__(
        self,
        name: str,
        transitions: List[Transition],
        weights: Sequence[float],
    ):
        """
        Args:
            name: The state name
            transitions: The list of transitions
            weights: The list of weights to assign to the transitions in probability notation.

        Raises:
            ValueError: If there are transitions with duplicate names
            ValueError: If the weights and transitions list lengths do not match
            ValueError: If the given weights do not sum up to 1
        """
        # initial base properties
        super().__init__(name, transitions)

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
            # even probabilities must always sum to 1
            if sum(self.weights) != 1:
                raise ValueError(
                    "Probabilities are uneven, sum of weights must be 1,"
                    f" but got {self.weights[-1]}!"
                )

    def next(self, log: BoundLogger, context: Context) -> Optional[Transition]:
        if len(self.transitions) > 0:
            return np.random.choice(a=self.transitions, p=self.weights)
        return None


class EquallyRandomState(ProbabilisticState):
    """Special type of probabilistic state using an equal random distribution for all transitions"""

    def __init__(self, name: str, transitions: List[Transition]):
        """
        Args:
            name: The state name
            transitions: The list of transitions

        Raises:
            ValueError: If there are transitions with duplicate names
        """
        # create even random distribution
        probability = 1.0 / len(transitions)
        weights = [probability for i in range(0, len(transitions))]
        # initialize using super
        super().__init__(name, transitions, weights)
