## 1. 4개 테이블 + JSONL 샘플만으로 충분할까?

**네, 충분합니다.** customers, orders, order_items, products 4개 테이블만으로도 자연어 데이터 조회 기능의 핵심 시나리오 대부분을 테스트할 수 있습니다.

| 시나리오 | 필요 테이블 | 비고 |
|----------|-------------|------|
| 고객 정보 조회 | customers | 이름/이메일/등급/포인트 등 |
| 주문 내역 조회 | customers + orders | 고객별 주문 이력 |
| 상품 정보 조회 | products | 상품명/가격/브랜드/재고 |
| 매출/실적 집계 | orders + order_items | 총매출, 상품별 판매량 |
| 리뷰 분석 | reviews + products | 평점, 리뷰 수 |
| 고객-주문-상품 연관 분석 | customers + orders + order_items + products | 고객 구매 패턴, 상품 선호도 |

**4개 테이블로 부족한 영역**:
- 배송/결제/반품 관련 질문 → shipping, payments, returns 테이블 필요
- 카테고리/공급사 관련 질문 → categories, suppliers 테이블 필요

→ **MVP(Minimum Viable Product) 테스트에는 4개 테이블이 충분**하며, 이후 확장 시 나머지 테이블을 추가하면 됩니다.

---

## 2. 데이터 구축 방법: JSONL vs SQLite

### 결론: **SQLite를 권장**합니다.

| 항목 | JSONL 단독 | SQLite |
|------|-----------|--------|
| **JOIN 쿼리** | 직접 구현 필요 | SQL로 간단 처리 |
| **집계/그룹화** | 직접 구현 필요 | GROUP BY, SUM 등 내장 |
| **필터링/정렬** | 직접 구현 필요 | WHERE, ORDER BY 내장 |
| **자연어→SQL 변환** | 복잡한 매핑 로직 필요 | Text-to-SQL로 간결 |
| **데이터 크기** | 수백 건까지만 적합 | 수만~수백만 건도 가능 |
| **확장성** | 낮음 | 높음 |

### 추천 접근법: JSONL → SQLite 변환

```python
# jsonl_to_sqlite.py
import sqlite3
import json
from pathlib import Path

DB_PATH = "data/techshop.db"

def load_jsonl(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

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

def insert_data(conn, table, data):
    if not data:
        return
    cursor = conn.cursor()
    columns = list(data[0].keys())
    placeholders = ','.join(['?' for _ in columns])
    col_names = ','.join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
    for row in data:
        cursor.execute(sql, [row.get(col) for col in columns])
    conn.commit()

def main():
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    
    for table in ['customers', 'products', 'orders', 'order_items']:
        jsonl_path = Path(f"data/{table}.jsonl")
        if jsonl_path.exists():
            data = load_jsonl(jsonl_path)
            insert_data(conn, table, data)
            print(f"Loaded {len(data)} rows into {table}")
    
    conn.close()

if __name__ == "__main__":
    main()
```

---

## 3. JSONL 샘플 데이터

### 3.1 customers.jsonl (20명)

