import sys

from importlib.util import (
    module_from_spec,
    spec_from_file_location,
)
from pathlib import Path
from typing import (
    Dict,
    List,
    Type,
)

from . import FACTORY_ENTRYPOINT
from .config import PluginConfig
from .errors import (
    StatemachineFactoryLoadError,
    StatemachineFactoryTypeError,
)
from .sm import StatemachineFactory


try:
    from importlib.metadata import EntryPoint  # type: ignore
    from importlib.metadata import entry_points  # type: ignore
except ImportError:
    # need to use backport for python < 3.8
    from importlib_metadata import (
        EntryPoint,
        entry_points,
    )


def get_factories(plugin_config: PluginConfig) -> Dict[str, EntryPoint]:
    # all available factories which are also included as per the config
    available_sm_factories: List[EntryPoint] = [
        ep
        for ep in entry_points().get(FACTORY_ENTRYPOINT, [])
        if any([pattern.match(ep.name) for pattern in plugin_config.include_names])
    ]

    # filter out plugins explicitly excluded
    allowed_sm_factories: Dict[str, EntryPoint] = {
        ep.name: ep
        for ep in available_sm_factories
        if not any([pattern.match(ep.name) for pattern in plugin_config.exclude_names])
    }

    return allowed_sm_factories


def get_factory(
    available_sm_factories: Dict[str, EntryPoint], sm_name: str
) -> StatemachineFactory:
    try:
        # try to load from python file
        if sm_name.endswith(".py"):
            # check if file exists
            plugin_path = Path(sm_name)
            if plugin_path.exists():
                # load the plugin file
                spec = spec_from_file_location(plugin_path.stem, plugin_path)
                factory_plugin = module_from_spec(spec)
                sys.modules[plugin_path.stem] = factory_plugin
                spec.loader.exec_module(factory_plugin)  # type: ignore
                # get the plugin class (must be name StateMachineFactory)
                factory_class: Type[
                    StatemachineFactory
                ] = factory_plugin.StatemachineFactory  # type: ignore
            else:
                raise StatemachineFactoryLoadError(sm_name)

        # try to load from entrypoint
        else:
            sm_entrypoint: EntryPoint = available_sm_factories[sm_name]
            factory_class = sm_entrypoint.load()

        if issubclass(factory_class, StatemachineFactory):
            return factory_class()
        else:
            raise StatemachineFactoryTypeError(factory_class)
    except KeyError:
        raise StatemachineFactoryLoadError(sm_name)
