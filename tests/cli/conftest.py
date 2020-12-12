from pydantic import BaseModel

from cr_kyoushi.simulation import sm
from cr_kyoushi.simulation import states
from cr_kyoushi.simulation import transitions
from tests.fixtures.transitions import debug_transition


class ExampleStatemachineConfig(BaseModel):
    example_field: str = "example"


class StatemachineFactory(sm.StatemachineFactory, ExampleStatemachineConfig):
    @property
    def name(self) -> str:
        return "TestFactory"

    @property
    def config_class(self):
        return ExampleStatemachineConfig

    def build(self, config: ExampleStatemachineConfig):
        initial_transition = transitions.Transition(
            name="initial_transition",
            transition_function=debug_transition,
            target="end",
        )
        initial_state = states.ProbabilisticState(
            "initial", [initial_transition], [1.0]
        )
        end_state = states.ProbabilisticState("end", [], [])

        state_list = [initial_state, end_state]

        return sm.Statemachine("initial", state_list)
