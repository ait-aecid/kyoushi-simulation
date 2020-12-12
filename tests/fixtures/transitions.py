from typing import Optional

from cr_kyoushi.simulation.errors import TransitionExecutionError
from cr_kyoushi.simulation.model import Context


def noop(current_state: str, context: Context, target: Optional[str] = None):
    pass


def exception_function_stub(
    current_state: str, context: Context, target: Optional[str] = None
):
    raise Exception("Impossible transition")


class FallbackFunctionStub:
    def __init__(
        self,
        fallback_state: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        self.fallback_state = fallback_state
        self.cause = cause

    def __call__(
        self, current_state: str, context: Context, target: Optional[str] = None
    ):
        raise TransitionExecutionError(
            message="Transition failed!",
            cause=self.cause,
            fallback_state=self.fallback_state,
        )
