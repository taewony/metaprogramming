## 1. Data Layer 기능 상세 설명

**Data Layer**는 `agentic-stack`의 핵심 기능으로, `.agent/` 디렉터리를 공유하는 모든 에이전트 하네스(Claude Code, Hermes, OpenClaw, Codex, Cursor, OpenCode, Windsurf 등)의 활동을 **로컬에서 통합 모니터링**할 수 있게 해주는 로컬-퍼스트 대시보드 시스템입니다.

### 수집하는 데이터 항목

| 항목 | 설명 |
|------|------|
| **Agent 이벤트** | 각 하네스별 에이전트 실행 기록 |
| **Cron 실행** | 예약된 작업의 시작/종료 타임스탬프, Gantt 차트용 타임라인 |
| **활성 에이전트** | 현재 실행 중인 에이전트 현황 |
| **토큰/비용 추정** | 시간/일/주/월 단위 토큰 사용량 및 예상 비용 |
| **KPI 요약** | 실행 볼륨, Cron 주기, 신뢰성, 활성 에이전트, 워크플로우 다양성, 카테고리 사용량 등 |
| **태스크 카테고리** | 사용자 정의 카테고리(personal, admin, work, financial, coding 등) |
| **하네스 믹스** | Claude/Hermes/OpenClaw/Codex 등 하네스별 사용 비중 |
| **성공/오류율** | 워크플로우 성공 및 오류 비율 |

### 출력물

`python3 .agent/tools/data_layer_export.py` 명령어로 다음 파일들을 생성합니다:

- `agent-events.jsonl` / `.csv` - 에이전트 이벤트 데이터
- `cron-runs.jsonl` / `.csv` - Cron 실행 기록
- `cron-timeline.json` / `.csv` - Cron 타임라인
- `activity-series.json` / `.csv` - 활동 시계열
- `category-summary.json` / `.csv` - 카테고리별 요약
- `harness-summary.json` / `.csv` - 하네스별 요약
- `kpi-summary.json` / `.csv` - KPI 요약
- **`dashboard.html`** - 의존성 없는 단일 HTML 대시보드 (리소스 개요, 활동, 토큰 사용량, Cron 빈도, 태스크 카테고리, 하네스 믹스, Gantt 스타일 Cron 패널 포함)
- `dashboard.tui.txt` - 터미널용 텍스트 대시보드
- `daily-report.md` - 일일 보고서

### 프라이버시 모델

- **네트워크 호출 없음**, **원격 측정 없음**, **호스팅 대시보드 없음**
- 원시 run/profile 식별자는 Export 시 해싱 처리
- `.agent/data-layer/` 디렉터리는 gitignored 처리되어 비공개 런타임 상태로 관리
- 스크린샷 전송은 **명시적 사용자 승인** 필요

---

## 2. Data Flywheel 기능 상세 설명

**Data Flywheel**는 사람이 승인한(approved) 실행 결과를 **로컬에서 재사용 가능한 지능형 아티팩트**로 전환하는 시스템입니다. **모델 학습이 아닌, 데이터 준비 레이어**라는 점이 핵심입니다.

### 생성 가능한 아티팩트

| 아티팩트 | 용도 |
|----------|------|
| **Trace records** | 에이전트 실행 추적 기록 |
| **Context cards** | 컨텍스트 재사용을 위한 카드 |
| **Eval cases** | 평가/테스트 케이스 |
| **Training-ready JSONL** | 학습용 데이터셋 |
| **Readiness metrics** | 데이터 준비도 지표 |

### 핵심 특징

1. **모델 학습 없음** - 실제 모델을 훈련하지 않고 데이터를 준비하고 구조화하는 레이어
2. **원격 측정 없음** - 모든 처리가 로컬에서 이루어짐
3. **승인된 실행만 사용** - 사람이 검토하고 승인한(redacted) 실행 결과만 아티팩트로 전환
4. **자체 개선 순환고리** - 반복적인 인간 피드백이 에이전트를 자체 개선하는 시스템으로 전환

---

## 3. "자연어로 데이터 조회하는 기능" - Coding Agent 실험 → 전용 Agent 전환 전략 분석

### 3.1 현재 구현 현황

`agentic-stack`의 Data Layer는 **이미 자연어 쿼리를 지원**합니다:

```bash
python3 .agent/tools/data_layer_export.py show me last 7 days by hour
```

