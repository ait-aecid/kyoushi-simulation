from typing import (
    Optional,
    Type,
)

from click import ClickException
from pydantic import ValidationError
from pydantic.error_wrappers import display_errors


__all__ = [
    "TransitionExecutionError",
    "ConfigValidationError",
    "StatemachineFactoryLoadError",
    "StatemachineFactoryTypeError",
    "SkipSectionError",
]


class TransitionExecutionError(Exception):
    """Base class for errors that occur during state transitions"""

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        fallback_state: Optional[str] = None,
    ):
        """
        Args:
            message: The error message
            cause: The underlying cause of the transition error.
            fallback_state: Optionally the name of the state to fallback to.
        """
        super().__init__(message)
        self.cause = cause
        self.fallback_state = fallback_state

    def __str__(self):
        ret = f"message: '{super().__str__()}'"
        if self.cause:
            ret += f" cause: {self.cause}"
        return ret


class ConfigValidationError(ClickException):
    """CLI exception indicating that the configuration file was not valid"""

    def __init__(self, cause: ValidationError):
        """
        Args:
            cause: Pydantic validation error that caused validation to fail.
        """
        formated_errors = display_errors(cause.errors())
        super().__init__(
            f"Failed to validate the configuration file.\n{formated_errors}"
        )
        self.__cause__ = cause


class StatemachineFactoryLoadError(ClickException):
    """CLI Exception indicating that a sm factory plugin could not be loaded"""

    def __init__(self, factory_name: str):
        """
        Args:
            factory_name: The name of the factory that failed to load
        """
        super().__init__(message=f"Failed to load sm factory: '{factory_name}'")


class StatemachineFactoryTypeError(ClickException):
    """CLI Exception indicating that a type error occurred while loading a sm factory plugin."""

    def __init__(self, factory_type: Type):
        """
        Args:
            factory_type: The python type of the factory that could not be loaded.
        """
        super().__init__(
            message=f"Failed to load sm factory plugin got invalid type: '{factory_type}'"
        )


class SkipSectionError(KeyboardInterrupt):
    """Utility exception to indicate that a task section should be skipped"""
