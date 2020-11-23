from click.testing import CliRunner

from cr_kyoushi.simulation import __version__
from cr_kyoushi.simulation.cli import version


def test_version_command():
    runner = CliRunner()
    result = runner.invoke(version)
    assert result.exit_code == 0
    assert result.output.strip() == __version__
