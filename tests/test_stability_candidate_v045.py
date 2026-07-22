import json
import tempfile
import unittest
from pathlib import Path

from dreamteam.operations import doctor, minimal_config, status, write_minimal_config

ROOT = Path(__file__).resolve().parents[1]


class StabilityCandidateV045Tests(unittest.TestCase):
    def test_operational_schemas_are_closed_and_versioned(self):
        for name in (
            "dreamteam-doctor-report.schema.json",
            "dreamteam-status-report.schema.json",
        ):
            schema = json.loads((ROOT / "core/schemas" / name).read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(schema["properties"]["schema_version"]["const"], 1)

    def test_doctor_and_status_payloads_match_declared_schema_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_minimal_config(root)
            doctor_payload = doctor(root).payload()
            status_payload = status(root).payload()
            doctor_schema = json.loads(
                (ROOT / "core/schemas/dreamteam-doctor-report.schema.json").read_text()
            )
            status_schema = json.loads(
                (ROOT / "core/schemas/dreamteam-status-report.schema.json").read_text()
            )
            self.assertEqual(set(doctor_payload), set(doctor_schema["properties"]))
            self.assertEqual(set(status_payload), set(status_schema["properties"]))
            self.assertEqual(minimal_config()["version"], 2)


if __name__ == "__main__":
    unittest.main()
