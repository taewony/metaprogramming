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
RUNTIME_SRC = ROOT / "activegraph" / "text-to-sql-agent" / "src"
AGENT_DIR = ROOT / "activegraph" / "text-to-sql-agent" / "agent"
BUILD_SCRIPT = SCRIPTS / "build_hospital_db.py"
DRIVER_SCRIPT = SCRIPTS / "hospital_tdd_driver.py"
CASES_FILE = EVALS / "hospital_cases.jsonl"
SYSTEM_MODEL_V02 = AGENT_DIR / "system-model.v02.yaml"
SYSTEM_MODEL_V03 = AGENT_DIR / "system-model.v03.yaml"

if str(RUNTIME_SRC) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SRC))

import yaml

from activegraph.cli.hospital_logic import (
    RuleCatalog,
    RuleCatalogError,
    UnsafeSQLError,
    deterministic_plan,
    load_rule_catalog_from_system_model,
)


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

def test_rule_catalog_loads_from_system_model_v02():
    catalog = load_rule_catalog_from_system_model(SYSTEM_MODEL_V02)

    assert catalog.id == "hospital_text_to_sql_rules_v02"
    assert len(catalog.rules) == 8
    assert catalog.eval_ids() == ["q001", "q002", "q003", "q004", "q005", "q006", "q007", "q008", "q009", "q010"]

    plan = catalog.plan("의사 몇명 있니?")
    assert plan.rule_id == "doctor_count_q002_q003_q004"
    assert plan.sql == "SELECT COUNT(*) FROM doctors"
    assert plan.params == []
    assert plan.answer_template == "의사는 모두 {value}명입니다."



def test_rule_catalog_loads_from_system_model_v03_with_capture_binding():
    catalog = load_rule_catalog_from_system_model(SYSTEM_MODEL_V03)

    assert catalog.id == "hospital_text_to_sql_rules_v03"
    assert len(catalog.rules) == 7
    assert catalog.eval_ids() == ["q001", "q002", "q003", "q004", "q005", "q006", "q007", "q008", "q009", "q010", "q011", "q012"]

    for prompt, doctor_name, specialty in [
        ("김지훈 의사의 전공은?", "김지훈", "내과"),
        ("이수진 의사의 전공은?", "이수진", "소아과"),
    ]:
        plan = catalog.plan(prompt)
        assert plan.rule_id == "doctor_specialty_by_name_capture_q001_q009"
        assert plan.intent["filters"]["name"] == doctor_name
        assert plan.sql == "SELECT specialty FROM doctors WHERE name = ?"
        assert plan.params == [doctor_name]
        assert plan.answer_template == f"{doctor_name} 의사의 전공은 {{value}}입니다."
        assert specialty not in plan.answer_template

    plan = catalog.plan("이수진 의사 병원?")
    assert plan.rule_id == "doctor_hospital_by_name_capture_q005_q011"
    assert plan.intent["filters"]["name"] == "이수진"
    assert plan.sql == "SELECT hospital_name FROM doctors WHERE name = ?"
    assert plan.params == ["이수진"]
    assert plan.answer_template == "이수진 의사는 {value}에 있습니다."


def test_deterministic_plan_defaults_to_v03_capture_catalog():
    plan = deterministic_plan("이수진 의사의 전공은?")

    assert plan.rule_id == "doctor_specialty_by_name_capture_q001_q009"
    assert plan.params == ["이수진"]
    assert plan.intent["filters"]["name"] == "이수진"
def test_rule_catalog_rejects_duplicate_rule_ids():
    data = yaml.safe_load(SYSTEM_MODEL_V02.read_text(encoding="utf-8"))
    rules = data["planning_model"]["rule_catalog"]["rules"]
    duplicate = dict(rules[0])
    rules.append(duplicate)

    try:
        RuleCatalog.from_system_model(data)
    except RuleCatalogError as exc:
        assert "duplicate rule id" in str(exc)
    else:
        raise AssertionError("duplicate rule id should be rejected")


def test_rule_catalog_rejects_unsafe_sql():
    data = yaml.safe_load(SYSTEM_MODEL_V02.read_text(encoding="utf-8"))
    data["planning_model"]["rule_catalog"]["rules"][0]["sql"]["text"] = "DELETE FROM doctors"

    try:
        RuleCatalog.from_system_model(data)
    except UnsafeSQLError as exc:
        assert "Only SELECT SQL is allowed" in str(exc)
    else:
        raise AssertionError("unsafe SQL should be rejected")


def test_deterministic_plan_uses_system_model_rule_catalog():
    plan = deterministic_plan("의사 몇명 있니?")

    assert plan.rule_id == "doctor_count_q002_q003_q004"
    assert plan.sql == "SELECT COUNT(*) FROM doctors"
    assert plan.params == []

