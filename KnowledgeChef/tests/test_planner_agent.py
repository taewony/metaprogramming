from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from kchef.planner_agent import PlannerPipeline, build_parser, load_system_model


class PlannerAgentTests(unittest.TestCase):
    def test_help_lists_planner_commands(self) -> None:
        help_text = build_parser().format_help()
        for command in ("plan", "ask", "doctor", "loop"):
            self.assertIn(command, help_text)

    def test_compound_question_builds_ir(self) -> None:
        system_model = load_system_model(__import__("pathlib").Path("data/techshop.db"))
        planner = PlannerPipeline(system_model, "kchef")
        ir = planner.plan("VIP 고객은 몇 명이고, 누구야?")

        self.assertEqual(ir.intent, "COMPOUND")
        self.assertIn("COUNT", ir.sub_intents or [])
        self.assertIn("LIST", ir.sub_intents or [])
        self.assertEqual(ir.playbook_used, "FILTER_AND_LIST")

    def test_plan_cli_json_mode(self) -> None:
        from kchef.planner_agent import _handle_plan
        import argparse
        import pathlib

        args = argparse.Namespace(
            question=["VIP", "고객은", "몇", "명이고,", "누구야?"],
            db=pathlib.Path("data/techshop.db"),
            skills_dir=pathlib.Path("kchef"),
            json=True,
        )
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = _handle_plan(args)
        self.assertEqual(code, 0)
        self.assertIn('"intent": "COMPOUND"', buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
