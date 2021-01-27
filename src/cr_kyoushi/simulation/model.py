import logging
import random

from datetime import (
    datetime,
    time,
    timedelta,
)
from enum import IntEnum
from typing import (
    Any,
    Dict,
    Optional,
    Set,
    TypeVar,
    Union,
)

from pydantic import (
    BaseModel,
    Field,
    validator,
)


__all__ = [
    "StatemachineConfig",
    "Context",
    "Weekday",
    "TimePeriod",
    "WeekdayActivePeriod",
    "ComplexActivePeriod",
    "SimpleActivePeriod",
    "ActivePeriod",
    "ApproximateFloat",
]

StatemachineConfig = TypeVar("StatemachineConfig", Dict[Any, Any], BaseModel)
"""Placeholder generic type for state machine configurations."""

Context = Union[BaseModel, Dict[str, Any]]
"""
    Contexts are used to store the state machine execution context.

    They can either be a custom defined pydantic model or `Dict[str, Any]`.
"""


class LogLevel(IntEnum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET

    @classmethod
    def lookup(cls):
        return {v: k for v, k in cls.__members__.items()}

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val: Union[str, int, "LogLevel"]):
        """Parses and validates `LogLevel` input in either `str`, `int` or `Enum` encoding.

        Args:
            val: The encoded input log level

        Raises:
            ValueError: if the given input is not a valid log level

        Returns:
            LogLevel enum
        """
        # check enum input
        if isinstance(val, LogLevel):
            return val
        # check int LogLevel input
        if isinstance(val, int):
            if val in cls.lookup().values():
                return LogLevel(val)
            raise ValueError("invalid integer LogLevel")
        # check str LogLevel input
        try:
            return cls.lookup()[val.upper()]
        except KeyError as key_error:
            raise ValueError("invalid string LogLevel") from key_error


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
        return {v: k for v, k in cls.__members__.items()}

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
            Weekday enum
        """
        # check enum input
        if isinstance(val, Weekday):
            return val
        # check int weekday input
        if isinstance(val, int):
            if val in cls.lookup().values():
                return Weekday(val)
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
        return Weekday(to_check.weekday()) is self.week_day and (
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
        return Weekday(to_check.weekday()) in self.week_days and (
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

    @validator("max")
    def validate_min_le_max(cls, v: float, values, **kwargs) -> float:
        """Custom validator to ensure min <= max"""
        assert values["min"] <= v, "Invalid boundaries must be min <= max"
        return v

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


class WorkHours(TimePeriod):
    """A special type of time period that does not allow over night periods"""

    @validator("end_time")
    def validate_start_before_end(
        cls,
        v: time,
        values: Dict[str, Any],
        **kwargs,
    ) -> time:
        """Validates that the start time is before the end time.

        This restricts work hours to be within a single day i.e., work hours
        can not be defined to start on one day and end on the following day.

        Args:
            v: The parsed end time to check
            values: A dictionary containing previously parsed and validated fields.
                    See [Pydantic](https://pydantic-docs.helpmanual.io/usage/validators/) for details.

        Returns:
            The end time if it is valid
        """
        # if start time is not in values it failed to validate
        # so we skip the check and let validation fail
        if "start_time" in values:
            assert values["start_time"] < v, "End time must be after start time"

        return v


class WorkSchedule(BaseModel):
    """A weekly work schedule represented by the week days and work hours for each day"""

    work_days: Dict[Weekday, WorkHours] = Field(
        description="Dictionary containing the work hours for each weekday"
    )

    def is_work_day(self, weekday: Weekday) -> bool:
        """Checks wether the given weekday is a work day.

        Args:
            weekday: The weekday to check encoded as integer (0-6)

        Returns:
            `True` if it is a work day `False` otherwise
        """
        return weekday in self.work_days

    def is_work_time(self, to_check: datetime) -> bool:
        """Checks wether the given datetime is work time.

        Something is considered to be work time if it is a work day
        and the time is within the work hours of that work day.

        Args:
            to_check: The datetime to check

        Returns:
            `True` if the given datetime is work time `False` otherwise
        """
        weekday: Weekday = Weekday(to_check.weekday())
        # check if the datetime is on a work day
        if self.is_work_day(weekday):
            # if its on a workday check if its with the days work hours
            return self.work_days[weekday].in_period(to_check.time())

        return False

    def next_work_start(self, to_check: datetime) -> Optional[datetime]:
        """Gets the next work time, relative to the given datetime.

        If the given datetime is within work hours the start time
        of that work day is returned.

        Args:
            to_check: The datetime to find the next work time for

        Returns:
            The next work time or `None` if there is no work time
        """

        weekday: Weekday = Weekday(to_check.weekday())

        if (
            # if the given datetime is a workday
            self.is_work_day(weekday)
            and (
                # and work has not begun yet
                to_check.time() <= self.work_days[weekday].start_time
                # or if we are still within work time
                # we return the given days start time
                or self.is_work_time(to_check)
            )
        ):
            return datetime.combine(to_check.date(), self.work_days[weekday].start_time)

        # otherwise next work start must be some day after
        # the given day so we check the next 7 days
        # (we might only work once a week)
        for i in range(1, 8):
            # increment weekday and be sure to start from 0 once we pass sunday (int: 6)
            weekday = Weekday((weekday + 1) % 7)
            if self.is_work_day(weekday):
                # add the days till the next work day to the given date
                next_work: datetime = to_check + timedelta(i)
                # get the start time for that day
                start_time = self.work_days[weekday].start_time

                return datetime.combine(next_work.date(), start_time)

        # if we got here then no workday is set so we will never start
        return None