```jsonl
{"id":1,"email":"alice@test.kr","name":"김민지","phone":"010-1234-5678","grade":"GOLD","point_balance":12500,"is_active":1,"created_at":"2024-01-15 10:30:00"}
{"id":2,"email":"bob@test.kr","name":"이현우","phone":"010-2345-6789","grade":"SILVER","point_balance":3200,"is_active":1,"created_at":"2024-02-20 14:15:00"}
{"id":3,"email":"carol@test.kr","name":"박서연","phone":"010-3456-7890","grade":"BRONZE","point_balance":500,"is_active":1,"created_at":"2024-03-10 09:00:00"}
{"id":4,"email":"dave@test.kr","name":"정민호","phone":"010-4567-8901","grade":"VIP","point_balance":45000,"is_active":1,"created_at":"2023-11-05 16:45:00"}
{"id":5,"email":"eve@test.kr","name":"최유진","phone":"010-5678-9012","grade":"GOLD","point_balance":8700,"is_active":0,"created_at":"2023-12-01 11:20:00"}
{"id":6,"email":"frank@test.kr","name":"장동훈","phone":"010-6789-0123","grade":"SILVER","point_balance":1500,"is_active":1,"created_at":"2024-04-25 13:50:00"}
{"id":7,"email":"grace@test.kr","name":"한소희","phone":"010-7890-1234","grade":"BRONZE","point_balance":200,"is_active":1,"created_at":"2024-05-12 08:30:00"}
{"id":8,"email":"hank@test.kr","name":"오세훈","phone":"010-8901-2345","grade":"VIP","point_balance":28000,"is_active":1,"created_at":"2023-09-18 15:10:00"}
{"id":9,"email":"iris@test.kr","name":"신혜진","phone":"010-9012-3456","grade":"GOLD","point_balance":5400,"is_active":1,"created_at":"2024-01-28 12:00:00"}
{"id":10,"email":"jack@test.kr","name":"임재현","phone":"010-0123-4567","grade":"SILVER","point_balance":2100,"is_active":1,"created_at":"2024-03-22 17:30:00"}
{"id":11,"email":"karen@test.kr","name":"윤아름","phone":"010-1234-5679","grade":"BRONZE","point_balance":100,"is_active":1,"created_at":"2024-06-01 10:00:00"}
{"id":12,"email":"leo@test.kr","name":"강태영","phone":"010-2345-6780","grade":"VIP","point_balance":32000,"is_active":1,"created_at":"2023-08-14 09:30:00"}
{"id":13,"email":"mia@test.kr","name":"서지원","phone":"010-3456-7891","grade":"GOLD","point_balance":9800,"is_active":1,"created_at":"2024-02-05 14:20:00"}
{"id":14,"email":"nick@test.kr","name":"배준호","phone":"010-4567-8902","grade":"SILVER","point_balance":4000,"is_active":1,"created_at":"2024-04-10 11:45:00"}
{"id":15,"email":"olivia@test.kr","name":"나은지","phone":"010-5678-9013","grade":"BRONZE","point_balance":0,"is_active":1,"created_at":"2024-05-20 16:00:00"}
{"id":16,"email":"peter@test.kr","name":"문창호","phone":"010-6789-0124","grade":"VIP","point_balance":51000,"is_active":0,"created_at":"2023-10-30 13:15:00"}
{"id":17,"email":"quinn@test.kr","name":"양지은","phone":"010-7890-1235","grade":"GOLD","point_balance":6700,"is_active":1,"created_at":"2024-01-10 08:50:00"}
{"id":18,"email":"rose@test.kr","name":"하연주","phone":"010-8901-2346","grade":"SILVER","point_balance":2800,"is_active":1,"created_at":"2024-03-01 15:30:00"}
{"id":19,"email":"sam@test.kr","name":"구자현","phone":"010-9012-3457","grade":"BRONZE","point_balance":300,"is_active":1,"created_at":"2024-06-15 12:10:00"}
{"id":20,"email":"tina@test.kr","name":"황미소","phone":"010-0123-4568","grade":"VIP","point_balance":39000,"is_active":1,"created_at":"2023-12-20 10:40:00"}
```

### 3.2 products.jsonl (15개)

