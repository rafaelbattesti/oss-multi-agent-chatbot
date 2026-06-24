from a2a.types import (
    AgentCapabilities,
    AgentInterface,
    AgentCard,
)

from config import load_config
from skills.decompose_query import decompose_query_extension, decompose_query_skill

config = load_config()

public_agent_card = AgentCard(
    name='Orchestrator',
    description='Orchestrates the tasks received from the users.',
    version='1.0.0',
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    capabilities=AgentCapabilities(
        streaming=False,
        extended_agent_card=True,
        extensions=[decompose_query_extension],
    ),
    supported_interfaces=[
        AgentInterface(
            protocol_binding='HTTP+JSON',
            url=config.public_base_url,
        )
    ],
    skills=[decompose_query_skill],
)
