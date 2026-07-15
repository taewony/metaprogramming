# harness/agent.py

import json
import uuid

from harness.context import WorkspaceContext
from harness.session import SessionStore
from harness import tools as tool_impl
from harness.utils import clip, middle, now

class MiniAgent:
    """
    Mini Coding Agent
        User
          │
          ▼
      Build Prompt
          │
          ▼
      LLM Completion
          │
      ┌───┴────┐
      │        │
   Tool Call  Final Answer
      │
      ▼
   Tool Result
      │
      └───────────Loop──────────►
    """

    def __init__(
        self,
        model_client,
        workspace: WorkspaceContext,
        session_store: SessionStore,
        approval_policy="ask",
        max_steps=6,
        max_new_tokens=512,
        max_depth=1,
        read_only=False,
    ):
        self.model_client = model_client
        self.workspace = workspace
        self.session_store = session_store
        self.root = workspace.repo_root
        self.max_steps = max_steps
        self.max_new_tokens = max_new_tokens
        self.max_depth = max_depth
        self.read_only = read_only
        self.approval_policy = approval_policy

        # session id
        self.session_id = str(uuid.uuid4())
        self.memory = []
        self.tools = self.build_tools()
        self.system_prompt = self.build_prefix()
        self.session_path = (
            self.session_store.root /
            f"{self.session_id}.json"
        )

    # ---------------------------------------------------------

    def build_tools(self):
        return {
            "list_files": {
                "schema": {
                    "path": "str='.'"
                },
                "risky": False,
                "run": lambda args:
                    tool_impl.tool_list_files(
                        self.root,
                        args.get("path", "."),
                    ),
            },

            "read_file": {
                "schema": {
                    "path": "str"
                },
                "risky": False,
                "run": lambda args:
                    tool_impl.tool_read_file(
                        self.root,
                        args["path"],
                    ),
            },

            "search": {
                "schema": {
                    "pattern": "str"
                },
                "risky": False,
                "run": lambda args:
                    tool_impl.tool_search(
                        self.root,
                        args["pattern"],
                    ),
            },

            "write_file": {
                "schema": {
                    "path": "str",
                    "content": "str",
                },
                "risky": True,
                "run": lambda args:
                    tool_impl.tool_write_file(
                        self.root,
                        args["path"],
                        args["content"],
                    ),
            },

            "run_shell": {
                "schema": {
                    "command": "str"
                },
                "risky": True,
                "run": lambda args:
                    tool_impl.tool_run_shell(
                        self.root,
                        args["command"],
                    ),
            },
        }

    # ---------------------------------------------------------

    def build_prefix(self):
        return f"""
You are Mini Coding Agent.
Workspace
{self.workspace.summary()}
Available Tools
{list(self.tools.keys())}
Rules
- Think step by step.
- Use tools when necessary.
- Return FINAL when finished.
Tool Format
{{
"type":"tool",
"name":"tool_name",
"args":{{...}}
}}

Final Format
{{
"type":"final",
"content":"..."
}}
"""

    # ---------------------------------------------------------

    def ask(self, user_message):
        self.memory.append(
            {
                "role": "user",
                "content": user_message,
            }
        )
        step = 0
        while step < self.max_steps:
            prompt = self.build_prompt()
            response = self.model_client.complete(
                prompt,
                max_tokens=self.max_new_tokens,
            )
            parsed = self.parse(response)
            if parsed["type"] == "final":
                self.memory.append(
                    {
                        "role": "assistant",
                        "content": parsed["content"],
                    }
                )
                return parsed["content"]
            elif parsed["type"] == "tool":
                result = self.run_tool(
                    parsed["name"],
                    parsed.get("args", {}),
                )
                self.memory.append(
                    {
                        "role": "tool",
                        "content": result,
                    }
                )
            else:
                return response

            step += 1
        return "Maximum reasoning steps exceeded."

    # ---------------------------------------------------------

    def build_prompt(self):
        history = []
        for item in self.memory:
            history.append(
                f"{item['role']}:\n{item['content']}"
            )
        return self.system_prompt + "\n\n" + "\n\n".join(history)

    # ---------------------------------------------------------

    def parse(self, text):
        try:
            obj = json.loads(text)
            return obj
        except Exception:
            return {
                "type": "final",
                "content": text,
            }

    # ---------------------------------------------------------

    def run_tool(self, name, args):
        tool = self.tools.get(name)
        if tool is None:
            return f"Unknown tool: {name}"
        try:
            result = tool["run"](args)
            return str(result)
        except Exception as e:
            return f"Tool Error: {e}"
            
    # ---------------------------------------------------------

    def reset(self):
        self.memory.clear()

    # ---------------------------------------------------------

    def memory_text(self):
        text = []
        for item in self.memory:
            text.append(
                f"[{item['role']}]"
            )
            text.append(item["content"])
            text.append("")
        return "\n".join(text)