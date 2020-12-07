import re

from click.testing import CliRunner

from cr_kyoushi.simulation import __version__
from cr_kyoushi.simulation.cli import version


def test_version_command():
    runner = CliRunner()
    result = runner.invoke(version)
    assert result.exit_code == 0
    output_lines = result.output.split("\n")
    assert re.match(r".*: " + __version__, output_lines[0])