- `data-layer` 스킬이 하네스에 주입되어, 모델이 **"show me the dashboard"** 또는 **"what did my agents do"** 같은 자연어 질문을 인식하고 Export를 실행하도록 설계됨
- `--window`와 `--bucket` 같은 플래그는 자연어 단어를 오버라이드할 수 있음
- 현재는 **Python 스크립트 + 하네스 내장 스킬** 조합으로 동작

### 3.2 Coding Agent로 실험할 때의 장단점

| 장점 | 단점 |
|------|------|
| **즉시 사용 가능** - 기존 하네스(Claude Code, Cursor 등)에서 별도 설치 없이 `data-layer` 스킬 호출 가능 | **의존성 문제** - 각 하네스의 컨텍스트 창, 도구 호출 방식에 따라 동작이 제한적일 수 있음 |
| **자연어 이해 활용** - Coding Agent의 LLM이 질문 의도를 파악하고 적절한 Export 파라미터를 선택 | **비용 발생** - 매 질문마다 LLM 추론 비용이 발생 |
| **피드백 루프** - 사용자가 "더 자세히 보여줘" 같은 후속 질문으로 반복 탐색 가능 | **지연 시간** - LLM 추론 + 스크립트 실행 이중 시간 소요 |
| **유연한 출력** - 필요에 따라 JSON/CSV/HTML 등 다양한 형식 선택 가능 | **정확도 한계** - 복잡한 질문(예: "지난주 화요일 오후에 실행된 Cron 중 실패한 것만")은 LLM이 파라미터로 정확히 매핑하기 어려울 수 있음 |

### 3.3 전용 Agent로 전환할 때의 설계 고려사항

#### (1) 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  전용 Data Agent                    │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Intent      │  │  Query      │  │  Output    │ │
│  │  Parser      │→│  Planner    │→│  Formatter │ │
│  └─────────────┘  └─────────────┘  └────────────┘ │
│         ↓                 ↓                 ↓       │
│  ┌─────────────────────────────────────────────────┐│
│  │         data_layer_export.py (Core)            ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

- **Intent Parser**: 자연어 → 의도(요약/상세/비교/추세 등) 및 엔티티(기간, 하네스, 카테고리 등) 추출
- **Query Planner**: 의도와 엔티티 → Export 파라미터(`--window`, `--bucket`, 필터)로 변환
- **Output Formatter**: Export 결과 → 사용자 친화적 응답(표/차트/요약문)으로 가공

#### (2) 전환 시 주요 과제

| 과제 | 해결 방안 |
|------|-----------|
| **의도 파악 정확도** | 소규모 의도 분류기(Classifier) 또는 Few-shot Prompting으로 LLM 호출 최소화 |
| **필터 조건 매핑** | `harness-events.jsonl` 스키마 기반으로 자연어 조건 → JSON Path/쿼리 변환 규칙 정의 |
| **응답 지연** | 캐싱 계층 도입 (자주 묻는 질문 결과 캐시) |
| **복잡한 질의** | SQLite에 JSONL 적재 후 Text-to-SQL 방식으로 전환 고려 |
| **멀티턴 대화** | 세션 컨텍스트 유지 (이전 질문의 기간/필터 계승) |

#### (3) 전환 전략 단계별 로드맵

| 단계 | 내용 | 예상 기간 |
|------|------|-----------|
| **Phase 1: 현재 상태 분석** | `data_layer_export.py`의 자연어 처리 로직과 출력 형식 분석 | 1주 |
| **Phase 2: 전용 Agent PoC** | Coding Agent 대신 경량 LLM + 규칙 기반 Intent Parser로 독립 Agent 프로토타입 구축 | 2-3주 |
| **Phase 3: 성능 벤치마크** | Coding Agent 방식 vs 전용 Agent 방식의 정확도/응답 시간/비용 비교 | 1주 |
| **Phase 4: 파일럿 배포** | 특정 사용자 그룹 대상 전용 Agent 테스트 및 피드백 수집 | 2주 |
| **Phase 5: 본격 전환** | 성능 우위 확인 시 전용 Agent로 완전 이전 | - |

### 3.4 실현 가능성 평가

