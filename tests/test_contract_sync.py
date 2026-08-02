import json
from pathlib import Path
import unittest

from scripts.sync_contract import extract_contract, render_catalog


ROOT = Path(__file__).resolve().parents[1]


class ContractSyncTests(unittest.TestCase):
    def test_checked_in_contract_has_35_unique_tools(self) -> None:
        contract = json.loads(
            (ROOT / "references" / "tubealfred-tools.json").read_text(encoding="utf-8")
        )
        names = [item["mcp_tool"] for item in contract["tools"]]
        operations = [(item["method"], item["path"]) for item in contract["tools"]]
        self.assertEqual(35, contract["tool_count"])
        self.assertEqual(35, len(names))
        self.assertEqual(35, len(set(names)))
        self.assertEqual(35, len(set(operations)))

    def test_extracts_path_query_and_json_body_parameters(self) -> None:
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Fixture", "version": "1"},
            "paths": {
                "/v1/youtube/things/{thing_id}": {
                    "post": {
                        "operationId": "things_page",
                        "summary": "Fixture page",
                        "x-mcp-tool": "youtube_things_page",
                        "x-credit-cost": "1 credit per call",
                        "parameters": [
                            {
                                "name": "thing_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            },
                            {
                                "name": "sort",
                                "in": "query",
                                "schema": {"type": "string", "enum": ["new", "top"]},
                            },
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["continuation_token"],
                                        "properties": {
                                            "continuation_token": {"type": "string"},
                                            "count": {"type": "integer"},
                                        },
                                    }
                                }
                            }
                        },
                    }
                }
            },
        }
        contract = extract_contract(spec, "2026-07-15")
        self.assertEqual(1, contract["tool_count"])
        parameters = contract["tools"][0]["parameters"]
        self.assertIn(
            {"name": "thing_id", "in": "path", "required": True, "type": "string"},
            parameters,
        )
        self.assertIn(
            {
                "name": "sort",
                "in": "query",
                "required": False,
                "type": "string",
                "enum": ["new", "top"],
            },
            parameters,
        )
        self.assertIn(
            {
                "name": "continuation_token",
                "in": "body",
                "required": True,
                "type": "string",
            },
            parameters,
        )

    def test_catalog_is_generated_and_warns_about_spend(self) -> None:
        contract = json.loads(
            (ROOT / "references" / "tubealfred-tools.json").read_text(encoding="utf-8")
        )
        catalog = render_catalog(contract)
        self.assertIn("**35 read-only tools**", catalog)
        self.assertIn("explicit user approval", catalog)
        self.assertIn("Treat video metadata", catalog)
        self.assertEqual(
            catalog,
            (ROOT / "skills" / "youtube-full" / "references" / "tool-catalog.md").read_text(
                encoding="utf-8"
            ),
        )


if __name__ == "__main__":
    unittest.main()
