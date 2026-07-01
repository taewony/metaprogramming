#!/usr/bin/env python3
"""Converted from `ch09_text_to_sql.ipynb`.

This module keeps the original hospital-db Text-to-SQL demo but makes it
importable, runnable as a script, and easier to diff/review than a notebook.

Modes:
- default: run the five sample queries
- `--serve`: launch the Gradio UI
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any


hospital_schema = """
-- 의사 테이블
CREATE TABLE doctors (
    doctor_id VARCHAR(10) PRIMARY KEY,  -- 의사ID (예: D001)
    name VARCHAR(50) NOT NULL,          -- 의사명
    specialty VARCHAR(50) NOT NULL,     -- 전공
    hospital_name VARCHAR(100) NOT NULL,-- 병원명
    office VARCHAR(20) NOT NULL,        -- 진료실
    phone VARCHAR(20) NOT NULL,         -- 전화번호
    email VARCHAR(100) NOT NULL         -- 이메일
);

-- 환자 테이블
CREATE TABLE patients (
    patient_id VARCHAR(10) PRIMARY KEY, -- 환자ID (예: P001)
    name VARCHAR(50) NOT NULL,          -- 환자명
    birth_date DATE NOT NULL,           -- 생년월일
    gender CHAR(1) NOT NULL,            -- 성별 (M/F)
    phone VARCHAR(20) NOT NULL,         -- 전화번호
    email VARCHAR(100) NOT NULL,        -- 이메일
    address VARCHAR(200) NOT NULL,      -- 주소
    insurance_number VARCHAR(20) NOT NULL, -- 보험번호
    blood_type VARCHAR(5) NOT NULL,     -- 혈액형
    allergies TEXT                      -- 알러지
);

