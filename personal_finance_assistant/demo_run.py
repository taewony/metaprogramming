"""Non-interactive demo runner for the Personal Finance Assistant."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from main import (
    analyze_expenses,
    financial_chat,
    plan_budget,
    suggest_investment,
)


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "sample_finance.json"
OUTPUT_PATH = ROOT / "outputs" / "demo_output.txt"


def block(title: str, content: str) -> str:
    cleaned = textwrap.dedent(content).strip()
    return f"{title}\n{'-' * len(title)}\n{cleaned}\n"


def main() -> None:
    sample = json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))

    expense_text, _ = analyze_expenses(sample["salary"], sample["expenses"], client=None)
    budget_text, _ = plan_budget(
        sample["budget"]["income"], sample["budget"]["saving_goal"], client=None
    )
    investment_low, _ = suggest_investment(sample["investment"]["risk_level"], client=None)
    investment_high, _ = suggest_investment("High", client=None)
    chat_text, _ = financial_chat(sample["chat_question"], client=None)

    transcript = "\n".join(
        [
            block(
                "Home",
                """
                Personal Finance Assistant
                (using Local SLM)
                --------------------------------
                1. Expense Analysis
                2. Budget Planning
                3. Investment Advice
                4. Financial Chat
                5. Exit
                """,
            ),
            block(
                "Demo 1 Input",
                """
                Salary
                3000

                Rent
                800

                Food
                500

                Shopping
                400

                Transport
                200
                """,
            ),
            block("Demo 1 SLM Output", expense_text),
            block(
                "Demo 2 Input",
                """
                Income
                3000

                Saving Goal
                1000
                """,
            ),
            block("Demo 2 SLM Output", budget_text),
            block(
                "Demo 3 Input",
                """
                Risk Level
                Low
                """,
            ),
            block("Demo 3 Output", investment_low),
            block(
                "Demo 3 Other Input",
                """
                Risk Level
                High
                """,
            ),
            block("Demo 3 Other Output", investment_high),
            block(
                "Demo 4 Input",
                """
                How can I reduce my monthly expenses?
                """,
            ),
            block("Demo 4 SLM Answer", chat_text),
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(transcript, encoding="utf-8")
    print(transcript)
    print(f"Demo output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
