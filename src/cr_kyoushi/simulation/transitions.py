from abc import ABCMeta
from abc import abstractmethod
from typing import Optional

from .model import Context


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

    @abstractmethod
    def execute(self, current_state: str, context: Context) -> Optional[str]:
        ...

    def __str__(self):
        return f"name='{self.name}' -> target={self.target}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', target={self.target})"