```jsonl
{"id":1,"name":"LG 그램 16인치","brand":"LG","sku":"LG-GEN-00001","price":1520000,"cost_price":1100000,"stock_qty":45,"is_active":1,"created_at":"2024-01-01 00:00:00"}
{"id":2,"name":"삼성 갤럭시 S24","brand":"Samsung","sku":"SS-GEN-00002","price":1350000,"cost_price":980000,"stock_qty":120,"is_active":1,"created_at":"2024-01-15 00:00:00"}
{"id":3,"name":"애플 맥북 에어 M3","brand":"Apple","sku":"AP-GEN-00003","price":1490000,"cost_price":1120000,"stock_qty":30,"is_active":1,"created_at":"2024-02-01 00:00:00"}
{"id":4,"name":"다이슨 V15 무선청소기","brand":"Dyson","sku":"DY-GEN-00004","price":890000,"cost_price":620000,"stock_qty":25,"is_active":1,"created_at":"2024-02-15 00:00:00"}
{"id":5,"name":"LG전자 퓨리케어 공기청정기","brand":"LG","sku":"LG-GEN-00005","price":550000,"cost_price":380000,"stock_qty":18,"is_active":1,"created_at":"2024-03-01 00:00:00"}
{"id":6,"name":"삼성 비스포크 냉장고","brand":"Samsung","sku":"SS-GEN-00006","price":2150000,"cost_price":1550000,"stock_qty":12,"is_active":1,"created_at":"2024-03-15 00:00:00"}
{"id":7,"name":"애플 아이폰 15 프로","brand":"Apple","sku":"AP-GEN-00007","price":1550000,"cost_price":1180000,"stock_qty":85,"is_active":1,"created_at":"2024-04-01 00:00:00"}
{"id":8,"name":"소니 WH-1000XM5","brand":"Sony","sku":"SN-GEN-00008","price":450000,"cost_price":310000,"stock_qty":60,"is_active":1,"created_at":"2024-04-15 00:00:00"}
{"id":9,"name":"로지텍 MX 마스터 3S","brand":"Logitech","sku":"LG-GEN-00009","price":139000,"cost_price":95000,"stock_qty":200,"is_active":1,"created_at":"2024-05-01 00:00:00"}
{"id":10,"name":"삼성 T7 실드 외장SSD","brand":"Samsung","sku":"SS-GEN-00010","price":189000,"cost_price":130000,"stock_qty":75,"is_active":1,"created_at":"2024-05-15 00:00:00"}
{"id":11,"name":"애플 워치 SE 2세대","brand":"Apple","sku":"AP-GEN-00011","price":420000,"cost_price":290000,"stock_qty":40,"is_active":1,"created_at":"2024-06-01 00:00:00"}
{"id":12,"name":"LG전자 32인치 모니터","brand":"LG","sku":"LG-GEN-00012","price":380000,"cost_price":260000,"stock_qty":0,"is_active":0,"created_at":"2024-01-20 00:00:00"}
{"id":13,"name":"샤오미 미밴드 9","brand":"Xiaomi","sku":"XM-GEN-00013","price":48000,"cost_price":32000,"stock_qty":500,"is_active":1,"created_at":"2024-03-20 00:00:00"}
{"id":14,"name":"닌텐도 스위치 OLED","brand":"Nintendo","sku":"NT-GEN-00014","price":420000,"cost_price":300000,"stock_qty":35,"is_active":1,"created_at":"2024-04-20 00:00:00"}
{"id":15,"name":"구글 픽셀 8a","brand":"Google","sku":"GG-GEN-00015","price":590000,"cost_price":420000,"stock_qty":28,"is_active":1,"created_at":"2024-05-20 00:00:00"}
```

### 3.3 orders.jsonl (30건)