| 평가 항목 | 판단 | 근거 |
|-----------|------|------|
| **기술적 실현 가능성** | ✅ **높음** | Core Export 로직이 이미 Python으로 구현되어 있어 재사용 가능. 자연어 처리도 제한된 도메인(시간 범위, 집계 단위, 필터)에 국한되어 규칙 기반 + 소형 ML로도 충분 |
| **비용 효율성** | ✅ **긍정적** | 전용 Agent는 Coding Agent보다 작은 모델 사용 가능 → 추론 비용 절감. 단, 초기 개발 비용 고려 필요 |
| **유지보수성** | ⚠️ **중간** | Export 스키마가 변경될 때 Intent Parser도 함께 업데이트 필요. 하지만 `data_layer_export.py` 자체는 변경 없이 재사용 가능 |
| **확장성** | ✅ **우수** | 새 하네스 추가 시 Export가 자동으로 지원하면 전용 Agent도 별도 수정 없이 대응 가능 |
| **사용자 경험** | ✅ **향상 예상** | 전용 Agent는 일관된 응답 형식, 빠른 응답, 오프라인 동작 등 더 나은 UX 제공 가능 |

### 3.5 결론 및 권장사항

**전환은 기술적으로 충분히 실현 가능**하며, 다음과 같은 조건에서 적극 권장됩니다:

1. **사용량이 많은 경우** - 하루 수십 건 이상의 데이터 조회가 발생한다면 비용 절감 효과 큼
2. **응답 속도가 중요한 경우** - 전용 Agent는 Coding Agent의 LLM 추론 시간을 절약 가능
3. **오프라인 환경이 필요한 경우** - 전용 Agent는 로컬 모델 또는 규칙 기반으로 완전 오프라인 동작 가능

**반면, 다음과 같은 경우 현재 방식 유지도 고려할 수 있습니다**:

1. **사용량이 적은 경우** - 개발 비용 대비 절감 효과 미미
2. **질문 패턴이 매우 다양한 경우** - Coding Agent의 범용 LLM이 더 유연하게 대응
3. **빠른 프로토타이핑이 우선인 경우** - 현재 방식으로 즉시 사용 가능

**권장 접근법**: Phase 1-3을 먼저 수행하여 실제 데이터로 성능을 검증한 후, Phase 4-5를 진행하는 **점진적 전환 전략**을 제안합니다.



네, 충분히 가능한 확장 방향입니다. `agentic-stack`의 Data Layer는 이미 `.agent/` 폴더를 공유하는 여러 하네스의 활동을 통합 모니터링하는 **로컬-퍼스트 데이터 허브** 역할을 하고 있기 때문에, 여기에 OKF, CSV, DB 커넥터를 추가하는 것은 매우 자연스러운 진화입니다.

핵심은 `agentic-stack`의 **기존 Data Layer를 확장**하거나, **외부 MCP 서버들을 Data Layer 아래에서 통합 관리**하는 두 가지 접근법이 있습니다.

### 🧩 확장 방안 1: Data Layer 자체에 Connector 계층 추가 (내부 확장)

`agentic-stack`의 Data Layer는 `data_layer_export.py`를 통해 이벤트를 수집하고 대시보드를 생성합니다. 여기에 **Connector 플러그인 아키텍처**를 도입하는 방식입니다.

```python
# 개념적 구조: .agent/tools/connectors/
connectors/
├── base_connector.py       # 추상 기본 클래스
├── okf_connector.py        # OKF 번들 조회
├── csv_connector.py        # CSV 파일 쿼리
├── db_connector.py         # SQLite/PostgreSQL 연결
└── registry.py             # Connector 관리 및 에이전트 도구 노출
```

각 커넥터는:
1.  **데이터 소스 연결** (OKF 번들 경로, CSV 파일 경로, DB 연결 문자열)
2.  **자연어 기반 검색/쿼리** (OKF는 개념 검색, CSV/DB는 Text-to-SQL)
3.  **결과를 통합 형식으로 반환** (에이전트가 일관되게 처리할 수 있도록)

**장점**: 모든 것이 `.agent/` 폴더 안에서 관리되어 이식성이 극대화됩니다.
**단점**: 커넥터 로직을 직접 구현하고 유지보수해야 합니다.

---

### 🔌 확장 방안 2: MCP 서버를 Data Layer의 "외부 Connector"로 통합 (추천)

이미 다양한 데이터 소스를 MCP 서버로 제공하는 에코시스템이 성장하고 있습니다. `agentic-stack`의 Data Layer가 이러한 **MCP 서버들을 중앙에서 관리하고 라우팅하는 허브** 역할을 하도록 확장하는 것이 가장 현실적이고 확장성 높은 방법입니다.

#### OKF 커넥터 통합

