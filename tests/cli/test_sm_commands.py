from pathlib import Path

from click.testing import CliRunner
from pytest_mock import MockFixture

from cr_kyoushi.simulation import cli
from cr_kyoushi.simulation import model


try:
    from importlib.metadata import EntryPoint  # type: ignore
except ImportError:
    # need to use backport for python < 3.8
    from importlib_metadata import EntryPoint


def test_sm_base_function(mocker: MockFixture):
    raw_config = {
        "plugin": {"include_names": ["test.*"]},
        "sm": {
            "activity_period": {
                "week_days": ["monday"],
                "time_period": {"start_time": "00:00", "end_time": "01:00"},
            }
        },
    }

    plugin_config = model.PluginConfig(include_names=["test.*"])

    ep_test = mocker.Mock(EntryPoint)
    ep_test.name = "FactoryName"
    ep_test.module = "test.module"
    ep_test.attr = "TestFactory"

    factory_eps = {"test": ep_test}
    info_obj = cli.Info()

    load_config_file = mocker.patch("cr_kyoushi.simulation.cli.load_config_file")
    load_config_file.return_value = raw_config

    load_plugin_config = mocker.patch("cr_kyoushi.simulation.cli.load_plugin_config")
    load_plugin_config.return_value = plugin_config

    get_factories = mocker.patch("cr_kyoushi.simulation.cli.plugins.get_factories")
    get_factories.return_value = factory_eps

    runner = CliRunner()
    result = runner.invoke(cli.sm, ["-c", "test.yml", "list"], obj=info_obj)

    # verify info is properly set
    assert info_obj.config_path == Path("test.yml")
    assert info_obj.config_raw == raw_config
    assert info_obj.plugin_config == plugin_config
    assert info_obj.available_factories == factory_eps

    # verify set entry points are in the output
    assert "FactoryName" in result.output
    assert "test.module:TestFactory" in result.output
