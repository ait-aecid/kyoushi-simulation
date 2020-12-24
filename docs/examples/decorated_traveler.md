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
    See the [examples directory]({{ config.repo_url }}-/tree/master/examples/decorated_traveler) for the full code example.

This example is an alternative implementation of the state machine shown in the [traveler example](traveler.md).
The implementation does not use stateful transitions and uses transition decorators as an alternative to creating transition instances in the factory build method.
Here we will only show case the implementation changes for the full example description please take a look at [traveler example](traveler.md).

<figure>
  <a data-fancybox="gallery" href="{{ image_url("images/traveler.svg") }}">
  <img src="{{ image_url("images/traveler.svg") }}" alt="Traveler state machine" />
  <figcaption>Traveler state machine</figcaption>
  </a>
</figure>

## Context

Since we do not use stateful transition functions in this version, we need to provide the configuration options to the
modified transition functions as part of the context. For our simple example it is enough to base our `TravelerContext` on
our `TravelerConfig` instead `BaseModel`. This way `TravelerContext` will inherit all attributes from `TravelerConfig`.

```python
class TravelerContext(TravelerConfig):
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

## Decorated Transition Functions

??? Hint "Reminder"
    We have the following transitions:

    1. `hello`: For this transition we will print the **name** of our traveler and what kind of **weather** they like.
    2. `select_city`: Here our traveler will randomly choose a potential travel destination from the list of cities.
    3. `check_weather`: After choosing a destination they will have to check the weather in the city.
    4. `going_to_city`: Should the weather be to our travelers liking they will tell us so and that they are going to the city.
    5. `not_going`: Should it not be to their liking then the traveler will inform us that they changed their mind.
    6. `arrive`: Once the traveler has arrived the city they again will inform us.
    7. `going_to_sleep`: Finally should the traveler have grown tiered of traveling for the day they will let us know and then go to sleep.


Using transition decorators like [`transitions.transition`][cr_kyoushi.simulation.transitions.transition] we can directly turn
a transition function into a transition. This is helpful to keep our code short and concise as we will not have to manually create
a transition instance in our factories build method.

??? Note
    Using a transition decorator on a transition function is equivalent to initializing a transition by passing
    the transition function i.e.,

    ```python
    @transitions.transition(target="some_state")
    def do_something(log, current_state, context, target):
        print("something")
    ```

    is equivalent to

    ```python
    def do_something_function(log, current_state, context, target):
        print("something")

    do_something = transitions.Transition(do_something_function, name="do_something", target="some_state")
    ```

### Updated transition functions

1. The hello transition now reads the traveler and and preferred weather from the config instead of having its own state.

    ```python
    @transitions.transition(target="selecting_city")
    def hello(log, current_state: str, context: TravelerContext, target: Optional[str]):
        """Transition function for the initial hello world message"""
        print(
            f"Hi I am {context.traveler}. "
            f"I like to travel to cities that have {context.desired_weather} weather."
        )
    ```

2. To select a city we need to first inline convert the weather map to a list of cities.

    ```python
    @transitions.delayed_transition(target="researching", delay_after=3)
    def select_city(log, current_state: str, context: TravelerContext, target: Optional[str]):
        cities = list(context.cities.keys())
        context.chosen_city = StrictStr(random.choice(cities))
        print(f"Maybe I will travel to somewhere in {context.chosen_city}.")
    ```

    !!! Note

        For the sake of execution efficiency one could also define the context and function so that this conversion
        is only executed on the first call and then persisted as part of the context.

3. For the weather check we now simply access the map through the context.

    ```python
    @transitions.delayed_transition(target="deciding", delay_before=1, delay_after=1)
    def check_weather(log, current_state: str, context: TravelerContext, target: Optional[str]):
        """Transition function to check the weather in the chosen city"""
        context.weather = context.cities[StrictStr(context.chosen_city)]
        print(f"The weather is {context.weather} in {context.chosen_city}")
    ```

4. Other than the decorator and name this is unchanged.

    ```python
    @transitions.delayed_transition(target="traveling", delay_after=10)
    def going_to_city(log, current_state: str, context: TravelerContext, target: Optional[str]):
        print(f"The weather is ok so I am going to {context.chosen_city} now ...")
    ```

5. Other than the decorator and name this is unchanged.

    ```python
    @transitions.delayed_transition(target="selecting_city", delay_before=2)
    def not_going(log, current_state: str, context: TravelerContext, target: Optional[str]):
        print(f"I don't like the weather in {context.chosen_city} so I am not going ...")
        context.chosen_city = None
        context.weather = None
    ```

6. Other than the decorator and name this is unchanged.

    ```python
    @transitions.transition(target="in_city")
    def arrive(log, current_state: str, context: TravelerContext, target: Optional[str]):
        print(
            f"I have arrived in {context.chosen_city} the weather is {context.weather} just how I like it."
        )
        context.current_location = context.chosen_city
        context.chosen_city = None
        context.weather = None
    ```

7. Similarly to the updated hello transition we now access the traveler name through the context.

    ```python
    @transitions.delayed_transition(target="sleeping", delay_before=3.5)
    def going_to_sleep(log, current_state: str, context: TravelerContext, target: Optional[str]):
        """Transition function that prints the final message before the traveler goes to sleep"""
        print(f"I {context.traveler} have travelled enough for now.")
        print(f"I am going to sleep in {context.current_location} ...")
        print("... zzzZZZzz ...")
    ```


## Statemachine and Context Setup

Since our modified `TravelerContext` now also contains the configuration options we have to modify our state machine initialization
and [context setup][cr_kyoushi.simulation.sm.Statemachine.setup_context]. Previously we simply created a `TravelerContext` instance
with everything set to its default values. In this version we pass our `TravelerConfig` instance when constructing the context.

```python
class TravelerStatemachine(sm.Statemachine):
    def __init__(
        self,
        initial_state: str,
        states: List[states.State],
        config: TravelerConfig,
        max_errors: int = 0,
    ):
        super().__init__(initial_state, states, max_errors=max_errors)
        self.__config = config

    def setup_context(self):
        """Initialize with config values and use defaults for the rest"""
        self.context = TravelerContext.parse_obj(self.__config)

```

!!! Note

    `#!python TravelerContext.parse_obj(self.__config)` is basically just a short hand provided by Pydantic for:

    ```python
    TravelerContext(
        traveler=self.__config.traveler,
        desired_weather=self.__config.desired_weather
    )
    ```

## Transition and State Configuration

The updated build method shows the biggest advantage of using transition decorator.
Since all our transition functions are decorated they are all automatically converted to transitions.
This means that we do not have to manually instantiate transition objects, but instead can directly pass
the converted transition functions into our states. This approach can significantly simplify and short our build functions
and state machine definitions.

```python

    ...

    def build(self, config: TravelerConfig):

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
        traveling = states.SequentialState("traveling", arrive)
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
            config=config,
        )
```

!!! Note

    You can only use transition decorators on functions (i.e., stateless transition functions).
    This is because stateful transition functions are classes that need to be instantiated before the can be
    used as transition functions.


## Running the Example

To run the example state machine you can simply use the Cyber Range Kyoushi CLI.

```bash
$ cd examples/decorated_traveler
$ cr-kyoushi-sim -c config.yml run -f traveler.py
```
<a data-fancybox="gallery" href="{{ image_url("images/traveler-demo.gif") }}">
<img src="{{ image_url("images/traveler-demo.gif") }}" alt="Traveler State Machine Demo" />
</a>
