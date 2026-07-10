from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "activegraph" / "text-to-sql-agent" / "scripts"
EVALS = ROOT / "activegraph" / "text-to-sql-agent" / "evals"
BUILD_SCRIPT = SCRIPTS / "build_hospital_db.py"
DRIVER_SCRIPT = SCRIPTS / "hospital_tdd_driver.py"
CASES_FILE = EVALS / "hospital_cases.jsonl"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_temp_db(tmp_path: Path) -> Path:
    builder = load_module(BUILD_SCRIPT, "build_hospital_db")
    db_file = tmp_path / "hospital.db"
    builder.build_database(db_file)
    return db_file


def test_prompt_driver_answers_doctor_specialty(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("김지훈 의사의 전공은?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "deterministic"
    assert result["prompt"] == "김지훈 의사의 전공은?"
    assert result["sql"] == "SELECT specialty FROM doctors WHERE name = ?"
    assert result["params"] == ["김지훈"]
    assert result["rows"] == [["내과"]]
    assert "내과" in result["answer"]




def test_driver_executes_named_sql_params(tmp_path):
    db_file = build_temp_db(tmp_path)
    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")

    rows = driver.execute_query(
        db_file,
        "SELECT specialty FROM doctors WHERE name = :name",
        {"name": "김지훈"},
    )

    assert rows == [["내과"]]

def test_prompt_driver_cli_outputs_json(tmp_path):
    db_file = build_temp_db(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER_SCRIPT),
            "ask",
            "김지훈 의사의 전공은?",
            "--db-file",
            str(db_file),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["planner"] == "deterministic"
    assert payload["rows"] == [["내과"]]
    assert "내과" in payload["answer"]


def test_eval_driver_runs_jsonl_cases(tmp_path):
    db_file = build_temp_db(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER_SCRIPT),
            "eval",
            "--cases",
            str(CASES_FILE),
            "--db-file",
            str(db_file),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["passed"] == 1
    assert payload["failed"] == 0
    assert payload["cases"][0]["id"] == "q001"


class FakeOpenAIHandler(BaseHTTPRequestHandler):
    requests: list[dict] = []

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        type(self).requests.append({"path": self.path, "payload": payload})

        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "sql": "SELECT specialty FROM doctors WHERE name = ?",
                                "params": ["김지훈"],
                                "answer_template": "김지훈 의사의 전공은 {value}입니다.",
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }
        body = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def test_llm_planner_uses_openai_compatible_ollama_request(tmp_path):
    db_file = build_temp_db(tmp_path)
    FakeOpenAIHandler.requests = []
    server = HTTPServer(("127.0.0.1", 0), FakeOpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
        result = driver.answer_prompt(
            "김지훈 의사의 전공은?",
            db_file,
            planner="llm",
            openai_base_url=f"http://127.0.0.1:{server.server_port}/v1",
            model="qwen3:8b",
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert result["ok"] is True
    assert result["planner"] == "llm"
    assert result["model"] == "qwen3:8b"
    assert result["rows"] == [["내과"]]
    assert FakeOpenAIHandler.requests[0]["path"] == "/v1/chat/completions"
    assert FakeOpenAIHandler.requests[0]["payload"]["model"] == "qwen3:8b"


def test_llm_planner_cli_accepts_openai_compatible_endpoint(tmp_path):
    db_file = build_temp_db(tmp_path)
    FakeOpenAIHandler.requests = []
    server = HTTPServer(("127.0.0.1", 0), FakeOpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(DRIVER_SCRIPT),
                "ask",
                "김지훈 의사의 전공은?",
                "--db-file",
                str(db_file),
                "--planner",
                "llm",
                "--openai-base-url",
                f"http://127.0.0.1:{server.server_port}/v1",
                "--model",
                "qwen3:8b",
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["planner"] == "llm"
    assert payload["model"] == "qwen3:8b"
    assert payload["rows"] == [["내과"]]