```jsonl
{"id":1,"order_number":"ORD-2024-01-00001","customer_id":1,"status":"confirmed","total_amount":1520000,"ordered_at":"2024-01-20 10:15:00"}
{"id":2,"order_number":"ORD-2024-01-00002","customer_id":4,"status":"confirmed","total_amount":1350000,"ordered_at":"2024-01-22 14:30:00"}
{"id":3,"order_number":"ORD-2024-01-00003","customer_id":8,"status":"cancelled","total_amount":890000,"ordered_at":"2024-01-25 09:45:00"}
{"id":4,"order_number":"ORD-2024-02-00004","customer_id":2,"status":"confirmed","total_amount":1490000,"ordered_at":"2024-02-05 11:00:00"}
{"id":5,"order_number":"ORD-2024-02-00005","customer_id":12,"status":"confirmed","total_amount":2150000,"ordered_at":"2024-02-10 16:20:00"}
{"id":6,"order_number":"ORD-2024-02-00006","customer_id":1,"status":"confirmed","total_amount":550000,"ordered_at":"2024-02-15 08:50:00"}
{"id":7,"order_number":"ORD-2024-02-00007","customer_id":17,"status":"confirmed","total_amount":450000,"ordered_at":"2024-02-20 13:10:00"}
{"id":8,"order_number":"ORD-2024-03-00008","customer_id":5,"status":"confirmed","total_amount":139000,"ordered_at":"2024-03-01 10:30:00"}
{"id":9,"order_number":"ORD-2024-03-00009","customer_id":13,"status":"confirmed","total_amount":1550000,"ordered_at":"2024-03-05 15:45:00"}
{"id":10,"order_number":"ORD-2024-03-00010","customer_id":8,"status":"confirmed","total_amount":420000,"ordered_at":"2024-03-10 09:20:00"}
{"id":11,"order_number":"ORD-2024-03-00011","customer_id":20,"status":"confirmed","total_amount":189000,"ordered_at":"2024-03-15 14:00:00"}
{"id":12,"order_number":"ORD-2024-03-00012","customer_id":6,"status":"cancelled","total_amount":48000,"ordered_at":"2024-03-20 11:30:00"}
{"id":13,"order_number":"ORD-2024-04-00013","customer_id":9,"status":"confirmed","total_amount":590000,"ordered_at":"2024-04-01 16:10:00"}
{"id":14,"order_number":"ORD-2024-04-00014","customer_id":14,"status":"confirmed","total_amount":420000,"ordered_at":"2024-04-05 10:00:00"}
{"id":15,"order_number":"ORD-2024-04-00015","customer_id":3,"status":"confirmed","total_amount":1350000,"ordered_at":"2024-04-10 13:40:00"}
{"id":16,"order_number":"ORD-2024-04-00016","customer_id":18,"status":"confirmed","total_amount":1520000,"ordered_at":"2024-04-15 09:15:00"}
{"id":17,"order_number":"ORD-2024-04-00017","customer_id":10,"status":"confirmed","total_amount":450000,"ordered_at":"2024-04-20 14:50:00"}
{"id":18,"order_number":"ORD-2024-05-00018","customer_id":7,"status":"confirmed","total_amount":890000,"ordered_at":"2024-05-01 11:20:00"}
{"id":19,"order_number":"ORD-2024-05-00019","customer_id":15,"status":"confirmed","total_amount":139000,"ordered_at":"2024-05-05 08:30:00"}
{"id":20,"order_number":"ORD-2024-05-00020","customer_id":11,"status":"confirmed","total_amount":48000,"ordered_at":"2024-05-10 15:00:00"}
{"id":21,"order_number":"ORD-2024-05-00021","customer_id":19,"status":"confirmed","total_amount":2150000,"ordered_at":"2024-05-15 10:45:00"}
{"id":22,"order_number":"ORD-2024-05-00022","customer_id":16,"status":"confirmed","total_amount":1550000,"ordered_at":"2024-05-20 16:30:00"}
{"id":23,"order_number":"ORD-2024-06-00023","customer_id":1,"status":"confirmed","total_amount":420000,"ordered_at":"2024-06-01 09:00:00"}
{"id":24,"order_number":"ORD-2024-06-00024","customer_id":4,"status":"confirmed","total_amount":590000,"ordered_at":"2024-06-05 13:15:00"}
{"id":25,"order_number":"ORD-2024-06-00025","customer_id":12,"status":"confirmed","total_amount":189000,"ordered_at":"2024-06-10 11:50:00"}
{"id":26,"order_number":"ORD-2024-06-00026","customer_id":2,"status":"confirmed","total_amount":1520000,"ordered_at":"2024-06-15 14:30:00"}
{"id":27,"order_number":"ORD-2024-06-00027","customer_id":17,"status":"confirmed","total_amount":1350000,"ordered_at":"2024-06-20 10:00:00"}
{"id":28,"order_number":"ORD-2024-06-00028","customer_id":8,"status":"returned","total_amount":550000,"ordered_at":"2024-06-22 09:30:00"}
{"id":29,"order_number":"ORD-2024-06-00029","customer_id":13,"status":"confirmed","total_amount":420000,"ordered_at":"2024-06-25 16:00:00"}
{"id":30,"order_number":"ORD-2024-06-00030","customer_id":20,"status":"confirmed","total_amount":48000,"ordered_at":"2024-06-28 12:20:00"}
```

