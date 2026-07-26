#!/usr/bin/env python3
"""Focused negative tests for validate_discovery_evidence.py."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate_discovery_evidence.py")
SPEC = importlib.util.spec_from_file_location("validate_discovery_evidence", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class FakeJavascriptParser:
    supported = True
    reason = "test parser"

    def __init__(self, symbols: list[validator.Located] | None = None) -> None:
        self.symbols = symbols or []

    def parse(self, path: Path) -> list[validator.Located]:
        return self.symbols


class UnsupportedJavascriptParser:
    supported = False
    reason = "no repository-local parser"


class EvidenceNegativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "sample.py").write_text(
            "from fastapi import APIRouter\n"
            "router = APIRouter(prefix='/api')\n"
            "\n"
            "class ChatHandler:\n"
            "    def preprocess_message(self):\n"
            "        return True\n"
            "\n"
            "@router.post('/chat')\n"
            "def chat_stream():\n"
            "    return True\n",
            encoding="utf-8",
        )
        (self.root / "sample.js").write_text(
            "export const present = () => true;\n", encoding="utf-8"
        )
        (self.root / "sample.sh").write_text(
            "#!/usr/bin/env bash\nreal_function() {\n  return 0\n}\n",
            encoding="utf-8",
        )
        self.backup = self.root / "copied-backups"
        self.backup.mkdir()
        for path in self.root.glob("sample.*"):
            shutil.copy2(path, self.backup / path.name)

    def tearDown(self) -> None:
        for backup in self.backup.iterdir():
            target = self.root / backup.name
            shutil.copy2(backup, target)
            self.assertEqual(target.read_bytes(), backup.read_bytes())
        self.temp.cleanup()

    def validate(
        self,
        evidence: dict[str, str],
        javascript_parser: object | None = None,
    ) -> validator.Validation:
        return validator.validate_evidence(
            self.root,
            "TEST-001",
            0,
            evidence,
            javascript_parser or FakeJavascriptParser(),
        )

    def test_missing_python_symbol(self) -> None:
        result = self.validate(
            {
                "path": "sample.py",
                "kind": "python-function",
                "locator": "fabricated",
                "line_range": "L1-L1",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-locator")

    def test_incorrect_qualified_method(self) -> None:
        result = self.validate(
            {
                "path": "sample.py",
                "kind": "python-method",
                "locator": "WrongHandler.preprocess_message",
                "line_range": "L5-L6",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-locator")

    def test_symbol_outside_cited_range(self) -> None:
        result = self.validate(
            {
                "path": "sample.py",
                "kind": "python-method",
                "locator": "ChatHandler.preprocess_message",
                "line_range": "L1-L2",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "locator-outside-range")

    def test_fabricated_test_function(self) -> None:
        result = self.validate(
            {
                "path": "sample.py",
                "kind": "test-function",
                "locator": "test_fabricated",
                "line_range": "L1-L2",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-locator")

    def test_nonexistent_javascript_symbol_with_parser(self) -> None:
        result = self.validate(
            {
                "path": "sample.js",
                "kind": "javascript-function",
                "locator": "missing",
                "line_range": "L1-L1",
                "explanation": "negative fixture",
            },
            FakeJavascriptParser(
                [validator.Located("present", "javascript-export", 1, 1)]
            ),
        )
        self.assertEqual(result.result, "invalid-locator")

    def test_unsupported_javascript_parser(self) -> None:
        result = self.validate(
            {
                "path": "sample.js",
                "kind": "javascript-function",
                "locator": "present",
                "line_range": "L1-L1",
                "explanation": "negative fixture",
            },
            UnsupportedJavascriptParser(),
        )
        self.assertEqual(result.result, "unsupported")

    def test_route_path_mismatch(self) -> None:
        result = self.validate(
            {
                "path": "sample.py",
                "kind": "python-route",
                "locator": "POST /api/wrong -> chat_stream",
                "line_range": "L9-L10",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-locator")
        self.assertIn("path", result.problem or "")

    def test_http_method_mismatch(self) -> None:
        result = self.validate(
            {
                "path": "sample.py",
                "kind": "python-route",
                "locator": "GET /api/chat -> chat_stream",
                "line_range": "L9-L10",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-locator")
        self.assertIn("method", result.problem or "")

    def test_shell_function_mismatch(self) -> None:
        result = self.validate(
            {
                "path": "sample.sh",
                "kind": "shell-function",
                "locator": "fabricated",
                "line_range": "L1-L4",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-locator")

    def test_invalid_file_level_evidence(self) -> None:
        result = self.validate(
            {
                "path": "missing.file",
                "kind": "file",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-path")

    def test_file_level_evidence_rejects_fake_symbol(self) -> None:
        result = self.validate(
            {
                "path": "sample.sh",
                "kind": "file",
                "locator": "whole-script",
                "explanation": "negative fixture",
            }
        )
        self.assertEqual(result.result, "invalid-locator")


if __name__ == "__main__":
    unittest.main()
