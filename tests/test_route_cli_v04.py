import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "adapters/claude-code/plugins/dreamteam/scripts/dreamteam_route.py"


def load_route():
    spec = importlib.util.spec_from_file_location("dreamteam_route_v04", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RouteCliV04Tests(unittest.TestCase):
    def test_string_false_is_not_coerced(self):
        module = load_route()
        data = {
            "criticality": "M0",
            "task_kind": "discovery",
            "direct_usage": {},
            "main_context_is_hot": "false",
        }
        with self.assertRaises(TypeError):
            module.parse_request(data)

    def test_unknown_request_field_is_rejected(self):
        module = load_route()
        data = {
            "criticality": "M0",
            "task_kind": "discovery",
            "direct_usage": {},
            "surprise": True,
        }
        with self.assertRaises(ValueError):
            module.parse_request(data)


if __name__ == "__main__":
    unittest.main()
