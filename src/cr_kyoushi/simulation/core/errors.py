from typing import Optional
from typing import Type

from click import ClickException
from pydantic import ValidationError
from pydantic.error_wrappers import display_errors


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


class ConfigValidationError(ClickException):
    def __init__(self, cause: ValidationError):
        formated_errors = display_errors(cause.errors())
        super().__init__(
            f"Failed to validate the configuration file.\n{formated_errors}"
        )
        self.__cause__ = cause


class StatemachineFactoryLoadError(ClickException):
    def __init__(self, factory_name: str):
        super().__init__(message=f"Failed to load sm factory: '{factory_name}'")


class StatemachineFactoryTypeError(ClickException):
    def __init__(self, factory_type: Type):
        super().__init__(
            message=f"Failed to load sm factory plugin got invalid type: '{factory_type}'"
        )
