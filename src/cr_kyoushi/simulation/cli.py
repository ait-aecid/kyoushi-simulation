#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    Optional,
)

import click

from . import plugins
from .config import (
    LogLevel,
    Settings,
    configure_seed,
    load_settings,
    load_sm_config,
)
from .logging import (
    configure_logging,
    get_logger,
)


try:
    from importlib.metadata import EntryPoint  # type: ignore
except ImportError:
    # need to use backport for python < 3.8
    from importlib_metadata import EntryPoint

__all__ = ["CliPath", "Info", "cli", "version", "sm_list", "sm_run"]

logger = get_logger()


class EnumChoice(click.Choice):
    """Click choice from an enum

    from https://github.com/pallets/click/issues/605#issuecomment-582574555
    """

    case_sensitive: bool
    use_value: bool

    def __init__(self, enum, case_sensitive=False, use_value=False):
        self.enum = enum
        self.use_value = use_value
        choices = [
            str(e.value) if use_value else e.name
            for e in self.enum.__members__.values()
        ]
        super().__init__(choices, case_sensitive)

    def convert(
        self,
        value: Any,
        param: Optional[click.Parameter] = None,
        ctx: Optional[click.Context] = None,
    ):
        if isinstance(value, Enum) and value in self.enum:
            return value
        result = super().convert(value, param, ctx)

        # if we got here result must be a value or enum key
        # since super will convert one of the choices

        if self.use_value:
            # using list instead of generator for test coverage
            # also we don't care about efficiency to much here
            return [e for e in self.enum if str(e.value) == result][0]

        return self.enum[result]


class CliPath(click.Path):
    """A Click path argument that returns a pathlib Path, not a string"""

    def convert(self, value, param, ctx):
        return Path(super().convert(value, param, ctx))


class Info:
    """An information object to pass data between CLI functions."""

    def __init__(self):  # Note: This object must have an empty constructor.
        """Create a new instance."""
        self.settings_path: Optional[Path] = None
        self.settings: Optional[Settings] = None
        self.available_factories: Optional[Dict[str, EntryPoint]] = None


# pass_info is a decorator for functions that pass 'Info' objects.
#: pylint: disable=invalid-name
pass_info = click.make_pass_decorator(Info, ensure=True)


# Change the options to below to suit the actual options for your task (or
# tasks).
@click.group()
@click.option("--log-level", type=EnumChoice(LogLevel), help="The log level")
@click.option(
    "--seed",
    default=None,
    type=click.INT,
    help="Global seeds for PRNGs used during simulation",
)
@click.option(
    "--config",
    "-c",
    type=CliPath(dir_okay=False, readable=True),
    default="config.yml",
    show_default=True,
    help="The Cyber Range Kyoushi Simulation settings file",
)
@pass_info
def cli(info: Info, log_level: LogLevel, seed: Optional[int], config: Path):
    """Run Cyber Range Kyoushi Simulation."""
    info.settings_path = config
    info.settings = load_settings(info.settings_path, log_level=log_level, seed=seed)
    info.available_factories = plugins.get_factories(info.settings.plugin)

    # setup logging
    configure_logging(info.settings.log)

    # setup prngs
    configure_seed(info.settings.seed)


@cli.command()
@pass_info
def version(info: Info):
    """Get the library version."""
    from .util import version_info

    click.echo(version_info(cli_info=info))


@cli.command(name="list")
@pass_info
def sm_list(info: Info):
    """List available state machine factories."""
    assert info.available_factories is not None
    click.echo(click.style("Available state machine factories:", bold=True))
    for factory_plugin in info.available_factories.values():
        click.echo(f"\t{factory_plugin.name} - {factory_plugin.value}")


@cli.command(name="run")
@pass_info
@click.option(
    "--sm-config",
    "-s",
    type=CliPath(dir_okay=False, readable=True),
    default="sm.yml",
    show_default=True,
    help="The state machine configuration file",
)
@click.option(
    "--factory",
    "-f",
    type=str,
    required=True,
    help="""
        The state machine factory to use.
        This can be either the name of a statemachine factory entrypoint plugin or
        the path to a python file containing a statemachine factory.
        """,
)
def sm_run(info: Info, sm_config: Path, factory: str):
    """Execute a state machine."""
    assert info.available_factories is not None

    # get factory
    factory_obj = plugins.get_factory(info.available_factories, factory)
    StatemachineConfig = factory_obj.config_class

    # load state machine config and build machine
    config = load_sm_config(sm_config, StatemachineConfig)
    logger.debug("Loaded config", config=config)
    machine = factory_obj.build(config)

    # execute machine
    machine.run()
