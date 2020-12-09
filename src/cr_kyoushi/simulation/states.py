import random

from abc import ABCMeta
from abc import abstractmethod
from itertools import accumulate
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from .model import Context
from .transitions import Transition
from .util import elements_unique


__all__ = [
    "State",
    "SequentialState",
    "FinalState",
    "ProbabilisticState",
    "EquallyRandomState",
]


class State(metaclass=ABCMeta):
    """A State contains various transitions to other states"""

    @property
    def name(self) -> str:
        return self._name

    @property
    def transitions(self) -> List[Transition]:
        return self._transitions

    def __init__(self, name: str, transitions: List[Transition]):
        self._name = name
        self._transitions = transitions

    @abstractmethod
    def next(self, context: Context) -> Optional[Transition]:
        ...

    def __str__(self):
        return f"name='{self.name}' transitions={self.transitions}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', transitions={self.transitions})"


class SequentialState(State):
    """Simple sequential state only having one possible transition"""

    def __init__(self, name: str, transition: Transition):
        super().__init__(name, [transition])
        self.__transition = transition

    def next(self, context: Context) -> Optional[Transition]:
        return self.__transition


class FinalState(State):
    """State with not further transitions which can be used as final state of a state machine"""

    def __init__(self, name: str):
        super().__init__(name, [])

    def next(self, context: Context) -> Optional[Transition]:
        return None


class ProbabilisticState(State):
    """A state that uses a propability table to select its successor"""

    @property
    def weights(self) -> Sequence[float]:
        return self.__weights

    def __init__(
        self,
        name: str,
        transitions: List[Transition],
        weights: Sequence[Union[int, float]],
        allow_uneven_probabilites: bool = False,
    ):
        # initial base properties
        super().__init__(name, transitions)

        # convert weights to cumulative weights
        self.__weights = list(accumulate(weights))

        # verify that given weights and transitions are sound
        self.__verify_weights(allow_uneven_probabilites)

    def __verify_weights(self, allow_uneven_probabilites: bool) -> None:
        # check that lengths match
        if len(self.transitions) != len(self.weights):
            raise ValueError(
                f"Size of transitions and weights do not match, \
                got transitions={len(self.transitions)} and weights={len(self.weights)}"
            )
        # if we were given an empty transition list
        # then there is nothing more to check
        if len(self.weights) > 0:
            # if we do not allow uneven probabilites we have to check for them
            if not allow_uneven_probabilites:
                # even probabilities must always sum to 100%
                # we allow definition in 0-1 or 0-100 format
                if self.weights[-1] != 1 and self.weights[-1] != 100:
                    raise ValueError(
                        f"Probabilities are uneven, sum of weights must \
                            be either 1 or 100, but got {self.weights[-1]}!"
                    )

            # check that transitions are unique
            if not elements_unique(self.transitions):
                raise ValueError(
                    "The transition list must not contain duplicate elements!"
                )

    def next(self, context: Context) -> Optional[Transition]:
        if len(self.transitions) > 0:
            return random.choices(self.transitions, cum_weights=self.weights, k=1)[0]
        return None


class EquallyRandomState(ProbabilisticState):
    """Special type of probabilistic state using an equal random distribution for all transitions"""

    def __init__(self, name: str, transitions: List[Transition]):
        # create even random distribution
        probability = 1.0 / len(transitions)
        weights = [probability for i in range(0, len(transitions))]
        # initialize using super
        super().__init__(name, transitions, weights)
