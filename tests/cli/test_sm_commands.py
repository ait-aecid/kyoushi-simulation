from pathlib import Path
from typing import Any
from typing import Dict

from click.testing import CliRunner
from pytest_mock import MockFixture

from cr_kyoushi.simulation import cli
from cr_kyoushi.simulation import model

from .conftest import ExampleStatemachineConfig
from .conftest import StatemachineFactory


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


def test_sm_run(mocker: MockFixture):
    raw_config: Dict[str, Any] = {
        "plugin": {},
        "sm": {},
    }

    ep_test = mocker.Mock(EntryPoint)
    ep_test.name = "FactoryName"
    ep_test.module = "test.module"
    ep_test.attr = "TestFactory"

    factory_eps = {"test": StatemachineFactory}
    factory_obj = StatemachineFactory()
    config_obj = ExampleStatemachineConfig()

    # mock factory functions
    machine_obj = factory_obj.build(ExampleStatemachineConfig())
    machine_mock = mocker.Mock(wraps=machine_obj)

    factory_mock = mocker.Mock(wraps=factory_obj)
    factory_mock.build.return_value = machine_mock
    # need to attach mock value to type object since it is a property
    type(factory_mock).config_class = mocker.PropertyMock(
        return_value=ExampleStatemachineConfig
    )

    # mock load functions
    get_factory = mocker.patch("cr_kyoushi.simulation.cli.plugins.get_factory")
    get_factory.return_value = factory_mock
    load_config = mocker.patch("cr_kyoushi.simulation.cli.load_config")
    load_config.return_value = config_obj

    # setup input info obj
    info_obj = cli.Info()
    info_obj.config_path = "test.yml"
    info_obj.config_raw = raw_config
    info_obj.available_factories = factory_eps

    runner = CliRunner()
    result = runner.invoke(cli.sm_run, ["-f", "test"], obj=info_obj)

    # verify  that the program exited correctly
    assert result.exit_code == 0

    # verify that factory was loaded correctly
    get_factory.assert_called_once_with(factory_eps, "test")
    load_config.assert_called_once_with(raw_config, ExampleStatemachineConfig)

    # verify that machine was built and run correctly
    factory_mock.build.assert_called_once_with(config_obj)
    machine_mock.run.assert_called_once()
