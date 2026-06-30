```
Sports 감독이 break-time에서 선수들의 역량과 현재 경기상황에 따라 작전지시를 선수들에게 하면서, 일종의 시합을 어떻게 풀어갈지 mental reharsal(simultion)을 함께 하는데,

우리의 Knowledge-Chef 혹은 Cognitive-Knowledge-OS 체계에서는 어떻게 주어진 user 질의에 대해

지식베이스 및 data store에서 원하는 fact들을 찾아 user가 원하는 응답을 만들지,

pattern matching 혹은 Solution Space Search 혹은 Query Language로 변환할지 planning을 어떻게 할지 전문가인 당신이 agent 구현 측면에서 체계적인 가이드를 해줘.

구체적으로 무엇을 만들어야 하는지 실현 가능한 설계 방안을 제시해줘. 필요한 SKILL.md를 작성해 주고, 필요한 python script의 skeleton code를 제시해 주고, Agent가 여러개라면, 어떤 역할을 하는 것인지 어떤 agent-loop를 실행하는지 자세히 설명해줘
```
## 1. ‘Mental Rehearsal’에서 ‘Cognitive Rehearsal’로: OKF 체계의 Planning

스포츠 감독이 break-time에 선수들의 능력과 경기 상황을 머릿속으로 시뮬레이션하며 작전을 지시하는 것처럼, **Cognitive-Knowledge-OS**의 Planner Agent는 사용자 질의를 받아 **지식베이스의 구조(index.md)와 데이터를 머릿속으로 탐색**하며 최적의 실행 계획을 수립합니다.

- **감독** = **Planner Agent** (혹은 Cognitive Compiler): 경기장(OKF 지식 공간)을 이해하고, 선수(데이터·문서)의 능력을 알고 있으며, 작전(Knowledge IR)을 만듭니다.
- **선수** = **Knowledge VM + Executor Agent**: 작전을 실제로 수행하여 결과를 가져옵니다.
- **Mental Rehearsal** = **Planner Agent 내부에서 발생하는 3단계 시뮬레이션**:
    1. **Query Analysis**: 사용자 질문을 분해하여 필요한 정보 조각(Goal, Constraints)을 추출합니다.
    2. **Knowledge Space Exploration**: OKF의 계층적 `index.md` 심볼 테이블을 순회하며 목표를 만족할 수 있는 데이터 경로를 탐색합니다. (Solution Space Search)
    3. **Execution Plan Synthesis**: 찾아낸 경로를 하나의 Knowledge IR(중간 표현)로 조립합니다.

이것이 완료되면, Executor는 IR을 Knowledge VM에 넘겨 결정론적으로 실행합니다.

---

## 2. 전체 아키텍처: Dual-Agent Rehearsal Loop

```text
USER QUESTION
       │
       ▼
┌─────────────────────────┐
│   PLANNER AGENT          │  ← Cognitive Compiler (Mental Rehearsal)
│  • Query Analysis        │
│  • Index.md Traversal    │
│  • IR Synthesis          │
└───────────┬─────────────┘
            │ Knowledge IR (Recipe)
            ▼
┌─────────────────────────┐
│   EXECUTOR AGENT          │  ← Knowledge VM Runner
│  • IR Interpreter         │
│  • Data Access Drivers    │
│  • Result Aggregation     │
└───────────┬─────────────┘
            │ Answer
            ▼
        USER
```

이 구조는 **Planner가 Runtime 이전에 모든 ‘생각’을 끝내는 정적 컴파일 방식**을 취합니다.  
(필요시 Executor가 오류를 Planner에게 보고하고, Planner가 IR을 수정하는 **Re-planning Loop**도 추가할 수 있습니다.)

---

## 3. SKILL.md: Planner Agent의 두뇌 지침

Planner Agent에게 주입할 `SKILL.md` 파일 예시입니다.  
이 지침이 곧 “감독의 작전 노트”가 됩니다.

```markdown
# SKILL: Cognitive Query Planner

## Role
You are the **Cognitive Rehearsal Planner** of a Knowledge Operating System.
Your sole task is to convert a natural language question into a structured **Knowledge IR** that an Executor can run blindly.

## The Knowledge Space (OKF Bundle)
The knowledge base is a hierarchical OKF bundle.
- Each directory contains an `index.md` acting as a **symbol table**.
- The symbol table lists concepts, data files (csv, xlsx), and documents, with their keys and paths.
- Relationships between concepts are described in the concept markdown files.

## Rehearsal Steps (You MUST follow these)

### Step 1: Parse the Question
Extract from the user question:
- `goal`: one of COUNT, LIST, SUMMARY, COMPARE, TREND
- `target_concept`: e.g., "student", "project", "budget"
- `constraints`: key-value pairs, e.g., {semester: "2026-1", department: "컴퓨터공학과"}
- `output_structure`: what fields should the answer contain.

### Step 2: Explore the Knowledge Space (Mental Simulation)
You have access to the tool `read_index(path)` and `search_hierarchy(keywords)`.
Simulate the exploration in your mind (or by actually calling these tools in sequence):
1. Read the root `.okf_domain/index.md` to know top-level structure.
2. Descend into the relevant branch (e.g., "semesters/2026-1") using constraint values.
3. Inside the branch's `index.md`, locate the target concept and its data sources.
4. If multiple data sources are needed, plan a **traversal chain** (e.g., semester → project → participation → student).
5. For each data source, note the exact file path and the filter columns.

### Step 3: Synthesize the Knowledge IR
Create a JSON object following this schema:
{
  "goal": "COUNT",
  "target": "student_id",
  "constraints": {"semester_id": "2026-1"},
  "traversal": [
    {"type": "index", "path": "semesters/2026-1/index.md"},
    {"type": "data", "path": "data/2026-1/projects.csv", "filter": {"semester_id": "2026-1"}},
    {"type": "data", "path": "data/project_participation.csv", "join_on": "project_id"},
    {"type": "data", "path": "data/students.csv", "join_on": "student_id"}
  ],
  "aggregation": "count(distinct student_id)"
}
If a text summary is needed, include a `content_extraction` block pointing to documents.

### Step 4: Simulate & Validate
Before outputting the IR, mentally simulate the execution:
- Does every `traversal` step have a concrete file path?
- Are all necessary columns present in those files? (You can assume the schema is as described in the index.md.)
- Will the aggregation produce exactly the `output_structure`?
If not, revise the IR.

### Output Format
Your final response must be ONLY the Knowledge IR JSON. No extra text.

### Tools Available
- `read_index(path)`: returns the contents of an index.md file (sections parsed).
- `search_hierarchy(keywords, base_path)`: returns list of matching index sections with paths.
```

