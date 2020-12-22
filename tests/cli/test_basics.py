import logging
import re

from pathlib import Path

import pytest

from click.testing import CliRunner

from cr_kyoushi.simulation import __version__
from cr_kyoushi.simulation.cli import Info
from cr_kyoushi.simulation.cli import cli
from cr_kyoushi.simulation.cli import version
from cr_kyoushi.simulation.logging import get_logger
from cr_kyoushi.simulation.model import LogLevel


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
