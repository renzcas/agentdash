from agents.agency_agent import AgencyAgent
from agents.builder_agent import BuilderAgent
from agents.compression_agent import CompressionAgent
from agents.observer_agent import ObserverAgent
from agents.strategist_agent import StrategistAgent
from agents.wisdom_agent import WisdomAgent


AGENTS = (
    ObserverAgent,
    StrategistAgent,
    WisdomAgent,
    BuilderAgent,
    CompressionAgent,
    AgencyAgent,
)


def run_agents(question: str) -> dict[str, dict[str, str]]:
    """Run each deterministic pillar against one investigation question."""
    results = {}
    for agent in AGENTS:
        result = agent.process(question)
        results[result["agent"]] = result
    return results