> **핵심**: Planner는 “실행하지 않고 시뮬레이션만” 합니다. 도구를 호출하여 OKF 구조를 확인할 수는 있지만, 실제 CSV를 읽거나 집계하지는 않습니다. 이는 컴파일 타임에 타입 체크만 하는 것과 같습니다.

---

## 4. SKILL.md: Executor Agent (VM Runner)

```markdown
# SKILL: Knowledge IR Executor

## Role
You are the **Execution Engine** of a Knowledge Operating System.
You receive a **Knowledge IR** and must execute it exactly as specified, returning a structured answer.

## Execution Rules
- Process the `traversal` steps in order.
- For `type: "index"`, skip (already used by Planner); you may verify existence.
- For `type: "data"`, use the `query_data(path, operation, ...)` tool with the given filters and joins.
- For `type: "document"`, use `extract_text(path)` to get content, then `summarize(content, instruction)`.
- Apply `aggregation` as the final step.

## Tools
- `query_data(path, filter=None, join=None, columns=None)`: returns a DataFrame.
- `extract_text(path)`: returns string content from docx/pptx.
- `summarize(text, instruction)`: returns a concise summary.

## Output
Your final output must be a JSON object:
{
  "result": { ... },  // the structured data
  "summary": "natural language answer",
  "citations": ["list of paths used"]
}
```

---

## 5. Python Skeleton Code (Planner, Executor, Agent Loop)

### 5.1 Knowledge IR Schema (Pydantic)

```python
# schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class TraversalStep(BaseModel):
    type: Literal["index", "data", "document"]
    path: str
    filter: Optional[Dict[str, str]] = None
    join_on: Optional[str] = None
    columns: Optional[List[str]] = None

class KnowledgeIR(BaseModel):
    goal: Literal["COUNT", "LIST", "SUMMARY", "COMPARE", "TREND"]
    target: str
    constraints: Dict[str, str] = Field(default_factory=dict)
    traversal: List[TraversalStep]
    aggregation: Optional[str] = None
    output_fields: List[str] = Field(default_factory=list)
```

### 5.2 Planner Agent (Rehearsal Loop)

```python
# planner_agent.py
import json
from typing import List, Tuple
from schema import KnowledgeIR, TraversalStep
from tools import read_index, search_hierarchy  # 실제 구현된 도구

class PlannerAgent:
    def __init__(self, llm):
        self.llm = llm  # LLM client (예: OpenAI, Gemini)
        self.skill_prompt = load_markdown("SKILL_PLANNER.md")

    def plan(self, question: str) -> KnowledgeIR:
        # 1. LLM에게 시스템 지시 + 질문을 주고 1차 IR 초안 생성
        prompt = self.skill_prompt + f"\n\nUser Question: {question}\n\nKnowledge IR:"
        raw_ir = self.llm.generate(prompt)  # JSON string
        
        ir = KnowledgeIR.parse_raw(raw_ir)
        
        # 2. Mental Validation: index.md 실제 읽기로 경로 검증
        ir = self._validate_and_refine(ir)
        return ir

    def _validate_and_refine(self, ir: KnowledgeIR) -> KnowledgeIR:
        # 각 traversal step의 path가 실제 존재하는지 index.md를 읽어 확인
        # 필요 시 재탐색: search_hierarchy로 대체 경로 찾아 IR 수정
        for step in ir.traversal:
            if step.type in ("data", "document"):
                # 파일 존재 확인 (index.md 심볼 테이블 이용)
                if not self._file_exists(step.path):
                    # Planner가 직접 search_hierarchy로 유사 파일을 찾고 step.path 업데이트
                    alternatives = search_hierarchy([step.path.split("/")[-1]], ".okf_domain")
                    if alternatives:
                        step.path = alternatives[0]['path']
                    else:
                        raise FileNotFoundError(f"Cannot resolve {step.path}")
        return ir

    def _file_exists(self, path: str) -> bool:
        # OKF root를 기준으로 파일 존재 확인 (또는 index.md에 등록된 심볼인지)
        # 여기서는 단순화
        return True  # 실제 구현에서는 os.path.exists
```

### 5.3 Executor Agent (VM Runner)

