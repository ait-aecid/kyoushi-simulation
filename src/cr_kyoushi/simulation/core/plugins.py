from typing import Dict
from typing import List
from typing import Type

from .. import __sm_factory_entrypoint__
from .errors import StatemachineFactoryLoadError
from .errors import StatemachineFactoryTypeError
from .model import PluginConfig
from .sm import StatemachineFactory


try:
    from importlib.metadata import EntryPoint  # type: ignore
    from importlib.metadata import entry_points  # type: ignore
except ImportError:
    # need to use backport for python < 3.8
    from importlib_metadata import EntryPoint
    from importlib_metadata import entry_points


def get_factories(plugin_config: PluginConfig) -> Dict[str, EntryPoint]:
    # all available factories which are also included as per the config
    available_sm_factories: List[EntryPoint] = [
        ep
        for ep in entry_points()[__sm_factory_entrypoint__]
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
    available_sm_factories: Dict[str, EntryPoint], sm_name
) -> StatemachineFactory:
    try:
        sm_entrypoint: EntryPoint = available_sm_factories[sm_name]
        factory_class: Type[StatemachineFactory] = sm_entrypoint.load()
        if issubclass(factory_class, StatemachineFactory):
            return factory_class()
        else:
            raise StatemachineFactoryTypeError(factory_class)
    except KeyError:
        raise StatemachineFactoryLoadError(sm_name)
