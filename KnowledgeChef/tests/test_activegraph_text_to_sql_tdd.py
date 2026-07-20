from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "activegraph" / "text-to-sql-agent" / "scripts"
EVALS = ROOT / "activegraph" / "text-to-sql-agent" / "evals"
RUNTIME_SRC = ROOT / "activegraph" / "text-to-sql-agent" / "src"
AGENT_DIR = ROOT / "activegraph" / "text-to-sql-agent" / "agent"
BUILD_SCRIPT = SCRIPTS / "build_hospital_db.py"
DRIVER_SCRIPT = SCRIPTS / "hospital_tdd_driver.py"
AGENT_SCRIPT = ROOT / "activegraph" / "text-to-sql-agent" / "agent.py"
CASES_FILE = EVALS / "hospital_cases.jsonl"
HOSPITAL_CONSOLIDATED_CASES = EVALS / "hospital_consolidated_cases.jsonl"
TECHSHOP_CASES_FILE = EVALS / "techshop_cases.jsonl"
EVAL_MANIFEST = EVALS / "eval_manifest.yaml"
PROMPT_ROBUSTNESS_CANDIDATES = EVALS / "prompt_robustness_candidates.yaml"
SYSTEM_MODEL_V02 = AGENT_DIR / "system-model.v02.yaml"
SYSTEM_MODEL_V03 = AGENT_DIR / "system-model.v03.yaml"
SYSTEM_MODEL_HOSPITAL_V06 = AGENT_DIR / "system-model.hospital.v06.yaml"
SYSTEM_MODEL_HOSPITAL_V11 = AGENT_DIR / "system-model.hospital.v11.yaml"
SYSTEM_MODEL_TECHSHOP_V06 = AGENT_DIR / "system-model.techshop.v06.yaml"
SYSTEM_MODEL_TECHSHOP_V11 = AGENT_DIR / "system-model.techshop.v11.yaml"

def v09_workspace(name: str) -> Path:
    workspace = ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "v09" / f"{name}-{uuid.uuid4().hex}"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace

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



def test_pack_registry_resolves_db_and_okf_bundle_paths():
    from activegraph.cli.pack_config import list_packs, resolve_pack

    packs = {pack.id: pack for pack in list_packs()}
    assert set(packs) == {
        "hospital-db",
        "techshop-db",
        "hospital-db-medical-kb",
        "techshop-db-commerce-kb",
    }

    hospital = resolve_pack("hospital-db")
    assert hospital.db_file == ROOT / "activegraph" / "data" / "hospital.db"
    assert hospital.event_store == ROOT / "activegraph" / "data" / "text_to_sql_events.sqlite"
    assert hospital.capabilities == {"db": True, "schema": True, "kb": False}
    assert hospital.system_model == SYSTEM_MODEL_HOSPITAL_V11
    assert hospital.schema_root == ROOT / "activegraph" / "okf-wiki" / "hospital-medical"
    assert hospital.llm["provider"] == "ollama"
    assert hospital.llm["base_url"] == "http://localhost:11434/v1"
    assert hospital.llm["model"] == "qwen2.5:7b"

    techshop = resolve_pack("techshop-db")
    assert techshop.llm["base_url"] == "http://localhost:11434/v1"
    assert techshop.llm["model"] == "qwen2.5:7b"

    hybrid = resolve_pack("hospital-db-medical-kb")
    assert hybrid.db_file == ROOT / "activegraph" / "data" / "hospital.db"
    assert hybrid.system_model == SYSTEM_MODEL_HOSPITAL_V11
    assert hybrid.reference_model == AGENT_DIR / "system-model.v99.yaml"
    assert hybrid.kb_root == ROOT / "activegraph" / "okf-wiki" / "hospital-medical"
    assert hybrid.schema_root == ROOT / "activegraph" / "okf-wiki" / "hospital-medical"
    assert hybrid.kb["format"] == "okf"
    assert hybrid.kb["approval_required"] is True