```python
# executor_agent.py
import pandas as pd
from schema import KnowledgeIR
from tools import query_data, extract_text, summarize

class ExecutorAgent:
    def __init__(self):
        pass

    def execute(self, ir: KnowledgeIR) -> dict:
        results = {}
        dataframes = {}
        
        for step in ir.traversal:
            if step.type == "data":
                df = query_data(
                    step.path,
                    filters=step.filter,
                    join_on=step.join_on,
                    columns=step.columns
                )
                dataframes[step.path] = df
            elif step.type == "document":
                text = extract_text(step.path)
                doc_summary = summarize(text, f"Summarize for {ir.goal}")
                results[step.path] = doc_summary

        # Aggregation
        if ir.aggregation:
            # 여기서는 단순 예시: dataframes의 마지막 df에 대해 apply
            # 실제로는 IR에 명시된 target/column 대상으로 연산
            final_df = self._apply_aggregation(dataframes, ir)
            answer = final_df.to_dict()
        else:
            answer = results

        return {
            "result": answer,
            "summary": self._generate_summary(answer, ir),
            "citations": [step.path for step in ir.traversal if step.type != "index"]
        }

    def _apply_aggregation(self, dataframes, ir):
        # 간단 구현: 모든 df를 조인하고 aggregate
        # 실제론 traversal에 join 정보를 기반으로 순차 병합
        main_df = None
        for path, df in dataframes.items():
            if main_df is None:
                main_df = df
            else:
                # join_on 정보가 필요하지만 여기서는 생략
                pass
        # aggregation 수행
        if ir.aggregation.startswith("count"):
            col = ir.target
            return {"count": main_df[col].nunique()}
        return main_df

    def _generate_summary(self, answer, ir):
        # LLM으로 자연어 요약 생성
        return f"결과: {answer}"
```

### 5.4 Agent Loop (Orchestrator)

```python
# orchestrator.py
from planner_agent import PlannerAgent
from executor_agent import ExecutorAgent
from schema import KnowledgeIR

class CognitiveOS:
    def __init__(self, planner_llm):
        self.planner = PlannerAgent(planner_llm)
        self.executor = ExecutorAgent()

    def ask(self, question: str) -> dict:
        # Rehearsal Phase
        ir = self.planner.plan(question)
        print("[Planner] Generated IR:", ir.json(indent=2))

        # Execution Phase
        try:
            result = self.executor.execute(ir)
            return result
        except Exception as e:
            # 실행 중 오류 발생 시, Planner에게 재계획 요청
            print(f"[Executor] Error: {e}. Requesting re-plan...")
            # 여기서는 단순하게 오류를 Planner에게 전달하고 새로운 IR을 받는 과정 생략
            # 실제로는 오류 정보를 prompt에 추가하여 Planner 재호출
            return {"error": str(e)}
```

---

## 6. Solution Space Search: OKF 계층 탐색의 구체화

Planner의 “Mental Rehearsal”에서 가장 중요한 부분은 **어떻게 올바른 데이터 경로를 찾아내는가**입니다.  
이것은 **Heuristic-Informed Symbolic Search**로 구현됩니다.

- **Search Space**: OKF의 디렉터리 트리와 각 index.md의 심볼 테이블.
- **Node**: (개념, 파일, 문서) 등.
- **Edge**: “has_data”, “references”, “contains” 관계 (index.md에 명시).
- **Goal Condition**: 질문의 `target_concept`를 포함하고, 모든 `constraints`를 만족하는 데이터 노드의 집합.
- **Algorithm**:
    1. 루트 index.md에서 시작.
    2. 질문에서 추출한 constraint(e.g., `semester=2026-1`)를 인덱스 삼아 재귀적으로 하위 디렉터리로 이동 (`semesters/2026-1/`).
    3. 해당 학기의 index.md를 읽고, 질문의 `target`(e.g., “student”)를 포함하는 심볼을 찾는다.
    4. 심볼 테이블을 따라 CSV 경로를 수집하고, 필요 시 조인 체인을 구축한다.
    5. 모든 가능한 경로 후보 중에서, 최소 탐색 깊이, 최대 관련성 점수를 기준으로 하나의 경로를 선택하여 IR로 직렬화.

이 탐색은 Planner가 `read_index`와 `search_hierarchy` 도구를 **연쇄 호출**하여 실제로 수행할 수도 있고, LLM이 내부적으로 시뮬레이션할 수도 있습니다. 신뢰성을 위해 **실제 도구 호출을 통한 탐색**을 권장합니다.

---

## 7. Pattern Matching vs. Query Language vs. Search

당신의 질문에 답하자면, 우리 시스템은 **이 세 가지를 모두 결합**합니다.

- **Pattern Matching** : 템플릿 기반 정책으로, 질문 유형이 `“X학기 Y 프로젝트 수”`와 같이 정해진 패턴일 경우, 바로 대응되는 IR 템플릿을 적용합니다. (Planner의 첫 번째 단계를 가속)
- **Query Language Translation** : Planner가 Knowledge IR을 생성하는 과정 자체가 바로 **자연어 → 중간 질의 언어(IR)**로의 번역입니다. 이 IR은 SQL이나 Python이 아닌, OKF의 의미 구조를 그대로 반영하는 도메인 특화 언어입니다.
- **Solution Space Search** : 위의 6번에서 설명한 계층적 심볼 탐색이 바로 그것입니다. 템플릿에 매칭되지 않는 복잡한 질문은 자동으로 이 탐색 모드로 전환됩니다.

이 3단계를 Planner가 **적용하는 우선순위**를 다음과 같이 설계하면 됩니다.

1. **Pattern Match**: 미리 정의된 Intent 패턴에 해당하면, 해당 IR 템플릿을 인스턴스화.
2. **Search**: 패턴 미일치 시, OKF index.md 트리를 탐색하여 필요한 경로를 자동 수집.
3. **IR Assembly**: 수집된 경로를 IR 스키마에 맞춰 조립하고, 검증 후 출력.