### 3.4 order_items.jsonl (주문 상세, 50건)

```jsonl
{"id":1,"order_id":1,"product_id":1,"quantity":1,"unit_price":1520000,"subtotal":1520000}
{"id":2,"order_id":2,"product_id":2,"quantity":1,"unit_price":1350000,"subtotal":1350000}
{"id":3,"order_id":3,"product_id":4,"quantity":1,"unit_price":890000,"subtotal":890000}
{"id":4,"order_id":4,"product_id":3,"quantity":1,"unit_price":1490000,"subtotal":1490000}
{"id":5,"order_id":5,"product_id":6,"quantity":1,"unit_price":2150000,"subtotal":2150000}
{"id":6,"order_id":6,"product_id":5,"quantity":1,"unit_price":550000,"subtotal":550000}
{"id":7,"order_id":7,"product_id":8,"quantity":1,"unit_price":450000,"subtotal":450000}
{"id":8,"order_id":8,"product_id":9,"quantity":1,"unit_price":139000,"subtotal":139000}
{"id":9,"order_id":9,"product_id":7,"quantity":1,"unit_price":1550000,"subtotal":1550000}
{"id":10,"order_id":10,"product_id":11,"quantity":1,"unit_price":420000,"subtotal":420000}
{"id":11,"order_id":11,"product_id":10,"quantity":1,"unit_price":189000,"subtotal":189000}
{"id":12,"order_id":12,"product_id":13,"quantity":1,"unit_price":48000,"subtotal":48000}
{"id":13,"order_id":13,"product_id":15,"quantity":1,"unit_price":590000,"subtotal":590000}
{"id":14,"order_id":14,"product_id":14,"quantity":1,"unit_price":420000,"subtotal":420000}
{"id":15,"order_id":15,"product_id":2,"quantity":1,"unit_price":1350000,"subtotal":1350000}
{"id":16,"order_id":16,"product_id":1,"quantity":1,"unit_price":1520000,"subtotal":1520000}
{"id":17,"order_id":17,"product_id":8,"quantity":1,"unit_price":450000,"subtotal":450000}
{"id":18,"order_id":18,"product_id":4,"quantity":1,"unit_price":890000,"subtotal":890000}
{"id":19,"order_id":19,"product_id":9,"quantity":1,"unit_price":139000,"subtotal":139000}
{"id":20,"order_id":20,"product_id":13,"quantity":1,"unit_price":48000,"subtotal":48000}
{"id":21,"order_id":21,"product_id":6,"quantity":1,"unit_price":2150000,"subtotal":2150000}
{"id":22,"order_id":22,"product_id":7,"quantity":1,"unit_price":1550000,"subtotal":1550000}
{"id":23,"order_id":23,"product_id":11,"quantity":1,"unit_price":420000,"subtotal":420000}
{"id":24,"order_id":24,"product_id":15,"quantity":1,"unit_price":590000,"subtotal":590000}
{"id":25,"order_id":25,"product_id":10,"quantity":1,"unit_price":189000,"subtotal":189000}
{"id":26,"order_id":26,"product_id":1,"quantity":1,"unit_price":1520000,"subtotal":1520000}
{"id":27,"order_id":27,"product_id":2,"quantity":1,"unit_price":1350000,"subtotal":1350000}
{"id":28,"order_id":28,"product_id":5,"quantity":1,"unit_price":550000,"subtotal":550000}
{"id":29,"order_id":29,"product_id":14,"quantity":1,"unit_price":420000,"subtotal":420000}
{"id":30,"order_id":30,"product_id":13,"quantity":1,"unit_price":48000,"subtotal":48000}
{"id":31,"order_id":1,"product_id":9,"quantity":2,"unit_price":139000,"subtotal":278000}
{"id":32,"order_id":2,"product_id":5,"quantity":1,"unit_price":550000,"subtotal":550000}
{"id":33,"order_id":4,"product_id":8,"quantity":1,"unit_price":450000,"subtotal":450000}
{"id":34,"order_id":5,"product_id":2,"quantity":1,"unit_price":1350000,"subtotal":1350000}
{"id":35,"order_id":6,"product_id":11,"quantity":1,"unit_price":420000,"subtotal":420000}
{"id":36,"order_id":7,"product_id":13,"quantity":2,"unit_price":48000,"subtotal":96000}
{"id":37,"order_id":9,"product_id":3,"quantity":1,"unit_price":1490000,"subtotal":1490000}
{"id":38,"order_id":10,"product_id":9,"quantity":3,"unit_price":139000,"subtotal":417000}
{"id":39,"order_id":13,"product_id":4,"quantity":1,"unit_price":890000,"subtotal":890000}
{"id":40,"order_id":15,"product_id":7,"quantity":1,"unit_price":1550000,"subtotal":1550000}
{"id":41,"order_id":16,"product_id":10,"quantity":1,"unit_price":189000,"subtotal":189000}
{"id":42,"order_id":18,"product_id":2,"quantity":1,"unit_price":1350000,"subtotal":1350000}
{"id":43,"order_id":21,"product_id":1,"quantity":1,"unit_price":1520000,"subtotal":1520000}
{"id":44,"order_id":22,"product_id":11,"quantity":1,"unit_price":420000,"subtotal":420000}
{"id":45,"order_id":24,"product_id":8,"quantity":1,"unit_price":450000,"subtotal":450000}
{"id":46,"order_id":26,"product_id":14,"quantity":1,"unit_price":420000,"subtotal":420000}
{"id":47,"order_id":27,"product_id":5,"quantity":1,"unit_price":550000,"subtotal":550000}
{"id":48,"order_id":28,"product_id":15,"quantity":1,"unit_price":590000,"subtotal":590000}
{"id":49,"order_id":29,"product_id":9,"quantity":2,"unit_price":139000,"subtotal":278000}
{"id":50,"order_id":30,"product_id":11,"quantity":1,"unit_price":420000,"subtotal":420000}
```

