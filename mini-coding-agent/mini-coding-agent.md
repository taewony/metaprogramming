## `mini_coding_agent.py` reverse engineering

원본 `mini_coding_agent.py`는 약 1,700줄 이상의 코드에 **Agent Loop, Ollama 호출, Tool 실행, Session 관리, Context 구성**이 모두 섞여 있습니다.

수업용으로는 위와 같이 분리하면 각 파일이 하나의 책임만 갖게 되어 다음 순서로 단계별 설명이 가능합니다.

0. **main.py** - Entry Point (진입점)
1. **TUI(Console)** — 사용자와 대화하는 Interface
2. **Model(Client)** — Ollama LLM와 통신하는 계층 (Model Response)
3. **Agent** — 전체 실행을 조정하는 오케스트레이터(Ochestrator)
4. **Context** — 프롬프트 생성 (Prompt Assembly)
5. **Session** — 대화 기억(Working memroy, etc)
6. **Tools** — 파일 읽기, 쓰기, Shell 실행 등의 기능

이 구조는 "UI → Agent → Model → Tool → Memory"라는 계층이 명확하여, 학생들이 이후 LangChain, LangGraph, OpenAI Agents SDK 같은 보다 큰 프레임워크를 배울 때도 자연스럽게 개념을 확장할 수 있는 교육용 아키텍처가 됩니다.


아래는 `mini_coding_agent.py`를 **모델(Model)**, **TUI**, **하네스(Harness)** 세 영역으로 나누고, 각각의 책임과 역할을 학생들이 이해하기 쉽도록 설명과 함께 정리한 구조입니다.

---

## 1. 전체 구조 개요

| 폴더 | 파일 | 주요 책임 |
|------|------|----------|
| `model/` | `client.py` | Ollama / Fake 모델 API 호출 및 응답 처리 |
| `tui/` | `console.py` | 명령줄 인터페이스(CLI)와 사용자 입력/출력 처리 |
| `harness/` | `context.py` | 작업 디렉터리, Git 상태, 프로젝트 문서 등 실행 환경 정보 제공 |
| | `session.py` | 대화 기록, 메모리, 세션 저장/불러오기 |
| | `tools.py` | 파일 읽기/쓰기, 검색, 셸 실행 등 실제 도구 구현 |
| | `agent.py` | 도구와 모델을 조합해 사용자 요청을 처리하는 핵심 에이전트 |
| | `utils.py` | 문자열 자르기(clip), XML 파싱 등 공통 유틸리티 |

---

## 2. 폴더별 상세 분해

### 🔌 `model/` – 모델 API 접속 처리

**역할:** Ollama 서버와 통신하거나, 테스트용 가짜 모델을 제공합니다.  
**핵심 클래스:** `OllamaModelClient`, `FakeModelClient`

```python
# model/client.py
import json
import urllib.error
import urllib.request

class OllamaModelClient:
    def __init__(self, model, host, temperature, top_p, timeout):
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout

    def complete(self, prompt, max_new_tokens):
        """Ollama API를 호출하고 모델의 응답을 반환"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "raw": False,
            "think": False,
            "options": {
                "num_predict": max_new_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
            },
        }
        request = urllib.request.Request(
            self.host + "/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("response", "")

class FakeModelClient:
    """테스트용 모델 – 미리 준비한 응답을 순서대로 반환"""
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.prompts = []

    def complete(self, prompt, max_new_tokens):
        self.prompts.append(prompt)
        if not self.outputs:
            raise RuntimeError("fake model ran out of outputs")
        return self.outputs.pop(0)
```

---

### 🖥️ `tui/` – 채팅 UI (터미널 인터페이스)

**역할:** 사용자 명령을 입력받고, 에이전트를 실행하며, 결과를 화면에 출력합니다.  
**핵심 함수:** `main()` – `argparse`로 인자를 해석하고, `MiniAgent`를 생성해 대화 루프를 실행합니다.

```python
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
```

---

### 🧩 `harness/` – 메모리, 도구, 에이전트 코어

이 폴더는 에이전트의 **두뇌와 팔** 역할을 하는 파일들로 구성됩니다.

#### 📁 `context.py` – 작업 환경 정보

```python
# harness/context.py
import subprocess
from pathlib import Path
from harness.utils import clip

DOC_NAMES = ("AGENTS.md", "README.md", "pyproject.toml", "package.json")

class WorkspaceContext:
    """현재 Git 저장소, 브랜치, 최근 커밋, 프로젝트 문서 등을 제공"""
    def __init__(self, cwd, repo_root, branch, default_branch, status, recent_commits, project_docs):
        self.cwd = cwd
        self.repo_root = repo_root
        # ...

    @classmethod
    def build(cls, cwd):
        # git 명령어로 저장소 정보 수집
        # 프로젝트 문서(README 등)를 읽어 clip()으로 축약
        return cls(...)

    def text(self):
        """프롬프트에 포함될 워크스페이스 요약 문자열"""
        return "\n".join([...])
```

#### 📁 `session.py` – 대화 기록 및 메모리