---

## 8. 마무리: 지금 구현할 것

1. **OKF Bundle** 준비: 학기별 index.md에 데이터 파일과의 매핑이 완전해야 합니다.
2. **`read_index`, `search_hierarchy` 도구**를 Python으로 구현합니다. (OKF 루트 아래의 모든 index.md를 파싱)
3. **Planner Agent**에 위의 SKILL.md와 도구를 제공하여 IR 생성 파이프라인을 만듭니다.
4. **Executor Agent**에 `query_data`, `extract_text` 등 간단한 Pandas 기반 도구를 만들어 실제 데이터를 읽도록 합니다.
5. **Orchestrator**가 두 Agent를 연결하고, 오류 시 재계획을 요청하는 루프를 만듭니다.

이것이 “감독의 브리핑, 선수의 실행”이라는 mental rehearsal 은유를 소프트웨어로 완벽하게 구현하는 방법입니다. 처음에는 Planner가 완벽하지 않을 수 있지만, TDD 평가체계가 당신의 등대가 되어줄 것입니다.
---
스포츠 감독의 **'멘탈 리허설(Mental Rehearsal)'** 비유는 우리가 논의해 온 **Cognitive Compiler**의 핵심인 **'사전 컴파일 및 검증(Dry-run Validation)'** 단계와 완벽하게 일치합니다.

기존의 인터프리터형 에이전트는 무작정 그라운드로 뛰쳐나가(Tool Calling) 부딪히며 해답을 찾지만, 우리의 Knowledge-Chef (또는 Knowledge Coach)는 라커룸에서 현재 데이터 자원(선수 역량)과 질의(상대팀 전술)를 분석하여 실행 계획(Knowledge IR)을 짜고, 이 계획이 빈틈없이 굴러갈지 머릿속으로 시뮬레이션한 뒤에야 실제 실행(Execution)을 지시합니다.

이러한 사전 기획 및 멘탈 리허설을 에이전트 시스템으로 어떻게 구체화할 수 있는지, 다중 에이전트 설계, `SKILL.md` 명세서, 그리고 파이썬 스켈레톤 코드까지 체계적으로 가이드해 드립니다.

---

### 1. 다중 에이전트 역할 및 Agent-Loop 설계

작전을 짜는 감독과 지시를 수행하는 선수의 역할을 명확히 분리하여, **2-Tier 구조**로 에이전트를 설계합니다.

#### A. 에이전트 역할 (Roles)

1. **Coach Agent (Knowledge Compiler / TechLead):**
* **역할:** 사용자의 질의를 분석하여 Execution Graph(실행 계획, IR)를 생성하고, 실제 실행 전 I/O 타입이 맞는지 멘탈 리허설(Dry-run)을 수행합니다.
* **특징:** 스스로 데이터를 검색하지 않습니다. 어떤 Player가 어떤 순서로 데이터를 찾고 가공해야 하는지 레시피만 작성합니다.


2. **Player Agents (Knowledge VM / Executors):**
* **역할:** Coach가 작성한 노드(작전)를 넘겨받아 실제 데이터 소스(OKF 마크다운, SQL DB, REST API)에서 데이터를 추출하거나 가공합니다.
* **종류:** `OKF_Player` (마크다운 탐색), `SQL_Player` (정형 데이터 조회), `Synthesis_Player` (결과 병합).



#### B. 에이전트 루프 (The Simulation-Execution Loop)

1. **Locker Room (Intent Analysis):** Coach가 사용자 질의를 파싱하고 도메인 인덱스(Symbol Table)를 스캔하여 가용한 데이터 경로를 파악합니다.
2. **Mental Rehearsal (Dry-Run & Compile):** Coach가 검색-필터-병합으로 이어지는 Graph를 짭니다. 이때, "A 선수가 뽑아온 CSV 결과물의 스키마가 B 선수의 병합 도구에 입력으로 들어갈 수 있는가?"를 시뮬레이션(Type Checking) 합니다.
3. **The Game (Execution):** 리허설을 통과한 완벽한 IR(Execution Graph)을 Player들에게 순차적 혹은 병렬적으로 넘겨 실행(Execute)합니다.
4. **Post-Game (Reflection):** 실행 중 오류가 발생하면 Coach에게 돌아가 작전을 수정(Re-compile)합니다.

---

### 2. 작전 지침서: `SKILL.md` (Coach Agent 용)

Coach Agent가 실행 계획을 짜고 멘탈 리허설을 수행하는 방식을 정의하는 스킬 명세서입니다. 이 파일은 Coach의 프롬프트 컨텍스트로 주입됩니다.