def test_agent_repl_help_mentions_pack_and_activegraph_mode():
    completed = subprocess.run(
        [sys.executable, str(AGENT_SCRIPT)],
        input="help\nexit\n",
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "pack list" in completed.stdout
    assert "pack schema <pack-id>" in completed.stdout
    assert "pack validate [pack-id]" in completed.stdout
    assert "pack import <pack-id>" in completed.stdout
    assert "eval-run export <id>" in completed.stdout
    assert "mode activegraph" in completed.stdout
    assert "Switch to original ActiveGraph shell with: mode activegraph" in completed.stdout
def test_agent_pack_list_cli_shows_local_pack_registry():
    completed = subprocess.run(
        [sys.executable, str(AGENT_SCRIPT), "pack", "list"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "hospital-db" in completed.stdout
    assert "techshop-db" in completed.stdout
    assert "hospital-db-medical-kb" in completed.stdout
    assert "techshop-db-commerce-kb" in completed.stdout

def test_schema_context_loads_hospital_schema_from_okf_projection():
    from activegraph.cli.pack_config import resolve_pack
    from activegraph.cli.schema_context import load_schema_context_for_pack

    payload = load_schema_context_for_pack(resolve_pack("hospital-db"))

    assert payload["ok"] is True
    assert payload["schema_projection"]["id"] == "hospital_okf_schema_projection"
    assert {table["name"] for table in payload["tables"]} == {
        "appointments",
        "availability",
        "doctors",
        "insurance",
        "medical_records",
        "patients",
        "prescriptions",
        "procedure_coverage",
    }
    doctors = next(table for table in payload["tables"] if table["name"] == "doctors")
    assert {column["name"] for column in doctors["columns"]} >= {"doctor_id", "name", "specialty", "hospital_name"}
    assert payload["validation"]["ok"] is True
    assert any(obj["type"] == "db.table" and obj["id"] == "table:doctors" for obj in payload["graph_projection"]["objects"])


def test_schema_context_loads_techshop_schema_from_okf_projection():
    from activegraph.cli.pack_config import resolve_pack
    from activegraph.cli.schema_context import load_schema_context_for_pack

    payload = load_schema_context_for_pack(resolve_pack("techshop-db"))

    assert payload["ok"] is True
    assert payload["schema_projection"]["id"] == "techshop_okf_schema_projection"
    assert {table["name"] for table in payload["tables"]} == {"customers", "products", "orders", "order_items"}
    assert payload["validation"]["ok"] is True
    customers = next(table for table in payload["tables"] if table["name"] == "customers")
    assert {column["name"] for column in customers["columns"]} >= {"id", "email", "name", "grade"}


def test_agent_pack_schema_cli_projects_techshop_schema():
    completed = subprocess.run(
        [sys.executable, str(AGENT_SCRIPT), "pack", "schema", "techshop-db", "--json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["pack_id"] == "techshop-db"
    assert payload["system_model"] == str(SYSTEM_MODEL_TECHSHOP_V11)
    assert {table["name"] for table in payload["tables"]} == {"customers", "products", "orders", "order_items"}
    assert payload["validation"]["ok"] is True
def test_pack_validate_all_local_packs():
    from activegraph.cli.pack_config import validate_all_packs

    payload = validate_all_packs()

    assert payload["ok"] is True
    assert {pack["id"] for pack in payload["packs"]} == {
        "hospital-db",
        "techshop-db",
        "hospital-db-medical-kb",
        "techshop-db-commerce-kb",
    }
    for pack in payload["packs"]:
        assert all(check["ok"] for check in pack["checks"])


def test_agent_pack_validate_cli_reports_ok():
    completed = subprocess.run(
        [sys.executable, str(AGENT_SCRIPT), "pack", "validate", "hospital-db-medical-kb", "--json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["id"] == "hospital-db-medical-kb"
    assert any(check["name"] == "system_model_executable" and check["ok"] for check in payload["checks"])
    assert any(check["name"] == "okf_index" and check["ok"] for check in payload["checks"])

def test_text_to_sql_snapshot_cli_captures_world_model():
    completed = subprocess.run(
        [sys.executable, str(AGENT_SCRIPT), "--pack", "techshop-db", "text-to-sql", "snapshot", "--json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["snapshot_type"] == "activegraph.world_model.v01"
    assert payload["pack"]["id"] == "techshop-db"
    assert payload["system_model"]["path"] == str(SYSTEM_MODEL_TECHSHOP_V11)
    assert payload["system_model"]["schema_projection_id"] == "techshop_okf_schema_projection"
    assert payload["system_model"]["schema_version"] == "system-model.v11"
    assert payload["system_model"]["entity_validation_model_id"] == "techshop_entity_validators_v05"
    assert payload["system_model"]["behavior_contract_count"] >= 4
    assert payload["schema_context"]["table_names"] == ["customers", "products", "orders", "order_items"]
    assert payload["schema_context"]["graph_projection"]["object_count"] > 0
    assert payload["schema_context"]["graph_projection"]["relation_count"] > 0
    assert {behavior["name"] for behavior in payload["behaviors"]} >= {
        "parse_intent",
        "compile_sql",
        "execute_sql",
        "synthesize_answer",
    }
    assert payload["event_store"]["path"].endswith("techshop_text_to_sql_events.sqlite")
    assert {item["command"] for item in payload["activegraph_event_log_capabilities"]} == {
        "inspect",
        "replay",
        "fork",
        "diff",
        "export-trace",
    }

def test_v06_full_context_assembly_for_techshop_prompt():
    from activegraph.cli.full_context import assemble_full_context
    from activegraph.cli.pack_config import resolve_pack

    pack = resolve_pack("techshop-db")
    payload = assemble_full_context(pack, "VIP는 몇명", tail=3)

    assert payload["ok"] is True
    assert payload["context_type"] == "activegraph.full_context.v01"
    assert payload["pack"]["id"] == "techshop-db"
    assert payload["system_prompt"]["is_empty"] is False
    assert "selected agent pack" in payload["system_prompt"]["text"]
    assert payload["system_model"]["schema_version"] == "system-model.v11"
    assert payload["system_model"]["full_context_model"]["id"] == "text_to_sql_full_context_v06"
    assert "schema_context" in payload["system_model"]["full_context_model"]["components"]
    assert [table["name"] for table in payload["schema_context"]["tables"]] == ["customers", "products", "orders", "order_items"]
    assert payload["planned_intent"]["ok"] is True
    assert payload["planned_intent"]["rule_id"] == "vip_customer_count"
    assert payload["planned_intent"]["sql"] == "SELECT COUNT(*) FROM customers WHERE grade = ?"
    assert payload["world_state"]["db"]["exists"] is True
    assert payload["llm_contract"]["dependency_required_for_current_path"] is False


def test_text_to_sql_context_cli_outputs_full_context():
    completed = subprocess.run(
        [sys.executable, str(AGENT_SCRIPT), "--pack", "techshop-db", "text-to-sql", "context", "VIP는 몇명", "--json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["context_type"] == "activegraph.full_context.v01"
    assert payload["pack"]["id"] == "techshop-db"
    assert payload["planned_intent"]["rule_id"] == "vip_customer_count"
    assert payload["schema_context"]["projection_id"] == "techshop_okf_schema_projection"
    assert payload["system_model"]["full_context_model"]["id"] == "text_to_sql_full_context_v06"
def test_text_to_sql_cli_uses_pack_selected_system_model(tmp_path):
    event_store = tmp_path / "pack-events.sqlite"

    completed = subprocess.run(
        [
            sys.executable,
            str(AGENT_SCRIPT),
            "--pack",
            "hospital-db-medical-kb",
            "text-to-sql",
            "ask",
            "의사는 모두 몇명이야?",
            "--event-store",
            str(event_store),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["system_model"] == str(SYSTEM_MODEL_HOSPITAL_V11)
    assert payload["event_store"] == str(event_store)
    assert payload["answer"] == "의사는 모두 5명입니다."

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


def test_v05_system_model_declares_behavior_contracts_and_entity_validators():
    catalog = load_rule_catalog_from_system_model(SYSTEM_MODEL_HOSPITAL_V06)

    assert catalog.id == "hospital_text_to_sql_rules_v03"
    assert catalog.entity_validators["doctor.name"].adapter == "sqlite_exists"
    assert catalog.entity_validators["doctor.name"].table == "doctors"
    assert catalog.entity_validators["doctor.name"].column == "name"

    parse_contract = catalog.behavior_spec("parse_intent")
    assert parse_contract is not None
    assert parse_contract["on"] == ["question.submitted"]
    assert parse_contract["creates"] == ["question", "intent", "entity_validation", "answer"]

    execute_contract = catalog.behavior_spec("execute_sql")
    assert execute_contract is not None
    assert execute_contract["on"] == ["sql.generated"]
    assert execute_contract["creates"] == ["query_result"]


def test_v05_entity_validation_uses_system_model_sql_adapter(tmp_path):
    from activegraph.cli.text_to_sql import run_text_to_sql

    db_file = build_temp_db(tmp_path)
    result = run_text_to_sql(
        "없는의사 의사의 전공은?",
        db_file,
        tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
        event_store=None,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
    )

    assert result["ok"] is True
    assert result["sql"] is None
    assert "없는의사" in result["answer"]

    graph_payload = json.loads(Path(result["artifacts"]["graph_file"]).read_text(encoding="utf-8"))
    validation = next(obj for obj in graph_payload["objects"] if obj["type"] == "entity_validation")
    assert validation["data"]["entity"] == "doctor.name"
    assert validation["data"]["status"] == "not_found"
    assert validation["data"]["source"] == "system_model.entity_validation_model"


def test_v05_techshop_vip_customer_list_rule_answers_event_log_repair_prompt():
    from activegraph.cli.text_to_sql import run_text_to_sql

    result = run_text_to_sql(
        "VIP는 누구?",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
        event_store=None,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
    )

    assert result["ok"] is True
    assert result["sql"] == "SELECT name FROM customers WHERE grade = ? ORDER BY id"
    assert result["params"] == ["VIP"]
    assert result["rows"] == [["정민호"], ["오세훈"], ["강태영"], ["문창호"], ["황미소"]]
    assert result["answer"] == "VIP 고객은 정민호, 오세훈, 강태영, 문창호, 황미소입니다."


def test_v05_techshop_vip_count_rule_accepts_short_prompt():
    from activegraph.cli.text_to_sql import run_text_to_sql

    result = run_text_to_sql(
        "VIP는 몇명",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
        event_store=None,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
    )

    assert result["ok"] is True
    assert result["sql"] == "SELECT COUNT(*) FROM customers WHERE grade = ?"
    assert result["params"] == ["VIP"]
    assert result["rows"] == [[5]]
    assert result["answer"] == "VIP 고객은 총 5명입니다."


def test_v06_techshop_vip_customer_total_revenue_rule():
    from activegraph.cli.text_to_sql import run_text_to_sql

    result = run_text_to_sql(
        "VIP 고객 총매출액",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
        event_store=None,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
    )

    assert result["ok"] is True
    assert result["sql"] == "SELECT CAST(SUM(o.total_amount) AS INTEGER) FROM orders o JOIN customers c ON c.id = o.customer_id WHERE c.grade = ? AND o.status = ?"
    assert result["params"] == ["VIP", "confirmed"]
    assert result["rows"] == [[6486000]]
    assert result["answer"] == "VIP 고객 총매출액은 6486000원입니다."




def test_v06_techshop_vip_revenue_accepts_common_sales_typo_with_llm_path():
    from activegraph.cli.pack_config import resolve_pack
    from activegraph.cli.text_to_sql import run_text_to_sql

    result = run_text_to_sql(
        "VIP 고객 총 맥출액",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
        event_store=None,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
        pack=resolve_pack("techshop-db"),
        llm_config={
            "enabled": True,
            "provider": "fake",
            "model": "fake-composer",
            "mode": "answer_composer",
            "fallback": "deterministic_answer",
            "fake_answer": "VIP 고객의 확정 주문 기준 총매출액은 6,486,000원입니다.",
        },
    )

    assert result["ok"] is True
    assert result["sql"] == "SELECT CAST(SUM(o.total_amount) AS INTEGER) FROM orders o JOIN customers c ON c.id = o.customer_id WHERE c.grade = ? AND o.status = ?"
    assert result["params"] == ["VIP", "confirmed"]
    assert result["rows"] == [[6486000]]
    assert result["answer_source"] == "llm"
    assert result["answer"] == "VIP 고객의 확정 주문 기준 총매출액은 6,486,000원입니다."


def test_v08_prompt_robustness_candidate_catalog_covers_hospital_and_techshop():
    data = yaml.safe_load(PROMPT_ROBUSTNESS_CANDIDATES.read_text(encoding="utf-8"))

    assert data["schema_version"] == "activegraph.prompt_robustness_candidates.v01"
    assert set(data["packs"]) == {"hospital-db", "techshop-db"}
    assert "supported_now" in data["packs"]["hospital-db"]
    assert "deferred" in data["packs"]["hospital-db"]
    assert "supported_now" in data["packs"]["techshop-db"]
    assert "deferred" in data["packs"]["techshop-db"]
    assert "VIP 고객 총 맥출액" in data["packs"]["techshop-db"]["supported_now"]["vip_revenue_total"]["prompts"]
    assert "그 의사는 어느 병원이야?" in data["packs"]["hospital-db"]["deferred"]["v10_multi_turn"]


def test_v08_hospital_prompt_robustness_variants():
    from activegraph.cli.text_to_sql import run_text_to_sql

    cases = [
        ("전체 의사 수", "SELECT COUNT(*) FROM doctors", [], [[5]], "5"),
        ("김지훈 전문분야는?", "SELECT specialty FROM doctors WHERE name = ?", ["김지훈"], [["내과"]], "내과"),
        ("이수진 진료과는 뭐야?", "SELECT specialty FROM doctors WHERE name = ?", ["이수진"], [["소아과"]], "소아과"),
        ("김지훈 어디 근무해?", "SELECT hospital_name FROM doctors WHERE name = ?", ["김지훈"], [["서울중앙병원"]], "서울중앙병원"),
        ("의료진 목록", "SELECT name FROM doctors ORDER BY doctor_id", [], [["김지훈"], ["이수진"], ["박준석"], ["최미영"], ["정태호"]], "김지훈"),
        ("김지훈 예약 가능 시간", "SELECT a.available_date, a.available_time FROM availability a JOIN doctors d ON d.doctor_id = a.doctor_id WHERE d.name = ? AND a.status = ? ORDER BY a.available_date, a.available_time", ["김지훈", "가능"], [["2025-04-02", "09:00"], ["2025-04-02", "11:00"], ["2025-04-02", "14:00"], ["2025-04-03", "09:00"], ["2025-04-03", "10:00"]], "2025-04-02 09:00"),
    ]

    for prompt, expected_sql, expected_params, expected_rows, expected_answer in cases:
        result = run_text_to_sql(
            prompt,
            ROOT / "activegraph" / "data" / "hospital.db",
            tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
            event_store=None,
            write_artifacts=False,
            system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
        )
        assert result["ok"] is True, result
        assert result["sql"] == expected_sql
        assert result["params"] == expected_params
        assert result["rows"] == expected_rows
        assert expected_answer in result["answer"]


def test_v08_techshop_prompt_robustness_variants():
    from activegraph.cli.text_to_sql import run_text_to_sql

    cases = [
        ("VIP 매출 합계", "SELECT CAST(SUM(o.total_amount) AS INTEGER) FROM orders o JOIN customers c ON c.id = o.customer_id WHERE c.grade = ? AND o.status = ?", ["VIP", "confirmed"], [[6486000]], "6486000"),
        ("VIP 판매액", "SELECT CAST(SUM(o.total_amount) AS INTEGER) FROM orders o JOIN customers c ON c.id = o.customer_id WHERE c.grade = ? AND o.status = ?", ["VIP", "confirmed"], [[6486000]], "6486000"),
        ("VIP 고객 이름", "SELECT name FROM customers WHERE grade = ? ORDER BY id", ["VIP"], [["정민호"], ["오세훈"], ["강태영"], ["문창호"], ["황미소"]], "정민호"),
        ("회원 수", "SELECT COUNT(*) FROM customers", [], [[20]], "20"),
        ("상품 몇 개야?", "SELECT COUNT(*) FROM products", [], [[15]], "15"),
    ]

    for prompt, expected_sql, expected_params, expected_rows, expected_answer in cases:
        result = run_text_to_sql(
            prompt,
            ROOT / "activegraph" / "data" / "techshop.db",
            tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
            event_store=None,
            write_artifacts=False,
            system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
        )
        assert result["ok"] is True, result
        assert result["sql"] == expected_sql
        assert result["params"] == expected_params
        assert result["rows"] == expected_rows
        assert expected_answer in result["answer"]

def test_v06_answer_composer_normalizes_direct_timeout_error():
    from activegraph.cli.llm_answer import LLMAnswerComposerError, call_openai_compatible_chat

    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        try:
            call_openai_compatible_chat(
                [{"role": "user", "content": "x"}],
                base_url="http://localhost:11434/v1",
                model="qwen2.5:7b",
                timeout=0.1,
            )
        except LLMAnswerComposerError as exc:
            assert "timed out" in str(exc)
        else:
            raise AssertionError("TimeoutError should be normalized to LLMAnswerComposerError")

def test_v06_answer_composer_can_use_fake_llm_and_records_graph():
    from activegraph.cli.pack_config import resolve_pack
    from activegraph.cli.text_to_sql import run_text_to_sql

    pack = resolve_pack("techshop-db")
    result = run_text_to_sql(
        "VIP 고객 총매출액",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
        event_store=None,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
        pack=pack,
        llm_config={
            "enabled": True,
            "provider": "fake",
            "model": "fake-composer",
            "mode": "answer_composer",
            "fallback": "deterministic_answer",
            "fake_answer": "VIP 고객의 확정 주문 기준 총매출액은 6,486,000원입니다.",
        },
    )

    assert result["ok"] is True
    assert result["answer"] == "VIP 고객의 확정 주문 기준 총매출액은 6,486,000원입니다."
    assert result["answer_source"] == "llm"
    assert result["deterministic_answer"] == "VIP 고객 총매출액은 6486000원입니다."
    assert result["llm"]["enabled"] is True
    assert result["llm"]["provider"] == "fake"
    assert result["llm"]["status"] == "completed"

    trace_events = [
        json.loads(line)["type"]
        for line in Path(result["artifacts"]["trace_file"]).read_text(encoding="utf-8").splitlines()
    ]
    assert "llm.invocation_requested" in trace_events
    assert "llm.response_received" in trace_events
    graph_payload = json.loads(Path(result["artifacts"]["graph_file"]).read_text(encoding="utf-8"))
    assert any(obj["type"] == "llm_invocation" for obj in graph_payload["objects"])
    assert any(obj["type"] == "decision_rationale" for obj in graph_payload["objects"])


class FakeOllamaAnswerHandler(BaseHTTPRequestHandler):
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
                                "answer": "VIP 고객의 확정 주문 총매출액은 6,486,000원입니다.",
                                "rationale": "SQL 결과의 첫 번째 값을 쉼표 표기로 다듬었습니다.",
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


def test_v06_answer_composer_uses_ollama_openai_compatible_endpoint():
    from activegraph.cli.pack_config import resolve_pack
    from activegraph.cli.text_to_sql import run_text_to_sql

    FakeOllamaAnswerHandler.requests = []
    server = HTTPServer(("127.0.0.1", 0), FakeOllamaAnswerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        result = run_text_to_sql(
            "VIP 고객 총매출액",
            ROOT / "activegraph" / "data" / "techshop.db",
            tests_dir=ROOT / "activegraph" / "text-to-sql-agent" / ".tests" / "runs",
            event_store=None,
            write_artifacts=False,
            system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
            pack=resolve_pack("techshop-db"),
            llm_config={
                "enabled": True,
                "provider": "ollama",
                "model": "qwen3:8b",
                "mode": "answer_composer",
                "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                "timeout_seconds": 5,
                "fallback": "deterministic_answer",
            },
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert result["ok"] is True
    assert result["answer_source"] == "llm"
    assert result["answer"] == "VIP 고객의 확정 주문 총매출액은 6,486,000원입니다."
    assert FakeOllamaAnswerHandler.requests[0]["path"] == "/v1/chat/completions"
    request_payload = FakeOllamaAnswerHandler.requests[0]["payload"]
    assert request_payload["model"] == "qwen3:8b"
    assert request_payload["response_format"] == {"type": "json_object"}
    assert "VIP 고객 총매출액은 6486000원입니다." in request_payload["messages"][1]["content"]
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






































def test_v09_adaptation_analyzer_classifies_unsupported_prompt_and_writes_artifacts():
    from activegraph.cli.adaptation import analyze_text_to_sql_adaptation
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("analyze")
    event_store = ROOT / "activegraph" / "data" / "techshop_text_to_sql_events.sqlite"
    result = run_text_to_sql(
        "VIP 고객 평균 주문액",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
    )
    assert result["ok"] is False

    analysis = analyze_text_to_sql_adaptation(
        event_store,
        run_selector=result["run_id"],
        output_dir=workspace / "adaptations",
        pack_id="techshop-db",
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
    )

    assert analysis["ok"] is True
    assert analysis["analysis_type"] == "activegraph.adaptation_analysis.v01"
    assert analysis["source_run_id"] == result["run_id"]
    assert analysis["summary"]["unsupported_prompts"] == 1
    assert analysis["classifications"][0]["kind"] == "unsupported_prompt"
    assert analysis["classifications"][0]["prompt"] == "VIP 고객 평균 주문액"
    assert analysis["proposals"][0]["status"] == "proposed"
    assert analysis["proposals"][0]["target"]["kind"] == "system_model.rule_catalog"
    assert analysis["proposals"][0]["draft_eval_case"]["prompt"] == "VIP 고객 평균 주문액"
    assert "add eval case" in analysis["proposals"][0]["validation_plan"][0]

    artifacts = analysis["artifacts"]
    assert Path(artifacts["analysis_file"]).exists()
    assert Path(artifacts["proposal_files"][0]).exists()
    assert Path(artifacts["event_file"]).exists()
    assert Path(artifacts["graph_file"]).exists()


def test_v09_adaptation_accept_generates_eval_case_and_patch_hint():
    from activegraph.cli.adaptation import accept_adaptation_proposal, analyze_text_to_sql_adaptation
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("accept")
    event_store = ROOT / "activegraph" / "data" / "text_to_sql_events.sqlite"
    result = run_text_to_sql(
        "김지훈 의사 이메일 알려줘",
        ROOT / "activegraph" / "data" / "hospital.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
    )
    assert result["ok"] is False
    analysis = analyze_text_to_sql_adaptation(
        event_store,
        run_selector=result["run_id"],
        output_dir=workspace / "adaptations",
        pack_id="hospital-db",
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
    )

    accepted = accept_adaptation_proposal(
        analysis["artifacts"]["proposal_files"][0],
        output_dir=workspace / "accepted",
    )

    assert accepted["ok"] is True
    assert accepted["status"] == "accepted"
    eval_case_file = Path(accepted["generated_artifacts"]["eval_case_file"])
    patch_hint_file = Path(accepted["generated_artifacts"]["system_model_patch_hint_file"])
    assert eval_case_file.exists()
    assert patch_hint_file.exists()
    eval_case = json.loads(eval_case_file.read_text(encoding="utf-8").splitlines()[0])
    assert eval_case["prompt"] == "김지훈 의사 이메일 알려줘"
    assert eval_case["source"] == "v09_adaptation_loop"


def test_v09_text_to_sql_adapt_cli_outputs_proposals():
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("cli")
    event_store = ROOT / "activegraph" / "data" / "techshop_text_to_sql_events.sqlite"
    result = run_text_to_sql(
        "VIP 평균 주문 단가",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
    )
    assert result["ok"] is False

    completed = subprocess.run(
        [
            sys.executable,
            str(AGENT_SCRIPT),
            "--pack",
            "techshop-db",
            "text-to-sql",
            "adapt",
            result["run_id"],
            "--event-store",
            str(event_store),
            "--output-dir",
            str(workspace / "adapt-cli"),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["summary"]["proposal_count"] == 1
    assert payload["proposals"][0]["classification"] == "unsupported_prompt"
    assert payload["proposals"][0]["draft_eval_case"]["prompt"] == "VIP 평균 주문 단가"


def test_v10_session_memory_resolves_hospital_doctor_anaphora():
    from activegraph.cli.session_memory import load_session_state
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("v10-hospital")
    session_id = "hospital-session-" + uuid.uuid4().hex
    event_store = ROOT / "activegraph" / "data" / "text_to_sql_events.sqlite"

    first = run_text_to_sql(
        "김지훈 전문분야는?",
        ROOT / "activegraph" / "data" / "hospital.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
        session_id=session_id,
        session_store_dir=workspace / "sessions",
        pack_id="hospital-db",
    )
    assert first["ok"] is True
    assert first["session"]["turn_count"] == 1

    second = run_text_to_sql(
        "그 의사는 어느 병원이야?",
        ROOT / "activegraph" / "data" / "hospital.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
        session_id=session_id,
        session_store_dir=workspace / "sessions",
        pack_id="hospital-db",
    )

    assert second["ok"] is True
    assert second["resolved_prompt"] == "김지훈 의사는 어느 병원이야?"
    assert second["answer"] == "김지훈 의사는 서울중앙병원에 있습니다."
    assert second["session"]["resolution"]["strategy"] == "doctor_anaphora"

    graph_payload = json.loads(Path(second["artifacts"]["graph_file"]).read_text(encoding="utf-8"))
    assert any(obj["type"] == "session" for obj in graph_payload["objects"])
    assert any(obj["type"] == "session_resolution" for obj in graph_payload["objects"])
    assert any(rel["type"] == "belongs_to_session" for rel in graph_payload["relations"])

    state = load_session_state(session_id, pack_id="hospital-db", session_store_dir=workspace / "sessions")
    assert state["turn_count"] == 2
    assert state["last_entities"]["doctor.name"] == "김지훈"
    assert state["memory_boundaries"]["session_memory"]["kind"] == "local_json_graph"


def test_v10_session_memory_resolves_techshop_vip_ellipsis():
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("v10-techshop")
    session_id = "techshop-session-" + uuid.uuid4().hex
    event_store = ROOT / "activegraph" / "data" / "techshop_text_to_sql_events.sqlite"

    first = run_text_to_sql(
        "VIP는 누구?",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
        session_id=session_id,
        session_store_dir=workspace / "sessions",
        pack_id="techshop-db",
    )
    assert first["ok"] is True
    assert first["session"]["last_entities"]["customer.grade"] == "VIP"

    second = run_text_to_sql(
        "몇 명이야?",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V06,
        session_id=session_id,
        session_store_dir=workspace / "sessions",
        pack_id="techshop-db",
    )

    assert second["ok"] is True
    assert second["resolved_prompt"] == "VIP 몇 명이야?"
    assert second["sql"] == "SELECT COUNT(*) FROM customers WHERE grade = ?"
    assert second["params"] == ["VIP"]
    assert second["answer"] == "VIP 고객은 총 5명입니다."
    assert second["session"]["resolution"]["strategy"] == "vip_ellipsis"


def test_v10_full_context_includes_session_memory_boundaries():
    from activegraph.cli.full_context import assemble_full_context
    from activegraph.cli.pack_config import resolve_pack
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("v10-context")
    session_id = "context-session-" + uuid.uuid4().hex
    pack = resolve_pack("hospital-db")
    run_text_to_sql(
        "김지훈 전문분야는?",
        ROOT / "activegraph" / "data" / "hospital.db",
        tests_dir=workspace / "runs",
        event_store=ROOT / "activegraph" / "data" / "text_to_sql_events.sqlite",
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
        session_id=session_id,
        session_store_dir=workspace / "sessions",
        pack_id="hospital-db",
    )

    payload = assemble_full_context(
        pack,
        "그 의사는 어느 병원이야?",
        session_id=session_id,
        session_store_dir=workspace / "sessions",
    )

    assert payload["session_context"]["enabled"] is True
    assert payload["session_context"]["resolved_prompt"] == "김지훈 의사는 어느 병원이야?"
    assert payload["session_context"]["resolution"]["strategy"] == "doctor_anaphora"
    assert payload["memory_boundaries"]["current_run"]["kind"] == "ephemeral_graph"
    assert payload["memory_boundaries"]["session_memory"]["kind"] == "local_json_graph"
    assert payload["memory_boundaries"]["pack_kb"]["kind"] == "okf_bundle_or_disabled"
    assert payload["memory_boundaries"]["long_term_adaptation"]["kind"] == "adaptation_artifacts"

def test_v10_agent_repl_uses_default_session_for_text_to_sql_shortcuts():
    completed = subprocess.run(
        [sys.executable, str(AGENT_SCRIPT)],
        input='pack use hospital-db\nask "김지훈 전문분야는?"\nask "그 의사는 어느 병원이야?"\ninspect 0\npack use techshop-db\nexit\n',
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "answer: 김지훈 의사의 전공은 내과입니다." in completed.stdout
    assert "answer: 김지훈 의사는 서울중앙병원에 있습니다." in completed.stdout
    assert "의사 '그'를 찾지 못했습니다." not in completed.stdout
    assert "before ask:" in completed.stdout
    assert "after ask:" in completed.stdout
    assert "session_resolution" in completed.stdout
    assert "belongs_to_session" in completed.stdout

def test_v10_inspect_shows_session_graph_before_current_ask():
    from activegraph.cli.text_to_sql import inspect_text_to_sql_run, run_text_to_sql

    workspace = v09_workspace("v10-inspect-before")
    session_id = "inspect-before-" + uuid.uuid4().hex
    event_store = ROOT / "activegraph" / "data" / "text_to_sql_events.sqlite"

    first = run_text_to_sql(
        "김지훈 전문분야는?",
        ROOT / "activegraph" / "data" / "hospital.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
        session_id=session_id,
        session_store_dir=workspace / "sessions",
        pack_id="hospital-db",
    )
    assert first["ok"] is True
    second = run_text_to_sql(
        "그 의사는 어느 병원이야?",
        ROOT / "activegraph" / "data" / "hospital.db",
        tests_dir=workspace / "runs",
        event_store=event_store,
        write_artifacts=False,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
        session_id=session_id,
        session_store_dir=workspace / "sessions",
        pack_id="hospital-db",
    )
    assert second["ok"] is True

    inspected = inspect_text_to_sql_run(
        second["run_id"],
        event_store=event_store,
        db_file=ROOT / "activegraph" / "data" / "hospital.db",
        system_model_file=SYSTEM_MODEL_HOSPITAL_V06,
        pack_id="hospital-db",
        session_store_dir=workspace / "sessions",
    )

    before = inspected["before"]
    assert before["graph_scope"] == "session_memory_before_run"
    assert before["session_id"] == session_id
    assert any(obj["type"] == "session" for obj in before["objects"])
    assert any(obj["type"] == "session_turn" and obj["data"]["run_id"] == first["run_id"] for obj in before["objects"])
    assert not any(obj["type"] == "session_turn" and obj["data"]["run_id"] == second["run_id"] for obj in before["objects"])
    assert any(rel["type"] == "belongs_to_session" for rel in before["relations"])

def test_v10_inspect_human_output_aligns_before_and_after_graph_format(capsys):
    from activegraph.cli.text_to_sql import echo_inspect_run

    payload = {
        "run_id": "run-2",
        "store_url": "sqlite:///example.sqlite",
        "before": {
            "graph_scope": "session_memory_before_run",
            "session_id": "session-a",
            "objects": [
                {"id": "session:session-a", "type": "session", "data": {"session_id": "session-a"}},
            ],
            "relations": [
                {"source": "turn:1", "type": "belongs_to_session", "target": "session:session-a"},
            ],
            "behaviors": [],
        },
        "after": {
            "graph_scope": "run_graph_after_replay",
            "session_id": "session-a",
            "event_count": 2,
            "object_count": 1,
            "relation_count": 1,
            "objects": [
                {"id": "question#1", "type": "question", "data": {"text": "그 의사는 어느 병원?"}},
            ],
            "relations": [
                {"source": "question#1", "type": "belongs_to_session", "target": "session#2"},
            ],
        },
        "failures": [],
        "recent_events": [],
    }

    echo_inspect_run(payload, as_json=False)
    out = capsys.readouterr().out
    before_block = out.split("before ask:", 1)[1].split("  behaviors:", 1)[0]
    after_block = out.split("after ask:", 1)[1].split("failures:", 1)[0]

    for block in (before_block, after_block):
        assert "  graph_scope:" in block
        assert "  session_id: session-a" in block
        assert "  events=" in block
        assert " objects=1 relations=1" in block
        assert "  objects:" in block
        assert "  relations:" in block

def test_v11_pack_registry_uses_v11_system_models():
    from activegraph.cli.pack_config import resolve_pack

    assert resolve_pack("hospital-db").system_model == SYSTEM_MODEL_HOSPITAL_V11
    assert resolve_pack("techshop-db").system_model == SYSTEM_MODEL_TECHSHOP_V11


def test_v11_resolved_prompt_records_planner_resolution_graph():
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("v11-resolved-planner")
    result = run_text_to_sql(
        "VIP 고객 총매출액",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=workspace / "runs",
        event_store=ROOT / "activegraph" / "data" / "techshop_text_to_sql_events.sqlite",
        system_model_file=SYSTEM_MODEL_TECHSHOP_V11,
        write_artifacts=True,
        pack_id="techshop-db",
    )

    assert result["ok"] is True
    assert result["planner_resolution"]["status"] == "resolved"
    assert result["planner_resolution"]["confidence"] >= 0.8
    assert "implicit_constraint" in result["planner_resolution"]["imperfection_types"]
    assert result["planner_resolution"]["llm_used"] is False
    assert result["sql"] == "SELECT CAST(SUM(o.total_amount) AS INTEGER) FROM orders o JOIN customers c ON c.id = o.customer_id WHERE c.grade = ? AND o.status = ?"

    graph_payload = json.loads(Path(result["artifacts"]["graph_file"]).read_text(encoding="utf-8"))
    planner_objects = [obj for obj in graph_payload["objects"] if obj["type"] == "planner_resolution"]
    assert len(planner_objects) == 1
    assert planner_objects[0]["data"]["status"] == "resolved"
    assert any(rel["type"] == "derived_from" and rel["source"] == planner_objects[0]["id"] for rel in graph_payload["relations"])
    assert any(obj["type"] == "decision_rationale" for obj in graph_payload["objects"])


def test_v11_ambiguous_prompt_requests_clarification_without_sql():
    from activegraph.cli.text_to_sql import run_text_to_sql

    workspace = v09_workspace("v11-ambiguous-planner")
    result = run_text_to_sql(
        "가장 많이 팔린 거",
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=workspace / "runs",
        event_store=ROOT / "activegraph" / "data" / "techshop_text_to_sql_events.sqlite",
        system_model_file=SYSTEM_MODEL_TECHSHOP_V11,
        write_artifacts=True,
        pack_id="techshop-db",
    )

    assert result["ok"] is True
    assert result["sql"] is None
    assert result["rows"] == []
    assert result["answer_source"] == "clarification"
    assert "무엇을 기준" in result["answer"]
    assert result["planner_resolution"]["status"] == "clarification_required"
    assert "ambiguity" in result["planner_resolution"]["imperfection_types"]

    graph_payload = json.loads(Path(result["artifacts"]["graph_file"]).read_text(encoding="utf-8"))
    assert any(obj["type"] == "clarification_request" for obj in graph_payload["objects"])
    assert not any(obj["type"] == "sql_query" for obj in graph_payload["objects"])

def test_consolidated_eval_manifest_covers_two_db_packs():
    manifest = yaml.safe_load(EVAL_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "activegraph.text_to_sql_evals.v01"
    assert set(manifest["packs"]) == {"hospital-db", "techshop-db"}
    assert manifest["packs"]["hospital-db"]["runnable"]["consolidated"] == "hospital_consolidated_cases.jsonl"
    assert manifest["packs"]["techshop-db"]["runnable"]["consolidated"] == "techshop_cases.jsonl"
    assert manifest["packs"]["hospital-db"]["coverage"]["consolidated_cases"] == 29
    assert manifest["packs"]["techshop-db"]["coverage"]["consolidated_cases"] == 23
    assert "그 의사는 어느 병원이야?" in manifest["packs"]["hospital-db"]["deferred"]["session_required"]


def test_consolidated_eval_files_are_runnable_for_two_dbs():
    from activegraph.cli.text_to_sql import load_cases, run_eval

    hospital_cases = load_cases(HOSPITAL_CONSOLIDATED_CASES)
    techshop_cases = load_cases(TECHSHOP_CASES_FILE)
    assert len(hospital_cases) == 29
    assert len(techshop_cases) == 23
    assert {case["id"] for case in hospital_cases} >= {"q001", "q012", "hospital_v08_017"}
    assert {case["id"] for case in techshop_cases} >= {"techshop_q001", "techshop_q008", "techshop_v11_004"}

    hospital = run_eval(
        HOSPITAL_CONSOLIDATED_CASES,
        ROOT / "activegraph" / "data" / "hospital.db",
        tests_dir=v09_workspace("eval-hospital-consolidated") / "runs",
        event_store=None,
        system_model_file=SYSTEM_MODEL_HOSPITAL_V11,
    )
    techshop = run_eval(
        TECHSHOP_CASES_FILE,
        ROOT / "activegraph" / "data" / "techshop.db",
        tests_dir=v09_workspace("eval-techshop-consolidated") / "runs",
        event_store=None,
        system_model_file=SYSTEM_MODEL_TECHSHOP_V11,
    )

    assert hospital["ok"] is True
    assert hospital["passed"] == 29
    assert techshop["ok"] is True
    assert techshop["passed"] == 23


def test_text_to_sql_eval_defaults_to_selected_pack_cases():
    completed = subprocess.run(
        [
            sys.executable,
            str(AGENT_SCRIPT),
            "--pack",
            "techshop-db",
            "text-to-sql",
            "eval",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["cases_file"].endswith("techshop_cases.jsonl")
    assert payload["system_model"] == str(SYSTEM_MODEL_TECHSHOP_V11)
    assert payload["passed"] == 23
    assert payload["failed"] == 0


def _write_thirdparty_fixture(tmp_path: Path) -> dict[str, Path]:
    import sqlite3

    root = tmp_path / "thirdparty"
    db_dir = root / "db"
    okf_dir = root / "okf-schema"
    eval_dir = root / "evals"
    tables_dir = okf_dir / "tables"
    db_dir.mkdir(parents=True)
    tables_dir.mkdir(parents=True)
    eval_dir.mkdir(parents=True)

    db_file = db_dir / "mini_crm.db"
    with sqlite3.connect(db_file) as conn:
        conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, grade TEXT NOT NULL)")
        conn.executemany(
            "INSERT INTO customers (id, name, grade) VALUES (?, ?, ?)",
            [(1, "Alice", "VIP"), (2, "Bob", "BASIC"), (3, "Choi", "VIP")],
        )

    (okf_dir / "index.md").write_text(
        "---\ntitle: Mini CRM Schema\ntype: knowledge-bundle\n---\n\n# Mini CRM Schema\n",
        encoding="utf-8",
    )
    (tables_dir / "customers.md").write_text(
        "---\n"
        "title: Customers\n"
        "type: table\n"
        "table: customers\n"
        "description: Customer records.\n"
        "columns:\n"
        "  - name: id\n"
        "    type: INTEGER\n"
        "    primary_key: true\n"
        "  - name: name\n"
        "    type: TEXT\n"
        "  - name: grade\n"
        "    type: TEXT\n"
        "---\n\n# Customers\n",
        encoding="utf-8",
    )
    cases_file = eval_dir / "cases.jsonl"
    cases_file.write_text(
        json.dumps(
            {
                "id": "mini_q001",
                "prompt": "고객은 몇 명이야?",
                "expected_sql": "SELECT COUNT(*) FROM customers",
                "expected_params": [],
                "expected_rows": [[3]],
                "expected_answer_contains": ["3"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"root": root, "db": db_file, "okf": okf_dir, "evals": cases_file}


def test_v115_import_pack_registers_thirdparty_db_and_generates_system_model(tmp_path):
    from activegraph.cli.pack_config import import_thirdparty_pack, resolve_pack, validate_pack
    from activegraph.cli.schema_context import load_schema_context_for_pack

    fixture = _write_thirdparty_fixture(tmp_path)
    config_file = tmp_path / "packs.yaml"
    manifest_file = tmp_path / "eval_manifest.yaml"
    config_file.write_text(
        yaml.safe_dump({"schema_version": "activegraph.packs.v01", "default_pack": "mini-crm", "packs": {}}, sort_keys=False),
        encoding="utf-8",
    )
    manifest_file.write_text(
        yaml.safe_dump({"schema_version": "activegraph.text_to_sql_evals.v01", "packs": {}}, sort_keys=False),
        encoding="utf-8",
    )

    payload = import_thirdparty_pack(
        "mini-crm",
        db_file=fixture["db"],
        okf_root=fixture["okf"],
        evals_file=fixture["evals"],
        config_file=config_file,
        eval_manifest_file=manifest_file,
        agent_dir=tmp_path,
        data_dir=tmp_path / "data",
        system_model_dir=tmp_path,
    )

    assert payload["ok"] is True
    pack = resolve_pack("mini-crm", config_file=config_file)
    assert pack.db_file == fixture["db"].resolve()
    assert pack.schema_root == fixture["okf"].resolve()
    assert pack.system_model.exists()
    assert validate_pack(pack)["ok"] is True
    schema_payload = load_schema_context_for_pack(pack)
    assert schema_payload["ok"] is True
    assert {table["name"] for table in schema_payload["tables"]} == {"customers"}

    model = yaml.safe_load(pack.system_model.read_text(encoding="utf-8"))
    rules = model["planning_model"]["rule_catalog"]["rules"]
    assert rules[0]["match"]["exact"] == "고객은 몇 명이야?"
    assert rules[0]["sql"]["text"] == "SELECT COUNT(*) FROM customers"

    manifest = yaml.safe_load(manifest_file.read_text(encoding="utf-8"))
    manifest_cases = Path(manifest["packs"]["mini-crm"]["runnable"]["consolidated"])
    if not manifest_cases.is_absolute():
        manifest_cases = manifest_file.parent / manifest_cases
    assert manifest_cases.resolve() == fixture["evals"].resolve()


def test_v115_run_eval_writes_eval_run_artifacts_and_external_score(tmp_path):
    from activegraph.cli.eval_run import attach_external_score
    from activegraph.cli.pack_config import import_thirdparty_pack, resolve_pack
    from activegraph.cli.text_to_sql import run_eval

    fixture = _write_thirdparty_fixture(tmp_path)
    config_file = tmp_path / "packs.yaml"
    manifest_file = tmp_path / "eval_manifest.yaml"
    config_file.write_text(
        yaml.safe_dump({"schema_version": "activegraph.packs.v01", "default_pack": "mini-crm", "packs": {}}, sort_keys=False),
        encoding="utf-8",
    )
    manifest_file.write_text(
        yaml.safe_dump({"schema_version": "activegraph.text_to_sql_evals.v01", "packs": {}}, sort_keys=False),
        encoding="utf-8",
    )
    import_thirdparty_pack(
        "mini-crm",
        db_file=fixture["db"],
        okf_root=fixture["okf"],
        evals_file=fixture["evals"],
        config_file=config_file,
        eval_manifest_file=manifest_file,
        agent_dir=tmp_path,
        data_dir=tmp_path / "data",
        system_model_dir=tmp_path,
    )
    pack = resolve_pack("mini-crm", config_file=config_file)
    eval_runs_dir = tmp_path / "eval-runs"

    payload = run_eval(
        fixture["evals"],
        pack.db_file,
        tests_dir=tmp_path / "runs",
        event_store=tmp_path / "events.sqlite",
        system_model_file=pack.system_model,
        pack=pack,
        eval_runs_dir=eval_runs_dir,
    )

    assert payload["ok"] is True
    assert payload["eval_run_id"].startswith("eval_")
    run_dir = Path(payload["artifacts"]["eval_run_dir"])
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "eval_events.jsonl").exists()
    case_dir = run_dir / "cases" / "mini_q001"
    scoring_input = json.loads((case_dir / "scoring-input.json").read_text(encoding="utf-8"))
    assert scoring_input["prompt"] == "고객은 몇 명이야?"
    assert scoring_input["sql"] == "SELECT COUNT(*) FROM customers"
    assert scoring_input["rows"] == [[3]]

    score_file = tmp_path / "score.json"
    score_file.write_text(json.dumps({"score": 1.0, "rubric": "exact", "notes": "ok"}), encoding="utf-8")
    attached = attach_external_score(payload["eval_run_id"], "mini_q001", score_file=score_file, eval_runs_dir=eval_runs_dir)
    assert attached["ok"] is True
    assert Path(attached["external_score_file"]).exists()
    events = (run_dir / "eval_events.jsonl").read_text(encoding="utf-8")
    assert "eval.case_scored" in events
    assert "external_judgment.recorded" in events
