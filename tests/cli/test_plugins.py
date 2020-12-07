import os

from typing import List

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation import __sm_factory_entrypoint__
from cr_kyoushi.simulation import errors
from cr_kyoushi.simulation import plugins
from cr_kyoushi.simulation.model import PluginConfig
from cr_kyoushi.simulation.sm import StatemachineFactory


try:
    from importlib.metadata import EntryPoint  # type: ignore
except ImportError:
    # need to use backport for python < 3.8
    from importlib_metadata import EntryPoint


FILE_DIR = os.path.dirname(__file__)


@pytest.fixture()
def mock_entry_points(mocker: MockFixture) -> List[EntryPoint]:
    ep_test = mocker.Mock(EntryPoint)
    ep_test_2 = mocker.Mock(EntryPoint)
    ep_test_3 = mocker.Mock(EntryPoint)
    ep_example = mocker.Mock(EntryPoint)
    ep_example_2 = mocker.Mock(EntryPoint)
    ep_example_3 = mocker.Mock(EntryPoint)

    # set name mocks
    ep_test.name = "test"
    ep_test_2.name = "test_2"
    ep_test_3.name = "test_3"
    ep_example.name = "example"
    ep_example_2.name = "example_2"
    ep_example_3.name = "example_3"

    return [
        ep_test,
        ep_test_2,
        ep_test_3,
        ep_example,
        ep_example_2,
        ep_example_3,
    ]


def __patch_entry_points(mocker: MockFixture, eps: List[EntryPoint]):
    entry_points = mocker.patch("cr_kyoushi.simulation.plugins.entry_points")
    entry_points.return_value = {__sm_factory_entrypoint__: eps}
    return entry_points


def test_get_factories_allow_all(
    mocker: MockFixture, mock_entry_points: List[EntryPoint]
):
    entry_points = __patch_entry_points(mocker, mock_entry_points)

    plugin_config = PluginConfig()

    factory_eps = plugins.get_factories(plugin_config)

    assert entry_points.called
    assert len(factory_eps.values()) == 6
    assert "test" in factory_eps.keys()
    assert "test_2" in factory_eps.keys()
    assert "test_3" in factory_eps.keys()
    assert "example" in factory_eps.keys()
    assert "example_2" in factory_eps.keys()
    assert "example_3" in factory_eps.keys()

    assert mock_entry_points[0] == factory_eps["test"]
    assert mock_entry_points[1] == factory_eps["test_2"]
    assert mock_entry_points[2] == factory_eps["test_3"]
    assert mock_entry_points[3] == factory_eps["example"]
    assert mock_entry_points[4] == factory_eps["example_2"]
    assert mock_entry_points[5] == factory_eps["example_3"]


def test_get_factories_include_prefix(
    mocker: MockFixture, mock_entry_points: List[EntryPoint]
):
    entry_points = __patch_entry_points(mocker, mock_entry_points)

    plugin_config = PluginConfig(include_names=[r"test.*"])

    factory_eps = plugins.get_factories(plugin_config)

    assert entry_points.called
    assert len(factory_eps.values()) == 3
    assert "test" in factory_eps.keys()
    assert "test_2" in factory_eps.keys()
    assert "test_3" in factory_eps.keys()
    assert "example" not in factory_eps.keys()
    assert "example_2" not in factory_eps.keys()
    assert "example_3" not in factory_eps.keys()

    assert mock_entry_points[0] == factory_eps["test"]
    assert mock_entry_points[1] == factory_eps["test_2"]
    assert mock_entry_points[2] == factory_eps["test_3"]


def test_get_factories_exclude_prefix(
    mocker: MockFixture, mock_entry_points: List[EntryPoint]
):
    entry_points = __patch_entry_points(mocker, mock_entry_points)

    plugin_config = PluginConfig(exclude_names=[r"example.*"])

    factory_eps = plugins.get_factories(plugin_config)

    assert entry_points.called
    assert len(factory_eps.values()) == 3
    assert "test" in factory_eps.keys()
    assert "test_2" in factory_eps.keys()
    assert "test_3" in factory_eps.keys()
    assert "example" not in factory_eps.keys()
    assert "example_2" not in factory_eps.keys()
    assert "example_3" not in factory_eps.keys()

    assert mock_entry_points[0] == factory_eps["test"]
    assert mock_entry_points[1] == factory_eps["test_2"]
    assert mock_entry_points[2] == factory_eps["test_3"]