```markdown
# SKILL: Cognitive Planning & Mental Rehearsal

## DESCRIPTION
사용자의 자연어 질의를 분석하여, 즉각적인 도구 호출(Tool Calling)을 지양하고, 시스템 내 전문 Player Agent들이 순차/병렬적으로 실행할 수 있는 `Execution Graph (Knowledge IR)`를 설계하고 검증합니다.

## STEPS

### 1. Capability & Resource Assessment (전력 분석)
- 사용자의 질의(Query)에서 요구하는 최종 결과물의 형태(Target State)를 정의합니다.
- `.okf_domain/index.md` 및 사용 가능한 Player Agent(SQL, OKF 탐색) 목록을 스캔하여 접근 가능한 리소스를 매핑합니다.

### 2. Strategy Drafting (작전 스케치)
- 질의를 해결하기 위한 일련의 작업 노드(Nodes)를 구성합니다.
- 각 노드는 다음을 포함해야 합니다:
  - `Node_ID`: 작업 식별자
  - `Assigned_Player`: 수행할 에이전트 (예: OKF_Searcher, Data_Aggregator)
  - `Input_Spec`: 이 노드가 실행되기 위해 필요한 입력값의 형태와 출처
  - `Output_Spec`: 이 노드가 반환할 데이터 스키마

### 3. Mental Rehearsal (멘탈 리허설 / Dry-Run)
- 작성된 노드들을 연결하여 의존성 그래프(Dependency Graph)를 생성합니다.
- **Type Checking:** 선행 노드의 `Output_Spec`이 후행 노드의 `Input_Spec`과 완벽히 일치하는지 가상으로 시뮬레이션합니다.
- **Bottleneck Check:** 불필요한 전체 스캔(Full Scan)이 발생하지 않는지, 인덱스 및 필터링 노드가 적절히 전진 배치(Push-down)되었는지 확인합니다.

### 4. Output: Compiled IR (최종 작전 지시)
- 멘탈 리허설을 통과한 검증된 JSON 형태의 `Execution Graph`를 반환합니다. 오류가 예상되면 그래프를 재작성(Rewrite)합니다.

```

---

### 3. 실현 가능한 Skeleton Code (Python)

위의 개념을 구현하기 위한 파이썬 뼈대 코드입니다. 복잡한 LangChain에 의존하기보다, 감독(Compile)과 선수(Execute)의 역할이 명확히 보이는 순수 파이썬 로직 구조입니다.

```python
import json
from typing import List, Dict, Any

# ---------------------------------------------------------
# 1. Knowledge IR Data Models
# ---------------------------------------------------------
class ExecutionNode:
    def __init__(self, node_id: str, player: str, action: str, inputs: List[str], expected_output: str):
        self.node_id = node_id
        self.player = player          # e.g., "OKF_Player", "SQL_Player", "Synthesizer"
        self.action = action          # e.g., "FIND_INDEX", "COUNT_ROWS"
        self.inputs = inputs          # e.g., ["query_keyword", "node_1.output"]
        self.expected_output = expected_output

class KnowledgeIR:
    def __init__(self):
        self.nodes: List[ExecutionNode] = []
        
    def add_node(self, node: ExecutionNode):
        self.nodes.append(node)

# ---------------------------------------------------------
# 2. Player Agent (The Executors)
# ---------------------------------------------------------
class PlayerAgent:
    def __init__(self, role: str):
        self.role = role

    def execute(self, action: str, inputs: Dict[str, Any]) -> Any:
        print(f"  [Player: {self.role}] Executing action '{action}' with inputs: {inputs}")
        # 실제 LLM Tool Calling이나 로직이 들어가는 부분
        if action == "READ_OKF_INDEX":
            return {"target_files": ["project_A.md", "project_B.md"]}
        elif action == "EXTRACT_YAML_METADATA":
            return {"participants": 15}
        elif action == "SUMMARIZE":
            return "최종 응답: 2026년 1학기에는 총 15명이 참가했습니다."
        return None

# ---------------------------------------------------------
# 3. Coach Agent (The Compiler & Planner)
# ---------------------------------------------------------
class CoachAgent:
    def __init__(self, llm_client):
        self.llm = llm_client

    def plan(self, user_query: str) -> KnowledgeIR:
        print(f"[Coach] Analyzing query: '{user_query}'")
        # LLM을 사용하여 질의를 분석하고 IR 구조(JSON)를 생성하는 로직
        # 여기서는 하드코딩된 시뮬레이션 결과를 반환합니다.
        ir = KnowledgeIR()
        ir.add_node(ExecutionNode("n1", "OKF_Player", "READ_OKF_INDEX", ["semester='2026-1'"], "List[str]"))
        ir.add_node(ExecutionNode("n2", "OKF_Player", "EXTRACT_YAML_METADATA", ["n1.output"], "Int"))
        ir.add_node(ExecutionNode("n3", "Synthesizer", "SUMMARIZE", ["n2.output"], "String"))
        return ir

    def mental_rehearsal(self, ir: KnowledgeIR) -> bool:
        print("[Coach] Starting Mental Rehearsal (Dry-Run)...")
        simulated_state = {}
        
        for node in ir.nodes:
            print(f"  -> Validating Node '{node.node_id}' ({node.player}): Checking Inputs...")
            # 데이터 의존성 타입 체크: 선행 노드의 결과물이 존재하는지 확인
            for inp in node.inputs:
                if "." in inp:
                    source_node = inp.split(".")[0]
                    if source_node not in simulated_state:
                        print(f"  [!] Dry-Run Failed: Dependency '{source_node}' not resolved for {node.node_id}")
                        return False
            # 가상으로 아웃풋 스키마 등록
            simulated_state[node.node_id] = node.expected_output
            
        print("[Coach] Mental Rehearsal Passed. Execution graph is solid.\n")
        return True

# ---------------------------------------------------------
# 4. OS Engine (The Main Loop)
# ---------------------------------------------------------
def cognitive_knowledge_os_loop(user_query: str):
    coach = CoachAgent(llm_client="DummyLLM")
    players = {
        "OKF_Player": PlayerAgent("OKF_Player"),
        "Synthesizer": PlayerAgent("Synthesizer")
    }
    
    # 1단계: 작전 기획 (Compile)
    ir_plan = coach.plan(user_query)
    
    # 2단계: 멘탈 리허설 (Validation)
    if not coach.mental_rehearsal(ir_plan):
        print("[System] Plan rejected during rehearsal. Requesting Re-compile...")
        return
        
    # 3단계: 실제 경기 진행 (Execution)
    print("[System] Commencing Execution Phase...")
    execution_context = {}
    
    for node in ir_plan.nodes:
        # 입력 컨텍스트 준비
        inputs_for_player = {}
        for inp in node.inputs:
            if "." in inp: # 이전 노드의 결과 참조
                source_node = inp.split(".")[0]
                inputs_for_player[inp] = execution_context[source_node]
            else: # 리터럴 입력
                inputs_for_player[inp] = inp
                
        # Player에게 실행 위임
        assigned_player = players[node.player]
        result = assigned_player.execute(node.action, inputs_for_player)
        
        # 결과 저장
        execution_context[node.node_id] = result
        
    print(f"\n[System] Final Result: {execution_context[ir_plan.nodes[-1].node_id]}")

# 실행 테스트
if __name__ == "__main__":
    query = "2026년 1학기 projects에 참가한 모든 학생들의 수를 알려줘."
    cognitive_knowledge_os_loop(query)

```