```python
# harness/session.py
import json
from pathlib import Path

class SessionStore:
    """세션을 JSON 파일로 저장/불러오기"""
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, session):
        path = self.root / f"{session['id']}.json"
        path.write_text(json.dumps(session, indent=2), encoding="utf-8")
        return path

    def load(self, session_id):
        return json.loads(self.path(session_id).read_text(encoding="utf-8"))
```

#### 📁 `tools.py` – 실제 도구 구현

```python
# harness/tools.py
import shutil
import subprocess
from pathlib import Path
from harness.utils import clip
from harness.context import IGNORED_PATH_NAMES

def tool_list_files(root, path):
    """디렉터리 내 파일/폴더 목록 반환"""
    # ...

def tool_read_file(root, path, start=1, end=200):
    """파일의 특정 줄 범위 읽기"""
    # ...

def tool_search(root, pattern, path="."):
    """ripgrep 또는 간단한 텍스트 검색"""
    # ...

def tool_run_shell(root, command, timeout=20):
    """셸 명령어 실행"""
    # ...

def tool_write_file(root, path, content):
    """파일 쓰기"""
    # ...

def tool_patch_file(root, path, old_text, new_text):
    """파일 내 특정 텍스트 치환"""
    # ...
```

#### 📁 `agent.py` – 에이전트 핵심 로직

```python
# harness/agent.py
import json
import uuid
from datetime import datetime, timezone
from harness.context import WorkspaceContext
from harness.session import SessionStore
from harness import tools as tool_impl
from harness.utils import clip, middle, now

class MiniAgent:
    def __init__(self, model_client, workspace, session_store, ...):
        self.model_client = model_client
        self.workspace = workspace
        self.session_store = session_store
        # ... 세션, 메모리, 도구 목록 초기화

    def build_tools(self):
        """도구 이름 → 스키마, 실행 함수, 위험 여부 매핑"""
        return {
            "list_files": {
                "schema": {"path": "str='.'"},
                "risky": False,
                "run": lambda args: tool_impl.tool_list_files(self.root, args.get("path", ".")),
            },
            # ... read_file, search, run_shell, write_file, patch_file, delegate
        }

    def build_prefix(self):
        """시스템 프롬프트(규칙, 도구 설명, 예제, 워크스페이스 정보) 생성"""
        return "\n\n".join([...])

    def ask(self, user_message):
        """사용자 메시지를 받아 도구 호출 루프를 실행하고 최종 답변 반환"""
        # 1. 메모리에 task 저장
        # 2. while steps < max_steps:
        #    - model_client.complete()로 응답 받음
        #    - parse()로 도구 호출 또는 최종 답변 식별
        #    - 도구 호출이면 run_tool() 실행 후 기록
        #    - 최종 답변이면 반환
        # 3. 단계 초과 시 중단 메시지 반환
```

#### 📁 `utils.py` – 공통 헬퍼

```python
# harness/utils.py
import re

def clip(text, limit):
    """긴 문자열을 앞부분만 잘라내고 ... 표시"""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + f"\n...[truncated {len(text) - limit} chars]"

def middle(text, limit):
    """문자열의 가운데 부분을 ...으로 축약"""
    # ...

def now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

# XML 파싱 헬퍼 (parse, extract, parse_xml_tool 등)
```

---

## 3. 학생들에게 전달할 때의 설명 포인트

| 개념 | 설명 |
|------|------|
| **관심사 분리** | 모델 통신, UI, 코어 로직을 분리하면 각 부분을 독립적으로 수정/테스트하기 쉬움 |
| **의존성 방향** | `tui` → `harness` → `model` (상위 계층이 하위 계층에 의존) |
| **도구 패턴** | `tools.py`는 에이전트가 사용할 수 있는 '팔'을 제공하고, `agent.py`는 '두뇌' 역할 |
| **세션 & 메모리** | `session.py`는 대화 기록을 파일에 저장해 재개 가능하게 함 |
| **프롬프트 엔지니어링** | `build_prefix()`가 시스템 프롬프트를 조립하는 방식 – 규칙, 도구 설명, 예제, 컨텍스트를 모두 포함 |

---

## 4. 실행 방법 (변경 후)

```bash
# 디렉터리 구조
mini-coding-agent/
├── model/
│   └── client.py
├── tui/
│   └── console.py
├── harness/
│   ├── agent.py
│   ├── context.py
│   ├── session.py
│   ├── tools.py
│   └── utils.py
└── __main__.py   # (선택) python -m mini-coding-agent 진입점

# 실행
python -m tui.console --model llama3.2
```

---

이 구조는 학생들이 **각 컴포넌트의 역할**을 명확히 이해하고, **확장이나 교체**가 어디서 이루어져야 하는지 직관적으로 파악할 수 있도록 돕습니다. 예를 들어:

- 모델을 바꾸고 싶다면 → `model/`만 수정
- UI를 개선하고 싶다면 → `tui/`만 수정
- 새 도구를 추가하고 싶다면 → `harness/tools.py`에 추가 후 `agent.py`의 `build_tools()`에 등록

---

좋은 아이디어입니다.

