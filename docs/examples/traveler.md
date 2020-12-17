# Traveler Example
{% macro image_url(url) %}
{%- if config.site_url|length -%}
{{ config.site_url }}{{ url }}
{%- else -%}
{{ fix_url(url) }}
{%- endif -%}
{% endmacro %}

{% set image_prefix = config.site_url if config.site_url|length else "" %}

!!! Hint
    See the [examples directory]({{ config.repo_url }}-/tree/master/examples/traveler) for the full code example.

This example implements the following basic state machine that simulates a choosy traveler. The traveler in this example likes to travel to various cities, but only if the current weather there is the weather they like. Also sometimes the traveler gets tired and will go to sleep in the city they are currently in.

<figure>
  <a data-fancybox="gallery" href="{{ image_url("images/traveler.svg") }}">
  <img src="{{ image_url("images/traveler.svg") }}" alt="Traveler state machine" />
  <figcaption>Traveler state machine</figcaption>
  </a>
</figure>

## Configuration

For the traveler 3 things need to be configured:

- The travelers name so they can say hello
- The type of weather they like
- The weather map

This is achieved by defining a Pydantic Model containing all the fields and type definitions for the configuration.

```python
class TravelerConfig(BaseModel):
    traveler: StrictStr = Field(StrictStr("Bob"), description="The travelers name")
    cities: Dict[StrictStr, Weather] = Field(
        description="A dictionary of cities mapped to their current weather"
    )
    desired_weather: Weather = Field(description="The weather the traveler likes")
```

??? Hint "Weather Enum"

    In the traveler example the weather is defined in the form of an `Enum`.
    The enum uses a custom pydantic validate method to allow case insensitive configuration input.
    For example any of the following would be valid `Weather`:

    - `heavy rain`
    - `HEAVY RAIN`
    - `heAVY raIN`

    ```python
    class Weather(str, Enum)
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
        def validate(cls, val: str) -> "Weather":
            """Custom case insensitive value enum validator"""
            if isinstance(val, Weather):
                return val

            if isinstance(val, str):
                try:
                    enum_v = Weather(val.upper())
                except ValueError:
                    raise EnumMemberError(enum_values=list(Weather))
                return enum_v
            raise EnumMemberError(enum_values=list(Weather))
    ```


Using custom validators we can also define additional validation e.g., to ensure that there is at least one city configured
and there is at least one city with weather the traveler likes.

```python
    @validator("cities")
    def validate_cities(cls, v: Dict[StrictStr, Weather]) -> Dict[StrictStr, Weather]:
        """Custom validation method for checking that at least **one** city was configured"""
        assert len(v) > 0, "too few cities, must at least have 1 city"
        return v

    @validator("desired_weather")
    def validate_desired_weather_exists(cls, v, values, **kwargs):
        """Custom validation method for checking that at lease one city has the weather the traveler likes"""
        # if cities is not in values then it failed to validate
        # so we do nothing
        if "cities" in values and v not in values["cities"].values():
            raise TypeError(f"Impossible no city with the desired weather {v}")
        return v
```

## Context

Similarly to the configuration we also define a Pydantic Model for out state machine context.
Here we store context information that is used in multiple transitions.
In theory we could use the context to store **all** information, but for the purposes of this example we will
also show case how to create stateful transition functions that do not rely on the state machine context.
Such stateful transition functions can be useful if you have want your transition functions to behave differently depending on
the passed configuration options. They can also be a useful to prevent the context from growing to large due large amount of
fields which are only used by a single transition function.

```python
class TravelerContext(BaseModel):
    current_location: Optional[StrictStr] = Field(
        None, description="The current location of the traveler."
    )
    chosen_city: Optional[StrictStr] = Field(
        description="The city the traveler as chosen as potential travel destination."
    )
    weather: Optional[Weather] = Field(
        description="The weather in the chosen city according to the travelers research."
    )
```

For the traveler state machine we use the context to share the **current location**, **city** and
the **weather** in the city across multiple transitions.

## Transition Functions

Now that we have prepared our state machine config and context models we have to prepare our transition functions.
If you refer to the state machine diagram above you can see that we need 7 functions in total.
We need functions for the following transitions:

1. `hello`: For this transition we will print the **name** of our traveler and what kind of **weather** they like.
2. `select_city`: Here our traveler will randomly choose a potential travel destination from the list of cities.
3. `check_weather`: After choosing a destination they will have to check the weather in the city.
4. `going_to_city`: Should the weather be to our travelers liking they will tell us so and that they are going to the city.
5. `not_going`: Should it not be to their liking then the traveler will inform us that they changed their mind.
6. `arrive`: Once the traveler has arrived the city they again will inform us.
7. `going_to_sleep`: Finally should the traveler have grown tiered of traveling for the day they will let us know and then go to sleep.

!!! Note
    The transition functions below do not adhere to the order of the list above. Instead they are grouped based
    on function type to show case the difference between stateless and stateful transition functions

### Stateless Transition Functions

Stateless transition functions are simply functions that follow the function signature provided by
the [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction] protocol.
For the sake of the example we will keep the actual implementation of our transitions simple.
Our traveler will mostly just print their current actions to the terminal.


4\. To print the city we are going to we simply the to read the passed `TravelerContext`.

```python
def goto_city_transition(
    current_state: str,
    context: TravelerContext,
    target: Optional[str],
):
    print(f"The weather is ok so I am going to {context.chosen_city} now ...")
```

