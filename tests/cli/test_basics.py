import logging
import re

from pathlib import Path

from click.testing import CliRunner

from cr_kyoushi.simulation import __version__
from cr_kyoushi.simulation.cli import Info
from cr_kyoushi.simulation.cli import cli
from cr_kyoushi.simulation.cli import version


def test_version_command():
    info = Info()
    info.config_path = Path("./test.yml")

    runner = CliRunner()
    result = runner.invoke(version, obj=info)
    assert result.exit_code == 0
    output_lines = result.output.split("\n")
    assert re.match(r".*: " + __version__, output_lines[0])
    assert re.match(r".*: " + str(info.config_path.absolute()), output_lines[1])


def test_verbose_switch_default_to_no_handler():
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(cli, ["version"], obj=info_obj)
    assert result.exit_code == 0
    assert info_obj.verbose == 0

    assert len(logging.getLogger("cr_kyoushi.simulation").handlers) == 0


def test_verbose_switch_once_to_info():
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(cli, ["-v", "version"], obj=info_obj)
    assert result.exit_code == 0
    assert info_obj.verbose == 1

    assert len(logging.getLogger("cr_kyoushi.simulation").handlers) == 1
    assert logging.getLogger("cr_kyoushi.simulation").level == logging.INFO


def test_verbose_switch_twice_to_debug():
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(cli, ["-vv", "version"], obj=info_obj)

    assert result.exit_code == 0
    assert info_obj.verbose == 2

    assert len(logging.getLogger("cr_kyoushi.simulation").handlers) == 1
    assert logging.getLogger("cr_kyoushi.simulation").level == logging.DEBUG


def test_verbose_switch_multiple_to_debug():
    info_obj = Info()
    runner = CliRunner()
    result = runner.invoke(cli, ["-vvvvvv", "version"], obj=info_obj)
    assert result.exit_code == 0
    assert info_obj.verbose == 6

    assert logging.getLogger("cr_kyoushi.simulation").level == logging.DEBUG
