{% macro image_url(url) %}
{%- if config.site_url|length -%}
{{ config.site_url }}{{ url }}
{%- else -%}
{{ fix_url(url) }}
{%- endif -%}
{% endmacro %}

Cyber Range Kyoushi Simulation provides and API and CLI for developing and running state machines
for simulating various actors in cyber ranges.

The development API revolves around 6 major components

- [`Statemachine`][cr_kyoushi.simulation.sm.Statemachine]
- [`Context`][cr_kyoushi.simulation.model.Context]
- [`State`][cr_kyoushi.simulation.states.State]
- [`Transition`][cr_kyoushi.simulation.transitions.Transition]
- [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction]
- [`StatemachineFactory`][cr_kyoushi.simulation.sm.StatemachineFactory]

Simulation state machines are defined by combining these 6 components.

## Statemachine

The [`Statemachine`][cr_kyoushi.simulation.sm.Statemachine] base class provides the high level state machine
execution logic for state machines. In its most basic form it is initialized with a **initial state** and a **list of states**.
After initialization a state machine can either be executed autonomously via [`Statemachine.run()`][cr_kyoushi.simulation.sm.Statemachine.run]
or manually via [`Statemachine.execute_step(...)`][cr_kyoushi.simulation.sm.Statemachine.execute_step].

State machines will execute according to the [`transitions`][cr_kyoushi.simulation.transitions.Transition] defined in
its [`states`][cr_kyoushi.simulation.states.State]. When using [`Statemachine.run()`][cr_kyoushi.simulation.sm.Statemachine.run] execution
will keep executing state transitions until either an end state is reached (defined as `None`) or the current state has no outgoing
transitions (i.e., [`State.next(...)`][cr_kyoushi.simulation.states.State.next] returns `None`).

Other thant the base [`Statemachine`][cr_kyoushi.simulation.sm.Statemachine] the API also provides other state machine classes which modify
normal state machine behavior. See the [sm module](../reference/sm.md) code reference for all available state machine types.

!!! Hint
    If you wish to change or extend high basic state machine execution flow you can extend
    [`Statemachine`][cr_kyoushi.simulation.sm.Statemachine] or one of its sub classes.


## Context

