import sqlite3
import json
from pathlib import Path
import os

DB_PATH = "data/techshop.db"

def load_jsonl(filepath):
    """JSONL 파일을 로드하고 각 라인의 딕셔너리 리스트로 반환"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 파싱 오류 (라인 {line_num}): {e}")
                print(f"   내용: {line[:100]}...")
    return data

def create_tables(conn):
    cursor = conn.cursor()
    # customers 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            email TEXT, name TEXT, phone TEXT,
            grade TEXT, point_balance INTEGER,
            is_active INTEGER, created_at TEXT
        )
    ''')
    # products 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT, brand TEXT, sku TEXT,
            price REAL, cost_price REAL, stock_qty INTEGER,
            is_active INTEGER, created_at TEXT
        )
    ''')
    # orders 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            order_number TEXT, customer_id INTEGER,
            status TEXT, total_amount REAL,
            ordered_at TEXT
        )
    ''')
    # order_items 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER, product_id INTEGER,
            quantity INTEGER, unit_price REAL,
            subtotal REAL
        )
    ''')
    conn.commit()
    print("✅ 테이블 생성 완료")

def insert_data(conn, table, data):
    if not data:
        print(f"⚠️ {table}: 삽입할 데이터가 없습니다.")
        return 0
    
    cursor = conn.cursor()
    columns = list(data[0].keys())
    placeholders = ','.join(['?' for _ in columns])
    col_names = ','.join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
    
    # 디버그: 첫 번째 데이터와 SQL 출력
    print(f"📝 {table} - 컬럼: {columns}")
    print(f"📝 {table} - 첫 데이터 샘플: {data[0]}")
    print(f"📝 {table} - 실행 SQL: {sql}")
    
    inserted = 0
    for i, row in enumerate(data):
        try:
            values = [row.get(col) for col in columns]
            cursor.execute(sql, values)
            inserted += 1
            # 100개마다 진행 상태 출력
            if (i + 1) % 100 == 0:
                print(f"   {table}: {i+1} rows inserted...")
        except Exception as e:
            print(f"❌ {table} 삽입 오류 (행 {i+1}): {e}")
            print(f"   데이터: {row}")
            # 오류 발생 시 롤백 없이 계속 (의도)
    
    conn.commit()
    print(f"✅ {table}: {inserted} rows inserted")
    return inserted

def main():
    # 1. 현재 작업 디렉토리 확인
    cwd = Path.cwd()
    print(f"📂 현재 작업 디렉토리: {cwd}")
    
    # 2. data 폴더 존재 확인
    data_dir = Path("data/raw")
    if not data_dir.exists():
        print("❌ 'data' 폴더가 존재하지 않습니다.")
        return
    print(f"📁 data 폴더 내 파일 목록: {list(data_dir.glob('*'))}")
    
    # 3. DB 연결
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    
    for table in ['customers', 'products', 'orders', 'order_items']:
        jsonl_path = data_dir / f"{table}.jsonl"
        if not jsonl_path.exists():
            print(f"⚠️ {table}: 파일 없음 ({jsonl_path})")
            continue
        
        # 파일 크기 확인
        file_size = jsonl_path.stat().st_size
        print(f"📄 {table}.jsonl 크기: {file_size} bytes")
        
        # 파일 내용 일부 미리보기 (처음 3줄)
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            preview_lines = [line.strip() for line in f.readlines()[:3]]
        print(f"📄 {table}.jsonl 처음 3줄:")
        for line in preview_lines:
            print(f"   {line[:200]}...")
        
        # 데이터 로드
        data = load_jsonl(jsonl_path)
        print(f"📊 {table}: JSONL 로드 완료, {len(data)} 레코드")
        
        if data:
            insert_data(conn, table, data)
        else:
            print(f"⚠️ {table}: 로드된 데이터가 없습니다.")
    
    conn.close()
    print("🎉 작업 완료")

if __name__ == "__main__":
    main()