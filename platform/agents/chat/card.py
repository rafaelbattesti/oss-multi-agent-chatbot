from a2a.types import (
    AgentCapabilities,
    AgentInterface,
    AgentCard,
)

public_agent_card = AgentCard(
    name='Chat',
    description='Direct chat service.',
    version='1.0.0',
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    capabilities=AgentCapabilities(
        streaming=False,
        extended_agent_card=False,
    ),
    supported_interfaces=[
        AgentInterface(
            protocol_binding='HTTP+JSON',
            url='http://localhost:9998',
        )
    ],
    skills=[],
)