The state machine execution context is used to pass information between the various states and transitions.
Allowed context types are `#!python Dict[str, Any]` or [Pydantic Models](https://pydantic-docs.helpmanual.io/).
A state machine execution context can be helpful when you complex a state machine for which some of the states
or transitions depend on some shared information or objects. For example if you are working with [Selenium](https://www.selenium.dev/)
you might want to store your Selenium `driver` in the context so that your transitions and states can all access the same Browser instance.

The [`Statemachine`][cr_kyoushi.simulation.sm.Statemachine] also implements simple context life cycle through the
[`Statemachine.setup_context`][cr_kyoushi.simulation.sm.Statemachine.setup_context] and
[`Statemachine.destroy_context`][cr_kyoushi.simulation.sm.Statemachine.destroy_context] methods. You can use extend this
methods to ensure that your custom context is properly initialized and destroyed in accordance with the state machine execution flow.

!!! Warning
    If you do not use [`Statemachine.run()`][cr_kyoushi.simulation.sm.Statemachine.run]
    and instead choose to manually execute your state machine you have to call the setup and destroy
    methods yourself before starting and stopping execution.

While you could also achieve something similar to the context by initializing custom State or Transition classes with
e.g., a shared `driver` object it is preferred to use the context for such things as it helps keep your code simple.
Also life cycle management for such custom solutions would have to be implemented and integrated with the state machine as well.

## State

A [`State`][cr_kyoushi.simulation.states.State] has zero or more out going transitions and implements the
method [`State.next(...)`][cr_kyoushi.simulation.states.State.next]. Each state also must have a unique
[`name`][cr_kyoushi.simulation.states.State.name] property so it can be stored in a dictionary (`name -> State`).

The `next(..)` method used in the state machine execution flow to determine the next transition to execute.
It is important to select the `State` type that fits your state machines definition e.g., if you want to implement a
probabilistic finite state machine the [`ProbabilisticState`][cr_kyoushi.simulation.states.ProbabilisticState] might be a good fit.

See the [states module](../reference/states.md) for all the provided state types.

!!! Hint
    You can also always implement a custom `State` if you need a more specific transition selection
    e.g., based on some of your context information.

## Transitions and Transition Functions

While states define the flow of the state machine transitions and transition functions define its actions.
A [`Transition`][cr_kyoushi.simulation.transitions.Transition] always has a name, target state and transition function.

!!! Reminder
    A target state of `None` indicates the final state i.e., end of execution.
    Alternatively you can also use [`FinalState`][cr_kyoushi.simulation.states.FinalState]
    if you wish to define end states more explicitly.

The [`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction] is what ultimately contains your custom code.
What actually is executed depends on your state machine e.g., your transition function could use a Selenium `driver`
to navigate from one page (**current state**) to another page (**target state**).

The [`Transition`][cr_kyoushi.simulation.transitions.Transition] object that wraps your transition function
determines how your transition function is executed and handles all state machine related actions (e.g., returning the target state).
You can extend the base transition class if you whish to change this behavior, for example,
the [`DelayedTransition`][cr_kyoushi.simulation.transitions.DelayedTransition] class makes it possible the define
a pre or post transition function execution delay. This might be useful when simulating human behavior
as humans tend to think before or after they do something. Alternatively you could also implement a custom transition class
that executes a different transition function depending on the *current state* or *context*.

!!! Warning
    While the API does not enforce it its recommend that a single transition instance
    only has one target state. This is recommend to keep state machine implementations
    as understandable as possible. Divergence from normal behavior due to errors are an
    exception to this and are made possible through
    [`TransitionExecutionErrors`][cr_kyoushi.simulation.errors.TransitionExecutionError].


### Stateless vs Stateful Transition Functions

Transition functions can be defined as either functions (stateless) or as callable objects (stateful).
They only need to implement the [`TransitionFunction protocol`][cr_kyoushi.simulation.transitions.TransitionFunction].

For example the following would be a stateless transition function

```python
def goto_city_transition(
    log: BoundLogger,
    current_state: str,
    context: TravelerContext,
    target: Optional[str],
):
    print(f"The weather is ok so I am going to {context.chosen_city} now ...")
```

We call this a stateless transition function, because it does not have its own internal state, i.e., variables that persist across
multiple executions. Stateless transition functions can only use the context object to store and read information.

Sometimes this is not enough as you might have many transition functions that require their own state variables
e.g., a transition function that increases a count and prints it out. If you have many such functions your context object
might contain many many fields that are only ever used by a single transition function and do not necessarily need to be shared
with other states and transitions. In such cases you might prefer to store this information outside the context object to avoid
this clutter. Another use case for stateful transition functions would be functions that can be configured to do something a specific way
depending on the state machine configuration.

As such stateful transition functions can simply be defined as callable objects where the `__call__` method
implements the [`TransitionFunction protocol`][cr_kyoushi.simulation.transitions.TransitionFunction].
As objects they can then be initialized based on the configuration and they can also store their own state
as attributes.

```python
class SayHello:
    """Transition function for the initial hello world message"""

    def __init__(self, traveler_name: StrictStr, desired_weather: Weather):
        self.traveler_name = traveler_name
        self.desired_weather = desired_weather

    def __call__(
        self,
        log: BoundLogger,
        current_state: str,
        context: TravelerContext,
        target: Optional[str],
    ):
        print(
            f"Hi I am {self.traveler_name}. "
            f"I like to travel to cities that have {self.desired_weather} weather."
        )
```

### Creating Transition Instances

The API provides to ways to create transition objects either by simply constructing one of the transition types
with a transition function as its argument e.g.,

```python
hello = transitions.Transition(
            name="hello",
            transition_function=say_hello,
            target="selecting_city",
        )
```

or in case of stateless transitions you can also use a *transition decorator*
(e.g., [`transition`][cr_kyoushi.simulation.transitions.transition]) that can directly
wrap a transition function definition into a transition object.

```python
@transitions.transition(target="selecting_city")
def hello(log, current_state: str, context: TravelerContext, target: Optional[str]):
    print(
        f"Hi I am {context.traveler}. "
        f"I like to travel to cities that have {context.desired_weather} weather."
    )
```

Using transition decorators for stateless transitions can save you some extra code and also
makes it very clear which transition executes which transition function. As stateful transition functions
are classes and only become actual functions after they have been initialized you cannot use transition decorators with them.

!!! Hint
    The API provides transition decorators for all its transition types.
    The decorator name is usually just camel case of the transition types class name.

## Statemachine Factories

Cyber Range Kyoushi Simulation also provides a CLI script for executing user defined state machines.
For this it provides the concept of [`StatemachineFactories`][cr_kyoushi.simulation.sm.StatemachineFactory] to allow
users to make their state machine implementations available to the CLI script. A state machine factory must have a human
readable name, a config class and a [build method][cr_kyoushi.simulation.sm.StatemachineFactory.build] that can be called
by the CLI to create the state machine instance. The CLI will also load and initialize your config class based on the
user supplied state machine configuration file on run time.

!!! Note
    The CLI supports config `dict` or [Pydantic models](https://pydantic-docs.helpmanual.io/) as config classes.
    It is recommend to use Pydantic as Pydantic models are automatically validated by the CLI.

!!! Hint
    See the [configuration section](./configuration.md) for more details on CLI and state machine configuration.

The build method is the most important part of a state machine factory. The CLI will automatically call this function
to initialize the state machine instance as such you have to ensure that all the state, transition setup is done here
and the final state machine object is returned. To keep your code a bit more structured you could also want define
a few helper methods (e.g., `build_transitions(..)`) that handle specific parts of the build process and are called
from within the main build method. A simple factory might look like this:

```python
...

class StatemachineFactory(sm.StatemachineFactory):
    @property
    def name(self) -> str:
        return "GettingStartedStatemachineFactory"

    @property
    def config_class(self):
        return dict

    def build(self, config: dict):

        # setup the states
        initial = states.SequentialState("initial", init_transition)
        example_state = states.SequentialState("example_state", example_transition)
        end = states.FinalState("end")

        # Initialize the state machine
        return GettingStartedStatemachine(
            "initial",
            [initial, example_state, end],
        )

...
```

See the [examples section](../examples) for complete example state machine implementations.

### Plugin System

There are two ways for a user to make their state machine factory accessible for the CLI system. Either through i
n the form of an entry point plugin using the entry point `cr_kyoushi.simulation` or through a self contained python
file that declares a `StatemachineFactory` class. Both approaches have their advantages and disadvantages.

Entry point plugins only work if the state machine code is installed as a proper python package, but by using this approach
you can use multiple python files (modules) to define your state machine. This can potential make your code more readable
and manageable.

Python script plugins have the advantage that they can be used as is not package config etc. required, but you
will have to keep all your in a single file or have to ensure that imports for your custom modules are resolvable
via the python path (e.g., relative imports will cause exceptions). Also with a pythons script plugin you can only
provide a single state machine while you could expose multiple entry point plugins using a single package.

!!! Important
    Regardless which plugin type you use your StatemachineFactory **must** have a default
    no arguments `__init__` method so the plugin system can create an instance of your factory.
