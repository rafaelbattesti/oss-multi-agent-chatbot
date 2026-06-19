from a2a.types import AgentExtension, AgentSkill

OUTPUT_SCHEMA = {
    'type': 'object',
    'properties': {
        'intent':      {'type': 'string'},
        'subject':     {'type': 'string'},
        'entities':    {'type': 'array', 'items': {'type': 'string'}},
        'complexity':  {'type': 'string', 'enum': ['simple', 'medium', 'complex']},
        'sub_queries': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['intent', 'subject', 'entities', 'complexity', 'sub_queries'],
}

decompose_query_skill = AgentSkill(
    id='decompose-query',
    name='Decompose Query',
    description='str → {intent, subject, entities[], complexity, sub_queries[]}',
    tags=['decomposition', 'query-analysis', 'intent-classification', 'nlp'],
    examples=[
        'What is the capital of France?',
        'How do I deploy a containerized Python app to Kubernetes with autoscaling?',
        'Compare transformer and LSTM architectures for time series forecasting',
    ],
    input_modes=['text/plain'],
    output_modes=['application/json'],
)

decompose_query_extension = AgentExtension(
    uri='bastion/skills/decompose-query/contract',
    required=True,
    params={
        'skill_id': decompose_query_skill.id,
        'input': {'type': 'string'},
        'output': OUTPUT_SCHEMA,
    },
)