---

## 4. 사용자 프롬프트 샘플 10개 + 예상 답변

| # | 사용자 질문 | 예상 SQL | 예상 답변 |
|---|------------|----------|-----------|
| 1 | "VIP 고객은 몇 명이고, 누구야?" | `SELECT id, name, email, point_balance FROM customers WHERE grade='VIP'` | VIP 고객은 5명입니다: 정민호(ID:4, 포인트 45,000), 오세훈(ID:8, 28,000), 강태영(ID:12, 32,000), 문창호(ID:16, 51,000), 황미소(ID:20, 39,000) |
| 2 | "가장 비싼 상품 3개 알려줘" | `SELECT name, brand, price FROM products ORDER BY price DESC LIMIT 3` | 1. 삼성 비스포크 냉장고 (2,150,000원), 2. 애플 아이폰 15 프로 (1,550,000원), 3. LG 그램 16인치 (1,520,000원) |
| 3 | "김민지 고객님의 총 주문 금액은?" | `SELECT SUM(o.total_amount) FROM orders o JOIN customers c ON o.customer_id=c.id WHERE c.name='김민지' AND o.status='confirmed'` | 김민지 고객님의 총 주문 금액은 2,490,000원입니다 (3건 주문). |
| 4 | "가장 많이 팔린 상품은?" | `SELECT p.name, SUM(oi.quantity) AS total_sold FROM order_items oi JOIN products p ON oi.product_id=p.id GROUP BY p.id ORDER BY total_sold DESC LIMIT 1` | 로지텍 MX 마스터 3S가 총 6개 판매되어 가장 많이 팔렸습니다. |
| 5 | "이번 달(6월) 매출은 얼마야?" | `SELECT SUM(total_amount) FROM orders WHERE strftime('%Y-%m', ordered_at)='2024-06' AND status='confirmed'` | 2024년 6월 매출은 5,180,000원입니다. |
| 6 | "리뷰가 없는 상품이 있나?" | `SELECT p.name FROM products p LEFT JOIN reviews r ON p.id=r.product_id WHERE r.id IS NULL` | 샤오미 미밴드 9, 구글 픽셀 8a 등 5개 상품에 아직 리뷰가 없습니다. |
| 7 | "실버 등급 고객 중 가장 많이 주문한 사람은?" | `SELECT c.name, COUNT(o.id) AS order_count FROM customers c JOIN orders o ON c.id=o.customer_id WHERE c.grade='SILVER' AND o.status='confirmed' GROUP BY c.id ORDER BY order_count DESC LIMIT 1` | 이현우 고객님이 2건 주문으로 실버 등급 중 가장 많이 주문했습니다. |
| 8 | "전체 평균 주문 금액은?" | `SELECT AVG(total_amount) FROM orders WHERE status='confirmed'` | 전체 평균 주문 금액은 823,333원입니다. |
| 9 | "취소된 주문이 있나? 몇 건?" | `SELECT COUNT(*) FROM orders WHERE status='cancelled'` | 취소된 주문은 총 2건입니다. |
| 10 | "애플 제품 중 재고가 50개 이상인 것 알려줘" | `SELECT name, stock_qty FROM products WHERE brand='Apple' AND stock_qty >= 50` | 애플 아이폰 15 프로 (85개)가 재고 50개 이상입니다. |

