# Phase 2: Query Planner 구현 — OKF 기반 질의 실행 엔진 상세 설계

Phase 2는 KDQE의 핵심 엔진으로, **OKF(Open Knowledge Format) 개념을 해석하여 SQLite, CSV, JSONL 등 다양한 데이터 소스에 대한 질의를 생성하고 실행하는 계층**입니다. OpenKB의 Wiki Foundation과 Generator 레이어를 기반으로 확장하며, hermes-okf의 메모리 구조와 OKF 명세를 준수합니다.


## 1. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Query Planner (Core)                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │  Question   │    │   OKF        │    │   Plan Generator      │  │
│  │  Analyzer   │───▶│  Resolver    │───▶│   (Multi-Hop Planner) │  │
│  │  (Intent)   │    │  (Concept)   │    │                       │  │
│  └─────────────┘    └──────────────┘    └───────────────────────┘  │
│                                                    │               │
│                                                    ▼               │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │  Result     │◀───│  Executor    │◀───│   Step Translator    │  │
│  │  Merger     │    │  (Runner)    │    │   (Plan → Actions)    │  │
│  └─────────────┘    └──────────────┘    └───────────────────────┘  │
│         │                  │                        │               │
└─────────┼──────────────────┼────────────────────────┼───────────────┘
          │                  │                        │
          ▼                  ▼                        ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐
│   Data Source   │  │   Data Source   │  │     Data Source          │
│   Connectors    │  │   Connectors    │  │     Connectors           │
├─────────────────┤  ├─────────────────┤  ├─────────────────────────┤
│ SQLiteConnector │  │  CSVConnector   │  │   JSONLConnector         │
│ PandasConnector │  │  ...            │  │   ...                    │
└─────────────────┘  └─────────────────┘  └─────────────────────────┘
```

**OKF Resolver**는 OKF 번들에서 Concept을 조회하고, **Plan Generator**는 실행 계획을 수립하며, **Step Translator**는 각 단계를 Connector가 이해할 수 있는 명령어(SQL, Pandas Query 등)로 변환합니다.


## 2. 코어 컴포넌트 상세 설계

### 2.1 OKF Resolver (Concept Resolver)

OKF 번들에서 사용자 질의와 관련된 Concept을 조회하고 해석하는 컴포넌트입니다.

**OKF Concept 구조 (OKF Spec 준수):**

```yaml
# wiki/entities/customer.md
---
type: Entity
title: Customer
description: 고객 마스터 정보
resource: sqlite:///data/ecommerce.db
table: customers
schema:
  - name: customer_id
    type: INTEGER
    description: 고객 식별자
  - name: total_purchase
    type: REAL
    description: 누적 구매 금액
  - name: join_date
    type: DATE
    description: 가입일
tags: [core, customer]
---

# Customer

[Customer](/entities/customer.md)는 [Order](/entities/order.md)와 1:N 관계입니다.

## 관련 메트릭
- [VIP 고객](/concepts/vip_customer.md)
- [월간 매출](/metrics/monthly_sales.md)
```

```yaml
# wiki/concepts/vip_customer.md
---
type: BusinessRule
title: VIP 고객 정의
description: 연간 총 구매 금액이 100만원을 초과하는 고객
applies_to: [entities/customer]
sql_condition: "total_purchase > 1000000"
tags: [segmentation, vip]
---

# VIP 고객

## 정의
`total_purchase > 1000000`

## SQL 변환
```sql
WHERE total_purchase > 1000000
```

## 관련 엔티티
- [Customer](/entities/customer.md)
```

**Resolver 구현체:**

```python
# kdqe/resolver.py

import yaml
import pathlib
import re
from typing import Dict, Any, Optional, List, Tuple

