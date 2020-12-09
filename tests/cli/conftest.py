import logging

from pydantic import BaseModel

from cr_kyoushi.simulation import sm
from cr_kyoushi.simulation import states
from cr_kyoushi.simulation import transitions


logger = logging.getLogger("cr_kyoushi.simulation")


class ExampleStatemachineConfig(BaseModel):
    example_field: str = "example"


class BasicTransition(transitions.Transition):
    @property
    def name(self) -> str:
        return self._name

    @property
    def target(self) -> str:
        return self._target

    def __init__(self, name, target):
        self._name = name
        self._target = target

    def execute_transition(self, current_state, context):
        logger.debug(
            "executing %s -- %s --> %s", current_state, self._name, self._target
        )
        return self._target


class StatemachineFactory(sm.StatemachineFactory, ExampleStatemachineConfig):
    @property
    def name(self) -> str:
        return "TestFactory"

    @property
    def config_class(self):
        return ExampleStatemachineConfig

    def build(self, config: ExampleStatemachineConfig):
        initial_transition = BasicTransition(name="initial_transition", target="end")
        initial_state = states.ProbabilisticState(
            "initial", [initial_transition], [1.0]
        )
        end_state = states.ProbabilisticState("end", [], [])

        state_list = [initial_state, end_state]

        return sm.Statemachine("initial", state_list)