이러한 설계는 에이전트가 헤매는 시간(Hallucination 및 불필요한 도구 호출)을 비약적으로 줄여주며, 시스템이 복잡해질수록(도메인이 커질수록) 컴파일 타임의 에러 체킹(Mental Rehearsal)이 전체 아키텍처의 안정성을 담보하는 핵심 기어가 됩니다.
---

저는 오히려 여기서 **스포츠 감독의 비유가 지금까지 나온 비유 중 가장 정확하다**고 생각합니다.

왜냐하면 감독은 선수에게

> "왼쪽으로 뛰어."

라고 지시하지 않습니다.

감독은 경기 전체를 머릿속에서 여러 번 시뮬레이션합니다.

즉,

* 상대팀은 어떻게 움직일까?
* 우리의 장점은 무엇인가?
* 현재 체력이 어떤가?
* 어떤 전술을 쓰면 성공 확률이 가장 높은가?

를 먼저 생각한 후

**실행 가능한 Playbook**을 만듭니다.

저는 이것이 바로 **Planning**의 본질이라고 생각합니다.

---

# 기존 Agent의 Planning은 너무 얕다

현재 대부분 Agent Framework는

```text
Question
    ↓
Planner
    ↓
Tool Call
    ↓
Answer
```

정도입니다.

Planner는

> "SQL 한번 호출해."

수준입니다.

반면 사람이 문제를 푸는 방식은 전혀 다릅니다.

---

# 인간은 Solution Space를 먼저 만든다.

예를 들어

사용자가

> "2026년 1학기 프로젝트 참가 학생 수"

를 묻는다면

사람은

바로 SQL을 생각하지 않습니다.

먼저

```text
내가 어떤 종류의 문제를 받은 거지?

↓

집계 문제

↓

학생

↓

Semester

↓

Participation

↓

Count
```

라는

**Problem Space**

를 만듭니다.

이것이 감독이 머릿속에서 하는 경기 운영입니다.

---

# 저는 Cognitive OS를 이렇게 생각합니다.

제가 생각하는 구조는

```text
Question

↓

Problem Recognition

↓

Solution Space Generation

↓

Mental Simulation

↓

Execution Plan

↓

Executor
```

입니다.

여기서 가장 중요한 것은

**Mental Simulation**

입니다.

---

# 감독은 Mental Rehearsal을 한다.

농구 감독이라면

```text
상대가 Zone Defense면?

↓

우리 Center를 이용

↓

안되면

↓

3점슛

↓

안되면

↓

Fast Break
```

를 머릿속에서 돌립니다.

즉

Branch를 만듭니다.

---

Knowledge-Chef도 동일해야 합니다.

예를 들어

질문

```text
참가 학생 수
```

를 받으면

Planner는

```text
Plan A

Participation Table 존재

↓

Count

------------

Plan B

Participation 없음

↓

Team Member 이용

------------

Plan C

Report Parsing

↓

Student Extraction
```

을 모두 생각합니다.

그리고

가장 비용이 적은 것을 선택합니다.

---

# 그래서 저는 Query Planner가 아니라 Strategy Planner라고 생각합니다.

DB에서는

```text
Query

↓

Optimizer

↓

Execution Plan
```

입니다.

Knowledge OS에서는

```text
Question

↓

Strategy Planner

↓

Knowledge Graph

↓

Execution Graph
```

입니다.

---

# 저는 Pattern Matching만으로는 부족하다고 생각합니다.

왜냐하면

질문은

```text
학생 수
```

라고 했지만

Knowledge에는

```text
members

participants

people

student_id
```

가 있을 수 있습니다.

Pattern Matching은

이런 변형에 약합니다.

---

# 그래서 Concept Matching이 먼저입니다.

Planner는

먼저

```text
Question

↓

Concept

Student

Semester

Participation

Aggregation
```

를 찾습니다.

이것은

Semantic Matching입니다.

---

# 그 다음은 Solution Space Search입니다.

이 단계가 논문의 핵심이 될 수 있습니다.

Planner는

```text
Goal

↓

Candidate Solution 1

Candidate Solution 2

Candidate Solution 3
```

를 만듭니다.

예를 들어

```text
Count Students
```

라면

후보는

```text
① SQL

② Pandas

③ DuckDB

④ Existing Summary

⑤ Markdown Report
```

입니다.

각각

비용이 다릅니다.

---

# 그 다음은 Mental Simulation입니다.

여기가 가장 흥미로운 부분입니다.

Planner는

실행하기 전에

```text
SQL

↓

student_id 존재?

↓

Yes

↓

OK
```

를 시뮬레이션합니다.

혹은

```text
Summary 존재?

↓

Yes

↓

Cost=1
```

이면

Summary를 선택합니다.