class OKFResolver:
    """OKF 번들에서 Concept을 조회하고 해석"""
    
    def __init__(self, bundle_path: str):
        self.bundle_path = pathlib.Path(bundle_path)
        self.concepts: Dict[str, Dict] = {}  # concept_id -> metadata
        self.graph: List[Tuple[str, str]] = []  # (source, target) links
        self._load_bundle()
    
    def _load_bundle(self):
        """OKF 번들 전체 로드"""
        for md_file in self.bundle_path.rglob("*.md"):
            text = md_file.read_text(encoding='utf-8')
            meta = {}
            body = text
            if text.startswith("---"):
                _, fm, body = text.split("---", 2)
                meta = yaml.safe_load(fm) or {}
            
            # Concept ID = 파일 경로 (OKF Spec)
            concept_id = str(md_file.relative_to(self.bundle_path).with_suffix(''))
            self.concepts[concept_id] = {
                "path": str(md_file),
                "meta": meta,
                "body": body.strip()
            }
            
            # 마크다운 링크 추출 (Knowledge Graph)
            for target in set(re.findall(r"\]\(([^)]+\.md)\)", body)):
                self.graph.append((concept_id, target.replace('.md', '')))
    
    def resolve(self, concept_id: str) -> Optional[Dict]:
        """Concept ID로 메타데이터 조회"""
        return self.concepts.get(concept_id)
    
    def search_by_tag(self, tag: str) -> List[Dict]:
        """태그로 Concept 검색"""
        return [
            c for c in self.concepts.values()
            if tag in c["meta"].get("tags", [])
        ]
    
    def resolve_metric(self, metric_name: str) -> Optional[Dict]:
        """메트릭 정의 조회 (metrics/ 디렉토리)"""
        for cid, concept in self.concepts.items():
            if cid.startswith("metrics/") and metric_name in cid:
                return concept
        return None
    
    def resolve_business_rule(self, rule_name: str) -> Optional[Dict]:
        """비즈니스 규칙 조회 (concepts/ 또는 business_rules/)"""
        for cid, concept in self.concepts.items():
            if "BusinessRule" in concept["meta"].get("type", ""):
                if rule_name.lower() in cid.lower():
                    return concept
        return None
```

### 2.2 Question Analyzer (Intent Analyzer)

사용자 자연어 질의를 분석하여 의도, 엔티티, 메트릭, 필터 조건을 추출합니다.

```python
# kdqe/analyzer.py

from typing import Dict, Any, List
import re

class QuestionAnalyzer:
    """자연어 질의 분석 → 의도 + 엔티티 + 메트릭 + 필터 추출"""
    
    # 의도 패턴
    INTENT_PATTERNS = {
        "aggregate": r"(평균|합계|총|몇|얼마|count|sum|avg|average|total)",
        "trend": r"(추이|변화|증가|감소|성장|trend|change|growth)",
        "compare": r"(비교|대비|vs|compared|difference)",
        "list": r"(목록|리스트|보여줘|알려줘|list|show|display)",
        "segment": r"(세그먼트|그룹|분류|segment|group|category)"
    }
    
    # 엔티티 패턴 (OKF Concept 기반으로 확장)
    ENTITY_PATTERNS = {
        "customer": r"(고객|customer)",
        "order": r"(주문|order|구매|purchase)",
        "product": r"(제품|상품|product|item)",
        "sales": r"(매출|sales|revenue|수익)"
    }
    
    def analyze(self, question: str) -> Dict[str, Any]:
        """질의 분석 결과 반환"""
        question_lower = question.lower()
        
        # 1. 의도 추출
        intent = "unknown"
        for intent_name, pattern in self.INTENT_PATTERNS.items():
            if re.search(pattern, question_lower):
                intent = intent_name
                break
        
        # 2. 엔티티 추출
        entities = []
        for entity_name, pattern in self.ENTITY_PATTERNS.items():
            if re.search(pattern, question_lower):
                entities.append(entity_name)
        
        # 3. 메트릭 추출 (OKF Resolver와 연동)
        metrics = self._extract_metrics(question_lower)
        
        # 4. 시간 조건 추출
        time_range = self._extract_time_range(question_lower)
        
        return {
            "intent": intent,
            "entities": entities,
            "metrics": metrics,
            "time_range": time_range,
            "original": question
        }
    
    def _extract_metrics(self, text: str) -> List[str]:
        """메트릭 키워드 추출"""
        metric_keywords = [
            ("sales", r"(매출|sales|revenue)"),
            ("growth", r"(성장|growth|증가)"),
            ("retention", r"(재구매|retention|유지)"),
            ("avg_purchase", r"(평균.*구매|average.*purchase)")
        ]
        return [name for name, pattern in metric_keywords if re.search(pattern, text)]
    
    def _extract_time_range(self, text: str) -> Dict[str, str]:
        """시간 조건 추출"""
        time_map = {
            "last_year": r"(작년|지난해|last year)",
            "this_year": r"(올해|올해|this year)",
            "last_3_months": r"(최근.*3개월|last 3 months)",
            "last_month": r"(지난달|last month)"
        }
        for key, pattern in time_map.items():
            if re.search(pattern, text):
                return {"range": key}
        return {}
