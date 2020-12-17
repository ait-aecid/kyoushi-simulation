import random
import re

from datetime import datetime
from datetime import time
from enum import IntEnum
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Pattern
from typing import Set
from typing import TypeVar
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic.generics import GenericModel


__all__ = [
    "StatemachineConfig",
    "Context",
    "PluginConfig",
    "Config",
    "Weekday",
    "TimePeriod",
    "WeekdayActivePeriod",
    "ComplexActivePeriod",
    "SimpleActivePeriod",
    "ActivePeriod",
]

StatemachineConfig = TypeVar("StatemachineConfig")
"""Placeholder generic type for state machine configurations."""

Context = Union[BaseModel, Dict[str, Any]]
"""
    Contexts are used to store the state machine execution context.

    They can either be a custom defined pydantic model or `Dict[str, Any]`.
"""


class PluginConfig(BaseModel):
    """Configuration options for the state machine factory plugin system."""

    include_names: List[Pattern] = Field(
        [re.compile(r".*")],
        description="A list of regular expressions used to define which plugins to include.",
    )
    exclude_names: List[Pattern] = Field(
        [],
        description="A list of regular expressions used to define \
        which plugins to explicitly exclude.",
    )


class Config(GenericModel, Generic[StatemachineConfig]):
    """Cyber Range Kyoushi Simulation configuration options"""

    plugin: PluginConfig = Field(
        PluginConfig(), description="The plugin system configuration"
    )
    sm: StatemachineConfig = Field(
        description="The configuration for the state machine"
    )


class Weekday(IntEnum):
    """
    Enumeration for representing the days of the week.

    Weekdays are represented as the integers 0-6 and can
    be constructed from either their int representations or
    their english names.
    """

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def lookup(cls):
        return {v: k.value for v, k in cls.__members__.items()}

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val: Union[str, int, "Weekday"]):
        """Parses and validates `Weekday` input in either `str`, `int` or `Enum` encoding.

        Args:
            val: The encoded input week day

        Raises:
            ValueError: if the given input is not a valid weekday

        Returns:
            [int]: `int` encoded week day
        """
        # check enum input
        if isinstance(val, Weekday):
            return val.value
        # check int weekday input
        if isinstance(val, int):
            if val in cls.lookup().values():
                return val
            raise ValueError("invalid integer weekday")
        # check str weekday input
        try:
            return cls.lookup()[val.upper()]
        except KeyError as key_error:
            raise ValueError("invalid string weekday") from key_error


class TimePeriod(BaseModel):
    """A time period as defined by a start and end time."""

    start_time: time = Field(description="The start time of the period")
    end_time: time = Field(description="The end time of the period")

    def in_period(self, to_check: time) -> bool:
        """Checks wether the given time of the day is within the scope of this time period.

        Args:
            to_check (time): The time of the day to check

        Returns:
            bool: `True` if within the time period `False` otherwise
        """
        if self.start_time <= self.end_time:
            return self.start_time <= to_check and self.end_time > to_check
        # start > end means our time period is between two days
        return self.start_time <= to_check or self.end_time > to_check


class WeekdayActivePeriod(BaseModel):
    """
    A `WeekdayActivePeriod` defines its active time based on the configure week day
    and time period.
    """

    week_day: Weekday = Field(description="The active day of the week")
    time_period: Optional[TimePeriod] = Field(
        description="The active time period (if this is not set the whole day is considered active)"
    )

    def in_active_period(self, to_check: datetime) -> bool:
        """Checks wether the given datetime is within the scope of this active period.

           This will be True if the week day matches and given time of the day is
           within the time period.

        Args:
            to_check (datetime): The datetime to check

        Returns:
            bool: `True` if inside the active period `False` otherwise
        """
        return to_check.weekday() is self.week_day and (
            self.time_period is None or self.time_period.in_period(to_check.time())
        )

    def __hash__(self):
        return hash(self.week_day)

    def __eq__(self, other) -> bool:
        return self.__class__ == other.__class__ and self.week_day == other.week_day


class ComplexActivePeriod(BaseModel):
    """
    A `ComplexActivePeriod` is defined by a set of
    [`WeekdayActivePeriod`][cr_kyoushi.simulation.model.WeekdayActivePeriod].

    This makes it possible to configure active times for each week day separately.
    """

    week_days: Set[WeekdayActivePeriod] = Field(
        description="Set of active periods, each week day can only have one configuration"
    )

    def in_active_period(self, to_check: datetime) -> bool:
        """Checks wether the given datetime is within this active period.

           This is `True` if the datetime is within the scope of **one** of
           the [`WeekdayActivePeriods`][cr_kyoushi.simulation.model.WeekdayActivePeriod].


        Args:
            to_check (datetime): The datetime to check

        Returns:
            bool: `True` if inside the active period `False` otherwise
        """
        return any(period.in_active_period(to_check) for period in self.week_days)


class SimpleActivePeriod(BaseModel):
    """
    Similar to [`ComplexActivePeriod`][cr_kyoushi.simulation.model.ComplexActivePeriod],
    but each week day has the same active time period.
    """

    week_days: Set[Weekday] = Field(description="A set of active week days.")
    time_period: Optional[TimePeriod] = Field(
        description="The daylie active time period \
        (if this is not set the whole days are considered active)."
    )

    def in_active_period(self, to_check: datetime) -> bool:
        """Checks wether the given datetime is within this active period.

           This is `True` if the datetime matches **one** of the active week days
           and the active time period.


        Args:
            to_check (datetime): The datetime to check

        Returns:
            bool: `True` if inside the active period `False` otherwise
        """
        return to_check.weekday() in self.week_days and (
            self.time_period is None or self.time_period.in_period(to_check.time())
        )


class ActivePeriod(BaseModel):
    """Active period union type.

    This class can be used in pydantic models to allow
    loading of [`ComplexActivePeriod`][cr_kyoushi.simulation.model.ComplexActivePeriod]
    or [`SimpleActivePeriod`][cr_kyoushi.simulation.model.SimpleActivePeriod].
    """

    __root__: Union[ComplexActivePeriod, SimpleActivePeriod]

    def in_active_period(self, to_check: datetime) -> bool:
        """Checks wether the given datetime is within this active period.

        The actual check is delegated to the underlying sub types own
        checking logic.

        Args:
            to_check (datetime): The datetime to check

        Returns:
            bool: `True` if inside the active period `False` otherwise
        """
        return self.__root__.in_active_period(to_check)


class ApproximateFloat(BaseModel):
    """Approximate float value within a given open interval"""

    min: float = Field(description="The lower boundary for the float value")
    max: float = Field(description="The upper boundary for the float value")

    @classmethod
    def convert(cls, value: float) -> "ApproximateFloat":
        """Coerces a single float value to its ApproximateFloat equivalent.

        i.e., value = min = max

        Args:
            value: The float value to convert

        Returns:
            `Approximate(min=value, max=value)`
        """
        return ApproximateFloat(min=value, max=value)

    @property
    def value(self) -> float:
        """Gets a random float within the approximate float range

        Returns:
            A float x for which `min <= x <= max`
        """
        return random.uniform(self.min, self.max)