Sebastian Raschka의 **mini-coding-agent**는 교육용으로는 너무 많은 기능이 하나의 `mini_coding_agent.py` 안에 들어있습니다. 공식 문서에서도 이 프로젝트의 핵심을 **Model, Context, Tools, Memory, Session, Agent Loop**의 6개 구성요소라고 설명하고 있습니다. ([GitHub][1])

학생들에게는 아래처럼 **MVC와 비슷한 계층 구조**로 나누면 훨씬 이해하기 쉽습니다.

```
mini-coding-agent/
│
├── __main__.py           # 프로그램 시작
│
├── model/
│   └── client.py         # Ollama API
│
├── tui/
│   └── console.py        # Console REPL
│
└── harness/
    ├── agent.py          # Agent Loop
    ├── context.py        # Prompt Context
    ├── session.py        # Memory / Transcript
    ├── tools.py          # Tool Dispatcher
    └── utils.py          # 공통 함수
```

---

# 전체 구조

```
┌───────────────────────────────┐
│          __main__.py          │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│        tui.console            │
│   (채팅 UI / REPL)            │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│     harness.agent             │
│     Agent Loop                │
└──────────────┬────────────────┘
               │
     ┌─────────┴──────────┐
     ▼                    ▼
context/session      tools/utils
     │
     ▼
┌───────────────────────────────┐
│      model.client             │
│     Ollama API                │
└───────────────────────────────┘
```

학생들에게는

> UI → Agent → Model

이라는 흐름이 매우 명확해집니다.

---

# 1. **main**.py

진입점은 아주 단순합니다.

```python
from tui.console import run_console

def main():
    run_console()

if __name__ == "__main__":
    main()
```

---

# 2. model/client.py

여기는 **LLM만 담당**

```python
class OllamaClient:

    def __init__(
        self,
        host="http://127.0.0.1:11434",
        model="qwen3.5:4b",
    ):
        self.host = host
        self.model = model

    def generate(self, prompt):

        ...
        # POST /api/generate

        return response
```

학생들에게는

```
Agent
   │
   ▼
OllamaClient.generate()
   │
   ▼
Ollama Server
```

만 설명하면 됩니다.

---

# 3. tui/console.py

Console UI만 담당합니다.

```python
from harness.agent import Agent

def run_console():

    agent = Agent()

    while True:

        user = input("You> ")

        if user == "/exit":
            break

        answer = agent.run(user)

        print(answer)
```

학생들은

```
입력

↓

Agent 호출

↓

출력
```

만 이해하면 됩니다.

---

# 4. harness/agent.py

가장 중요한 부분입니다.

Agent Loop만 남깁니다.

```python
class Agent:

    def __init__(self):

        self.model = OllamaClient()

        self.session = Session()

        self.context = Context()

        self.tools = ToolDispatcher()

    def run(self, user_input):

        prompt = self.context.build(
            self.session,
            user_input,
        )

        reply = self.model.generate(prompt)

        result = self.tools.execute(reply)

        self.session.append(user_input, result)

        return result
```

학생들이 이해해야 하는 것은

```
Input

↓

Context 생성

↓

LLM 호출

↓

Tool 실행

↓

Memory 저장

↓

Output
```

입니다.

---

# 5. harness/context.py

Prompt 생성 전담

```python
class Context:

    def build(self, session, user):

        prompt = f"""
History

{session.history()}

User

{user}
"""

        return prompt
```

역할은

```
Memory

+

현재 질문

↓

Prompt
```

입니다.

---

# 6. harness/session.py

Conversation Memory

```python
class Session:

    def __init__(self):

        self.messages = []

    def append(self, user, assistant):

        self.messages.append(
            ("user", user)
        )

        self.messages.append(
            ("assistant", assistant)
        )

    def history(self):

        return "\n".join(
            f"{r}: {m}"
            for r, m in self.messages
        )
```

학생들은

```
List

↓

Transcript

↓

Prompt
```

를 이해하면 됩니다.

---

# 7. harness/tools.py

Tool Dispatcher

```python
class ToolDispatcher:

    def execute(self, model_output):

        if "<tool>" not in model_output:
            return model_output

        ...

        return tool_result
```

여기에는

```
read_file()

write_file()

shell()

```

등을 추가하면 됩니다.

---

# 8. harness/utils.py

공통 함수

예를 들면

```python
def clip_text(text, max_chars=2000):

    ...

def safe_join(path):

    ...

def print_color(msg):

    ...
```

정도의 Utility만 넣습니다.

---

# 전체 실행 흐름

학생들에게는 이 그림 하나면 거의 끝납니다.

```
             __main__

                 │

                 ▼

         tui.console

                 │

                 ▼

        Agent.run(user)

                 │

        ┌────────┴────────┐

        ▼                 ▼

    Context          Session

        │                 │

        └──────┬──────────┘

               ▼

      Prompt 생성

               │

               ▼

       OllamaClient.generate()

               │

               ▼

         LLM Response

               │

               ▼

      ToolDispatcher.execute()

               │

               ▼

        Session 저장

               │

               ▼

         Console 출력
```