5\. When the traveler decides to not go to the choses city we also have to reset the **city** and **weather** context attributes.

```python
def do_not_go_transition(
    current_state: str,
    context: TravelerContext,
    target: Optional[str],
):
    print(f"I don't like the weather in {context.chosen_city} so I am not going ...")
    context.chosen_city = None
    context.weather = None
```

6\. Similarly when we arrive in a city we have to set it in the context and reset our selection information.

```python
def arrive_transition(
    current_state: str,
    context: TravelerContext,
    target: Optional[str]
):
    print(
        f"I have arrived in {context.chosen_city} the weather" +
        f" is {context.weather} just how I like it."
    )
    context.current_location = context.chosen_city
    context.chosen_city = None
    context.weather = None
```

### Stateful Transition Functions

Stateful transition functions implement the [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction]
protocol through callable objects instead of using simple functions. To define such a callable objects one has only define a
[`__call__(self[, args...])`](https://docs.python.org/3/reference/datamodel.html#object.__call__) method.

!!! Note
    Since stateful transition functions are classes you have to create an object instance to use one.

1\. For our hello transition function we create a stateful transition function so that we can initialize
    it with the travelers name and desired weather.

```python
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
```

2\. To select a random city we have to initialize our function with a list of cities obtained from the weather map.

```python
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
```

3\. To check the weather we need access to the whole weather map.

```python
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
```

7\. Similarly to the hello function for the message we need the travelers name in addition to the their current location.

```python
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
```

## Custom State and Context Setup

As shown in the state machine diagram above we have a state which selects the successor transition
based on the weather the user likes and the chosen cities weather. Such a conditional can be implemented
by extending the base state and implementing a custom [`State.next(...)`][cr_kyoushi.simulation.states.State.next]
method.

The below custom state is initialized with the two possible transitions and the desired weather.
The `next(...)` function then simply checks if the desired weather matches the currently chosen cities weather.

```python
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

    def next(self, context: TravelerContext) -> Optional[transitions.Transition]:
        if context.weather == self.desired_weather:
            return self.going
        return self.not_going
```
In addition to our custom state class we also need to extend the base state machine class so we can
extend the default state machine [context setup][cr_kyoushi.simulation.sm.Statemachine.setup_context] method.
For our example state machine it is enough to simply initialize the traveler context with its default values.

```python
class TravelerStatemachine(sm.Statemachine):
    def setup_context(self):
        """Initialize traveler context with default values"""
        self.context = TravelerContext()
```

## Transition and State Configuration

The final step is to define the state machine factory and implement the [build][cr_kyoushi.simulation.sm.StatemachineFactory.build] method.

To define the factory we need to set the factory [name][cr_kyoushi.simulation.sm.StatemachineFactory.name] and the
[config class][cr_kyoushi.simulation.sm.StatemachineFactory.config_class].

!!! Important
    The config class must be set to our config type `TravelerConfig`

!!! Important
    Also note that for python file state machine factory plugins the factory class
    **must** be named **StatemachineFactory** for the plugin system to detect it correctly!

```python
class StatemachineFactory(sm.StatemachineFactory):
    @property
    def name(self) -> str:
        return "TravelerStatemachineFactory"

    @property
    def config_class(self):
        return TravelerConfig

    ...
```

!!! Note
    If you wish you can also define multiple helper functions for your various build steps.
    For the purposes of this example we decided to put everything in the main build method.

The first thing we will have to do is initialize all our stateful transition functions using the
traveler config object that is passed to the build method.

```python
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

        ...
```

Next create our transition objects by initializing them with their **unique names**, **transition functions**
and their **target state names**. We decided to use the [`DelayedTransition`][cr_kyoushi.simulation.transitions.DelayedTransition]
for some of our transitions. This special transition type allows us to set pre- and/or post transition execution delays.
For our example this will simulate our travelers thought process and the time it takes them to execute some of their actions.

!!! Tip
    As you can see in the code below we use hardcoded strings for the transition and state names.
    For bigger state machines this can lead to mistakes quickly so we suggest to use centrally defined
    string constants or enums instead.


```python
        ...

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

        ...
```

As final step we have to create our states and initialize the state machine with them.
Our traveler state machine uses four different types of states.

- [`SequentialState`][cr_kyoushi.simulation.states.SequentialState]: This is a simple state that only has one outgoing transition making
  it easy to define a fixed sequence of states.
- [`ProbabilisticState`][cr_kyoushi.simulation.states.ProbabilisticState]: This state type allows us to assign a probability to each outgoing transition, it is very
  useful for defining probabilistic state machines and simulating seemingly random behavior.
- [`FinalState`][cr_kyoushi.simulation.states.FinalState]: As the name states this is a final state with no outgoing transitions, entering this state will stop
  the state machine.
- and our custom `DecidingState` we defined above.

We use a [`ProbabilisticState`][cr_kyoushi.simulation.states.ProbabilisticState] to simulate our traveler getting tired.
Each time they reach a new city there is 30% chance of them going to sleep instead of continuing their travels.

```python
        ...

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
```

## Running the Example

To run the example state machine you can simply use the Cyber Range Kyoushi CLI.

```bash
$ cd examples/traveler
$ cr-kyoushi-sim -c config.yml run -f traveler.py
```
<a data-fancybox="gallery" href="{{ image_url("images/traveler-demo.gif") }}">
<img src="{{ image_url("images/traveler-demo.gif") }}" alt="Traveler State Machine Demo" />
</a>
