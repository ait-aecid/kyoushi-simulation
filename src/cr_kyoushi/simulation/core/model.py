from datetime import datetime
from datetime import time
from enum import IntEnum
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Set
from typing import Union

from pydantic import BaseModel


if TYPE_CHECKING:
    from pydantic.typing import AnyCallable

    CallableGenerator = Generator[AnyCallable, None, None]

Config = Dict[str, Any]
Context = Dict[str, Any]


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
    def validate(cls, v: Union[str, int, "Weekday"]):
        if isinstance(v, Weekday):

            return v.value
        elif isinstance(v, int):
            if v in cls.lookup().values():
                return v
            else:
                raise ValueError("invalid integer weekday")
        else:
            try:
                return cls.lookup()[v.upper()]
            except KeyError:
                raise ValueError("invalid string weekday")


class TimePeriod(BaseModel):
    start_time: time
    end_time: time

    def in_period(self, to_check: time) -> bool:
        if self.start_time <= self.end_time:
            return self.start_time <= to_check and self.end_time > to_check
        else:
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

    def __eq__(self, other):
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
