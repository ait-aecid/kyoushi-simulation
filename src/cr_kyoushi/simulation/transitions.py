from abc import ABCMeta
from abc import abstractmethod
from typing import Optional

from .model import Context
from .util import sleep


__all__ = ["Transition"]


class Transition(metaclass=ABCMeta):
    """The Transition class describes a transition from one state into another"""

    @property
    def name(self) -> str:
        return self._name

    @property
    def target(self) -> Optional[str]:
        return self._target

    def __init__(self, name: str, target: Optional[str] = None):
        self._name = name
        self._target = target

    def execute(self, current_state: str, context: Context) -> Optional[str]:
        return self.execute_transition(current_state, context)

    @abstractmethod
    def execute_transition(self, current_state: str, context: Context) -> Optional[str]:
        ...

    def __str__(self):
        return f"name='{self.name}' -> target={self.target}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', target={self.target})"


class DelayedTransition(Transition):
    @property
    def delay_before(self) -> float:
        return self._delay_before

    @property
    def delay_after(self) -> float:
        return self._delay_after

    def __init__(
        self,
        name: str,
        target: Optional[str] = None,
        delay_before: float = 0.0,
        delay_after: float = 0.0,
    ):
        super().__init__(name, target)
        self._delay_before = delay_before
        self._delay_after = delay_after

    def execute(self, current_state, context) -> Optional[str]:
        sleep(self.delay_before)
        next_state = super().execute(current_state, context)
        sleep(self.delay_after)
        return next_state
