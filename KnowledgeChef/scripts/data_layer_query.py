#!/usr/bin/env python3
"""
Data Layer Query Script - SQLite 질의 실행 및 결과 반환
Codex의 kchef Skill에 의해 호출됨
"""

import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "techshop.db"

def run_query(sql: str) -> list:
    """SQLite 쿼리 실행 및 결과 반환"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return results
    except sqlite3.Error as e:
        conn.close()
        raise e

def format_results(results: list, headers: list = None) -> str:
    """결과를 자연어/표 형식으로 포맷팅"""
    if not results:
        return "⚠️ 결과가 없습니다."
    
    if not headers:
        # 첫 행의 길이로 헤더 자동 생성
        headers = [f"col_{i+1}" for i in range(len(results[0]))]
    
    # 표 형태로 출력 (Markdown 테이블)
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in results:
        row_str = "| " + " | ".join(str(v) if v is not None else "" for v in row) + " |"
        lines.append(row_str)
    
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python data_layer_query.py '<SQL query>'")
        sys.exit(1)
    
    sql = sys.argv[1]
    try:
        results = run_query(sql)
        print(format_results(results))
        print(f"\n📈 총 {len(results)}개 행")
    except sqlite3.Error as e:
        print(f"❌ SQL 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()