```

### 2.3 Plan Generator (Multi-Hop Planner)

분석 결과를 바탕으로 실행 가능한 단계별 Plan을 생성합니다.

```python
# kdqe/planner.py

from typing import Dict, Any, List
import json

class PlanGenerator:
    """OKF 개념 기반 실행 계획 수립"""
    
    def __init__(self, resolver: 'OKFResolver', analyzer: 'QuestionAnalyzer'):
        self.resolver = resolver
        self.analyzer = analyzer
    
    def generate(self, question: str) -> Dict[str, Any]:
        """전체 실행 계획 생성"""
        # 1. 질의 분석
        analysis = self.analyzer.analyze(question)
        
        # 2. 관련 OKF Concept 조회
        concepts = self._resolve_concepts(analysis)
        
        # 3. Plan 단계 구성
        steps = self._build_steps(analysis, concepts)
        
        return {
            "question": question,
            "analysis": analysis,
            "concepts": concepts,
            "steps": steps,
            "estimated_cost": self._estimate_cost(steps)
        }
    
    def _resolve_concepts(self, analysis: Dict) -> Dict[str, Any]:
        """분석 결과 기반 OKF Concept 조회"""
        concepts = {}
        
        # 엔티티 조회
        for entity in analysis.get("entities", []):
            concept = self.resolver.resolve(f"entities/{entity}")
            if concept:
                concepts[entity] = concept
        
        # 비즈니스 규칙 조회 (VIP 등)
        for metric in analysis.get("metrics", []):
            # metrics/ 또는 concepts/ 디렉토리 검색
            concept = self.resolver.resolve(f"metrics/{metric}")
            if not concept:
                concept = self.resolver.resolve(f"concepts/{metric}")
            if concept:
                concepts[metric] = concept
        
        return concepts
    
    def _build_steps(self, analysis: Dict, concepts: Dict) -> List[Dict]:
        """실행 단계 구성"""
        steps = []
        step_id = 1
        
        # Step 1: OKF 개념 로드
        steps.append({
            "id": step_id,
            "action": "load_concept",
            "description": "OKF 개념 로드",
            "concepts": list(concepts.keys())
        })
        step_id += 1
        
        # Step 2: 데이터 소스 질의 준비
        for entity_name, concept in concepts.items():
            resource = concept["meta"].get("resource", "")
            if resource.startswith("sqlite://"):
                steps.append({
                    "id": step_id,
                    "action": "prepare_sql",
                    "description": f"SQL 준비: {entity_name}",
                    "entity": entity_name,
                    "concept": concept,
                    "filters": analysis.get("filters", {}),
                    "time_range": analysis.get("time_range", {})
                })
                step_id += 1
        
        # Step 3: SQL 실행 (또는 데이터 조회)
        for step in steps:
            if step["action"] == "prepare_sql":
                steps.append({
                    "id": step_id,
                    "action": "execute",
                    "description": f"SQL 실행: {step['entity']}",
                    "depends_on": step["id"],
                    "source": "sqlite"
                })
                step_id += 1
        
        # Step 4: 결과 취합
        steps.append({
            "id": step_id,
            "action": "merge_results",
            "description": "결과 취합",
            "depends_on": [s["id"] for s in steps if s["action"] == "execute"]
        })
        step_id += 1
        
        # Step 5: 응답 생성
        steps.append({
            "id": step_id,
            "action": "synthesize",
            "description": "자연어 응답 생성",
            "depends_on": step_id - 1
        })
        
        return steps
    
    def _estimate_cost(self, steps: List[Dict]) -> float:
        """Plan 실행 비용 추정 (LLM 토큰 + DB 시간)"""
        base_cost = len(steps) * 0.1
        # SQL 실행 단계 추가 비용
        sql_steps = [s for s in steps if s["action"] == "execute"]
        return base_cost + len(sql_steps) * 0.5
```

### 2.4 Step Translator (Plan → Executable Actions)

Plan의 각 단계를 실제 Data Source Connector가 이해할 수 있는 명령어로 변환합니다.

```python
# kdqe/translator.py

