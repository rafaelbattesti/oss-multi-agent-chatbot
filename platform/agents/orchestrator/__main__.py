import logging
import uvicorn

logging.basicConfig(level=logging.DEBUG)

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore

from executor import OrchestratorAgentExecutor
from card import public_agent_card

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware


if __name__ == '__main__':
    request_handler = DefaultRequestHandler(
        agent_executor=OrchestratorAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=public_agent_card,
        extended_agent_card=public_agent_card,
    )

    routes = []
    routes.extend(create_agent_card_routes(public_agent_card))
    routes.extend(create_rest_routes(request_handler))

    app = Starlette(routes=routes)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run(app, host='0.0.0.0', port=9999)