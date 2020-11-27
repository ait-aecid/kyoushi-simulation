from typing import Optional


class TransitionExecutionError(Exception):
    """Base class for errors that occur during state transitions"""

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        fallback_state: Optional[str] = None,
    ):
        super().__init__(message)
        self.cause = cause
        self.fallback_state = fallback_state

    def __str__(self):
        ret = f"message: '{super().__str__()}'"
        if self.cause:
            ret += f" cause: {self.cause}"
        return ret
