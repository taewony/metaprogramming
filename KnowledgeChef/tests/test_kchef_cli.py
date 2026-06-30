from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from kchef.kchef import build_parser, cognitive_knowledge_os_loop


class KChefCliTests(unittest.TestCase):
    def test_top_level_help_lists_prd_commands(self) -> None:
        help_text = build_parser().format_help()

        for command in ("init", "add", "merge", "dedupe", "diff", "validate", "index", "query", "loop"):
            self.assertIn(command, help_text)

    def test_loop_scaffold_prints_plan(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cognitive_knowledge_os_loop("VIP 고객은 몇 명이고, 누구야?")

        self.assertEqual(code, 0)
        output = buffer.getvalue()
        self.assertIn("KnowledgeChef agent loop scaffold", output)
        self.assertIn("Intent analysis", output)
        self.assertIn("Response synthesis", output)


if __name__ == "__main__":
    unittest.main()
