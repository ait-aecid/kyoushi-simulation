The Cyber Range Kyoushi Simulation CLI supports two different configuration files.


1. CLI Settings (default path `config.yml`)
2. State Machine Config (default path `sm.yml`)

## Supported File Formats

- [YAML](https://yaml.org/) loaded with [ruamel](https://yaml.readthedocs.io/en/latest/)

## CLI Settings

The CLI settings are used to configure the CLI scripts behavior it self e.g., logging and the plugin system.
[Pydantic settings management](https://pydantic-docs.helpmanual.io/usage/settings/) is used for this.
As such it is possible to override the default value using environment variables.

!!! Note
    Fields which are nested Pydantic Models must be set using JSON encoded environment variables.
    Sadly directly setting nested fields is currently not supported.

Also some of the configuration settings can also be overridden by CLI options and arguments (see the [CLI reference](cli.md)).

See the [config module reference](../reference/config.md) for the complete settings model and and its sub models.
The following is a complete settings file with all default values:

```yaml
# plugin system configuration
plugin:
  # factory entry point plugins which should or should not be loaded
    include_names:
      - .*
    exclude_names: []

# logging configuration
log:
    # the log level
    level: WARNING

    # configuration for the timestamp format
    timestamp:
        # string format
        # (if this is no set a unix epoch timestamp will be used)
        format: null
        # use UTC time or the local time
        utc: True
        # the log event key to use
        key: "timestamp"

    # configuration of the console logger
    console:
        enabled: yes
        # output format
        format: colored


    # configuration of the file logger
    file:
        enabled: no
        format: json
        # the path to log to
        path: sm.log
```

## State Machine Configuration

State machines that require or optionally provide configuration options can do so
via the state machine configuration file (default path `sm.yml`). The configuration file
can be in any format supported by the CLIs' configuration system (see above).

This the configuration file will automatically be loaded and converted to the config class
for your state machine factory
(see [`StatemachineFactory.config_class`][cr_kyoushi.simulation.sm.StatemachineFactory.config_class]).

The system supports both raw configuration in the form of Python dictionaries or as
[Pydantic Models](https://pydantic-docs.helpmanual.io/). It is recommend to use Pydantic for as this allows
the CLI system to validate the correctness of the configuration options for you.

!!! Hint
    You can also use a [`BaseSettings`](https://pydantic-docs.helpmanual.io/usage/settings/)
    as the base class for your configuration, if you want to enable support environment variables
    for your state machine configuration.

The state machine configuration can be very useful tool for creating more dynamic state machines.
For example you could easily create a probabilistic state machine with configurable probabilities
for transitions. Using Pydantic you can also ensure that these probabilities are validated on
configuration load time.
