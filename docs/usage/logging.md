The Cyber Range Kyoushi CLI uses [structlog](https://www.structlog.org/) as its logging framework.

Structlog makes it possible to add additional keys to log messages allowing us to create more structured and
annotated log messages. This also enables us to easily provide both human and computer readable log formats (e.g., JSON)
which can then later be parsed by other Cyber Range Kyoushi framework tools.

## Usage

The 3 main execution flow method calls [`State.next`][cr_kyoushi.simulation.states.State.next],
[`Transition.execute`][cr_kyoushi.simulation.transitions.Transition.execute] and
[`TransitionFunction`][cr_kyoushi.simulation.transitions.TransitionFunction] are passed a `log` object.


This `log` object is already pre initialized with some information about the state machine execution as
extra log record keys:

- `run`: A UUID uniquely identifying the state machine run
- `transition_id`: A UUID uniquely identifying the current transition execution
- `state`: The current states name
- `transition`: The current transitions name
- `target`: The transitions target states name
-
As such it is highly recommended to use this `log` object when logging state machine execution
related log messages.

For logging other things such as initialization in your state machine factory use the logger
provided by the [`get_logger`][cr_kyoushi.simulation.logging.get_logger] function from the logging module.

!!! Important
    You can use any object that is JSON serializable by Pydantics' custom JSON encoder.
    Note that for Pydantic Models custom encoders are currently not supported.
    All non serializable objects must be converted to a serializable format before logging them.

### Key Binding
You can log normal messages as you would with the Python native `logging` module

```python
log.info("This is the %d message", count)
```

or you can also include extra keys

```python
log.info("This is the %d message", count, message_id=uuid4())
```

Structlog also allows you to bind keys to a log instance so it will be included in all future log messages.

```python
# bind adds keys to the current bindings
log = log.bind(message_id=uuid4())
log.info("This is the %d message", count)
log.info("It is sunny outside")

count++

# new will clear out the current bindings
log = log.new(foo="bar")
log.info("This is the %d message", count)
log.info("It is sunny outside")
```

```bash
This is the 1 message   message_id=UUID('012a36e9-c5b0-4b98-a804-ae9b0cd1b870')
It is sunny outside     message_id=UUID('012a36e9-c5b0-4b98-a804-ae9b0cd1b870')

This is the 2 message   foo=bar
It is sunny outside     foo=bar
```

See the [structlog documentation](https://www.structlog.org/en/stable/) for more details.
