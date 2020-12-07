from abc import ABCMeta
from abc import abstractmethod
from typing import Optional

from .model import Context


__all__ = ["Transition"]


class Transition(metaclass=ABCMeta):
    """The Transition class describes a transition from one state into another"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def target(self) -> Optional[str]:
        ...

    @abstractmethod
    def execute(self, current_state: str, context: Context) -> Optional[str]:
        ...

    def __str__(self):
        return f"name='{self.name}' -> target={self.target}"

    def __repr__(self):
        return f"{self.name}(name='{self.name}', target={self.target})"
