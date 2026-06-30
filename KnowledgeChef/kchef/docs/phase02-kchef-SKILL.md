---
name: kchef
version: 2026-06-29
description: Unified schema and instructions for querying the TechShop e-commerce database.
triggers:
  - "VIP"
  - "고객"
  - "매출"
  - "주문"
  - "제품"
tools:
  - bash
preconditions:
  - .agent exists
constraints:
  - TechShop schema has customers, products, orders, and order_items only unless local DB inspection proves otherwise
  - Prefer read-only SELECT queries for natural-language answers
category: data
---

# kchef: TechShop E-Commerce Database Query Skill

## 📊 데이터베이스 스키마

TechShop 데이터베이스는 다음 4개 테이블로 구성됩니다:

### 1. customers (고객)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER | PK |
| email | TEXT | 이메일 |
| name | TEXT | 고객명 |
| phone | TEXT | 전화번호 |
| grade | TEXT | 등급 (VIP, GOLD, SILVER, BRONZE) |
| point_balance | INTEGER | 포인트 잔액 |
| is_active | INTEGER | 활성 여부 (1=활성, 0=비활성) |
| created_at | TEXT | 가입일 (ISO 8601) |

### 2. products (제품)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER | PK |
| name | TEXT | 제품명 |
| brand | TEXT | 브랜드 |
| sku | TEXT | 재고 관리 코드 |
| price | REAL | 판매가 |
| cost_price | REAL | 원가 |
| stock_qty | INTEGER | 재고 수량 |
| is_active | INTEGER | 판매 활성 여부 |
| created_at | TEXT | 등록일 |

### 3. orders (주문)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER | PK |
| order_number | TEXT | 주문 번호 |
| customer_id | INTEGER | 고객 ID (customers.id) |
| status | TEXT | 주문 상태 (pending, paid, shipped, delivered, cancelled) |
| total_amount | REAL | 총 주문 금액 |
| ordered_at | TEXT | 주문 일시 |

### 4. order_items (주문 상세)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER | PK |
| order_id | INTEGER | 주문 ID (orders.id) |
| product_id | INTEGER | 제품 ID (products.id) |
| quantity | INTEGER | 수량 |
| unit_price | REAL | 단가 |
| subtotal | REAL | 소계 (quantity * unit_price) |

---

## 🔍 비즈니스 규칙 (OKF 개념)

### VIP 고객 정의
- `grade = 'VIP'` 인 고객
- 관련 질문: "VIP 고객 수", "VIP 고객 목록", "VIP 고객 평균 구매액"

### 활성 고객
- `is_active = 1` 인 고객

### 최근 주문
- `ordered_at >= date('now', '-7 days')` (최근 7일)

---

## 🗣️ 자연어 → SQL 변환 패턴

| 자연어 질문 예시 | 변환될 SQL |
|-----------------|-----------|
| "VIP 고객은 몇 명이고, 누구야?" | `SELECT id, name, email FROM customers WHERE grade = 'VIP'` |
| "전체 고객 수는?" | `SELECT COUNT(*) FROM customers` |
| "가장 비싼 상품 3개" | `SELECT name, price FROM products ORDER BY price DESC LIMIT 3` |
| "카테고리별 평균 가격" | `SELECT category, AVG(price) FROM products GROUP BY category` |
| "최근 7일간 주문 목록" | `SELECT order_number, total_amount FROM orders WHERE ordered_at >= date('now', '-7 days')` |
| "VIP 고객의 평균 구매액" | `SELECT AVG(total_amount) FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.grade = 'VIP'` |

---

## 📌 응답 형식

SQL 실행 결과는 다음과 같은 자연어 형식으로 응답해야 합니다:

- **집계 질문**: "VIP 고객은 총 5명입니다."
- **목록 질문**: "VIP 고객 목록: 1. 홍길동 (hong@test.kr), 2. 김철수 (kim@test.kr), ..."
- **비교/추세**: "가장 비싼 상품은 '삼성 비스포크 냉장고'로 2,150,000원입니다."
