## OKF Bundle 및 Concept

### Bundle은 하나의 Knowledge Namespace.
  - 하나의 git repository, knowledge package, context universe
  - Bundle은 Knowledge Graph의 Forest
```
  - Bundle:
      ○────○
      │    │
      │    ○────○
      │
      ○────○
```
- Bundle을 Bounded Context 단위로 나누는 것이 좋다.
마치 DDD처럼, Engineering과 Finance가 다른 Bundle로 나뉜다.

### Concepts
- Concept는 "파일"이 아니라 "의미", 중요한 점은 orders.md라는 파일이 중요한 것이 아니라 Order라는 개념이 중요한 것입니다.
- Markdown은 그 개념을 표현하는 저장 방식일 뿐입니다.

## 자연어 기반 질의/응답 서비스를 위한 사고체계

- 질의응답 시스템을 설계할 때는 문서 중심(Document-first)이 아니라 개념 중심(Concept-first)으로 생각하는 것이 좋습니다.
```
User Question
      │
      ▼
질문을 하나 이상의 핵심 Concept로 매핑
      │
      ▼
Concept Graph를 따라 관련 Concept 탐색
      │
      ▼
필요한 Bundle 경계를 넘나들며 Context 조립
      │
      ▼
최종 답변 생성
```
```
- 지식베이스의 설계 접근법
Bundle 설계: 어떤 업무 영역(교육, 커널, 연구 등)으로 지식을 나눌 것인가?
Concept 설계: 각 영역에서 AI가 이해하고 조합해야 할 "의미 단위"는 무엇인가?
Agent는 CSV 등 data source를 직접 이해하는 것이 아니라, CSV를 설명하는 Concept를 통해 접근한다.
Planner는 Execution Plan을 만듭니다.
Knowledge Agent는 Concept 검색하고, Execution Agent는 CSV/Excel 실행, 마지막으로 Answer가 생성된다.
Knowledge Agent는 CSV/Excel 등 data를 모르고, Student/Project/
Semester/Participation 등 Concepts만 안다.
```

```
                User Question
                      │
                      ▼
            Intent / Planner Agent
                      │
          (필요한 Concept 결정)
                      │
                      ▼
            OKF Concept Graph
      (Student, Project, Semester...)
                      │
      (논리 계획: Filter, Join, Count)
                      │
                      ▼
          Execution Planner Agent
                      │
        (DuckDB / Pandas / Polars)
                      │
                      ▼
      CSV · Excel · Database · API
                      │
                      ▼
          Result + Provenance
                      │
                      ▼
             Answer Generation
```
```
Natural Language
↓
IR (Intermediate Recipe)
↓
Execution Plan
↓
Execution
```

### Progressive Knowledge Compilation

- Knowledge를 점진적으로 Compile하며 지식을 증식시켜 간다.
- Knowledge ΔK(지식 증가량)
```
Taskₙ
    │
    ▼
Artifactₙ
    │
    ├──► Product
    │
    └──► Knowledge ΔK
                │
                ▼
      Context / Rules / Skills / Recipes
                │
                ▼
           Taskₙ₊₁
```
TechLead Agent의 본질은 프로젝트 관리자가 아니라 Knowledge Curator입니다. Executor가 코드를 만들고 실행한다면, TechLead는 지식을 축적하고 재구성하여 다음 문제의 탐색 공간(Search Space)을 줄이는 역할을 합니다.
이 프레임워크 안에서 Cognitive Compiler는 각 단계의 작업을 실행 가능한 Recipe로 컴파일하는 엔진이고, TechLead Agent는 그 Compiler와 Knowledge Base를 지속적으로 진화시키는 메타 계층입니다. 즉, 당신이 설계한 방법론은 Cognitive Compiler를 포함하지만, 그보다 한 단계 상위에서 Agent와 Knowledge를 함께 성장시키는 개발 프레임워크이다.

Google에서 최근 발표한 **OKF(Open Knowledge Format)** 와 **MCP(Model Context Protocol)** 가 결합된 아키텍처 화면이군요. 이 두 가지는 AI 에이전트가 조직의 지식을 마치 사람처럼 쉽게 읽고 활용할 수 있도록 돕는 새로운 지식 인프라 표준입니다.

질문하신 세 가지 핵심 용어의 의미를 명확히 정리하고, 대학교 프로젝트 질의응답 서비스를 구축하는 구체적인 시나리오를 설명해 드리겠습니다.

---

### 1. 핵심 용어 정리: Bundle, Concept, OKF Resource

* **Bundle (번들):**
* **의미:** 연관된 지식들이 모여 있는 **하나의 전체 디렉토리(폴더)** 를 뜻합니다.
* **특징:** 복잡한 데이터베이스나 전용 API 환경이 아닌, Git 등에서 버전 관리가 가능한 단순 마크다운(Markdown) 파일들의 집합체입니다.