def test_get_factories_include_and_exclude(
    mocker: MockFixture, mock_entry_points: List[EntryPoint]
):
    entry_points = __patch_entry_points(mocker, mock_entry_points)

    plugin_config = PluginConfig(include_names=[r"test.*"], exclude_names=[r".*_.*"])

    factory_eps = plugins.get_factories(plugin_config)

    assert entry_points.called
    assert len(factory_eps.values()) == 1
    assert "test" in factory_eps.keys()
    assert "test_2" not in factory_eps.keys()
    assert "test_3" not in factory_eps.keys()
    assert "example" not in factory_eps.keys()
    assert "example_2" not in factory_eps.keys()
    assert "example_3" not in factory_eps.keys()

    assert mock_entry_points[0] == factory_eps["test"]


def test_get_factory_with_valid_ep(mocker: MockFixture):
    class TestFactory(StatemachineFactory):
        @property
        def name(self) -> str:
            return "TestFactory"

        @property
        def config_class(self):
            pass

        def build(self, config):
            pass

    ep_test = mocker.Mock(EntryPoint)
    ep_test.name = "test"
    ep_test.load.return_value = TestFactory

    factory_eps = {"test": ep_test}

    test_factory = plugins.get_factory(factory_eps, "test")

    assert ep_test.load.called
    assert isinstance(test_factory, TestFactory)


def test_get_factory_with_invalid_ep(mocker: MockFixture):
    class InvalidTestFactory:
        pass

    ep_test = mocker.Mock(EntryPoint)
    ep_test.name = "test"
    ep_test.load.return_value = InvalidTestFactory

    factory_eps = {"test": ep_test}

    with pytest.raises(errors.StatemachineFactoryTypeError):
        plugins.get_factory(factory_eps, "test")

    assert ep_test.load.called


def test_get_factory_with_invalid_ep_name(mocker: MockFixture):
    class TestFactory(StatemachineFactory):
        @property
        def name(self) -> str:
            return "TestFactory"

        @property
        def config_class(self):
            pass

        def build(self, config):
            pass

    ep_test = mocker.Mock(EntryPoint)
    ep_test.name = "test"
    ep_test.load.return_value = TestFactory

    factory_eps = {"test": ep_test}

    with pytest.raises(errors.StatemachineFactoryLoadError):
        plugins.get_factory(factory_eps, "InvalidName")


def test_load_plugin_from_file():
    factory = plugins.get_factory({}, FILE_DIR + "/plugin_file_check.py")
    assert factory.name == "TestFactory"
    assert factory.config_class.__name__ == "TestStatemachineConfig"

    config_fields = factory.config_class.__fields__

    # verify correct config class
    assert "example_field" in config_fields
    assert config_fields["example_field"].type_ == str
    assert config_fields["example_field"].required is False
    assert config_fields["example_field"].default == "example"

    # load empty default config
    config = factory.config_class.parse_obj({})
    assert config.example_field == "example"

    machine = factory.build(config)

    # verify that the statemachine was loaded correctly
    assert type(machine).__name__ == "Statemachine"
    assert machine.initial_state == "initial"
    # check initial state
    assert machine.states["initial"].name == "initial"
    assert machine.states["initial"].transitions[0].name == "initial_transition"
    assert machine.states["initial"].transitions[0].target == "end"
    # check endstate
    assert machine.states["end"].name == "end"
    assert len(machine.states["end"].transitions) == 0


def test_load_plugin_from_non_existent_file():
    with pytest.raises(errors.StatemachineFactoryLoadError):
        plugins.get_factory({}, FILE_DIR + "/DOES_NOT_EXIST.py")
