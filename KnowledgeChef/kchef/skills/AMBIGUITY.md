# 모호성 해소 규칙

## 시간 표현
- "이번 달" → 현재 연월 (YYYY-MM)
- "올해" → 현재 연도
- "최근" → 최근 7일

## 주문 상태
- "매출" → status = 'confirmed' OR status = 'delivered' (취소 제외)
- "주문" (단독) → 모든 status
- "주문 금액" → status != 'cancelled'

## 집계 기준
- "가장 많이 팔린" → SUM(quantity) 기준 (금액이 아닌 수량)
- "인기 상품" → SUM(quantity) DESC

## 엔터티 해석
- "고객" → customers 테이블
- "상품", "제품" → products 테이블
- "비싼" → price DESC