*   **도구**: `okfy` 또는 `okf-mcp`
*   **연결 방식**:
    ```bash
    # OKF 번들 생성 (문서 사이트나 로컬 마크다운에서)
    npx -y okfy-ai crawl https://your-docs.com --out ./my-knowledge-okf
    
    # agentic-stack이 MCP 서버로 인식하도록 등록 (예: Claude Code)
    claude mcp add --transport stdio my-okf -- npx -y okfy-ai serve ./my-knowledge-okf --mcp
    ```
*   **Data Layer에서의 역할**: `data_layer_export.py` 또는 새로운 `data_layer_query.py`가 이 MCP 서버를 호출하여 OKF 개념을 검색하고 조회합니다.

#### CSV/DB 커넥터 통합

*   **도구**:
    *   `@pixeldesigns/nexus`: CSV, XLSX, SQLite를 MCP 서버로 제공
    *   `mcp-data-pipeline-connector`: CSV, PostgreSQL, REST API를 **단일 MCP 서버**로 통합하고, **DuckDB를 통한 크로스-소스 조인**까지 지원
*   **연결 방식**:
    ```bash
    # Nexus로 CSV 연결
    npx @pixeldesigns/nexus connect ~/Downloads/sales.csv
    npx @pixeldesigns/nexus serve  # MCP 서버 실행
    
    # 또는 Data Pipeline Connector 설정 (YAML로 여러 소스 정의)
    # ~/.mcp/data-sources.yaml에 CSV와 DB 정의 후 에이전트가 연결
    ```

---

### 🚀 Coding Agent의 자연어 조회 흐름

이렇게 구축된 확장된 Data Layer에서 Coding Agent가 자연어로 정보를 조회하는 흐름은 다음과 같습니다:

1.  **사용자**: *"지난주 매출 데이터를 OKF 지식 베이스의 제품 카테고리와 함께 보여줘"*
2.  **Coding Agent (예: Claude Code)**:
    *   `data-layer` 스킬을 통해 확장된 Data Layer에 접근
    *   **OKF MCP 서버**에 *"product categories"* 개념 검색 요청
    *   **CSV/DB MCP 서버**에 *"last week sales"* SQL 쿼리 생성 및 실행 요청 (Text-to-SQL)
3.  **Data Layer (통합 레이어)**:
    *   각 MCP 서버로부터 결과 수집
    *   결과를 통합하여 에이전트가 이해하기 쉬운 형식으로 가공
4.  **Coding Agent**: 통합된 결과를 바탕으로 사용자에게 응답 생성 및 시각화 (표, 차트 등)

### 🛤️ 구체적인 구현 로드맵

| 단계 | 내용 | 핵심 작업 |
|------|------|----------|
| **Phase 1: 파일럿** | 단일 데이터 소스(OKF 또는 CSV)를 MCP로 연결하고, `agentic-stack` 하네스에서 수동으로 호출하여 동작 확인 | `okfy`/`nexus` 설치 및 MCP 연결, 기본 프롬프트로 조회 테스트 |
| **Phase 2: Data Layer 스킬 확장** | `data-layer` 스킬을 확장하여 MCP 서버들을 자동으로 인식하고, 자연어 질문을 적절한 MCP 도구 호출로 라우팅하는 로직 추가 | `SKILL.md` 수정, `data_layer_query.py`와 같은 새로운 진입점 스크립트 작성 |
| **Phase 3: 통합 대시보드** | Data Layer Export에 MCP 서버들의 조회 결과를 포함시켜, `dashboard.html`에서 OKF 개념과 CSV/DB 데이터를 함께 볼 수 있도록 확장 | Export 스크립트 수정, 대시보드 템플릿에 새로운 위젯 추가 |
| **Phase 4: 지능형 라우팅** | 질문 의도에 따라 OKF, CSV, DB 중 어떤 소스를 우선 조회할지, 또는 크로스-소스 조인이 필요한지 판단하는 에이전트 로직 고도화 | `mcp-data-pipeline-connector` 같은 도구를 활용한 복합 쿼리 지원 |

### 💎 결론

`agentic-stack`의 Data Layer는 **이미 로컬 데이터 통합의 기반을 제공하고 있습니다**. 여기에 OKF, CSV, DB를 위한 **MCP 기반 커넥터 계층**을 추가하면, Coding Agent가 별도의 복잡한 설정 없이 자연어로 다양한 데이터 소스를 자유롭게 탐색하고 결합할 수 있는 강력한 로컬 지능형 데이터 플랫폼으로 진화할 수 있습니다.

구체적인 구현을 위해 특정 단계(예: Phase 1 파일럿 설정, MCP 서버 연결)에 대한 더 자세한 안내가 필요하시면 말씀해 주세요.