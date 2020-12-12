import random

from enum import Enum
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import StrictStr
from pydantic import validator
from pydantic.errors import EnumMemberError

from cr_kyoushi.simulation import sm
from cr_kyoushi.simulation import states
from cr_kyoushi.simulation import transitions


class Weather(str, Enum):
    SNOW = "SNOW"
    SLEET = "SLEET"
    HAIL = "HAIL"
    THUNDERSTORM = "THUNDERSTORM"
    HEAVY_RAIN = "HEAVY RAIN"
    LIGHT_RAIN = "LIGHT RAIN"
    SHOWERS = "SHOWERS"
    HEAVY_CLOUD = "HEAVY CLOUD"
    LIGHT_CLOUD = "LIGHT CLOUD"
    CLEAR = "CLEAR"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val: str):
        """Custom case insensitive enum validator"""
        if isinstance(val, str):
            try:
                enum_v = Weather(val.upper())
            except ValueError:
                # Weather.type_ should be an enum, so will be iterable
                raise EnumMemberError(enum_values=list(Weather))
            return enum_v
        raise EnumMemberError(enum_values=list(Weather))


class TravelerContext(BaseModel):
    current_location: Optional[StrictStr] = None
    chosen_city: Optional[StrictStr]
    weather: Optional[Weather]


class TravelerConfig(BaseModel):
    traveler: StrictStr = StrictStr("Bob")
    cities: Dict[StrictStr, Weather]
    desired_weather: Weather

    @validator("cities")
    def validate_cities(cls, v: Dict[StrictStr, Weather]):
        assert len(v) > 0, "too few cities, must at least know 1 city"
        return v

    @validator("desired_weather")
    def validate_desired_weather_exists(cls, v, values, **kwargs):
        # if cities is not in values then it failed to validate
        # so we do nothing
        if "cities" in values and v not in values["cities"].values():
            raise TypeError(f"Impossible no city with the desired weather {v}")
        return v


class HelloTransition(transitions.Transition):
    def __init__(
        self,
        name: str,
        traveler_name: StrictStr,
        desired_weather: Weather,
        target: Optional[str],
    ):
        super().__init__(name, target)
        self.traveler_name = traveler_name
        self.desired_weather = desired_weather

    def execute_transition(self, current_state: str, context: TravelerContext):
        print(
            f"Hi I am {self.traveler_name}. "
            + f"I like to travel to cities that have {self.desired_weather} weather."
        )
        return self.target


class SelectCityTransition(transitions.DelayedTransition):
    """Transition that randomly selects a city from the configured list"""

    def __init__(
        self,
        name: str,
        cities: List[str],
        target: Optional[str] = None,
        delay_before: float = 0.0,
        delay_after: float = 0.0,
    ):
        super().__init__(
            name, target=target, delay_before=delay_before, delay_after=delay_after
        )
        self.cities = cities

    def execute_transition(self, current_state: str, context: TravelerContext):
        context.chosen_city = StrictStr(random.choice(self.cities))
        print(f"Maybe I will travel to somewhere in {context.chosen_city}.")
        return self.target


class CheckWeatherTransition(transitions.DelayedTransition):
    def __init__(
        self,
        name: str,
        weather_map: Dict[StrictStr, Weather],
        target: Optional[str] = None,
        delay_before: float = 0.0,
        delay_after: float = 0.0,
    ):
        super().__init__(
            name, target=target, delay_before=delay_before, delay_after=delay_after
        )
        self.weather_map = weather_map

    def execute_transition(self, current_state: str, context: TravelerContext):
        context.weather = self.weather_map[StrictStr(context.chosen_city)]
        print(f"The weather is {context.weather} in {context.chosen_city}")
        return self.target


class GotoCityTransition(transitions.DelayedTransition):
    def execute_transition(self, current_state: str, context: TravelerContext):
        print(f"The weather is ok so I am going to {context.chosen_city} now ...")
        return self.target


class DoNotGoTransition(transitions.DelayedTransition):
    def execute_transition(self, current_state: str, context: TravelerContext):
        print(
            f"I don't like the weather in {context.chosen_city} so I am not going ..."
        )
        context.chosen_city = None
        context.weather = None
        return self.target


class ArriveTransition(transitions.Transition):
    def execute_transition(self, current_state: str, context: TravelerContext):
        print(
            f"I have arrived in {context.chosen_city} the weather is {context.weather} just how I like it."
        )
        context.current_location = context.chosen_city
        context.chosen_city = None
        context.weather = None
        return self.target


class GoingToSleepTransition(transitions.DelayedTransition):
    def __init__(
        self,
        name: str,
        traveler_name: StrictStr,
        target: Optional[str] = None,
        delay_before: float = 0.0,
        delay_after: float = 0.0,
    ):
        super().__init__(
            name, target=target, delay_before=delay_before, delay_after=delay_after
        )
        self.traveler_name = traveler_name

    def execute_transition(self, current_state: str, context: TravelerContext):
        print(f"I {self.traveler_name} have travelled enough for now.")
        print(f"I am going to sleep in {context.current_location} ...")
        print("... zzzZZZzz ...")
        return self.target


class DecidingState(states.State):
    def __init__(
        self,
        name: str,
        going: transitions.Transition,
        not_going: transitions.Transition,
        desired_weather: Weather,
    ):
        super().__init__(name, [going, not_going])
        self.going = going
        self.not_going = not_going
        self.desired_weather = desired_weather

    def next(self, context: TravelerContext):
        if context.weather == self.desired_weather:
            return self.going
        return self.not_going


class WeatherStatemachine(sm.Statemachine):
    def setup_context(self):
        self.context = TravelerContext()


class StatemachineFactory(sm.StatemachineFactory):
    @property
    def name(self) -> str:
        return "WeatherStatemachineFactory"

    @property
    def config_class(self):
        return TravelerConfig

    def build(self, config: TravelerConfig):

        hello = HelloTransition(
            name="hello",
            traveler_name=config.traveler,
            desired_weather=config.desired_weather,
            target="selecting_city",
        )

        select_city = SelectCityTransition(
            "select_city",
            cities=list(config.cities.keys()),
            target="researching",
            delay_after=3,
        )
        check_weather = CheckWeatherTransition(
            "check_weather",
            weather_map=config.cities,
            target="deciding",
            delay_before=1,
            delay_after=1,
        )

        going_to_city = GotoCityTransition(
            "going_to_city", target="traveling", delay_after=10
        )
        not_going = DoNotGoTransition(
            "not_going", target="selecting_city", delay_before=2
        )
        arrive_in_city = ArriveTransition("arrive", "in_city")
        going_to_sleep = GoingToSleepTransition(
            "going_to_sleep", config.traveler, target="sleeping", delay_before=3.5
        )

        initial = states.SequentialState("initial", hello)
        selecting_city = states.SequentialState("selecting_city", select_city)
        researching = states.SequentialState("researching", check_weather)
        deciding = DecidingState(
            "deciding",
            going=going_to_city,
            not_going=not_going,
            desired_weather=config.desired_weather,
        )
        traveling = states.SequentialState("traveling", arrive_in_city)
        in_city = states.ProbabilisticState(
            "in_city", [going_to_sleep, select_city], [0.3, 0.7]
        )

        sleeping = states.FinalState("sleeping")

        return WeatherStatemachine(
            "initial",
            [
                initial,
                selecting_city,
                researching,
                deciding,
                traveling,
                in_city,
                sleeping,
            ],
        )
