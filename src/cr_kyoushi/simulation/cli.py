#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

import click

from . import plugins
from .config import load_config
from .config import load_config_file
from .config import load_plugin_config
from .model import PluginConfig


try:
    from importlib.metadata import EntryPoint  # type: ignore
except ImportError:
    # need to use backport for python < 3.8
    from importlib_metadata import EntryPoint

__all__ = ["CliPath", "Info", "cli", "version", "sm_list", "sm_run"]

logger = logging.getLogger("cr_kyoushi.simulation")


class CliPath(click.Path):
    """A Click path argument that returns a pathlib Path, not a string"""

    def convert(self, value, param, ctx):
        return Path(super().convert(value, param, ctx))


class Info:
    """An information object to pass data between CLI functions."""

    def __init__(self):  # Note: This object must have an empty constructor.
        """Create a new instance."""
        self.verbose: int = 0
        self.config_path: Optional[Path] = None
        self.config_raw: Optional[Dict[str, Any]] = None
        self.plugin_config: Optional[PluginConfig] = None
        self.available_factories: Optional[Dict[str, EntryPoint]] = None


# pass_info is a decorator for functions that pass 'Info' objects.
#: pylint: disable=invalid-name
pass_info = click.make_pass_decorator(Info, ensure=True)


def __setup_logging(info: Info, verbose: int) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
        )
    )
    logger.addHandler(handler)
    # Use the verbosity count to determine the logging level...
    if verbose > 0:
        logger.setLevel(logging.DEBUG)
        click.echo(
            click.style(
                f"Verbose logging is enabled. " f"(LEVEL={logger.getEffectiveLevel()})",
                fg="yellow",
            )
        )
    else:
        logger.setLevel(logging.INFO)
    info.verbose = verbose


# Change the options to below to suit the actual options for your task (or
# tasks).
@click.group()
@click.option("--verbose", "-v", count=True, help="Enable verbose output.")
@click.option(
    "--config",
    "-c",
    type=CliPath(dir_okay=False, readable=True),
    default="config.yml",
    show_default=True,
    help="The state machine configuration file",
)
@pass_info
def cli(info: Info, verbose: int, config: Path):
    """Run Cyber Range Kyoushi Simulation."""
    __setup_logging(info, verbose)

    info.config_path = config
    info.config_raw = load_config_file(info.config_path)
    info.plugin_config = load_plugin_config(info.config_raw)
    info.available_factories = plugins.get_factories(info.plugin_config)


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
        click.echo(
            f"\t{factory_plugin.name} - {factory_plugin.module}:{factory_plugin.attr}"
        )


@cli.command(name="run")
@pass_info
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
def sm_run(info: Info, factory: str):
    """Execute a state machine."""
    assert info.available_factories is not None
    assert info.config_raw is not None

    # get factory
    factory_obj = plugins.get_factory(info.available_factories, factory)
    StatemachineConfig = factory_obj.config_class

    # load state machine config and build machine
    config = load_config(info.config_raw, StatemachineConfig)
    logger.debug("Loaded config %s", config)
    machine = factory_obj.build(config)

    # execute machine
    machine.run()
