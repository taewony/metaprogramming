import sqlite3
import pandas as pd

DB_PATH = "data/techshop.db"

def query_to_dataframe(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

test_queries = [
    ("VIP 고객 목록", 
     "SELECT id, name, email FROM customers WHERE grade='VIP'"),
    ("가장 비싼 상품 3개",
     "SELECT name, price FROM products ORDER BY price DESC LIMIT 3"),
]

for desc, sql in test_queries:
    df = query_to_dataframe(sql)
    print(f"\n{'='*60}")
    print(f"📊 {desc}")
    print(f"{'='*60}")
    print(df.to_string(index=False))
    print(f"📈 총 {len(df)}개 행")