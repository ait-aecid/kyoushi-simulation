import logging
import os
import re

from pathlib import Path

import pytest

from click.testing import CliRunner

from cr_kyoushi.simulation import __version__
from cr_kyoushi.simulation.cli import (
    Info,
    cli,
    version,
)
from cr_kyoushi.simulation.config import get_seed
from cr_kyoushi.simulation.logging import get_logger
from cr_kyoushi.simulation.model import LogLevel


FILE_DIR = os.path.dirname(__file__) + "/files"


def test_version_command():
    info = Info()
    info.settings_path = Path("./test.yml")

    runner = CliRunner()
    result = runner.invoke(version, obj=info)
    assert result.exit_code == 0
    output_lines = result.output.split("\n")
    assert re.match(r".*: " + __version__, output_lines[0])
    assert re.match(r".*: " + str(info.settings_path.absolute()), output_lines[1])


def test_logging_default_to_warning_and_console():
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(cli, ["version"], obj=info_obj)

    handlers = get_logger().handlers

    assert result.exit_code == 0
    assert info_obj.settings.log.console.enabled is True
    assert info_obj.settings.log.level == LogLevel.WARNING
    assert get_logger().level == LogLevel.WARNING

    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)


@pytest.mark.parametrize(
    "option, expected_level",
    [pytest.param(key, val, id=key) for key, val in LogLevel.__members__.items()],
)
def test_verbose_switch_once_to_info(option, expected_level):
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(cli, ["--log-level", option, "version"], obj=info_obj)

    handlers = get_logger().handlers

    assert result.exit_code == 0
    assert info_obj.settings.log.console.enabled is True
    assert info_obj.settings.log.level == expected_level
    assert get_logger().level == expected_level

    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)


def test_configure_seed_file():
    expected_seed = "THIS_IS_THE_SEED_FILE"
    cfg_file = FILE_DIR + "/config_seed.yml"
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(cli, ["-c", cfg_file, "version"], obj=info_obj)

    assert result.exit_code == 0
    assert info_obj.settings.seed == expected_seed
    assert get_seed() == expected_seed


@pytest.mark.parametrize(
    "expected_seed, seed_type",
    [
        pytest.param("THIS_IS_THE_SEED_CLI", str, id="str-seed-value"),
        pytest.param(1337, int, id="int-seed-value"),
        pytest.param(42.42, float, id="float-seed-value"),
    ],
)
def test_configure_seed_cli(expected_seed, seed_type):
    cfg_file = FILE_DIR + "/config_seed.yml"
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(
        cli, ["--seed", str(expected_seed), "-c", cfg_file, "version"], obj=info_obj
    )

    assert result.exit_code == 0
    assert info_obj.settings.seed == expected_seed
    assert get_seed() == expected_seed
    assert type(get_seed()) == seed_type