def test_prompt_driver_answers_doctor_specialty(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("김지훈 의사의 전공은?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "김지훈 의사의 전공은?"
    assert result["sql"] == "SELECT specialty FROM doctors WHERE name = ?"
    assert result["params"] == ["김지훈"]
    assert result["rows"] == [["내과"]]
    assert "내과" in result["answer"]




def test_behavior_driver_answers_doctor_name_list_q010(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("의사 명단", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "의사 명단"
    assert result["sql"] == "SELECT name FROM doctors ORDER BY doctor_id"
    assert result["params"] == []
    assert result["rows"] == [["김지훈"], ["이수진"], ["박준석"], ["최미영"], ["정태호"]]
    for name in ["김지훈", "이수진", "박준석", "최미영", "정태호"]:
        assert name in result["answer"]
def test_behavior_driver_answers_second_doctor_specialty_from_q009(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("이수진 의사의 전공은?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "이수진 의사의 전공은?"
    assert result["sql"] == "SELECT specialty FROM doctors WHERE name = ?"
    assert result["params"] == ["이수진"]
    assert result["rows"] == [["소아과"]]
    assert "소아과" in result["answer"]
def test_behavior_driver_answers_doctor_hospital_lookup(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("김지훈 의사 병원?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "김지훈 의사 병원?"
    assert result["sql"] == "SELECT hospital_name FROM doctors WHERE name = ?"
    assert result["params"] == ["김지훈"]
    assert result["rows"] == [["서울중앙병원"]]
    assert "서울중앙병원" in result["answer"]



def test_behavior_driver_records_missing_captured_doctor_q012(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("없는의사 의사의 전공은?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "없는의사 의사의 전공은?"
    assert result["sql"] is None
    assert result["params"] == []
    assert result["rows"] == []
    assert "없는의사" in result["answer"]
    assert "찾지 못했습니다" in result["answer"]

    graph_file = Path(result["artifacts"]["graph_file"])
    graph_payload = json.loads(graph_file.read_text(encoding="utf-8"))
    validations = [
        obj for obj in graph_payload["objects"]
        if obj["type"] == "entity_validation"
    ]
    assert len(validations) == 1
    assert validations[0]["data"]["status"] == "not_found"
    assert validations[0]["data"]["entity"] == "doctor.name"
    assert validations[0]["data"]["value"] == "없는의사"


def test_behavior_driver_answers_second_doctor_hospital_from_q011(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("이수진 의사 병원?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "이수진 의사 병원?"
    assert result["sql"] == "SELECT hospital_name FROM doctors WHERE name = ?"
    assert result["params"] == ["이수진"]
    assert result["rows"] == [["서울중앙병원"]]
    assert "서울중앙병원" in result["answer"]
def test_behavior_driver_answers_patient_insurance_lookup(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("홍길동 환자의 보험은?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "홍길동 환자의 보험은?"
    assert result["sql"] == "SELECT insurance_number FROM patients WHERE name = ?"
    assert result["params"] == ["홍길동"]
    assert result["rows"] == [["I12345"]]
    assert "I12345" in result["answer"]

def test_behavior_driver_answers_scheduled_appointment_count(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("예정된 예약은 몇 개야?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "예정된 예약은 몇 개야?"
    assert result["sql"] == "SELECT COUNT(*) FROM appointments WHERE status = ?"
    assert result["params"] == ["예정됨"]
    assert result["rows"] == [[2]]
    assert "2" in result["answer"]
    assert "개" in result["answer"]

def test_behavior_driver_answers_doctor_count_existential_question(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("의사 몇명 있니?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "의사 몇명 있니?"
    assert result["sql"] == "SELECT COUNT(*) FROM doctors"
    assert result["params"] == []
    assert result["rows"] == [[5]]
    assert "5" in result["answer"]
    assert "명" in result["answer"]

def test_behavior_driver_answers_doctor_available_slots(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("김지훈 의사의 가능한 시간은?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "김지훈 의사의 가능한 시간은?"
    assert result["sql"] == "SELECT a.available_date, a.available_time FROM availability a JOIN doctors d ON d.doctor_id = a.doctor_id WHERE d.name = ? AND a.status = ? ORDER BY a.available_date, a.available_time"
    assert result["params"] == ["김지훈", "가능"]
    assert result["rows"] == [
        ["2025-04-02", "09:00"],
        ["2025-04-02", "11:00"],
        ["2025-04-02", "14:00"],
        ["2025-04-03", "09:00"],
        ["2025-04-03", "10:00"],
    ]
    assert "2025-04-02 09:00" in result["answer"]
    assert "2025-04-03 10:00" in result["answer"]

def test_behavior_driver_answers_doctor_count_short_question(tmp_path):
    db_file = build_temp_db(tmp_path)

    driver = load_module(DRIVER_SCRIPT, "hospital_tdd_driver")
    result = driver.answer_prompt("의사는 모두 몇명?", db_file)

    assert result["ok"] is True
    assert result["planner"] == "behavior"
    assert result["prompt"] == "의사는 모두 몇명?"
    assert result["sql"] == "SELECT COUNT(*) FROM doctors"
    assert result["params"] == []
    assert result["rows"] == [[5]]
    assert "5" in result["answer"]
    assert "명" in result["answer"]


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
    assert payload["planner"] == "behavior"
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
    assert payload["passed"] == 12
    assert payload["failed"] == 0
    assert [case["id"] for case in payload["cases"]] == ["q001", "q002", "q003", "q004", "q005", "q006", "q007", "q008", "q009", "q010", "q011", "q012"]


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
