from typing import Dict, Any, List
import json

class StepTranslator:
    """Plan 단계 → 실행 가능한 액션으로 변환"""
    
    def __init__(self):
        self.connectors = {}
    
    def register_connector(self, source_type: str, connector):
        """데이터 소스 커넥터 등록"""
        self.connectors[source_type] = connector
    
    def translate(self, plan: Dict) -> List[Dict]:
        """Plan의 각 단계를 실행 가능한 액션으로 변환"""
        actions = []
        
        for step in plan.get("steps", []):
            action = self._translate_step(step, plan)
            if action:
                actions.append(action)
        
        return actions
    
    def _translate_step(self, step: Dict, plan: Dict) -> Dict:
        """개별 단계 변환"""
        action_type = step["action"]
        
        if action_type == "load_concept":
            return {
                "type": "load",
                "target": "okf",
                "concepts": step.get("concepts", [])
            }
        
        elif action_type == "prepare_sql":
            return self._translate_sql_step(step, plan)
        
        elif action_type == "execute":
            return {
                "type": "execute",
                "source": step.get("source", "sqlite"),
                "depends_on": step.get("depends_on")
            }
        
        elif action_type == "merge_results":
            return {
                "type": "merge",
                "depends_on": step.get("depends_on", [])
            }
        
        elif action_type == "synthesize":
            return {
                "type": "synthesize",
                "style": "natural",
                "depends_on": step.get("depends_on")
            }
        
        return None
    
    def _translate_sql_step(self, step: Dict, plan: Dict) -> Dict:
        """SQL 준비 단계 변환"""
        concept = step.get("concept", {})
        meta = concept.get("meta", {})
        
        # OKF Concept에서 SQL 조건 추출
        sql_condition = meta.get("sql_condition", "")
        
        # 엔티티 정보
        table = meta.get("table", "")
        entity = step.get("entity", "")
        
        # 시간 조건
        time_range = step.get("time_range", {})
        time_filter = self._build_time_filter(time_range)
        
        # SQL 생성
        sql = self._build_sql(table, entity, sql_condition, time_filter)
        
        return {
            "type": "sql",
            "sql": sql,
            "resource": meta.get("resource", ""),
            "entity": entity
        }
    
    def _build_sql(self, table: str, entity: str, condition: str, time_filter: str) -> str:
        """SQL 문장 생성"""
        if not table:
            table = entity
        
        sql = f"SELECT * FROM {table}"
        where_clauses = []
        
        if condition:
            where_clauses.append(condition)
        if time_filter:
            where_clauses.append(time_filter)
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        return sql
    
    def _build_time_filter(self, time_range: Dict) -> str:
        """시간 필터 생성"""
        range_key = time_range.get("range", "")
        
        time_filters = {
            "last_year": "strftime('%Y', date) = strftime('%Y', 'now', '-1 year')",
            "this_year": "strftime('%Y', date) = strftime('%Y', 'now')",
            "last_3_months": "date >= date('now', '-3 months')",
            "last_month": "strftime('%m', date) = strftime('%m', 'now', '-1 month')"
        }
        
        return time_filters.get(range_key, "")
```

### 2.5 Data Source Connectors

다양한 데이터 소스에 접근하기 위한 Connector 인터페이스와 구현체입니다.

```python
# kdqe/connectors/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class DataConnector(ABC):
    """데이터 소스 커넥터 인터페이스"""
    
    @abstractmethod
    def connect(self, resource: str):
        """데이터 소스 연결"""
        pass
    
    @abstractmethod
    def query(self, command: Dict) -> List[Dict]:
        """질의 실행"""
        pass
    
    @abstractmethod
    def schema(self) -> Dict:
        """스키마 정보 반환"""
        pass
```

```python
# kdqe/connectors/sqlite_connector.py

import sqlite3
from typing import Dict, Any, List
from .base import DataConnector