---

## 5. 프로젝트 폴더 구조 (최종)

```
nldqa-project/                          # 프로젝트 루트
├── README.md                           # 프로젝트 개요 및 실행 방법
├── requirements.txt                    # Python 의존성 목록
│
├── data/                               # ✅ 데이터 저장소
│   ├── raw/                            # 원본 JSONL 파일
│   │   ├── customers.jsonl
│   │   ├── products.jsonl
│   │   ├── orders.jsonl
│   │   └── order_items.jsonl
│   ├── techshop.db                     # SQLite DB (생성됨)
│   └── schema/                         # DB 스키마 정의
│       └── schema.sql                  # 모든 테이블 CREATE 문
│
├── scripts/                            # ✅ 실행 스크립트
│   ├── jsonl_to_sqlite.py              # JSONL → SQLite 변환
│   ├── query_executor.py               # 자연어→SQL 실행 엔진
│   └── test_queries.py                 # 테스트 쿼리 실행
│
├── .agent/                             # ✅ agentic-stack (Phase 2에서 추가)
│   ├── tools/
│   │   ├── data_layer_export.py        # 기존 Export
│   │   └── data_layer_query.py         # [신규] DB/OKF 쿼리
│   └── skills/
│       └── kdqe/
│           └── SKILL.md                # [신규] TechShop DB Query Skill
│
├── okf-kb/                             # ✅ OKF 지식베이스 (Phase 1-2에서 구축)
│   ├── index.md
│   ├── schemas/
│   │   ├── customers.md
│   │   ├── products.md
│   │   ├── orders.md
│   │   └── order_items.md
│   └── examples/
│       └── queries.md
│
├── tests/                              # ✅ 테스트
│   ├── test_queries.json               # 10개 프롬프트 + 예상 답변
│   └── test_results/                   # 실행 결과 저장
│
└── docs/                               # ✅ 문서
    ├── PRD.md                          # 프로젝트 계획서
    ├── schema_diagram.md               # ERD 및 테이블 관계도
    └── experiment_log.md               # 실험 기록
```