-- 의사 가용 시간 테이블
CREATE TABLE availability (
    doctor_id VARCHAR(10) NOT NULL,     -- 의사ID
    available_date DATE NOT NULL,       -- 날짜
    available_time TIME NOT NULL,       -- 시간
    status VARCHAR(10) NOT NULL,        -- 예약상태 (가능/불가능)
    PRIMARY KEY (doctor_id, available_date, available_time),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- 예약 테이블
CREATE TABLE appointments (
    appointment_id VARCHAR(10) PRIMARY KEY, -- 예약ID (예: A0001)
    patient_id VARCHAR(10) NOT NULL,     -- 환자ID
    doctor_id VARCHAR(10) NOT NULL,      -- 의사ID
    appointment_date DATE NOT NULL,      -- 예약날짜
    appointment_time TIME NOT NULL,      -- 예약시간
    reason TEXT,                         -- 방문이유
    status VARCHAR(20) NOT NULL,         -- 상태 (예정됨/완료됨/취소됨)
    notes TEXT,                          -- 진료노트
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- 의료 기록 테이블
CREATE TABLE medical_records (
    record_id VARCHAR(10) PRIMARY KEY,  -- 기록ID (예: M0001)
    patient_id VARCHAR(10) NOT NULL,    -- 환자ID
    doctor_id VARCHAR(10) NOT NULL,     -- 의사ID
    record_date DATE NOT NULL,          -- 기록일자
    record_type VARCHAR(20) NOT NULL,   -- 기록유형 (진단/처방/검사)
    content TEXT NOT NULL,              -- 내용
    notes TEXT,                         -- 메모
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- 처방전 테이블
CREATE TABLE prescriptions (
    prescription_id VARCHAR(10) PRIMARY KEY, -- 처방ID (예: R0001)
    patient_id VARCHAR(10) NOT NULL,     -- 환자ID
    doctor_id VARCHAR(10) NOT NULL,      -- 의사ID
    prescription_date DATE NOT NULL,     -- 처방일자
    medication VARCHAR(100) NOT NULL,    -- 약품명
    dosage VARCHAR(50) NOT NULL,         -- 용량
    frequency VARCHAR(50) NOT NULL,      -- 빈도
    duration VARCHAR(20) NOT NULL,       -- 기간
    status VARCHAR(20) NOT NULL,         -- 상태 (발급완료/만료됨)
    renewable BOOLEAN NOT NULL,          -- 갱신가능
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- 보험 테이블
CREATE TABLE insurance (
    insurance_id VARCHAR(10) PRIMARY KEY, -- 보험ID (예: I12345)
    patient_id VARCHAR(10) NOT NULL,     -- 환자ID
    provider VARCHAR(100) NOT NULL,      -- 보험사
    insurance_type VARCHAR(50) NOT NULL, -- 보험유형
    coverage_start DATE NOT NULL,        -- 보장시작일
    coverage_end DATE NOT NULL,          -- 보장종료일
    copay_percentage INT NOT NULL,       -- 자기부담금 비율
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

-- 시술 보장 범위 테이블
CREATE TABLE procedure_coverage (
    insurance_id VARCHAR(10) NOT NULL,   -- 보험ID
    procedure_code VARCHAR(10) NOT NULL, -- 시술코드
    procedure_name VARCHAR(100) NOT NULL,-- 시술명
    coverage_rate INT NOT NULL,          -- 보장율
    max_coverage INT NOT NULL,           -- 최대보장금액
    PRIMARY KEY (insurance_id, procedure_code),
    FOREIGN KEY (insurance_id) REFERENCES insurance(insurance_id)
);
"""


sample_doctors = """
INSERT INTO doctors VALUES('D001', '김지훈', '내과', '서울중앙병원', '301호', '02-123-4567', 'jihoon.kim@hospital.com');
INSERT INTO doctors VALUES('D002', '이수진', '소아과', '서울중앙병원', '302호', '02-123-4568', 'sujin.lee@hospital.com');
INSERT INTO doctors VALUES('D003', '박준석', '정형외과', '서울중앙병원', '401호', '02-123-4569', 'junseok.park@hospital.com');
INSERT INTO doctors VALUES('D004', '최미영', '피부과', '서울중앙병원', '402호', '02-123-4570', 'miyoung.choi@hospital.com');
INSERT INTO doctors VALUES('D005', '정태호', '신경과', '서울중앙병원', '501호', '02-123-4571', 'taeho.jung@hospital.com');
"""


sample_patients = """
INSERT INTO patients VALUES('P001', '홍길동', '1980-05-15', 'M', '010-1234-5678', 'hong@example.com', '서울시 강남구', 'I12345', 'A+', '페니실린');
INSERT INTO patients VALUES('P002', '김영희', '1992-08-20', 'F', '010-2345-6789', 'kim@example.com', '서울시 서초구', 'I23456', 'O+', NULL);
INSERT INTO patients VALUES('P003', '이철수', '1975-12-10', 'M', '010-3456-7890', 'lee@example.com', '서울시 송파구', 'I34567', 'B-', '계란, 견과류');
INSERT INTO patients VALUES('P004', '박미선', '1988-03-25', 'F', '010-4567-8901', 'park@example.com', '서울시 마포구', 'I45678', 'AB+', NULL);
INSERT INTO patients VALUES('P005', '정민준', '2000-01-30', 'M', '010-5678-9012', 'jung@example.com', '서울시 영등포구', 'I56789', 'A-', '라텍스');
"""


sample_availability = """
INSERT INTO availability VALUES('D001', '2025-04-02', '09:00', '가능');
INSERT INTO availability VALUES('D001', '2025-04-02', '10:00', '불가능');
INSERT INTO availability VALUES('D001', '2025-04-02', '11:00', '가능');
INSERT INTO availability VALUES('D001', '2025-04-02', '14:00', '가능');
INSERT INTO availability VALUES('D001', '2025-04-02', '15:00', '불가능');
INSERT INTO availability VALUES('D001', '2025-04-03', '09:00', '가능');
INSERT INTO availability VALUES('D001', '2025-04-03', '10:00', '가능');
INSERT INTO availability VALUES('D002', '2025-04-02', '09:00', '불가능');
INSERT INTO availability VALUES('D002', '2025-04-02', '10:00', '가능');
INSERT INTO availability VALUES('D002', '2025-04-02', '11:00', '가능');
"""


sample_appointments = """
INSERT INTO appointments VALUES('A0001', 'P001', 'D002', '2025-03-20', '10:00', '열 및 두통', '완료됨', '감기 증상. 안정 권장 및 처방전 발급함.');
INSERT INTO appointments VALUES('A0002', 'P002', 'D003', '2025-03-25', '11:00', '무릎 통증', '완료됨', '연골 손상 의심. MRI 검사 예약 완료.');
INSERT INTO appointments VALUES('A0003', 'P001', 'D001', '2025-04-05', '09:00', '정기 검진', '예정됨', NULL);
INSERT INTO appointments VALUES('A0004', 'P003', 'D005', '2025-03-30', '14:00', '두통 및 어지러움', '취소됨', '환자 요청으로 취소됨');
INSERT INTO appointments VALUES('A0005', 'P004', 'D004', '2025-04-06', '15:00', '피부 발진', '예정됨', NULL);
"""


sample_medical_records = """
INSERT INTO medical_records VALUES('M0001', 'P001', 'D002', '2025-03-20', '진단', '급성 상기도 감염', '처방전 발급함');
INSERT INTO medical_records VALUES('M0002', 'P001', 'D002', '2025-03-20', '처방', '타이레놀 500mg, 하루 3회', '7일분 처방');
INSERT INTO medical_records VALUES('M0003', 'P002', 'D003', '2025-03-25', '진단', '무릎 연골 손상 의심', 'MRI 검사 요청함');
INSERT INTO medical_records VALUES('M0004', 'P002', 'D003', '2025-03-25', '검사', '무릎 MRI 검사', '다음 주 예약 완료');
INSERT INTO medical_records VALUES('M0005', 'P003', 'D001', '2025-03-15', '처방', '디아제팜 5mg, 취침 전 1회', '30일분 처방');
"""


sample_prescriptions = """
INSERT INTO prescriptions VALUES('R0001', 'P001', 'D002', '2025-03-20', '타이레놀 500mg', '1정', '하루 3회', '7일', '발급완료', TRUE);
INSERT INTO prescriptions VALUES('R0002', 'P003', 'D001', '2025-03-15', '디아제팜 5mg', '1정', '취침 전 1회', '30일', '발급완료', FALSE);
INSERT INTO prescriptions VALUES('R0003', 'P005', 'D005', '2025-03-10', '아스피린 100mg', '1정', '하루 1회', '90일', '발급완료', TRUE);
INSERT INTO prescriptions VALUES('R0004', 'P002', 'D001', '2025-02-25', '암로디핀 5mg', '1정', '하루 1회', '30일', '만료됨', TRUE);
INSERT INTO prescriptions VALUES('R0005', 'P004', 'D004', '2025-03-05', '프레드니솔론 크림', '소량', '하루 2회', '14일', '발급완료', FALSE);
"""


sample_insurance = """
INSERT INTO insurance VALUES('I12345', 'P001', '국민건강보험', '기본형', '2024-01-01', '2025-12-31', 20);
INSERT INTO insurance VALUES('I23456', 'P002', '한화생명', '프리미엄', '2024-01-01', '2025-12-31', 10);
INSERT INTO insurance VALUES('I34567', 'P003', '메리츠화재', '기본형', '2024-01-01', '2025-12-31', 15);
INSERT INTO insurance VALUES('I45678', 'P004', '삼성생명', '프리미엄', '2024-01-01', '2025-12-31', 5);
INSERT INTO insurance VALUES('I56789', 'P005', '국민건강보험', '기본형', '2024-01-01', '2025-12-31', 20);
"""


sample_procedure_coverage = """
INSERT INTO procedure_coverage VALUES('I12345', 'PC001', '기본 진료', 80, 50000);
INSERT INTO procedure_coverage VALUES('I12345', 'PC002', 'X-ray 검사', 70, 100000);
INSERT INTO procedure_coverage VALUES('I23456', 'PC001', '기본 진료', 90, 100000);
INSERT INTO procedure_coverage VALUES('I23456', 'PC003', 'MRI 검사', 80, 500000);
INSERT INTO procedure_coverage VALUES('I34567', 'PC004', 'CT 검사', 75, 300000);
"""


hospital_complete_schema = (
    hospital_schema
    + sample_doctors
    + sample_patients
    + sample_availability
    + sample_appointments
    + sample_medical_records
    + sample_prescriptions
    + sample_insurance
    + sample_procedure_coverage
)


DB = None
AGENT = None
SYSTEM_PROMPT = ""
CONVERSATION: list[dict[str, str]] = []
EXEC_LOG = ""


def _load_llama_index_components():
    from llama_index.core import SQLDatabase
    from llama_index.llms.openai import OpenAI
    from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, AgentOutput

    return SQLDatabase, OpenAI, FunctionAgent, ToolCallResult, AgentOutput


def create_hospital_db(db_file: str | None = None):
    """Create the temporary SQLite DB and return a llama_index SQLDatabase."""
    SQLDatabase, _, _, _, _ = _load_llama_index_components()

    if db_file is None:
        db_file = os.path.join(tempfile.gettempdir(), "hospital.db")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript(
        """
        DROP TABLE IF EXISTS procedure_coverage;
        DROP TABLE IF EXISTS insurance;
        DROP TABLE IF EXISTS prescriptions;
        DROP TABLE IF EXISTS medical_records;
        DROP TABLE IF EXISTS appointments;
        DROP TABLE IF EXISTS availability;
        DROP TABLE IF EXISTS patients;
        DROP TABLE IF EXISTS doctors;
        """
    )

    cursor.executescript(hospital_schema)
    cursor.executescript(sample_doctors)
    cursor.executescript(sample_patients)
    cursor.executescript(sample_availability)
    cursor.executescript(sample_appointments)
    cursor.executescript(sample_medical_records)
    cursor.executescript(sample_prescriptions)
    cursor.executescript(sample_insurance)
    cursor.executescript(sample_procedure_coverage)

    conn.commit()
    conn.close()

    return SQLDatabase.from_uri(f"sqlite:///{db_file}")


def build_system_prompt() -> str:
    return f"""당신은 병원 DB 어시스턴트입니다.

아래는 병원 DB의 전체 테이블 스키마입니다:
------------------------------------------------
{hospital_schema}
------------------------------------------------

[규칙]
1) DB 조회가 필요한 질문이면, SQL 쿼리를 작성하고 db_query 함수를 호출하세요.
2) 일반 질문(날씨, 잡담 등)은 함수 호출 없이 답변하세요.
3) DB 결과를 간단히 요약해 최종 답변을 만드세요.
4) 이전 대화 맥락(멀티턴)도 유지하세요.
"""


def initialize_demo(db_file: str | None = None):
    global DB, AGENT, SYSTEM_PROMPT, CONVERSATION, EXEC_LOG

    SQLDatabase, OpenAI, FunctionAgent, _, _ = _load_llama_index_components()
    llm = OpenAI(model="gpt-4o", temperature=0)

    DB = create_hospital_db(db_file=db_file)
    SYSTEM_PROMPT = build_system_prompt()
    CONVERSATION = [{"role": "system", "content": SYSTEM_PROMPT}]
    EXEC_LOG = ""

    def db_query(sql_query: str) -> str:
        """Run SQL against the hospital DB and return a string result."""
        try:
            result = DB.run_sql(sql_query)
            if not result:
                return "쿼리 결과가 없습니다."
            return str(result)
        except Exception as e:
            return f"[DB 오류] {e}"

    AGENT = FunctionAgent(
        tools=[db_query],
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        max_iterations=3,
        verbose=True,
    )

    print("데이터베이스가 성공적으로 생성되었습니다.")
    print(f"사용 가능한 테이블: {DB.get_usable_table_names()}")
    doctors_example = DB.run_sql("SELECT * FROM doctors LIMIT 3;")
    print(f"의사 테이블 샘플: {doctors_example}")


def _require_initialized():
    if DB is None or AGENT is None:
        raise RuntimeError("Call initialize_demo() before using the demo helpers.")


async def run_agent_verbose(query: str):
    _require_initialized()
    _, _, _, ToolCallResult, AgentOutput = _load_llama_index_components()

    handler = AGENT.run(query)
    async for event in handler.stream_events():
        if isinstance(event, ToolCallResult):
            print(f"[ToolCall] name={event.tool_name}, args={event.tool_kwargs}")
            print(f" -> result: {event.tool_output}\n")
    result = await handler
    return result


async def test_five_queries():
    queries = [
        "김지훈 의사의 전공은?",
        "홍길동 환자의 보험은?",
        "날씨가 궁금해",
        "의사 몇명 있니?",
        "김지훈 의사 병원?",
    ]
    for i, q in enumerate(queries, start=1):
        out = await run_agent_verbose(q)
        print(f"[Q{i}] 최종 답변: {str(out)}")


def build_prompt(new_user_msg: str) -> str:
    lines = []
    for turn in CONVERSATION:
        r = turn["role"]
        c = turn["content"]
        if r == "system":
            lines.append(f"System: {c}")
        elif r == "user":
            lines.append(f"User: {c}")
        elif r == "assistant":
            lines.append(f"Assistant: {c}")
    lines.append(f"User: {new_user_msg}")
    lines.append("Assistant:")
    return "\n".join(lines)


async def chat_handler(user_text, chat_history):
    _require_initialized()
    global EXEC_LOG
    _, _, _, ToolCallResult, AgentOutput = _load_llama_index_components()

    full_prompt = build_prompt(user_text)
    handler = AGENT.run(full_prompt)
    tool_calls_str = ""
    async for event in handler.stream_events():
        if isinstance(event, ToolCallResult):
            tool_calls_str += f"[ToolCall] {event.tool_name}, args={event.tool_kwargs}\n"
            tool_calls_str += f" -> result: {event.tool_output}\n\n"

    final_out = await handler
    bot_answer = str(final_out)

    CONVERSATION.append({"role": "user", "content": user_text})
    CONVERSATION.append({"role": "assistant", "content": bot_answer})

    chat_history.append({"role": "user", "content": user_text})
    chat_history.append({"role": "assistant", "content": bot_answer})

    turn_log = f"[User] {user_text}\n"
    turn_log += tool_calls_str
    turn_log += f"[Assistant] {bot_answer}\n"
    turn_log += ("=" * 50) + "\n"
    EXEC_LOG += turn_log

    return "", chat_history, EXEC_LOG


def clear_all():
    global CONVERSATION, EXEC_LOG
    CONVERSATION = [{"role": "system", "content": SYSTEM_PROMPT}]
    EXEC_LOG = ""
    return [], ""


def launch_gradio():
    _require_initialized()
    import gradio as gr

    with gr.Blocks(css="footer {visibility: hidden}") as demo:
        gr.Markdown("## 병원 DB Text-to-SQL (멀티턴) + 실행 로그 (Right)")

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="대화창", height=400, type="messages")
                user_inp = gr.Textbox(label="질문 입력", placeholder="예) 김지훈 의사 이메일?")
                clr_btn = gr.Button("대화 초기화")
            with gr.Column(scale=1):
                logs = gr.Textbox(label="실행 로그", lines=20)

        user_inp.submit(fn=chat_handler, inputs=[user_inp, chatbot], outputs=[user_inp, chatbot, logs])
        clr_btn.click(fn=clear_all, outputs=[chatbot, logs])

        gr.Markdown(
            """
            **사용 예시:**
            - "김지훈 의사의 이메일 알려줘"
            - "그 의사의 빈 시간은 언제야?" (맥락: 김지훈)
            - "날씨 어때?" (DB 불필요)
            - "김영희 환자 보험번호 알려줘"
            """
        )

    demo.launch(debug=True, share=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Converted hospital Text-to-SQL notebook")
    parser.add_argument("--db-file", type=str, default=None, help="Optional SQLite path")
    parser.add_argument("--serve", action="store_true", help="Launch the Gradio UI")
    parser.add_argument("--test-five", action="store_true", help="Run the five sample queries")
    args = parser.parse_args(argv)

    initialize_demo(db_file=args.db_file)

    if args.serve:
        launch_gradio()
        return 0

    if args.test_five or not args.serve:
        asyncio.run(test_five_queries())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
