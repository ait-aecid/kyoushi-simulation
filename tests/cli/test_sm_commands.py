from pathlib import Path

from click.testing import CliRunner
from pytest_mock import MockFixture

from cr_kyoushi.simulation import (
    cli,
    config,
)

from .conftest import (
    ExampleStatemachineConfig,
    StatemachineFactory,
)


try:
    from importlib.metadata import EntryPoint  # type: ignore
except ImportError:
    # need to use backport for python < 3.8
    from importlib_metadata import EntryPoint


def test_sm_base_function(mocker: MockFixture):
    raw_settings = {"plugin": {"include_names": ["test.*"]}}
    settings = config.Settings(**raw_settings)

    ep_test = mocker.Mock(EntryPoint)
    ep_test.name = "FactoryName"
    ep_test.value = "test.module:TestFactory"

    factory_eps = {"test": ep_test}
    info_obj = cli.Info()

    load_settings = mocker.patch("cr_kyoushi.simulation.cli.load_settings")
    load_settings.return_value = settings

    get_factories = mocker.patch("cr_kyoushi.simulation.cli.plugins.get_factories")
    get_factories.return_value = factory_eps

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["-c", "test.yml", "list"], obj=info_obj)

    # verify info is properly set
    assert info_obj.settings_path == Path("test.yml")
    assert info_obj.settings == settings
    assert info_obj.available_factories == factory_eps

    # verify set entry points are in the output
    assert "FactoryName" in result.output
    assert "test.module:TestFactory" in result.output


def test_sm_run(mocker: MockFixture):
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
    load_sm_config = mocker.patch("cr_kyoushi.simulation.cli.load_sm_config")
    load_sm_config.return_value = config_obj

    # setup input info obj
    info_obj = cli.Info()
    info_obj.config_path = "test.yml"
    info_obj.settings = config.Settings()
    info_obj.available_factories = factory_eps

    # sm config path
    sm_config_path = "test-sm.yml"

    runner = CliRunner()
    result = runner.invoke(
        cli.sm_run,
        ["-s", sm_config_path, "-f", "test"],
        obj=info_obj,
    )

    # verify  that the program exited correctly
    assert result.exit_code == 0

    # verify that factory was loaded correctly
    get_factory.assert_called_once_with(factory_eps, "test")
    load_sm_config.assert_called_once_with(
        Path(sm_config_path), ExampleStatemachineConfig
    )

    # verify that machine was built and run correctly
    factory_mock.build.assert_called_once_with(config_obj)
    machine_mock.run.assert_called_once()
