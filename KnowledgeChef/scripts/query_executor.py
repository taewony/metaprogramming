import sqlite3
import re

class NLQueryEngine:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.rules = self._build_rules()
    
    def _build_rules(self):
        return [
            # 패턴: "VIP 고객" → grade='VIP'
            (r'VIP\s*고객', "SELECT id, name, email FROM customers WHERE grade='VIP'"),
            # 패턴: "가장 비싼 상품 N개" → ORDER BY price DESC LIMIT N
            (r'가장\s*비싼\s*상품\s*(\d+)\s*개', 
             lambda m: f"SELECT name, price FROM products ORDER BY price DESC LIMIT {m.group(1)}"),
            # ... 더 많은 규칙
        ]
    
    def query(self, natural_language):
        for pattern, sql in self.rules:
            match = re.search(pattern, natural_language)
            if match:
                if callable(sql):
                    sql = sql(match)
                return self._execute(sql)
        return "죄송합니다. 질문을 이해하지 못했습니다."
    
    def _execute(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

# 테스트
engine = NLQueryEngine("data/techshop.db")
print("VIP 고객은 누구야?")
print(engine.query("VIP 고객은 누구야?"))
print()
print("가장 비싼 상품 3개 알려줘")
print(engine.query("가장 비싼 상품 3개 알려줘"))