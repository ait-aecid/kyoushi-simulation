from typing import Optional

from structlog import BoundLogger

from cr_kyoushi.simulation.errors import TransitionExecutionError
from cr_kyoushi.simulation.logging import get_logger
from cr_kyoushi.simulation.model import Context


logger = get_logger()


class Noop:
    def __call__(
        self,
        log: BoundLogger,
        current_state: str,
        context: Context,
        target: Optional[str] = None,
    ):
        pass


def noop(
    log: BoundLogger,
    current_state: str,
    context: Context,
    target: Optional[str] = None,
):
    pass


def debug_transition(
    self,
    log: BoundLogger,
    current_state: str,
    context: Context,
    target: Optional[str] = None,
):
    logger.debug("executing %s -- %s --> %s", current_state, self._name, self._target)


def exception_function_stub(
    log: BoundLogger,
    current_state: str,
    context: Context,
    target: Optional[str] = None,
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
        self,
        log: BoundLogger,
        current_state: str,
        context: Context,
        target: Optional[str] = None,
    ):
        raise TransitionExecutionError(
            message="Transition failed!",
            cause=self.cause,
            fallback_state=self.fallback_state,
        )