---

## 6. 1단계: 구체적 진행 방법

### Step 1: 프로젝트 초기화 (Day 1)

```bash
# 1. 프로젝트 디렉토리 생성
mkdir -p nldqa-project/{data/raw,scripts,tests,docs}
cd nldqa-project

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 필요 패키지 설치
pip install sqlite3 pandas pytest

# 4. requirements.txt 생성
pip freeze > requirements.txt

# 5. Git 초기화
git init
echo "venv/\ndata/techshop.db\n.agent/" > .gitignore
git add .
git commit -m "Project init: NLDQA structure"
```

### Step 2: JSONL 샘플 데이터 생성 (Day 2)

```bash
# data/raw/ 디렉토리에 위 4개 JSONL 파일 생성
# 직접 복사 붙여넣기 또는 Python 스크립트로 생성
```

### Step 3: SQLite DB 구축 (Day 3)

```python
# scripts/jsonl_to_sqlite.py 실행
python scripts/jsonl_to_sqlite.py

# 확인
sqlite3 data/techshop.db "SELECT COUNT(*) FROM customers;"
sqlite3 data/techshop.db "SELECT COUNT(*) FROM products;"
sqlite3 data/techshop.db "SELECT COUNT(*) FROM orders;"
sqlite3 data/techshop.db "SELECT COUNT(*) FROM order_items;"
```

### Step 4: 기본 SQL 쿼리 테스트 (Day 4)

```python
# scripts/test_queries.py
import sqlite3
import json

DB_PATH = "data/techshop.db"

def run_query(sql):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()
    return results

# 10개 프롬프트에 대한 SQL 실행 및 결과 확인
test_queries = [
    ("VIP 고객 목록", "SELECT id, name, email FROM customers WHERE grade='VIP'"),
    ("가장 비싼 상품 3개", "SELECT name, price FROM products ORDER BY price DESC LIMIT 3"),
    # ... 나머지 8개
]

for desc, sql in test_queries:
    result = run_query(sql)
    print(f"{desc}: {result}")
```

### Step 5: 자연어→SQL 변환 파일럿 구현 (Day 5-7)

```python
# scripts/query_executor.py (간단한 규칙 기반)
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
print(engine.query("VIP 고객은 누구야?"))
print(engine.query("가장 비싼 상품 3개 알려줘"))
```

---

## 7. 1단계 성공 기준 (Checkpoint)

| 항목 | 확인 방법 | 통과 기준 |
|------|-----------|-----------|
| ✅ DB 생성 | `sqlite3 data/techshop.db ".tables"` | customers, products, orders, order_items 출력 |
| ✅ 데이터 적재 | 각 테이블 SELECT COUNT(*) | customers≥20, products≥15, orders≥30, order_items≥50 |
| ✅ 기본 쿼리 실행 | 10개 샘플 SQL 실행 | 모두 정상 결과 반환 |
| ✅ 자연어→SQL 변환 | `query_executor.py`로 5개 이상 질문 테스트 | 80% 이상 정확도 |
| ✅ 문서화 | `docs/experiment_log.md` 작성 | 진행 상황 기록 |

---

## 8. 다음 단계 (Phase 2 이후)

1. **agentic-stack 설치 및 Data Layer 확장**
   - `.agent/` 디렉토리 생성
   - `data_layer_query.py` 구현 (SQLite + OKF 통합)
   - `kdqe` Skill 작성

2. **OKF 지식베이스 구축**
   - `okf-kb/` 디렉토리에 스키마 문서화
   - openkb로 컴파일 및 테스트

3. **Coding Agent 통합 실험**
   - Antigravity CLI에서 Skill 호출 테스트
   - 자연어 질의→SQL→응답 전체 플로우 검증

4. **전용 Agent로 전환**
   - Local LLM 기반 독립 실행형 Agent 개발
   - 성능 비교 및 최적화