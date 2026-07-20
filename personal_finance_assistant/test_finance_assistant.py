"""Simple self-test for the Personal Finance Assistant project."""

from main import analyze_expenses, financial_chat, plan_budget, suggest_investment


def test_expense_analysis() -> None:
    text, used_slm = analyze_expenses(
        3000,
        {"Rent": 800, "Food": 500, "Shopping": 400, "Transport": 200},
        client=None,
    )
    assert used_slm is False
    assert "Total Income : $3000" in text
    assert "Total Expense : $1900" in text
    assert "Saving : $1100" in text
    assert "Reduce shopping expenses." in text


def test_budget_planner() -> None:
    text, _ = plan_budget(3000, 1000, client=None)
    assert "Recommended Budget" in text
    assert "Housing\n30%" in text
    assert "Saving\n30%" in text


def test_investment_advice() -> None:
    low, _ = suggest_investment("Low", client=None)
    high, _ = suggest_investment("High", client=None)
    assert "50% Bond" in low
    assert "30% ETF" in low
    assert "60% ETF" in high
    assert "30% Stock" in high


def test_financial_chat() -> None:
    text, _ = financial_chat("How can I reduce my monthly expenses?", client=None)
    assert "Here are three suggestions." in text
    assert "Reduce unnecessary shopping." in text
    assert "Set a monthly budget." in text
    assert "Track every expense." in text


def main() -> None:
    test_expense_analysis()
    test_budget_planner()
    test_investment_advice()
    test_financial_chat()
    print("All tests passed.")


if __name__ == "__main__":
    main()
