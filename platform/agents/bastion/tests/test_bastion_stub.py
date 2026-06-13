import json
import pathlib
import sys
import tomllib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class ProjectMetadataTests(unittest.TestCase):
    def test_project_is_uv_managed_with_pinned_dependencies(self) -> None:
        pyproject = PROJECT_ROOT / "pyproject.toml"
        lockfile = PROJECT_ROOT / "uv.lock"

        self.assertTrue(pyproject.exists())
        self.assertTrue(lockfile.exists())

        data = tomllib.loads(pyproject.read_text())
        dependencies = data["project"]["dependencies"]

        self.assertIn("langgraph==1.2.5", dependencies)
        self.assertIn("a2a-sdk[http-server]==1.1.0", dependencies)


class GraphTests(unittest.TestCase):
    def test_graph_encapsulates_received_payload_in_response_text(self) -> None:
        from bastion.graph import run_stub_graph

        payload = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "ping"}],
                },
            },
        }

        result = run_stub_graph(payload)

        self.assertEqual(
            json.loads(result["response_text"]),
            {"received_payload": payload},
        )


class A2AServerTests(unittest.TestCase):
    def test_server_exposes_agent_card_discovery_and_jsonrpc_routes(self) -> None:
        from bastion.server import agent_card, app

        route_paths = {route.path for route in app.routes}

        self.assertEqual(agent_card.name, "Bastion Stub Agent")
        self.assertIn("/.well-known/agent-card.json", route_paths)
        self.assertIn("/", route_paths)

    def test_executor_response_text_contains_payload_received_by_agent(self) -> None:
        from bastion.executor import build_response_message_text

        payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "hello"}],
            },
        }

        self.assertEqual(
            json.loads(build_response_message_text(payload)),
            {"received_payload": payload},
        )


if __name__ == "__main__":
    unittest.main()
