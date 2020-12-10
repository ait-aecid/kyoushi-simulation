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

Context = Union[BaseModel, Dict[str, Any]]


class PluginConfig(BaseModel):
    include_names: List[Pattern] = [re.compile(r".*")]
    exclude_names: List[Pattern] = []


class Config(GenericModel, Generic[StatemachineConfig]):
    plugin: PluginConfig = PluginConfig()
    sm: StatemachineConfig


class Weekday(IntEnum):
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
    start_time: time = Field(description="The start time of the period")
    end_time: time = Field(description="The end time of the period")

    def in_period(self, to_check: time) -> bool:
        if self.start_time <= self.end_time:
            return self.start_time <= to_check and self.end_time > to_check
        # start > end means our time period is between two days
        return self.start_time <= to_check or self.end_time > to_check


class WeekdayActivePeriod(BaseModel):
    week_day: Weekday
    time_period: Optional[TimePeriod]

    def in_active_period(self, to_check: datetime) -> bool:
        return to_check.weekday() is self.week_day and (
            self.time_period is None or self.time_period.in_period(to_check.time())
        )

    def __hash__(self):
        return hash(self.week_day)

    def __eq__(self, other) -> bool:
        return self.__class__ == other.__class__ and self.week_day == other.week_day


class ComplexActivePeriod(BaseModel):
    week_days: Set[WeekdayActivePeriod]

    def in_active_period(self, to_check: datetime) -> bool:
        return any(period.in_active_period(to_check) for period in self.week_days)


class SimpleActivePeriod(BaseModel):
    week_days: Set[Weekday]
    time_period: Optional[TimePeriod]

    def in_active_period(self, to_check: datetime) -> bool:
        return to_check.weekday() in self.week_days and (
            self.time_period is None or self.time_period.in_period(to_check.time())
        )


class ActivePeriod(BaseModel):
    __root__: Union[ComplexActivePeriod, SimpleActivePeriod]

    def in_active_period(self, to_check: datetime) -> bool:
        return self.__root__.in_active_period(to_check)