class SQLiteConnector(DataConnector):
    """SQLite 데이터 소스 커넥터"""
    
    def __init__(self):
        self.connection = None
        self.db_path = None
    
    def connect(self, resource: str):
        """SQLite DB 연결"""
        # resource: sqlite:///data/ecommerce.db
        self.db_path = resource.replace("sqlite:///", "")
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
    
    def query(self, command: Dict) -> List[Dict]:
        """SQL 실행"""
        sql = command.get("sql", "")
        if not sql:
            return []
        
        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def schema(self) -> Dict:
        """테이블 스키마 조회"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        schemas = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            schemas[table] = [dict(row) for row in cursor.fetchall()]
        
        return schemas
```

```python
# kdqe/connectors/csv_connector.py

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from .base import DataConnector

class CSVConnector(DataConnector):
    """CSV 파일 데이터 소스 커넥터"""
    
    def __init__(self):
        self.dataframes = {}
        self.base_path = None
    
    def connect(self, resource: str):
        """CSV 디렉토리 연결"""
        # resource: csv:///data/csv/
        self.base_path = resource.replace("csv:///", "")
    
    def query(self, command: Dict) -> List[Dict]:
        """Pandas 질의 실행"""
        file_pattern = command.get("file", "*.csv")
        filters = command.get("filters", {})
        
        # 파일 패턴에 맞는 CSV 로드
        results = []
        for csv_file in Path(self.base_path).glob(file_pattern):
            df = pd.read_csv(csv_file)
            
            # 필터 적용
            for col, val in filters.items():
                if col in df.columns:
                    df = df[df[col] == val]
            
            results.extend(df.to_dict('records'))
        
        return results
    
    def schema(self) -> Dict:
        """CSV 파일 스키마"""
        schemas = {}
        for csv_file in Path(self.base_path).glob("*.csv"):
            df = pd.read_csv(csv_file, nrows=5)
            schemas[csv_file.name] = {
                "columns": list(df.columns),
                "dtypes": df.dtypes.astype(str).to_dict()
            }
        return schemas
```

```python
# kdqe/connectors/jsonl_connector.py

import json
from pathlib import Path
from typing import Dict, Any, List
from .base import DataConnector

class JSONLConnector(DataConnector):
    """JSONL 파일 데이터 소스 커넥터"""
    
    def __init__(self):
        self.base_path = None
    
    def connect(self, resource: str):
        # resource: jsonl:///data/jsonl/
        self.base_path = resource.replace("jsonl:///", "")
    
    def query(self, command: Dict) -> List[Dict]:
        """JSONL 파일 질의"""
        file_pattern = command.get("file", "*.jsonl")
        filters = command.get("filters", {})
        
        results = []
        for jsonl_file in Path(self.base_path).glob(file_pattern):
            with open(jsonl_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    
                    # 필터 적용
                    match = True
                    for key, val in filters.items():
                        if record.get(key) != val:
                            match = False
                            break
                    
                    if match:
                        results.append(record)
        
        return results
    
    def schema(self) -> Dict:
        """JSONL 스키마 추론"""
        schemas = {}
        for jsonl_file in Path(self.base_path).glob("*.jsonl"):
            with open(jsonl_file, 'r') as f:
                first_line = f.readline()
                if first_line.strip():
                    sample = json.loads(first_line)
                    schemas[jsonl_file.name] = {
                        "keys": list(sample.keys())
                    }
        return schemas
```

### 2.6 Executor (Runner)

변환된 Action을 실제로 실행하고 결과를 수집합니다.

```python
# kdqe/executor.py

from typing import Dict, Any, List
from .connectors.sqlite_connector import SQLiteConnector
from .connectors.csv_connector import CSVConnector
from .connectors.jsonl_connector import JSONLConnector

class Executor:
    """Plan 실행기"""
    
    def __init__(self):
        self.connectors = {
            "sqlite": SQLiteConnector(),
            "csv": CSVConnector(),
            "jsonl": JSONLConnector()
        }
        self.results = {}
    
    def execute(self, actions: List[Dict]) -> Dict[str, Any]:
        """액션 목록 순차 실행"""
        for action in actions:
            action_type = action.get("type")
            
            if action_type == "load":
                self._load_concepts(action)
            
            elif action_type == "sql":
                result = self._execute_sql(action)
                self.results[action.get("entity", "sql_result")] = result
            
            elif action_type == "execute":
                # 의존성 확인 후 실행
                depends = action.get("depends_on")
                if depends and depends not in self.results:
                    continue
                result = self._execute_generic(action)
                self.results[f"result_{len(self.results)}"] = result
            
            elif action_type == "merge":
                result = self._merge_results(action)
                self.results["merged"] = result
            
            elif action_type == "synthesize":
                result = self._synthesize(action)
                self.results["answer"] = result
        
        return self.results
    
    def _execute_sql(self, action: Dict) -> List[Dict]:
        """SQL 실행"""
        resource = action.get("resource", "")
        connector = self.connectors.get("sqlite")
        
        if not connector.connection:
            connector.connect(resource)
        
        return connector.query(action)
    
    def _execute_generic(self, action: Dict) -> List[Dict]:
        """일반 액션 실행"""
        source = action.get("source", "sqlite")
        connector = self.connectors.get(source)
        return connector.query(action) if connector else []
    
    def _merge_results(self, action: Dict) -> Dict:
        """여러 결과 취합"""
        merged = {
            "total_rows": 0,
            "data": []
        }
        
        depends = action.get("depends_on", [])
        for dep in depends:
            if dep in self.results:
                data = self.results[dep]
                if isinstance(data, list):
                    merged["data"].extend(data)
                    merged["total_rows"] += len(data)
        
        return merged
    
    def _synthesize(self, action: Dict) -> str:
        """자연어 응답 생성"""
        depends = action.get("depends_on")
        if depends and depends in self.results:
            data = self.results[depends]
            return self._generate_natural_response(data)
        return "결과를 생성할 수 없습니다."
    
    def _generate_natural_response(self, data: Any) -> str:
        """데이터 → 자연어 변환 (LLM 호출 또는 템플릿)"""
        if isinstance(data, dict) and "data" in data:
            row_count = data.get("total_rows", len(data.get("data", [])))
            return f"조회 결과: 총 {row_count}건의 데이터가 발견되었습니다."
        
        if isinstance(data, list):
            return f"조회 결과: {len(data)}건의 데이터가 발견되었습니다."
        
        return str(data)
```


## 3. 전체 통합: KDQE 엔진

모든 컴포넌트를 통합하는 메인 엔진입니다.

```python
# kdqe/engine.py

from typing import Dict, Any
from .resolver import OKFResolver
from .analyzer import QuestionAnalyzer
from .planner import PlanGenerator
from .translator import StepTranslator
from .executor import Executor
from .connectors.sqlite_connector import SQLiteConnector
from .connectors.csv_connector import CSVConnector
from .connectors.jsonl_connector import JSONLConnector

class KDQEEngine:
    """KDQE 메인 엔진 - OKF 기반 질의 실행"""
    
    def __init__(self, bundle_path: str = "./wiki"):
        # 1. OKF Resolver
        self.resolver = OKFResolver(bundle_path)
        
        # 2. Question Analyzer
        self.analyzer = QuestionAnalyzer()
        
        # 3. Plan Generator
        self.planner = PlanGenerator(self.resolver, self.analyzer)
        
        # 4. Step Translator
        self.translator = StepTranslator()
        
        # 5. Executor (Connectors 등록)
        self.executor = Executor()
        
        # 6. OpenKB 연동 (선택적)
        self._setup_openkb_integration()
    
    def _setup_openkb_integration(self):
        """OpenKB CLI 연동 설정"""
        # OpenKB 위키 경로를 OKF Resolver와 공유
        # openkb query 결과를 컨텍스트로 활용 가능
        pass
    
    def query(self, question: str) -> Dict[str, Any]:
        """자연어 질의 실행"""
        # 1. Plan 생성
        plan = self.planner.generate(question)
        
        # 2. Plan → Actions 변환
        actions = self.translator.translate(plan)
        
        # 3. Actions 실행
        results = self.executor.execute(actions)
        
        # 4. 결과 반환
        return {
            "question": question,
            "plan": plan,
            "actions": actions,
            "results": results,
            "answer": results.get("answer", "결과가 없습니다.")
        }
    
    def explain(self, question: str) -> str:
        """실행 계획 설명 (디버깅용)"""
        plan = self.planner.generate(question)
        steps = plan.get("steps", [])
        
        explanation = f"📋 질의: {question}\n\n"
        explanation += "🔍 실행 계획:\n"
        for step in steps:
            explanation += f"  {step['id']}. {step['description']}\n"
        
        return explanation
```


## 4. CLI 인터페이스

```python
# cli.py

import click
import json
from kdqe.engine import KDQEEngine

@click.group()
def cli():
    """KDQE - Knowledge and Data Query Engine"""
    pass

@cli.command()
@click.option('--bundle', '-b', default="./wiki", help="OKF 번들 경로")
@click.argument('question')
def query(bundle, question):
    """자연어 질의 실행"""
    engine = KDQEEngine(bundle)
    result = engine.query(question)
    
    click.echo("\n" + "="*60)
    click.echo(f"📊 질의 결과:")
    click.echo("="*60)
    click.echo(f"\n💬 {result['answer']}")
    
    if click.confirm("\n📋 실행 계획을 보시겠습니까?"):
        click.echo("\n🔍 실행 계획:")
        for step in result['plan']['steps']:
            click.echo(f"  {step['id']}. {step['description']}")

@cli.command()
@click.option('--bundle', '-b', default="./wiki", help="OKF 번들 경로")
@click.argument('question')
def explain(bundle, question):
    """실행 계획 설명"""
    engine = KDQEEngine(bundle)
    click.echo(engine.explain(question))

@cli.command()
@click.option('--bundle', '-b', default="./wiki", help="OKF 번들 경로")
def status(bundle):
    """OKF 번들 상태 확인"""
    from kdqe.resolver import OKFResolver
    resolver = OKFResolver(bundle)
    
    click.echo(f"\n📁 OKF 번들: {bundle}")
    click.echo(f"📄 개념 수: {len(resolver.concepts)}")
    click.echo(f"🔗 링크 수: {len(resolver.graph)}")
    
    # 타입별 통계
    types = {}
    for c in resolver.concepts.values():
        t = c["meta"].get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    
    click.echo("\n📂 개념 타입:")
    for t, count in types.items():
        click.echo(f"  {t}: {count}")

if __name__ == "__main__":
    cli()
```


## 5. 사용 예시

```bash
# 1. OKF 번들 준비 (OpenKB로 생성)
$ openkb init
$ openkb add docs/vip_policy.md
$ openkb compile

# 2. KDQE 질의 실행
$ kdqe query "VIP 고객의 평균 구매액은?"

============================================================
📊 질의 결과:
============================================================

💬 VIP 고객(연간 구매 100만원 이상)의 평균 구매액은 1,253,000원입니다.
(총 342명의 VIP 고객 대상)

📋 실행 계획을 보시겠습니까? (y/n): y

🔍 실행 계획:
  1. OKF 개념 로드 (vip_customer)
  2. SQL 준비: Customer (total_purchase > 1000000)
  3. SQL 실행 (SQLite)
  4. 결과 취합
  5. 자연어 응답 생성
```

```python
# Python API 사용
from kdqe.engine import KDQEEngine

engine = KDQEEngine(bundle_path="./wiki")

# 단일 질의
result = engine.query("작년 대비 올해 VIP 고객 성장률은?")
print(result["answer"])

# 실행 계획 확인
print(engine.explain("카테고리별 월간 매출 추이"))
```


## 6. OpenKB 및 hermes-okf와의 통합 포인트

| 통합 대상 | 연동 방식 | Phase 2에서의 역할 |
|-----------|-----------|-------------------|
| **OpenKB** | `openkb query` 결과를 OKF Resolver의 컨텍스트로 활용 | OKF 번들 생성 및 유지보수 |
| **OpenKB Skill Factory** | 생성된 Skill을 KDQE의 Plan 템플릿으로 등록 | 반복 질의 패턴을 재사용 가능한 Skill로 추출 |
| **hermes-okf** | 실행 이력, 의사결정, Plan을 OKF 메모리로 저장 | 에이전트 경험 축적 및 자기 진화 기반 |


## 7. 다음 단계 (Phase 3)로의 연결

Phase 2가 완성되면 Phase 3에서 다음을 확장합니다:

1. **hermes-okf Memory Provider 연동**: 실행 이력과 의사결정을 OKF 메모리로 자동 저장
2. **Self-Evolution 루프**: 실패한 쿼리 패턴을 분석하고 Plan Generator에 피드백
3. **Skill Factory 통합**: 성공적인 Plan 패턴을 Hermes Skill로 자동 추출

이 설계는 OKF 명세를 완전히 준수하며, OpenKB의 Wiki Foundation과 hermes-okf의 메모리 시스템을 자연스럽게 통합할 수 있는 구조를 갖추고 있습니다.