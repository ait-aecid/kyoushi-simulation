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
        assert len(v) > 0, "too few cities, must at least have 1 city"
        return v

    @validator("desired_weather")
    def validate_desired_weather_exists(cls, v, values, **kwargs):
        # if cities is not in values then it failed to validate
        # so we do nothing
        if "cities" in values and v not in values["cities"].values():
            raise TypeError(f"Impossible no city with the desired weather {v}")
        return v


class SayHello:
    def __init__(self, traveler_name: StrictStr, desired_weather: Weather):
        self.traveler_name = traveler_name
        self.desired_weather = desired_weather

    def __call__(
        self,
        current_state: str,
        context: TravelerContext,
        target: Optional[str],
    ):
        print(
            f"Hi I am {self.traveler_name}. "
            + f"I like to travel to cities that have {self.desired_weather} weather."
        )


class SelectRandomCity:
    """Transition function that randomly selects a city from the configured list"""

    def __init__(self, cities: List[str]):
        self.cities = cities

    def __call__(
        self,
        current_state: str,
        context: TravelerContext,
        target: Optional[str],
    ):
        context.chosen_city = StrictStr(random.choice(self.cities))
        print(f"Maybe I will travel to somewhere in {context.chosen_city}.")


class CheckWeatherMap:
    def __init__(self, weather_map: Dict[StrictStr, Weather]):
        self.weather_map = weather_map

    def __call__(
        self,
        current_state: str,
        context: TravelerContext,
        target: Optional[str],
    ):
        context.weather = self.weather_map[StrictStr(context.chosen_city)]
        print(f"The weather is {context.weather} in {context.chosen_city}")


def goto_city_transition(
    current_state: str,
    context: TravelerContext,
    target: Optional[str],
):
    print(f"The weather is ok so I am going to {context.chosen_city} now ...")


def do_not_go_transition(
    current_state: str,
    context: TravelerContext,
    target: Optional[str],
):
    print(f"I don't like the weather in {context.chosen_city} so I am not going ...")
    context.chosen_city = None
    context.weather = None


def arrive_transition(
    current_state: str,
    context: TravelerContext,
    target: Optional[str],
):
    print(
        f"I have arrived in {context.chosen_city} the weather is {context.weather} just how I like it."
    )
    context.current_location = context.chosen_city
    context.chosen_city = None
    context.weather = None


class SleepInCity:
    def __init__(self, traveler_name: StrictStr):
        self.traveler_name = traveler_name

    def __call__(
        self,
        current_state: str,
        context: TravelerContext,
        target: Optional[str],
    ):
        print(f"I {self.traveler_name} have travelled enough for now.")
        print(f"I am going to sleep in {context.current_location} ...")
        print("... zzzZZZzz ...")


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


class TravelerStatemachine(sm.Statemachine):
    def setup_context(self):
        self.context = TravelerContext()


class StatemachineFactory(sm.StatemachineFactory):
    @property
    def name(self) -> str:
        return "TravelerStatemachineFactory"

    @property
    def config_class(self):
        return TravelerConfig

    def build(self, config: TravelerConfig):

        # Stateful transition functions init
        # ----------------------------------

        say_hello = SayHello(
            traveler_name=config.traveler,
            desired_weather=config.desired_weather,
        )

        select_random_city = SelectRandomCity(cities=list(config.cities.keys()))

        check_weather_on_map = CheckWeatherMap(weather_map=config.cities)

        sleep_in_city = SleepInCity(traveler_name=config.traveler)

        # Transitions
        # ----------------------------------

        hello = transitions.Transition(
            name="hello",
            transition_function=say_hello,
            target="selecting_city",
        )

        select_city = transitions.DelayedTransition(
            name="select_city",
            transition_function=select_random_city,
            target="researching",
            delay_after=3,
        )

        check_weather = transitions.DelayedTransition(
            name="check_weather",
            transition_function=check_weather_on_map,
            target="deciding",
            delay_before=1,
            delay_after=1,
        )

        going_to_city = transitions.DelayedTransition(
            name="going_to_city",
            transition_function=goto_city_transition,
            target="traveling",
            delay_after=10,
        )

        not_going = transitions.DelayedTransition(
            name="not_going",
            transition_function=do_not_go_transition,
            target="selecting_city",
            delay_before=2,
        )
        arrive_in_city = transitions.Transition(
            name="arrive",
            transition_function=arrive_transition,
            target="in_city",
        )

        going_to_sleep = transitions.DelayedTransition(
            name="going_to_sleep",
            transition_function=sleep_in_city,
            target="sleeping",
            delay_before=3.5,
        )

        # States
        # ----------------------------------
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

        # Initialize the state machine
        return TravelerStatemachine(
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