* **Concept (콘셉트):**
* **의미:** 번들 내에 존재하는 **개별 마크다운 파일 하나**를 의미합니다. 하나의 프로젝트, 데이터셋, 보고서 등 독립된 지식 단위를 나타냅니다.
* **특징:** 파일 상단에는 메타데이터(타입, 태그 등)를 담은 YAML Frontmatter가 위치하고, 하단에는 실제 내용이 마크다운 텍스트나 표로 작성됩니다.


* **OKF Resource (리소스):**
* **의미:** 에이전트가 특정 Concept에 접근하기 위해 사용하는 **고유 식별자 및 경로(URI)** 입니다. (이미지의 `okf://acme/weekly_active` 등)
* **특징:** MCP 서버는 물리적인 마크다운 파일(Concept)들을 에이전트가 네트워크를 통해 즉각적으로 호출할 수 있도록 이 Resource 형태로 변환하여 노출(Serve)합니다.



---

### 2. 대학 프로젝트 Q&A 서비스 구축 시나리오

**목표:** "2026년 1학기 projects에 참가한 모든 학생들의 수를 알려달라"는 질문에 정확히 답하는 에이전트 및 OKF 지식베이스 구성.

다양한 포맷(CSV, Excel, Word, PPTX)으로 흩어진 데이터를 에이전트가 즉각적으로 이해할 수 있는 OKF 기반 지식베이스로 세팅하는 구체적인 과정은 다음과 같습니다.

#### 단계 1: 데이터 추출 및 마크다운 변환 (OKF Bundle 생성)

에이전트는 원본 엑셀이나 PPTX 파일을 직접 열고 분석하는 데 리소스를 낭비하지 않습니다. 모든 데이터는 사전 파이프라인을 거쳐 정규화된 마크다운 파일(Concept)로 변환되어야 합니다.

* **정형 데이터 (CSV, Excel):** 학생 명단이나 통계 데이터는 마크다운 표(Table) 포맷으로 변환하거나, 전체 학생 수 같은 핵심 수치를 추출해 파일 상단 메타데이터에 기입합니다.
* **비정형 데이터 (Word, PPTX):** PRD(제품 요구사항 정의서)나 결과보고서는 텍스트와 핵심 구조만 추출하여 깔끔한 평문 마크다운으로 변환합니다.

#### 단계 2: 지식베이스 구조화 (Concepts 구성)

생성된 파일들을 2026년 1학기 디렉토리(Bundle)에 모으고, 에이전트가 검색하기 쉽도록 메타데이터를 부여합니다.

* **메타데이터 (YAML Frontmatter) 세팅:** 각 파일 최상단에 속성을 명시하여 에이전트가 내용을 읽지 않고도 데이터를 필터링할 수 있게 합니다.
```yaml
---
type: Project_Report
semester: "2026-1"
project_name: "AI Campus Guide"
participant_count: 5
---

```


* **Index 파일 구성:** 번들의 최상단에 `index.md`를 두어, 에이전트가 전체 프로젝트 목록과 구조를 한눈에 파악할 수 있는 진입점을 제공합니다.

#### 단계 3: MCP 서버 설정 (Serve the bundle over MCP)

* 구성이 완료된 OKF Bundle 폴더를 MCP 서버에 연결합니다.
* MCP 서버는 폴더 내부의 마크다운 파일들을 에이전트가 접근할 수 있는 리소스로 서빙합니다.
* 예: `okf://university/projects/2026-1/ai-campus-guide`
* 예: `okf://university/projects/2026-1/student_roster`



#### 단계 4: 에이전트의 질의응답 처리 원리

사용자가 질문을 던지면, 에이전트는 다음과 같이 행동합니다.

1. **목록 및 메타데이터 스캔:** MCP 파이프를 통해 `okf://university/projects/2026-1/index` 리소스에 접근하여 1학기에 진행된 프로젝트 목록을 확보합니다.
2. **데이터 수집:** 개별 프로젝트 리소스들을 호출하여 상단의 `participant_count` YAML 메타데이터를 연속으로 읽어 들입니다. (또는 명단이 담긴 마크다운 표의 행 개수를 셉니다.)
3. **답변 합성:** 획득한 숫자들을 에이전트 내부에서 합산한 뒤, "2026년 1학기에는 총 N명의 학생이 참가했습니다."라는 자연어 형태의 최종 결과를 사용자에게 반환합니다.

---

이러한 OKF와 MCP의 조합은 복잡한 벡터 DB(Vector Database) 세팅이나 청킹(Chunking) 없이도, 사람과 AI 모두가 쉽게 읽고 수정할 수 있는 직관적인 텍스트 기반 시스템을 구축할 수 있게 해줍니다.

현재 보유하고 계신 원본 문서와 데이터(CSV, PPT 등)를 마크다운으로 일괄 자동 변환하는 파이프라인 도구나 스크립트 작성에 대해서도 구체적인 가이드가 필요하신가요?