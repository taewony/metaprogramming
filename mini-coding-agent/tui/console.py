# tui/console.py
import argparse
import sys
from pathlib import Path
from model.client import OllamaModelClient
from harness.agent import MiniAgent
from harness.session import SessionStore
from harness.context import WorkspaceContext

WELCOME_ART = (
    r"/\   /\  ",
    r"{  `---' }",
    r"{  O O   }",
    r"~~>   V   <~~",
    r" \   |   /  ",
    r"  `-----'__ ",
)

HELP_DETAILS = "\n".join(
    [
        "Commands:",
        "/help    Show this help message.",
        "/memory  Show the agent's distilled working memory.",
        "/session Show the path to the saved session file.",
        "/reset   Clear the current session history and memory.",
        "/exit    Exit the agent.",
    ]
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max_steps", type=int, default=6)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--max_depth", type=int, default=1)
    parser.add_argument("--approval", default="ask", choices=["ask", "auto", "never"])
    parser.add_argument("--read_only", action="store_true")
    parser.add_argument("--session")
    parser.add_argument("--cwd")
    # ... (인자 처리)
    args = parser.parse_args()

    # 1. 모델 클라이언트 생성
    model_client = OllamaModelClient(
        model=args.model,
        host=args.host,
        temperature=args.temperature,
        top_p=args.top_p,
        timeout=args.timeout,
    )

    # 2. 작업 공간(context) 구성
    workspace = WorkspaceContext.build(args.cwd or Path.cwd())

    # 3. 세션 저장소 준비
    store = SessionStore(root=Path(".mini-coding-agent"))

    # 4. 에이전트 생성 (기존 세션 불러오기 또는 새로 만들기)
    if args.session:
        agent = MiniAgent.from_session(
            model_client, workspace, store, args.session,
            approval_policy=args.approval,
            max_steps=args.max_steps,
            max_new_tokens=args.max_new_tokens,
            max_depth=args.max_depth,
            read_only=args.read_only,
        )
    else:
        agent = MiniAgent(
            model_client, workspace, store,
            approval_policy=args.approval,
            max_steps=args.max_steps,
            max_new_tokens=args.max_new_tokens,
            max_depth=args.max_depth,
            read_only=args.read_only,
        )

    # 5. 환영 메시지 출력
    print("\n".join(WELCOME_ART))
    if hasattr(agent, "session_path"):
        print(f"Session: {agent.session_path}")
    print("Type /help for commands.")

    # 6. 대화 루프
    while True:
        try:
            user_input = input("\n> ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/help":
            print(HELP_DETAILS)
            continue
        if user_input == "/memory":
            print(agent.memory_text())
            continue
        if user_input == "/session":
            print(agent.session_path)
            continue
        if user_input == "/reset":
            agent.reset()
            print("Session reset.")
            continue

        # 일반 사용자 메시지 → 에이전트 실행
        response = agent.ask(user_input)
        print("\n" + response)