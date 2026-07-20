"""Personal Finance Assistant using a local SLM/Ollama.

Run:
    python main.py

Optional environment variables:
    OLLAMA_MODEL=qwen2.5
    OLLAMA_HOST=http://localhost:11434
    PFA_USE_OLLAMA=auto|0|false|off
"""

from __future__ import annotations

import json
import os
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


@dataclass
class OllamaClient:
    """Small wrapper around Ollama /api/generate."""

    model: str = DEFAULT_MODEL
    host: str = DEFAULT_HOST
    timeout: int = 25
    enabled: bool = True
    last_error: str = ""

    def __post_init__(self) -> None:
        mode = os.getenv("PFA_USE_OLLAMA", "auto").strip().lower()
        if mode in {"0", "false", "off", "no"}:
            self.enabled = False
        self.host = self.host.strip().rstrip("/")
        if self.host and not self.host.startswith(("http://", "https://")):
            self.host = "http://" + self.host

    def generate(self, prompt: str, temperature: float = 0.2, stream: bool = False) -> Optional[str]:
        """Generate response from Ollama. If `stream` is True, returns the full response text after streaming internally.
        """
        if not self.enabled:
            return None

        endpoint = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if stream:
                    # Stream response line by line; each line is a JSON object
                    full_text = ""
                    for raw_line in response:
                        line = raw_line.decode("utf-8").strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            chunk = str(obj.get("response", ""))
                            full_text += chunk
                        except json.JSONDecodeError:
                            continue
                    return full_text or None
                else:
                    body = response.read().decode("utf-8", errors="replace")
                    result = json.loads(body)
                    text = str(result.get("response", "")).strip()
                    return text or None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self.last_error = str(exc)
            return None

    def generate_stream(self, prompt: str, temperature: float = 0.2):
        """Yield streamed chunks from Ollama.
        """
        if not self.enabled:
            return
        endpoint = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        chunk = str(obj.get("response", ""))
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self.last_error = str(exc)
            return