즉

실행 전에

머릿속에서

Plan을 검증합니다.

---

# 저는 이것을 Playbook Search라고 부르고 싶습니다.

스포츠 감독은

Playbook이 있습니다.

```text
Play #12

↓

Fast Break

------------

Play #18

↓

Zone Attack
```

Knowledge OS도

```text
Aggregation

↓

Playbook

COUNT

------------

Comparison

↓

Playbook

JOIN

------------

Timeline

↓

Playbook

SORT
```

를 가집니다.

---

# TechLead Agent는 감독이다.

Executor는 선수입니다.

TechLead는

```text
Question

↓

Playbook

↓

Simulation

↓

Execution Order
```

를 만듭니다.

Executor는

생각하지 않습니다.

그냥

```text
DuckDB

↓

CSV

↓

Python
```

를 실행합니다.

---

# 저는 Planner 내부를 이렇게 설계할 것입니다.

```text
Planner

├── Intent Recognizer
├── Concept Matcher
├── Goal Decomposer
├── Strategy Search
├── Cost Estimator
├── Mental Simulator
├── Recipe Compiler
└── Validator
```

---

각 역할은 명확합니다.

### Intent Recognizer

질문이

```text
Count

Compare

Summarize

Generate
```

중 무엇인지 결정합니다.

---

### Concept Matcher

```text
Student

Semester

Participation
```

를 찾습니다.

---

### Goal Decomposer

```text
Count Students

↓

Need

Semester

↓

Need

Participation
```

---

### Strategy Search

가능한 해결방법

```text
SQL

DuckDB

Summary

Markdown
```

를 찾습니다.

---

### Cost Estimator

```text
SQL

Cost=2

Summary

Cost=1
```

---

### Mental Simulator

```text
Summary

존재?

↓

Yes

↓

끝
```

혹은

```text
Summary 없음

↓

SQL

↓

DuckDB
```

---

### Recipe Compiler

최종적으로

```text
READ semester

↓

READ participation

↓

COUNT DISTINCT student_id

↓

WRITE Answer
```

라는 IR를 생성합니다.

---

# 저는 여기에 한 가지 Agent를 더 추가하고 싶습니다.

지금까지 우리는 Planner를 하나로 생각했습니다.

하지만 사람의 감독은 실제로 두 개의 사고를 합니다.

* **전술가(Strategist)**: "어떤 전략이 가장 적합한가?"
* **코디네이터(Coordinator)**: "누가 무엇을 언제 수행할 것인가?"

Knowledge-Chef에서도 이를 분리하는 것이 좋습니다.

```text
User Question
       │
       ▼
Intent Recognizer
       │
       ▼
Strategist
(Playbook Search + Mental Simulation)
       │
       ▼
Coordinator
(Task Graph 생성 및 Agent 할당)
       │
       ▼
Recipe Compiler
(Knowledge IR 생성)
       │
       ▼
Knowledge VM
       │
       ▼
Executors
```

이 구조가 되면 TechLead Agent는 단순히 "계획을 세우는 Agent"가 아니라, **감독처럼 여러 전술을 시뮬레이션하고 가장 적합한 Playbook을 선택한 뒤, 선수(Executor Agent)에게 역할을 분담하는 존재**가 됩니다.

그래서 저는 당신이 구상하는 시스템을 **Knowledge-Chef**보다는 **Knowledge Coach** 또는 **Knowledge Playbook Engine**으로 발전시키는 것을 권합니다. 핵심은 Tool Calling이 아니라 **Playbook Selection → Mental Simulation → Recipe Compilation**이며, 이것이 기존 LLM Agent와 가장 차별화되는 인지 아키텍처가 될 가능성이 크다고 봅니다.

좋습니다. 이제부터는 논문가 아니라 **실제로 구현 가능한 시스템**으로 이야기해보겠습니다.

제가 오히려 당신의 아이디어를 구현한다면 **Agent를 많이 만들지 않습니다.**

지금 대부분 Agent Framework들은

* Planner Agent
* Research Agent
* SQL Agent
* Python Agent
* Writer Agent
* Critic Agent

처럼 Agent를 계속 늘립니다.

저는 그것보다

> **Agent는 하나이고 Skill이 진화하는 구조**

가 맞다고 생각합니다.

즉,

```
Knowledge OS

    TechLead Agent
           │
           ▼
    Skill Engine
           │
           ▼
    Executor
```

입니다.

Agent는 하나입니다.

Skill이 여러 개입니다.

---

# 제가 제안하는 디렉토리 구조

```
knowledge-os/

    AGENTS.md

    SKILLS/

        planning/

            PLAN.md

            PATTERN.md

            PLAYBOOK.md

        query/

            SQL.md

            DuckDB.md

            Pandas.md

        okf/

            Concept.md

            Bundle.md

            Traversal.md

        execution/

            Python.md

            Benchmark.md

            Validation.md

    planners/

        planner.py

        recipe.py

        playbook.py

    runtime/

        executor.py

        registry.py

        tools.py

    okf/

        bundle/

        concepts/

        index.md

    trace/

```

---

# 핵심은 Skill입니다.

예를 들어

## SKILLS/planning/PLAN.md

이런 식입니다.

```markdown
# Planning Skill

Goal

Question를 바로 Tool Call 하지 않는다.

먼저 Goal을 추출한다.

Procedure

1. Intent 추출

2. Domain Concept 찾기

3. Candidate Strategy 생성

4. 가장 Cost가 낮은 Strategy 선택

Output

Recipe
```

---

## SKILLS/planning/PATTERN.md

