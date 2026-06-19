from a2a.types import (
    AgentCapabilities,
    AgentInterface,
    AgentCard,
)

from skills.decompose_query import decompose_query_extension, decompose_query_skill

public_agent_card = AgentCard(
    name='Bastion',
    description='Gateway agent: validates, classifies, and routes user queries to the agent layer.',
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
            url='http://localhost:9999',
        )
    ],
    skills=[decompose_query_skill],
)