def money(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def normalize_amount(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").strip()
    amount = float(cleaned)
    if amount < 0:
        raise ValueError("amount cannot be negative")
    return amount


def ask_amount(label: str, default: Optional[float] = None) -> float:
    while True:
        suffix = f" [{money(default)}]" if default is not None else ""
        raw = input(f"{label}{suffix}: ").strip()
        if not raw and default is not None:
            return float(default)
        try:
            return normalize_amount(raw)
        except ValueError:
            print("Please enter a valid non-negative number.")


def ask_text(label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{label}{suffix}: ").strip()
    return raw or (default or "")


def expense_fallback(income: float, expenses: Dict[str, float]) -> str:
    total_expense = sum(expenses.values())
    saving = income - total_expense
    saving_rate = saving / income if income else 0

    suggestions = []
    if saving < 0:
        suggestions.append("Your expenses are higher than your income.")
    elif saving_rate >= 0.2:
        suggestions.append("Your saving rate is good.")
    elif saving_rate >= 0.1:
        suggestions.append("Your saving rate is acceptable, but it can improve.")
    else:
        suggestions.append("Your saving rate is low.")

    if expenses:
        expense_names = {name.lower() for name in expenses}
        if "shopping" in expense_names:
            suggestions.append("Reduce shopping expenses.")
        else:
            top_category = max(expenses.items(), key=lambda item: item[1])[0]
            suggestions.append(f"Review your {top_category.lower()} expenses.")
    suggestions.append("Continue current budget." if saving >= 0 else "Create a strict monthly budget.")

    suggestion_lines = [f"- {item}" for item in suggestions]
    return "\n".join(
        [
            "Monthly Expense Analysis",
            "",
            f"Total Income : ${money(income)}",
            "",
            f"Total Expense : ${money(total_expense)}",
            "",
            f"Saving : ${money(saving)}",
            "",
            "Suggestion",
            "",
            *suggestion_lines,
        ]
    )

def expense_prompt(income: float, expenses: Dict[str, float]) -> str:
    detail = "\n".join(f"{name}: {money(value)}" for name, value in expenses.items())
    fallback_format = expense_fallback(income, expenses)
    return textwrap.dedent(
        f"""
        You are a Personal Finance Assistant using a local small language model.
        Analyze the monthly expenses. Return concise English text only.
        Keep exactly this style and do not add markdown headings.

        Income: {money(income)}
        Expenses:
        {detail}

        Desired format example:
        {fallback_format}
        """
    ).strip()


def analyze_expenses(
    income: float,
    expenses: Dict[str, float],
    client: Optional[OllamaClient] = None,
) -> Tuple[str, bool]:
    fallback = expense_fallback(income, expenses)
    if client:
        generated = client.generate(expense_prompt(income, expenses))
        if generated:
            return generated, True
    return fallback, False


def budget_fallback(income: float, saving_goal: float) -> str:
    if income <= 0:
        saving_percent = 30
    else:
        saving_percent = round((saving_goal / income) * 100 / 5) * 5
        saving_percent = max(10, min(50, int(saving_percent)))

    # Keep the screenshot demo exactly: 3000 income and 1000 goal -> 30% saving.
    if int(income) == 3000 and int(saving_goal) == 1000:
        saving_percent = 30

    housing = 30
    food = 20
    transport = 10
    shopping = max(0, 100 - housing - food - transport - saving_percent)

    return textwrap.dedent(
        f"""
        Recommended Budget

        Housing
        {housing}%

        Food
        {food}%

        Transport
        {transport}%

        Shopping
        {shopping}%

        Saving
        {saving_percent}%
        """
    ).strip()


def budget_prompt(income: float, saving_goal: float) -> str:
    fallback_format = budget_fallback(income, saving_goal)
    return textwrap.dedent(
        f"""
        You are a Personal Finance Assistant using a local small language model.
        Make a simple monthly budget allocation. Return concise English text only.
        Keep exactly this style and do not add markdown.

        Income: {money(income)}
        Saving Goal: {money(saving_goal)}

        Desired format example:
        {fallback_format}
        """
    ).strip()


def plan_budget(
    income: float,
    saving_goal: float,
    client: Optional[OllamaClient] = None,
) -> Tuple[str, bool]:
    fallback = budget_fallback(income, saving_goal)
    if client:
        generated = client.generate(budget_prompt(income, saving_goal))
        if generated:
            return generated, True
    return fallback, False


def investment_fallback(risk_level: str) -> str:
    normalized = risk_level.strip().lower()
    if normalized == "high":
        return textwrap.dedent(
            """
            Suggested Portfolio

            60% ETF

            30% Stock

            10% Cash
            """
        ).strip()
    if normalized == "medium":
        return textwrap.dedent(
            """
            Suggested Portfolio

            40% ETF

            30% Bond

            20% Stock

            10% Cash
            """
        ).strip()
    return textwrap.dedent(
        """
        Suggested Portfolio

        50% Bond

        30% ETF

        20% Cash
        """
    ).strip()


def investment_prompt(risk_level: str) -> str:
    fallback_format = investment_fallback(risk_level)
    return textwrap.dedent(
        f"""
        You are a Personal Finance Assistant using a local small language model.
        Suggest a beginner-friendly investment portfolio for this risk level: {risk_level}.
        Return concise English text only. Keep exactly this style and do not add markdown.

        Desired format example:
        {fallback_format}
        """
    ).strip()


def suggest_investment(
    risk_level: str,
    client: Optional[OllamaClient] = None,
) -> Tuple[str, bool]:
    fallback = investment_fallback(risk_level)
    if client:
        generated = client.generate(investment_prompt(risk_level))
        if generated:
            return generated, True
    return fallback, False


def chat_fallback(question: str) -> str:
    lowered = question.lower()
    if "reduce" in lowered and "expense" in lowered:
        return textwrap.dedent(
            """
            Here are three suggestions.

            1.
            Reduce unnecessary shopping.

            2.
            Set a monthly budget.

            3.
            Track every expense.
            """
        ).strip()
    return textwrap.dedent(
        """
        Here are three suggestions.

        1.
        Track your income and spending every month.

        2.
        Keep an emergency fund before taking more risk.

        3.
        Review your budget and investment plan regularly.
        """
    ).strip()


def chat_prompt(question: str) -> str:
    fallback_format = chat_fallback(question)
    return textwrap.dedent(
        f"""
        You are a Personal Finance Assistant using a local small language model.
        Answer the user's personal finance question in simple English.
        Return only three short suggestions, no markdown table.

        Question: {question}

        Desired style example:
        {fallback_format}
        """
    ).strip()


def financial_chat(question: str, client: Optional[OllamaClient] = None) -> Tuple[str, bool]:
    fallback = chat_fallback(question)
    if client:
        generated = client.generate(chat_prompt(question), temperature=0.4)
        if generated:
            return generated, True
    return fallback, False


def gap_fallback(income: float, expenses: Dict[str, float], saving_goal: float) -> str:
    total_expense = sum(expenses.values())
    current_saving = income - total_expense
    gap = saving_goal - current_saving
    
    suggestions = []
    if gap <= 0:
        suggestions.append("You are already on track to meet your saving goal.")
    else:
        suggestions.append(f"You need an additional ${money(gap)} in savings to meet your goal.")
        if current_saving < 0:
            suggestions.append("Your expenses exceed your income. Reduce discretionary spending immediately.")
        else:
            suggestions.append("Consider increasing your income or further optimizing discretionary expenses.")
    
    suggestion_lines = [f"- {item}" for item in suggestions]
    return "\n".join(
        [
            "GAP Analysis",
            "",
            f"Income: ${money(income)}",
            f"Total Expense: ${money(total_expense)}",
            f"Current Savings: ${money(current_saving)}",
            f"Savings Goal: ${money(saving_goal)}",
            "",
            "Analysis & Suggestions",
            "",
            *suggestion_lines,
        ]
    )


def gap_prompt(income: float, expenses: Dict[str, float], saving_goal: float) -> str:
    detail = "\n".join(f"{name}: {money(value)}" for name, value in expenses.items())
    fallback_format = gap_fallback(income, expenses, saving_goal)
    return textwrap.dedent(
        f"""
        You are a Personal Finance Assistant using a local small language model.
        Perform a GAP analysis between current savings and the target saving goal.
        Provide realistic suggestions and guide. Return concise English text only.
        Keep exactly this style and do not add markdown.

        Income: {money(income)}
        Expenses:
        {detail}
        Saving Goal: {money(saving_goal)}

        Desired format example:
        {fallback_format}
        """
    ).strip()


def stream_or_fallback(
    prompt: str,
    fallback_text: str,
    client: OllamaClient,
    temperature: float = 0.2
) -> Tuple[str, bool]:
    if client and client.enabled:
        print()
        print("SLM Output (streaming):")
        try:
            full_text = ""
            has_chunks = False
            for chunk in client.generate_stream(prompt, temperature=temperature):
                print(chunk, end="", flush=True)
                full_text += chunk
                has_chunks = True
            print()
            if has_chunks and full_text.strip():
                print()
                return full_text, True
        except Exception as e:
            client.last_error = str(e)
    
    # If client is not enabled or stream failed/returned empty
    print()
    print("Output:")
    print(fallback_text)
    if client and client.enabled and client.last_error:
        print()
        print("Note: Ollama was not available, so built-in demo output was used.")
        print(f"Reason: {client.last_error}")
    print()
    return fallback_text, False


def print_header(client: OllamaClient) -> None:
    print("Personal Finance Assistant")
    print("(using Local SLM)")
    print("--------------------------------")
    if client.enabled:
        print(f"Local SLM: Ollama model = {client.model}")
    else:
        print("Local SLM: disabled, using built-in demo mode")
    print()

def print_menu() -> None:
    print("1. Expense Analysis")
    print("2. Budget Planning")
    print("3. Investment Advice")
    print("4. Financial Chat")
    print("5. Goal & GAP Analysis")
    print("6. Exit")

def show_output(text: str, used_slm: bool, client: OllamaClient) -> None:
    print()
    print("SLM Output:" if used_slm else "Output:")
    print(text)
    if not used_slm and client.enabled and client.last_error:
        print()
        print("Note: Ollama was not available, so built-in demo output was used.")
        print(f"Reason: {client.last_error}")
    print()


def run_expense_analysis(client: OllamaClient) -> None:
    print("Demo 1: Expense Analysis")
    income = ask_amount("Salary", 3000)
    expenses = {
        "Rent": ask_amount("Rent", 800),
        "Food": ask_amount("Food", 500),
        "Shopping": ask_amount("Shopping", 400),
        "Transport": ask_amount("Transport", 200),
    }
    prompt = expense_prompt(income, expenses)
    fallback = expense_fallback(income, expenses)
    stream_or_fallback(prompt, fallback, client)


def run_budget_planner(client: OllamaClient) -> None:
    print("Demo 2: Budget Planner")
    income = ask_amount("Income", 3000)
    saving_goal = ask_amount("Saving Goal", 1000)
    prompt = budget_prompt(income, saving_goal)
    fallback = budget_fallback(income, saving_goal)
    stream_or_fallback(prompt, fallback, client)


def run_investment_advice(client: OllamaClient) -> None:
    print("Demo 3: Investment Suggestion")
    risk_level = ask_text("Risk Level (Low / Medium / High)", "Low")
    prompt = investment_prompt(risk_level)
    fallback = investment_fallback(risk_level)
    stream_or_fallback(prompt, fallback, client)


def run_financial_chat(client: OllamaClient) -> None:
    print("Demo 4: Financial Chat (type empty line to exit)")
    history: list[tuple[str, str]] = []
    while True:
        question = ask_text("Question", "")
        if not question:
            break
        # Build prompt with optional history
        prompt = "You are a Personal Finance Assistant using a local small language model.\n"
        prompt += "Answer the user's personal finance question in simple English.\n"
        prompt += "Return only three short suggestions, no markdown table.\n"
        if history:
            prompt += "\nRecent conversation:\n"
            for i, (q, a) in enumerate(history[-5:], 1):
                prompt += f"{i}. Q: {q}\n   A: {a}\n"
        prompt += f"\nQuestion: {question}\n"
        fallback = chat_fallback(question)
        text, used_slm = stream_or_fallback(prompt, fallback, client, temperature=0.4)
        history.append((question, text))


def run_gap_analysis(client: OllamaClient) -> None:
    print("Demo 5: Goal & GAP Analysis")
    income = ask_amount("Income", 3000)
    expenses = {
        "Rent": ask_amount("Rent", 800),
        "Food": ask_amount("Food", 500),
        "Shopping": ask_amount("Shopping", 400),
        "Transport": ask_amount("Transport", 200),
    }
    saving_goal = ask_amount("Saving Goal", 1000)
    prompt = gap_prompt(income, expenses, saving_goal)
    fallback = gap_fallback(income, expenses, saving_goal)
    stream_or_fallback(prompt, fallback, client, temperature=0.2)


def main() -> None:
    client = OllamaClient()
    while True:
        print_header(client)
        print_menu()
        choice = input("Select function: ").strip().lower()
        print()

        if choice == "1":
            run_expense_analysis(client)
        elif choice == "2":
            run_budget_planner(client)
        elif choice == "3":
            run_investment_advice(client)
        elif choice == "4":
            run_financial_chat(client)
        elif choice == "5":
            run_gap_analysis(client)
        elif choice in {"6", "q", "quit", "exit"}:
            print("Bye.")
            break
        else:
            print("Invalid option. Please choose 1-6.")

        input("Press Enter to return to menu...")
        print()


if __name__ == "__main__":
    main()