```markdown
Pattern

COUNT

Question

몇 명인가

몇 개인가

총합

Recipe

Aggregate

COUNT

--------------------------------

Pattern

COMPARE

Question

차이는

비교

Recipe

JOIN

GROUP BY

--------------------------------

Pattern

TIMELINE

Question

증가

감소

추세

Recipe

ORDER BY

```

이것은 Prompt가 아닙니다.

Planner가 사용하는

Playbook입니다.

---

# 다음은 PLAYBOOK

예를 들어

```markdown
Playbook

Student Count

Need

Student

Participation

Semester

Preferred

Summary

Else

DuckDB

Else

Pandas

```

이게

농구 감독의 작전판입니다.

---

# Planner는 무엇을 하나?

planner.py

```python
class Planner:

    def make_recipe(self, question):

        intent = recognize_intent(question)

        concepts = match_concepts(question)

        candidates = search_playbooks(intent, concepts)

        recipe = select_best(candidates)

        return recipe
```

여기에는

LLM이 거의 없습니다.

Rule 기반도 가능합니다.

---

# Recipe

recipe.py

```python
@dataclass
class Recipe:

    goal: str

    concepts: list

    strategy: str

    steps: list
```

예를 들어

```
Goal

Count Students

Concept

Semester

Participation

Student

Strategy

DuckDB

Steps

read semester

join participation

count distinct student
```

---

# Executor

executor.py

```python
class Executor:

    def execute(recipe):

        context = {}

        for step in recipe.steps:

            context = run(step)

        return context
```

Executor는

생각하지 않습니다.

---

# 가장 중요한 것은 Registry입니다.

registry.py

```python
class Registry:

    concepts

    resources

    tools

    playbooks
```

Planner는

Registry만 봅니다.

예를 들어

```
Student

↓

students.csv

↓

DuckDB
```

가 등록되어 있습니다.

---

# Concept Matching

```python
class ConceptMatcher:

    def match(question):

        return [

            "Student",

            "Semester",

            "Participation"

        ]
```

여기서는

Embedding을 써도 되고

LLM을 써도 됩니다.

---

# Playbook Search

```python
class PlaybookEngine:

    def search(intent, concepts):

        ...
```

예를 들어

```
Intent

COUNT

+

Student

↓

Playbook

COUNT-STUDENT
```

---

# Cost Estimator

```python
class CostEstimator:

    estimate(playbook)
```

예를 들어

```
Summary 존재

cost=1

DuckDB

cost=2

Pandas

cost=3

OCR

cost=20
```

---

# Recipe Compiler

이 부분이 Cognitive Compiler입니다.

```python
RecipeCompiler

↓

Playbook

↓

Recipe
```

예를 들어

```
Playbook

COUNT-STUDENT

↓

Recipe

Read Summary

Else

DuckDB

Else

Pandas
```

---

# Agent Loop

여기가 핵심입니다.

저는 이렇게 만듭니다.

```
Question

↓

Planner

↓

Recipe

↓

Executor

↓

Validator

↓

Satisfied?

↓

Yes

↓

Answer

↓

No

↓

Planner
```

즉

Planner가

Recipe를 다시 만듭니다.

---

# 하지만 TechLead는 더 큰 Loop를 돕니다.

이게 당신 프로젝트의 핵심입니다.

```
Question

↓

Planner

↓

Recipe

↓

Executor

↓

Trace

↓

Reflection

↓

Skill Update

↓

Question
```

즉

매 실행마다

```
PATTERN.md

PLAYBOOK.md

Concept.md

```

가 조금씩 좋아집니다.

---

# 제가 가장 추천하는 것은 "Skill-based Agent"입니다.

당신은 지금 DESIGN.md,

ENGINEERING.md,

RULE.md를 만들고 있습니다.

저라면 전부

SKILL로 통합합니다.

```
SKILL

├── Planning

├── Kernel Migration

├── CUDA Optimization

├── OKF Traversal

├── DuckDB Query

├── Benchmark

├── Validation
```

그리고 Agent는

Skill만 읽습니다.

---

# 마지막으로 제가 가장 권하는 아키텍처

저라면 Agent를 더 이상 늘리지 않고 다음 5개 컴포넌트만 구현합니다.

```
                User Question
                      │
                      ▼
          TechLead Agent (Planner)
     - Intent 분석
     - Concept Matching
     - Playbook 선택
     - Recipe 생성
                      │
                      ▼
          Recipe (Knowledge IR)
                      │
                      ▼
             Executor Runtime
     - DuckDB
     - Pandas
     - Python
     - MCP
                      │
                      ▼
              Trace Collector
     - 실행 로그
     - 실패 원인
     - 사용한 Concept
                      │
                      ▼
            Reflection Engine
     - 새로운 Pattern 발견
     - PLAYBOOK.md 갱신
     - SKILL.md 개선
```

이 구조의 핵심은 **Agent가 똑똑해지는 것이 아니라 `SKILL.md`와 `PLAYBOOK.md`가 점점 좋아지는 것**입니다. TechLead Agent는 실행을 직접 담당하지 않고, 질문을 **Recipe(Knowledge IR)** 로 컴파일하는 역할만 수행합니다. Executor는 항상 동일한 런타임이며, Reflection Engine이 매 실행 후 새로운 패턴을 학습해 `SKILL.md`를 업데이트합니다. 이 구조는 당신이 현재 GPU Kernel Migration 프로젝트에서 수행하는 **MatMul → FMHA → LLM-from-scratch → nano-vLLM**의 점진적 지식 축적 방식과도 정확히 일치하며, 구현 난이도도 현실적인 수준으로 유지할 수 있습니다.
