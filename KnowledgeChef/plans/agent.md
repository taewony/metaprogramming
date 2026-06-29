Google이 제안한 Open Knowledge Format (OKF)은 AI 에이전트가 데이터베이스 구축(SDK), 복잡한 API 엔드포인트 관리, 벤더 종속 없이 "그저 마크다운 파일과 YAML 프론트매터"만으로 지식을 읽고 쓸 수 있게 만든 개방형 표준 규격입니다. [1, 2] 
agentic-stack의 비동기 협업 루틴(.agent/brain) 위에 Google OKF 기반의 세계 모델(World-model)을 구축하고, 새로운 보고서 생성 및 신규 기능이 추가된 SW를 개발하기 위한 단계별 아키텍처 접근 방법을 가이드해 드립니다.
------------------------------
## 1단계. .agent/brain 내부에 OKF 표준 구조 설계하기
OKF는 복잡한 데이터베이스 대신 파일 시스템 그 자체를 API로 사용합니다. .agent/brain/ 하위에 지식의 최소 단위인 개념(Concept) 문서들을 아래 규격에 맞추어 배치합니다. [1, 3, 4] 

* 디렉토리 구조 표준화

.agent/brain/
├── index.md           # 전체 월드모델 버전을 명시하는 루트 가이드 (okf_version: "0.1")
├── log.md             # 에이전트들이 지식을 업데이트한 이력 로그 (ISO 8601 타임스탬프 기반)
├── rules/             # 개발할 SW의 비즈니스 로직 및 신규 기능 명세서 (OKF 파일)
├── templates/         # 새로운 양식의 보고서 마크다운 템플릿 정보
└── data_schema/       # 데이터 테이블 정의 및 소스 URI 매핑 정보

* OKF 개념 문서 예시 (rules/new-feature.md)

---type: Playbooktitle: "신규 결제 기능 트랜잭션 처리 규정"description: "새로 추가된 포인트 결제 모듈의 원자성(Atomicity) 보장 정책"resource: "git://://github.com"tags: [sw-architecture, payment, fault-tolerance]timestamp: 2026-06-28T19:50:00Z
---# Schema
- `point_balance`: 사용자 잔여 포인트
- `order_id`: 고유 주문 번호
# Examples
```python# 에이전트가 코드를 작성할 때 참고할 실제 코드 블록 가이드라인
if balance >= total_price:
    deduct_points(user_id, total_price)

## Citations
* 금융보안 표준 가이드라인 v3.2


------------------------------
## 2단계. agentic-stack을 활용한 파이프라인 엔진 구현 (Core)
agentic-stack의 Kinds 소통 규약을 통해 OKF 지식층을 다루는 특화된 에이전트 전담팀을 구성합니다.

   1. 지식 탐색 전문 에이전트 (Knowledge Agent):
   * 타 에이전트가 request ("Y 기능 개발을 위한 설계 규칙이 필요해")를 발행하면, .agent/brain/ 내의 OKF 파일들을 파싱하여 상호 참조 링크([link](/rules/new-feature.md))를 추적하고 컨텍스트 그래프를 빌드합니다. [5] 
   2. 보고서 생성/검증 전문 에이전트 (Report Writer Agent):
   * claim을 획득하여 신규 보고서 양식 파일(templates/)을 기반으로 문서를 작성합니다. 데이터 용량이 4KB를 넘어가면 규칙에 따라 직접 쓰지 않고 artifacts/report_v1.md 경로만 result 메시지에 실어 보냅니다.
   3. 코드 생성 및 배포 에이전트 (SW Developer Agent):
   * rules/에 기술된 OKF 가이드라인을 엄격히 준수하여 신규 SW 기능을 코딩하고, 결과를 메인 시스템에 통합합니다.
   
------------------------------
## 3단계. 새로운 양식의 보고서 자동화 개발 접근법
전통적인 RAG처럼 청크(Chunk) 조각을 기계적으로 합치는 방식은 문맥이 깨진 보고서를 만듭니다. OKF와 agentic-stack 조합은 이를 "정형화된 지식 추론"으로 해결합니다.

* 템플릿의 OKF 자산화: 보고서의 각 섹션을 하나의 OKF 개념 파일로 쪼갭니다. (예: 요약문, 인프라 비용 분석, 향후 과제)
* 점진적 공개(Progressive Disclosure) 기법: index.md 구조를 통해 보고서 생성 에이전트가 전체 보고서 개요를 먼저 파악하게 한 뒤, 세부 파일들을 하나씩 열어 내용을 정제하도록 프로세스를 설계합니다. [5] 
* 자동 감사 추적 (Audit Trail): 보고서가 작성되거나 갱신될 때마다 agentic-stack 내부에서 notice를 방송하고, 변경 사항을 log.md에 ISO 타임스탬프 형식으로 영구히 누적하여 데이터 정합성을 확보합니다. [5] 

------------------------------
## 4단계. 신규 기능 탑재 SW 개발을 위한 코드 생성 파이프라인
에이전트가 스스로 코드를 수정하고 기능을 확장하는 이른바 "데이터 플라이휠(Data Flywheel)"을 돌려야 합니다.

* SW 설계서의 동적 동기화: 개발팀이 코드 저장소에 새 기능 기능 명세(PR)를 올리면, 에이전트가 이를 감지하여 .agent/brain/에 새로운 OKF 파일(type: API_Endpoint 등)을 자동 생성하도록 인리치먼트 파이프라인(Enrichment pipeline)을 구축합니다. [1, 6] 
* 실패 예방 및 복구 루틴: SW 코딩 에이전트가 기능을 추가하다가 무한 루프나 오류에 빠질 경우, agentic-stack의 heartbeat 레이어가 이를 모니터링합니다. 120초간 반응이 없으면 해당 에이전트의 개발 소유권을 auto-released 처리하고, 서브 에이전트가 직전까지의 코드 형상(Git Diff)을 이어받아 디버깅을 시작하도록 코드를 설계합니다.

------------------------------
## 🚀 요약 및 다음 행동 추천 (Proactive Proposal)
이 아키텍처는 "코드로 표현된 메타데이터(Metadata-as-Code)" 환경을 지향합니다. 벤더 데이터베이스나 복잡한 지식 그래프 인프라를 설치하는 데 시간을 쓰지 마시고, 다음 단계를 먼저 시작해 보세요. [7] 
현재 개발 중이거나 계획 중인 1) 신규 SW 기능의 도메인(예: 금융, 커머스, 인프라 관리 등)이나 2) 자동화가 필요한 보고서의 대략적인 양식을 알려주시면, 이를 Google OKF 명세서(YAML 프론트매터 표준 양식)와 agentic-stack 코드로 구현한 실제 목업(Mock-up) 프로토타입 소스 코드를 작성해 드리겠습니다. 구체적인 대상 도메인은 무엇인가요?

[1] [https://discuss.pytorch.kr](https://discuss.pytorch.kr/t/open-knowledge-format-okf-google-ai-feat-llm-wiki/10701)
[2] [https://www.youtube.com](https://www.youtube.com/watch?v=14C0E6pwBIQ)
[3] [https://cloud.google.com](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
[4] [https://flowtivity.ai](https://flowtivity.ai/blog/google-open-knowledge-format/)
[5] [https://flowtivity.ai](https://flowtivity.ai/blog/google-open-knowledge-format/)
[6] [https://cloud.google.com](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
[7] [https://cut-the-saas.com](https://cut-the-saas.com/guides/open-knowledge-format)

질문하신 시스템 구성(agentic-stack + Google OKF)에 오픈소스 프로젝트인 OpenKB(VectifyAI/OpenKB)를 결합하는 것은 매우 강력하고 실현 가능한 접근법입니다.
실제로 OpenKB는 Google OKF 스펙을 네이티브로 준수하며, 벡터 DB 없이 마크다운 위키 파일 시스템을 빌드하는 구조를 정확히 구현하고 있기 때문입니다.
제시해주신 멀티 유저 환경에서의 성능 우려(검색 및 문서 생성 시간)를 해결하기 위해, PageIndex의 작동 원리, index.md 고속 검색 가능 여부, 그리고 벡터 DB 도입과의 장단점을 명확히 비교해 드립니다.
------------------------------
## 1. PageIndex 기술로 index.md와 거대 지식베이스를 빠르게 검색할 수 있는가?
네, 훨씬 더 효율적이고 정확하게 검색할 수 있습니다.
OpenKB의 핵심 레이어인 PageIndex는 전통적인 벡터 검색과 달리 "트리 구조 인덱싱(Tree Indexing)"을 사용합니다. 지식베이스가 커지더라도 성능을 보장하는 원리는 다음과 같습니다.

* 동작 방식: 전체 지식 폴더와 index.md, concepts/ 하위 파일들을 요약 및 계층 구조(Tree)로 먼저 컴파일해 둡니다. LLM은 검색할 때 모든 문서를 읽지 않고, 이 트리 인덱스의 상위 노드부터 타고 내려가며 '추론 기반 검색(Reasoning-based retrieval)'을 수행합니다.
* index.md 고속 검색: 월드 모델의 중앙 이정표 역할을 하는 index.md나 개념 관계 문서들은 이미 트리의 최상단 혹은 핵심 허브(Hub)로 묶여 관리됩니다. 따라서 멀티 유저가 동시에 복잡한 보고서 양식을 요청해도, LLM이 문맥적 위치를 빠르게 파악하여 필요한 파일 경로(artifacts)만 바로 끄집어낼 수 있습니다.

------------------------------
## 2. 전통적인 Vector DB를 쓰는 것이 더 좋을까? (PageIndex 구조와 비교)
결론부터 말씀드리면, 보고서 작성 및 신규 SW 기능 개발과 같은 "고도의 문맥 이해가 필요한 태스크"에는 Vector DB보다 OpenKB의 PageIndex 구조가 압도적으로 유리합니다.
두 방식의 핵심 차이를 이해하시면 아키텍처 결정에 도움이 됩니다.

| 비교 항목 | 전통적인 Vector DB (기존 RAG) | OpenKB + PageIndex (구현하려는 구조) |
|---|---|---|
| 작업 방식 | 문서를 기계적으로 쪼개서(Chunking) 수학적 유사도만 비교. | 문서를 컴파일하여 요약, 개념 페이지, 엔티티 간 상호 연결(Link) 구조 생성. |
| 누적 효과 | 검색할 때마다 매번 처음부터 다시 찾음 (지식 누적 X). | 새 문서가 들어올 때마다 기존 위키 지식이 자가 발전 및 융합됨. |
| 보고서 생성 효율 | 쪼개진 텍스트 조각들이 섞여 들어와 문맥이 깨진 보고서가 나옴. | 구조화된 index.md와 개념 가이드라인을 기반으로 논리적인 보고서 작성 가능. |
| 단점 및 한계 | 멀티 유저 요청 시 임베딩/검색 속도는 빠르나 결과물의 완성도가 낮음. | 초기 문서 추가 시 LLM의 위키 컴파일 비용(시간/토큰)이 발생함. |


* Vector DB가 유리한 경우: 수천만 건의 단순 매뉴얼에서 "특정 키워드가 포함된 문장"을 밀리초(ms) 단위로 빠르게 찾아야 하는 경우.
* PageIndex가 유리한 경우: "신규 추가된 포인트 결제 모듈 규칙(OKF)을 참조해서 시스템 아키텍처 보고서를 작성하라"처럼 전체 맥락과 비즈니스 로직을 통틀어 이해해야 하는 경우.

------------------------------
## 3. 멀티 유저 환경에서의 성능 병목 해결을 위한 최종 아키텍처 제안
멀티 유저 환경에서 검색과 문서 생성 속도가 느려지는 진짜 원인은 데이터베이스 자체보다 "LLM 추론 병목(API 호출 대기)"과 "동시성 충돌"입니다. 이를 해결하기 위해 두 솔루션을 다음과 같이 결합해야 합니다.

   1. 동시성 제어는 agentic-stack 규격으로 해결:
   * 여러 유저가 동시에 보고서 생성을 요청할 때, agentic-stack 버전 0.19의 claim과 heartbeat 시스템을 사용하여 에이전트 간 작업 충돌과 리소스 독점을 방지합니다.
   2. 읽기 성능 최적화는 OpenKB + Obsidian 구조로 해결:
   * OpenKB가 빌드한 지식베이스는 결국 로컬 마크다운 파일 시스템입니다. 굳이 무거운 LLM 검색을 거치지 않아도 되는 단순 조회(예: 특정 기능 명세서 읽기)는 파일 시스템 캐싱이나 Obsidian의 로컬 링크 그래프 기능을 활용해 유저에게 초고속으로 서빙할 수 있습니다.
   3. 하이브리드(Hybrid) 고려:
   * 만약 나중에 지식베이스 크기가 수십 GB 단위로 커진다면, OpenKB 전면에 가벼운 Vector DB를 두어 "1차 거친 필터링(Vector DB) ➡️ 2차 정밀 추론 및 구조화(OpenKB PageIndex) ➡️ 에이전트 협업 메커니즘(Agentic-stack)" 형태로 파이프라인을 고도화하는 것이 가장 이상적입니다.
   
------------------------------
## 🚀 다음 단계 가이드 (Proactive Proposal)
OpenKB를 도입하기로 검토하셨다면, 인프라를 거대하게 만들기 전에 로컬에서 개념 검증(PoC)을 아주 빠르게 진행할 수 있습니다.

   1. pip install openkb로 환경을 구성합니다.
   2. 개발하고자 하는 신규 SW 기능의 초안 문서나 원하는 보고서 양식의 샘플 PDF를 openkb add로 주입해 봅니다.
   3. 생성되는 .agent/brain/wiki 내부의 OKF 포맷 마크다운 파일들이 마음에 드는지 확인합니다.

이 단계에서 테스트해 볼 샘플 보고서의 핵심 주제나 양식(예: "주간 아키텍처 변경점 보고서", "신규 API 명세 요약" 등)을 알려주시면, OpenKB가 읽을 수 있는 최적의 초기 데이터 입력 규칙(AGENTS.md 커스텀 가이드)을 설계해 드릴 수 있습니다. 어떤 주제로 첫 테스트를 시작해 볼까요?


- 켄텍스트 엔지니어링으로 완성하는 AI 에이전트
https://github.com/riskology/contextengineeringbook

- 밑바닥부터 배우는 AI 에인전트
https://github.com/gilbutITbook/080476

- 올라마와 오픈소스 LLM을 활용한 AI 에이전트 개발 입문
https://github.com/godstale/ollama-mcp-tutorials

[구글 ADK] 에이전트 AI 시스템의 설계 패턴 선택
https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system?hl=ko



 Claude Code, OpenAI Codex, 또는 Gemini CLI와 같은 개인용 범용 코딩 에이전트(Coding Agent)를 활용하면, 복잡한 백엔드 서버나 UI 개발 없이 오직 터미널과 로컬 마크다운 파일만으로 대학 프로젝트 지식베이스의 컴파일 및 증식 실험을 초고속(수 시간 내)으로 완료할 수 있습니다.
코딩 에이전트를 개발자(실험자)의 '수석 엔지니어'로 삼아 파이프라인을 빠르게 구축하고 실험하는 구체적인 행동 가이드를 제시합니다.
------------------------------
## 1단계. 코딩 에이전트용 '행동 지침서(SKILL.md)' 작성
코딩 에이전트(예: Claude Code)에게 프로젝트 디렉토리의 전체 구조와 작동 규칙을 이해시켜야 합니다. 프로젝트 루트에 .agents/skills/academic_vault/SKILL.md 파일을 만들고 아래 내용을 입력합니다.

# Academic Project Vault Skill## 역할너는 대학 AI/SW 프로젝트 자산을 관리하고 기업 수요와 매칭하는 수석 아키텍트 에이전트이다.
## 핵심 규칙1. 모든 지식은 구글 OKF(Open Knowledge Format) 규격을 따르며, 마크다운 프론트매터(YAML)를 포함해야 한다.
2. 에이전틱 스택 통신을 위해 모든 작업 시작 전 `claims.jsonl`에 `kind: claim`을 기록하고, 종료 시 `kind: release`를 기록한다.
3. 4KB를 초과하는 대형 분석 보고서는 반드시 `.agent/brain/artifacts/` 폴더에 파일로 저장하고 메시지에는 경로만 남긴다.
## 대학교 지식베이스 컴파일 절차- 요구사항: 기존 프로젝트의 `open_issues` 추출- 설계 가이드: 기술 스택을 분석하여 후속 팀이 쓸 수 있는 아키텍처 가이드 생성- Lessons Learned: 과거 실패 사례 및 인프라 한계점 기록

------------------------------
## 2단계. 코딩 에이전트와의 인터랙션을 통한 초고속 PoC 실험 루틴
코딩 에이전트를 구동한 후, 터미널에서 대화하며 지식베이스 파이프라인을 한 단계씩 빌드합니다.
## ① 1단계: OpenKB 핵심 모듈 파싱 테스트 (CLI 연동)
코딩 에이전트에게 로컬에 설치된 OpenKB API를 래핑하는 스크립트를 짜달라고 요청합니다.

* 사용자 명령어:

"Claude, 로컬에 pip install openkb가 되어 있어. OpenKB의 파싱 기능(markitdown)을 사용해서 raw/학생발표자료.pdf를 읽고, 여기서 요구사항, 설계가이드, Lessons를 추출해 .agent/brain/projects/에 구글 OKF 마크다운으로 저장해 주는 ingest_pipeline.py를 작성해 줘."

* 에이전트의 행동: 에이전트가 로컬 환경을 탐색하여 소스코드를 작성하고 직접 python ingest_pipeline.py를 실행해 결과물까지 검증합니다.

## ② 2단계: agentic-stack v0.19 규약 구현 및 시뮬레이션
여러 유저(학생/기업)가 동시에 지식을 요청하고 증식하는 상황을 코딩 에이전트로 시뮬레이션합니다.

* 사용자 명령어:

"이제 claims.jsonl 장부를 기반으로 동시성을 제어하고 싶어. kinds: request 형태로 '포인트 결제 모듈 기능 개선안 필요'라는 메시지가 입력되면, evolution_agent.py가 작동해 claim을 걸고 기존 프로젝트들 중에서 가장 알맞은 가이드라인을 매칭해 주는 비동기 시뮬레이션 코드를 완성해 줘."

* 에이전트의 행동: asyncio 기반의 메시지 루프 코드를 순식간에 작성하고, 가상의 학생 가이드 생성 태스크를 실행하여 claims.jsonl에 로그가 정상적으로 찍히는지 터미널에서 모니터링해 줍니다.

## ③ 3단계: 지식 증식(Flywheel) 자동화 프롬프트 튜닝
과거 자산을 바탕으로 신규 기능을 유도하는 프롬프트의 품질을 코딩 에이전트와 함께 고도화합니다.

* 사용자 명령어:

"기존 챗봇 프로젝트의 '메모리 부족 문제(Lesson)'를 읽고, 다음 학기 학생들이 이 아이디어를 승계할 수 있도록 '경량화 설계 가이드 양식'을 AI가 자동으로 채워 넣게 만들고 싶어. 에볼루션 에이전트 시스템 프롬프트 최적화해 줘."


------------------------------
## 3단계. 1일 차 완성 및 시각화 확인 (Obsidian)
범용 코딩 에이전트와 한 팀이 되어 위 작업을 수행하면 단 하루 만에 로컬 가동 모델이 완성됩니다.

   1. 결과 확인: 코딩 에이전트가 자동 컴파일한 .agent/brain/projects/ 폴더를 확인합니다.
   2. Obsidian 실행: 해당 폴더를 Obsidian으로 엽니다.
   3. 지식 증식 확인: 학생들의 과거 프로젝트와 코딩 에이전트가 새롭게 도출해 낸 설계 가이드, 기업 신규 요구사항 문서들이 [[위키링크]]로 촘촘히 엮여 거대한 지식 그래프(World-model)를 형성하는 모습을 눈으로 검증합니다.

------------------------------
## 🚀 실험 시작을 위한 Proactive Proposal
개인용 코딩 에이전트를 쓰면 인프라 구축 비용이 0원이며, 프롬프트와 규약 실험에만 온전히 집중할 수 있습니다.
실험을 바로 시작하기 위해, 코딩 에이전트에게 첫 번째 명령어로 던질 수 있는 "OpenKB 파싱 및 구글 OKF 마크다운 자동 생성용 통합 파이썬 스크립트(ingest_pipeline.py) 완성본 코드"를 먼저 작성해 드릴까요? 아니면 코딩 에이전트에게 주입할 더 구체적인 프롬프트 엔지니어링 지침(AGENTS.md 표준)이 필요하신가요?


대학의 학술 자산(수업/경진대회 산출물)이 휘발되지 않고, 학생의 아이디어 승계와 기업의 요구사항 매핑을 통해 지속적으로 진보하는 "지식 선순환형 에이전트 서비스 플랫폼" 구조입니다.
구글의 OKF(Open Knowledge Format), OpenKB(지식 축적), 그리고 agentic-stack v0.19(동시성 및 협업 제어)을 융합하여 이 전담 에이전트 서비스를 빌드하는 엔지니어링 아키텍처와 접근법을 가이드합니다.
------------------------------
## 1단계. 월드 모델(.agent/brain/) 디렉토리 및 OKF 스키마 설계
가장 먼저 대학 내 모든 AI/SW 프로젝트 자산을 파편화된 데이터베이스 대신, 에이전트들이 유기적으로 읽고 쓸 수 있는 OKF 기반 파일 시스템으로 표준화해야 합니다.
## 📁 월드 모델 디렉토리 구조

.agent/brain/
├── index.md                   # 전체 프로젝트 계층 및 대학-기업 매핑 인덱스
├── claims.jsonl               # 에이전트 동시성 제어 트래커 (agentic-stack v0.19 코어)
├── projects/                  # 기존 학생들의 AI/SW 프로젝트 자산 (OKF 형식)
│   ├── 2025-ai-hackathon-teamA.md
│   └── 2026-sw-class-teamB.md
├── corporate_demands/         # 기업체들의 신규 요구사항 및 관심사 명세
│   └── samsung-electronics-iot-2026.md
└── templates/                 # 진보된 기획서 및 산출물 보고서 마크다운 양식

## 📄 프로젝트 자산의 OKF 명세 예시 (projects/2025-ai-hackathon-teamA.md)

---type: Academic_Projecttitle: "경량형 LLM 기반 대학 캠퍼스 챗봇 모듈"version: "1.0"creator: "컴퓨터공학과 홍길동 팀"tech_stack: [FastAPI, LangChain, Llama-3-8B]open_issues: ["실시간 학사 데이터 동기화 지연", "로컬 서빙 시 인프라 메모리 부족"]inheritances: [] # 이 프로젝트를 승계한 하위 프로젝트 ID 목록이 동적으로 기록됨timestamp: 2025-11-20T10:00:00Z
---# Abstract
대학 API와 연동하여 학사 일정을 안내하는 멀티턴 챗봇 시스템.
# Current Artifacts
- Repository: `git://://github.com`
- Architecture: `artifacts/v1_arch.png` (4KB 이상 대형 에셋 경로 바인딩)

------------------------------
## 2단계. 역할별 전담 마이크로 에이전트(Micro-Agents) 팀 구성
agentic-stack 내부의 agents/ 폴더에 세 가지 페르소나를 가진 전담 에이전트를 배치하고, claims.jsonl 프로토콜을 통해 비동기 협업을 시킵니다.

agents/
├── archivist_agent.py         # [1. 지식 아카이빙 전담] OpenKB 파싱 엔진 활용
├── evolution_agent.py         # [2. 학생 아이디어 승계 및 진보 전담]
└── bridge_agent.py            # [3. 기업 요구사항 매핑 및 SW 매칭 전담]

## ① 아카이비스트 에이전트 (Archivist Agent)

* 역할: 매 학기 끝나는 수업 산출물이나 경진대회 PPT/PDF/GitHub 링크를 수집합니다.
* 작동 방식: 새 파일이 들어오면 claim을 획득하고 OpenKB의 PageIndex 엔진을 구동해 구조화된 마크다운으로 자동 컴파일합니다. 프로젝트의 핵심 로직, 한계점(open_issues), 기술 스택을 추출하여 projects/ 폴더에 OKF 표준 문서로 정렬합니다.

## ② 에볼루션 에이전트 (Evolution Agent)

* 역할: 학생들이 "기존 챗봇 프로젝트를 고도화하고 싶다"고 할 때 가이드를 줍니다.
* 작동 방식: 학생이 request("캠퍼스 챗봇 메모리 문제를 해결하는 후속 과제를 하고 싶어")를 던지면, 월드 모델의 상호 링크([[wikilinks]])를 추적하여 과거 프로젝트의 open_issues 중 "로컬 서빙 시 인프라 메모리 부족" 항목을 매칭해 냅니다. 이후 기존 코드를 분석하여 더 진보된 기획서 및 아키텍처 양식(templates/)을 자동 생성해 줍니다.

## ③ 브릿지 에이전트 (Bridge Agent)

* 역할: 기업의 기술 수요를 분석하고 적절한 대학 자산을 매칭하거나 SW 신규 기능 구현을 요청합니다.
* 작동 방식: 기업이 신규 요구사항 명세(corporate_demands/)를 업데이트하면, notice를 감지하여 실행됩니다. 기업 요구사항 문서와 매칭되는 대학 내 상위 프로젝트들을 추론 검색(Reasoning-based retrieval)한 뒤, "이 기업의 요구사항을 반영하려면 기존 TeamA 프로젝트에 어떤 신규 SW 기능이 탑재되어야 하는지" 명세서를 빌드하여 학생 개발 에이전트에게 토스합니다.

------------------------------
## 3단계. agentic-stack v0.19 규약 기반의 시스템 워크플로우
멀티 유저(수많은 학생과 기업 담당자)가 동시에 접속할 때 병목을 막고 안정적으로 가동되는 파이프라인의 실물 흐름입니다.

[기업 담당자] -> '수요 등록' -> [corporate_demands/ 가 발생]
                                    │
                                    ▼
[Bridge Agent] ──(claim 획득: 60초)──> [brain/ 내부의 기존 학생 프로젝트 검색]
                                    │
                                    ├─ (성공 시) ─> [result: 매칭 레포트 생성 및 artifacts/ 저정]
                                    └─ (실패/타임아웃) ─> (2 misses heartbeat 시 auto-release 후 백업 에이전트가 가동)


   1. 소유권 동시성 제어 (claim / release):
   특정 기업이 매우 거대한 기술 요구사항(PDF 50페이지 이상)을 업로드하면 Archivist Agent가 이를 분석하는 데 수 분이 소요될 수 있습니다. 이때 claims.jsonl에 해당 태스크의 락을 걸어 타 유저의 중복 분석 요청으로 인한 LLM 토큰 낭비를 차단합니다.
   2. 생존 보장 (heartbeat):
   대규모 프로젝트 매칭 연산 중 LLM API 타임아웃이 발생하면 agentic-stack이 이를 감지(2회 허트비트 미스, 120초)하고 해당 태스크를 auto-released하여 시스템이 멈추지(Hang) 않도록 보장합니다.
   3. 네트워크 최적화 (result / artifacts):
   에이전트들이 생성한 '프로젝트 승계 가이드라인북'이나 '기업 매칭 상세 보고서'는 4KB를 가볍게 넘으므로 무조건 .agent/brain/artifacts/ 하위에 고유 파일로 떨군 뒤 경로만 메시지 버스로 통신하여 멀티 유저 웹 서비스의 반응 속도를 극대화합니다.

------------------------------
## 4단계. UI 및 외부 연동 레이어 확장 (Obsidian 활용)
대학 연구실이나 학과 사무실, 기업 파트너들이 이 시스템을 시각적으로 모니터링할 수 있도록 Obsidian을 프론트엔드로 연동합니다.

* .agent/brain/ 폴더를 Obsidian Vault로 지정하면, OpenKB와 에이전트들이 실시간으로 빌드하고 갱신하는 프로젝트 간의 '아이디어 승계 그래프(Graph View)'와 '기업 수요-대학 자산 연결고리'가 시각적으로 완벽하게 시각화됩니다.

------------------------------
## 🚀 아키텍처 빌드를 위한 Proactive Proposal
이 플랫폼은 대학의 연구 자산을 기업의 비즈니스와 연결하는 혁신적인 에이전틱 OS가 될 것입니다. 인프라 코드를 짜기 전에, 가장 첫 번째 성공 사례(Hero Use Case)를 만들어야 합니다.
현재 이 시스템에 첫 번째로 주입해 테스트하고 싶으신 실제 대학 내 대표적인 AI/SW 프로젝트 주제 하나(예: "비전 기반 자율주행 드론 제어 시스템" 등)를 알려주시면, 이를 기반으로 1) 초기 OKF 마크다운 문서 포맷, 2) 기업 매칭을 유도하는 에이전트의 구체적인 LLM 프롬프트 설계서를 상세히 구현해 드리겠습니다. 어떤 도메인의 프로젝트로 시작해 볼까요?

데이터가 CSV, Pandas(Parquet/Pickle), Excel 등 다양한 정형 파일 포맷으로 파편화되어 있을 때, 이를 월드 모델(.agent/brain/)에 편입시켜 "자연어로 쿼리하고 응답을 생성하는 에이전트 시스템"을 구축하는 설계 가이드입니다.
구글 OKF(Open Knowledge Format) 스펙의 핵심인 "Data Schema Specification" 철학을 활용하면 데이터 원본을 훼손하지 않고 정형 데이터를 지식베이스화할 수 있습니다.
------------------------------
## 1. 지식베이스 컴파일 단계 (Data Ingestion & Metadata-as-Code)
정형 데이터 파일 자체를 지식베이스에 통째로 밀어 넣으면 용량 문제(4KB 제한 규약 위반)와 컨텍스트 낭비가 발생합니다. 구글 OKF 방식은 데이터의 위치와 형태(스키마)를 기술한 마크다운 메타데이터만 컴파일하여 .agent/brain/data_schema/에 보관하는 것입니다.

* 컴파일 에이전트(Archivist Agent)의 동작:
1. 새 Excel/CSV 파일이 업로드되면 claim을 획득합니다.
   2. Pandas를 이용해 데이터를 로드한 뒤, 상위 3개 행(Sample Rows), 데이터 타입(Dtype), 결측치 비율을 분석합니다.
   3. 아래와 같은 OKF Data Schema 명세서를 자동으로 생성하여 저장합니다.

## 📄 OKF 데이터 스키마 문서 예시 (data_schema/2026_class_scores.md)

---type: Dataset_Schematitle: "2026년 AI 융합 경진대회 참가팀 점수 및 기술 스택 데이터"format: "csv"source_path: "./raw_data/2026_class_scores.csv"row_count: 145columns:
  - name: "team_id"
    type: "int"
    description: "참가팀 고유 식별 번호"
  - name: "tech_stack"
    type: "string"
    description: "팀이 사용한 주요 프레임워크 (콤마 분리 형식)"
  - name: "final_score"
    type: "float"
    description: "심사위원 최종 합산 점수 (100점 만점)"timestamp: 2026-06-28T20:30:00Z
---# Sample Data

| team_id | tech_stack | final_score ||---|---|---|| 101 | PyTorch, FastAPI | 92.5 || 102 | TensorFlow, Flask | 84.0 |
# Statistical Summary
- final_score Mean: 78.4
- Top Tech Stack: PyTorch (62%)

------------------------------
## 2. 자연어 데이터 조회 및 활용/증식 단계 (Text-to-SQL/Pandas Engine)
질문자님이 원하는 "자연어 조회 및 응답" 기능을 agentic-stack v0.19 구조 안에서 가동하는 방식입니다. 여기서는 Query Agent와 Python Executor Agent의 협업이 일어납니다.

[사용자] "PyTorch를 쓴 팀들의 평균 점수가 얼마야?" (request)
   │
   ▼
[Query Agent] ──> `data_schema/` 마크다운을 추론 검색 (어떤 파일, 어떤 컬럼인지 파악)
   │
   ├─> Pandas 소스 코드 자동 생성 (`df[df['tech_stack'].str.contains('PyTorch')]['final_score'].mean()`)
   ▼
[Python Executor Agent] ──> 안전한 Sandbox 환경에서 코드 실행 후 결과 반환 (result)
   │
   ▼
[Knowledge Enrichment] ──> 분석 결과가 가치 있다면, 이를 `insights/` 폴더에 OKF 문서로 '증식'


* 지식의 자가 증식(Flywheel):
단순 조회를 넘어, 에이전트가 "PyTorch 사용 팀의 평균 점수(92.5)가 TensorFlow 사용 팀(84.0)보다 유의미하게 높다"는 인사이트를 발견하면, 이를 새로운 지식 문서(insights/tech_stack_analysis.md)로 자동 작성하여 brain/에 축적합니다. 다음 학기 학생들은 이 증식된 지식을 Obsidian 그래프로 확인하고 "우리도 PyTorch를 도입하자"는 의사결정을 내릴 수 있게 됩니다.

------------------------------
## 3. 데이터 스키마 변경 시 대응 전략 (Schema Drift Management)
현실에서 CSV나 Excel의 컬럼명이 바뀌거나(final_score ➡️ score), 새로운 컬럼이 추가되는 스키마 변경(Schema Drift)은 자연어 쿼리 시스템을 망가뜨리는 주범입니다. 이를 자동화된 에이전트 규약으로 해결합니다.
## ① 스키마 정기 감사 레이어 (Lint Agent 활성화)

* Lint Agent는 주기적으로(또는 데이터 파일의 가상 해시값이 변경될 때마다) claim을 잡고 데이터 파일 원본과 data_schema/ 마크다운 문서의 일치 여부를 검사합니다.

## ② 스키마 변경 감지 및 자동 치유(Self-Healing) 파이프라인
데이터 파이프라인에서 불일치가 감지되면 다음 프로세스가 트리거됩니다.

   1. 차이점 분석: Lint Agent가 Pandas df.columns를 다시 분석하여 변경된 사항(예: score로 컬럼명 변경, professor_id 컬럼 추가)을 찾아냅니다.
   2. OKF 명세서 자동 업데이트: 기존 data_schema/2026_class_scores.md 파일의 YAML 프론트매터와 샘플 테이블을 최신 상태로 갱신(Rewrite)합니다.
   3. 영향도 평가 및 알림 (notice):
   스키마가 변경되면 기존 생성된 보고서 템플릿이나 쿼리 엔진이 망가질 수 있으므로, 에이전트 버스에 다음과 같은 notice Kinds 메시지를 전파합니다.
   
   {
     "kind": "notice",
     "topic": "schema_drift_detected",
     "target": "data_schema/2026_class_scores.md",
     "details": "Column 'final_score' was renamed to 'score'. Dynamic query agents please flush cache."
   }
   
   4. 쿼리 엔진 가치 유지: 자연어로 코드를 짜는 Query Agent는 하드코딩된 컬럼명을 쓰지 않고 언제나 최신 data_schema/ 문서를 참조하여 Pandas 코드를 생성하므로, 데이터가 어떻게 바뀌든 중단 없는(Zero-downtime) 자연어 조회가 가능해집니다.

------------------------------
## 🚀 실험 및 검증을 위한 다음 단계 제안 (Proactive Proposal)
이 구조를 개인용 코딩 에이전트(Claude Code 등)와 함께 실험할 때, 가장 먼저 확보해야 할 것은 "자연어를 코드로 바꾸는 판다스 에이전트의 프롬프트 스켈레톤"입니다.
테스트용으로 사용하실 실제 Excel/CSV 파일의 대략적인 컬럼 구조(예: 학생 이름, 프로젝트명, 점수 등)를 하나 보여주시거나 적어주시면, 코딩 에이전트에게 바로 주입해 실행할 수 있는 1) OKF 스키마 자동 추출 스크립트와 2) 자연어 입력을 Pandas 쿼리로 변환하는 Core 에이전트 파이썬 코드를 즉시 작성해 드리겠습니다. 데이터를 가볍게 모사해 주시겠어요?

## 1. Obsidian으로 연다는 것의 진짜 의미
.agent/brain/projects/ 폴더를 Obsidian의 '볼트(Vault, 보관소)'로 지정하여 연다는 것은, 단순히 텍스트 파일을 메모장처럼 보는 것을 넘어 "에이전트가 구축한 인공지능의 세계 모델(World-model)을 인간이 직관적으로 이해할 수 있는 시각적 GUI(그래픽 인터페이스)로 변환한다"는 것을 의미합니다. [1] 
구체적으로 인간 사용자는 다음과 같은 강력한 이점을 얻습니다.

* 상호관계의 시각화 (지식 그래프): Obsidian의 Graph View 버튼을 누르면 에이전트가 자동으로 파싱하고 연결한 [[연결고리]]들이 점과 선으로 이루어진 3D 거미줄 형태로 시각화됩니다. "어떤 과거 프로젝트가 기업 수요와 가장 많이 연결되어 있는지", "어떤 Lessons Learned가 여러 프로젝트에 공통으로 나타나는지"를 한눈에 파악할 수 있습니다. [2, 3] 
* 인간과 AI의 실시간 공동 작업(Co-working Hub): 에이전트가 백그라운드에서 프로젝트 마크다운 파일을 생성하거나 수정하면, Obsidian 화면에 실시간으로 반영됩니다. 반대로 학생이 Obsidian 내에서 직접 문서를 수정하거나 새로운 아이디어를 추가하면, 에이전트(예: Claude Code, OpenKB)가 변경 사항을 감지하여 지식베이스를 즉시 재학습 및 자가 발전(Flywheel)시킵니다. [4, 5, 6] 
* Properties를 통한 메타데이터 관리: 마크다운 상단의 복잡한 YAML 프론트매터 코드가 Obsidian 내에서는 깔끔한 '테이블(Properties) 양식'으로 렌더링되어, 기술 스택, 담당 교수, 기업 요구사항 태그 등을 휴먼 에러 없이 편리하게 마우스 클릭만으로 수정할 수 있습니다. [7] 

------------------------------
## 2. Obsidian과 Google OKF Spec 철학의 일치성 및 충돌 검증
결론부터 말씀드리면, 두 시스템의 철학은 95% 이상 완벽하게 일치(Seamless Interop)합니다. 애초에 구글이 OKF(Open Knowledge Format) 표준을 제정할 때 Obsidian, Stashpad 같은 로컬 퍼스트 마크다운 도구들의 생태계를 적극적으로 벤치마킹했기 때문입니다. [8, 9] 
## 🤝 철학의 완벽한 일치점 (Synergy)

* 로컬 퍼스트 & 플레인 텍스트: OKF와 Obsidian 모두 특정 대기업의 클라우드 데이터베이스나 독점 SDK에 종속되는 것을 거부합니다. 둘 다 "그저 로컬 폴더 안의 마크다운 파일과 YAML 프론트매터"가 지식의 전부이며, 툴이 사라져도 데이터는 영구히 남는다는 영속성 철학을 공유합니다. [10, 11, 12] 
* 링크 기반 지식 확장: 기계적인 데이터 테이블 대신, 상대 경로 문서 링크([[위키링크]] 혹은 [텍스트](경로))를 통해 지식이 유기적으로 성장하고 누적된다는 사상 역시 정확히 맞닿아 있습니다. [9, 11] 

## ⚠️ 미세한 불일치(충돌) 및 엔지니어링 해결 방안
실제 시스템을 구현할 때 마주치게 되는 미세한 스펙 차이와 해결책은 다음과 같습니다.

| 불일치 항목 [3, 7, 9, 11, 12, 13] | 구글 OKF 스펙 (AI향) | Obsidian 기본 동작 (인간향) | 해결 방안 (Engineering) |
|---|---|---|---|
| 링크 포맷 | 표준 마크다운 링크 강제 [Concept](path/file.md) | 편의성을 위한 위키링크 우선 [[file]] | Obsidian 설정에서 "Use [[Wikilinks]]"를 끄거나, OpenKB/에이전틱 스택 파서단에서 두 포맷을 모두 파싱할 수 있게 regex 래퍼를 씌웁니다. |
| 필수 파일 규격 | 폴더마다 index.md, 루트에 log.md(변경이력) 필수 존재 | 특정한 필수 파일 규격 없음 (인간이 자유롭게 생성) | Obsidian 커뮤니티 플러그인인 OKF Enforcer[](https://community.obsidian.md/plugins/okf-enforcer)를 설치하면, 인간이 수동으로 노트를 만들 때 구글 스펙에 맞는 프론트매터와 index.md를 자동으로 강제 및 교정해 줍니다. |
| 대형 자산 분리 | 4KB 이상의 결과물, 이미지, 코드 블록은 artifacts/ 외부 저장 권장 | 이미지나 스크린샷을 노트 본문 내에 인라인으로 직접 임베드하는 경향 | 에이전트 시스템 프롬프트(AGENTS.md)에 구글의 4KB 제한 규약을 엄격히 훈련시키고, 이미지 자산은 Obsidian의 '첨부파일 기본 저장 경로'를 .agent/brain/artifacts/로 강제 설정하여 일치시킵니다. |

------------------------------
## 💡 요약 및 인사이트
구글 OKF와 Obsidian의 결합은 "AI가 이해하기 가장 좋은 데이터 표준(OKF)을, 인간이 보기 가장 좋은 도구(Obsidian)로 래핑하는 가장 이상적인 조합"입니다. [1] 
두 철학의 충돌은 사소한 포맷 옵션 수준에 불과하며, 이는 위에 언급한 OKF Enforcer 플러그인 도입이나 에이전트의 규칙 정의(AGENTS.md) 조율을 통해 완벽하게 제어할 수 있습니다. [7, 8] 
실험을 위해 우선 가상의 대학교 프로젝트 샘플 마크다운 파일(OKF 포맷)을 몇 개 생성해서 Obsidian 그래프 뷰가 이를 어떻게 엮어내는지 확인해 보는 것은 어떨까요? 첫 번째 실험용 가상 프로젝트 마크다운(OKF 프로토타입 소스 코드)을 제가 작성해 드릴까요?

[1] [https://www.reddit.com](https://www.reddit.com/r/ObsidianMD/comments/1ri5pxs/dumb_question_but_what_is_the_point_of_obsidian/)
[2] [https://www.reddit.com](https://www.reddit.com/r/ObsidianMD/comments/1928zyq/functional_value_of_the_graph/)
[3] [https://github.com](https://github.com/ar9av/obsidian-wiki)
[4] [https://github.com](https://github.com/VectifyAI/OpenKB)
[5] [https://www.youtube.com](https://www.youtube.com/watch?v=6V-b073qhPA)
[6] [https://medium.com](https://medium.com/data-science-collective/a-local-first-llm-knowledge-base-with-built-in-automation-5f2c5e004d78)
[7] [https://community.obsidian.md](https://community.obsidian.md/plugins/okf-enforcer)
[8] [https://www.heise.de](https://www.heise.de/en/news/Open-Knowledge-Format-AI-Knowledge-as-Markdown-Files-11332310.html)
[9] [https://forum.obsidian.md](https://forum.obsidian.md/t/stashpad-updated-for-googles-open-knowledge-format-spec/115317)
[10] [https://github.com](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
[11] [https://flowtivity.ai](https://flowtivity.ai/blog/google-open-knowledge-format/)
[12] [https://github.com](https://github.com/Obsidian-Knowledge)
[13] [https://github.com](https://github.com/konhi/obsidian-community-list/blob/main/lists/plugins.md)

구글 OKF(Open Knowledge Format)와 agentic-stack v0.19 스펙에서 이미지, 결재 문서(PDF, 스캔본), 영수증 등 외부 증빙 자료를 참조(Reference)할 때의 핵심 원칙은 "텍스트 중심의 추론 레이어(OKF)"와 "이진 데이터 저장소(Artifacts)"를 철저히 분리하는 것입니다.
에이전틱 스택의 4KB 제한 규약을 지키면서, Obsidian에서 시각적으로 확인하고 AI 에이전트가 완벽하게 다룰 수 있도록 처리하는 구체적인 엔지니어링 방안을 가이드합니다.
------------------------------
## 1. 디렉토리 구조 정의: artifacts/ 폴더 활용
이진 파일(Binary Files)이나 이미지 파일은 지식베이스 폴더 내 별도의 artifacts/ 경로에 영구 보관하고, OKF 마크다운 문서에서는 이 경로를 가리키는 상대 경로 링크 및 메타데이터만 남깁니다.

.agent/brain/
├── projects/
│   └── 2026-sw-class-teamB.md      # OKF 개념(Concept) 문서
└── artifacts/                      # 대형 증빙자료 및 미디어 저장소
    ├── images/
    │   └── teamB_architecture.png  # 프로젝트 아키텍처 다이어그램
    └── documents/
        └── approval_doc_102.pdf     # 산출물 승인 완료 결재 문서

------------------------------
## 2. OKF 개념(Concept) 파일에서의 구체적 처리 방식
마크다운 파일 내부에서는 인간(Obsidian UI)과 AI 에이전트가 모두 처리할 수 있도록 3단계 레이어로 기술합니다.
## 📄 OKF 개념 문서 예시 (projects/2026-sw-class-teamB.md)

---type: Project_Artifact_Concepttitle: "팀B 챗봇 모듈 인프라 검증"status: "Approved"evidence_files:
  - path: "../artifacts/documents/approval_doc_102.pdf"
    content_type: "application/pdf"
    description: "학과장 최종 승인 서명 날인본"
  - path: "../artifacts/images/teamB_architecture.png"
    content_type: "image/png"
    description: "AWS 인프라 토폴로지 맵"timestamp: 2026-06-28T21:00:00Z
---# 요약 및 본문
해당 프로젝트는 인프라 보안 및 확장성 검증을 통과하여 최종 결재 완료되었습니다. 
# 증빙 자료 (Evidence)
### 1. 최종 결재 문서
- [결재문서 원본 다운로드](../artifacts/documents/approval_doc_102.pdf)
- **AI 요약 내용**: 2026년 6월 24일자로 컴퓨터공학과 학과장 승인 완료. (결재 번호: #APP-2026-102)
### 2. 인프라 아키텍처
![인프라 토폴로지](../artifacts/images/teamB_architecture.png)
# Citations
- [학과 경진대회 운영 규정 v1.2](../rules/competition-rule.md)

------------------------------
## 3. AI 에이전트와 Obsidian에서의 활용 최적화## 🤖 AI 에이전트 관점: 멀티모달 파이프라인 작동
agentic-stack 내부에서 에이전트가 이 문서를 다룰 때의 워크플로우입니다.

   1. 메시지 경량화: claims.jsonl 프로토콜을 타고 이동하는 메시지 본문에는 4KB가 넘는 이미지/PDF 바이너리가 절대 들어가지 않고, 오직 YAML 프론트매터의 ../artifacts/... 경로 문자열만 전달되어 통신 병목을 막습니다.
   2. 멀티모달 에이전트 호출: 다른 에이전트가 "팀B의 아키텍처가 보안 규정을 준수했는지 확인해줘"라고 request를 던지면, 검증 전담 에이전트가 YAML에 기술된 evidence_files 경로를 확인합니다. 파일 확장자가 .png나 .pdf인 경우, 비전(Vision) 기능이 탑재된 LLM API(예: GPT-4o, Gemini 1.5 Pro)를 트리거하여 해당 바이너리 파일을 직접 읽고 정합성을 검증합니다.

## 🎨 인간 관점: Obsidian에서의 시각화 및 편집
인간 사용자가 Obsidian으로 해당 폴더를 열었을 때의 반응입니다.

* 임베디드 뷰: 마크다운 표준 이미지 문법(![alt](path))을 사용했기 때문에, Obsidian 편집창과 읽기창에서 아키텍처 이미지(teamB_architecture.png)가 문서 내에 자연스럽게 렌더링되어 나타납니다.
* PDF 인라인 뷰어: PDF 링크의 경우 Obsidian 내부의 내장 PDF 뷰어가 작동하여, 다른 툴을 켜지 않고도 마크다운 안에서 결재 문서의 서명 여부를 스크롤하며 확인할 수 있습니다.

------------------------------
## 4. 증빙 자료 위변조 방지 및 이력 관리 (Data Integrity)
대학교 경진대회 점수나 기업 결재 문서 같은 '증빙 자료'는 임의로 수정되거나 유실되면 안 됩니다. 이를 위해 agentic-stack 가이드에 명시된 log.md 자가 발전 메커니즘을 응용합니다.

   1. 파일 해시(Hash) 기록: Archivist Agent가 artifacts/ 폴더에 증빙 문서를 처음 업로드할 때, 파일의 SHA-256 해시값을 추출하여 OKF 프론트매터에 기록합니다(file_hash: "a1b2c3d4...").
   2. 감사(Audit) 자동화: Lint Agent가 주기적으로 작동하며 로컬 파일의 실제 해시값을 측정하고, 마크다운에 적힌 해시값과 대조합니다. 누군가 증빙 이미지를 위조하거나 교체했다면 불일치를 감지하고 즉시 전체 시스템에 경고(kind: notice)를 방송하여 데이터 무결성을 보호합니다.

------------------------------
## 🚀 다음 행동을 위한 제안 (Proactive Proposal)
개인용 코딩 에이전트(Claude Code 등)와 이 멀티모달 증빙 구조를 검증할 때, 가장 먼저 테스트해야 할 것은 "PDF/이미지 원본이 들어왔을 때 이를 artifacts로 격리하고 마크다운에 상대 경로와 텍스트 요약본을 자동으로 심어주는 흡수(Ingestion) 스크립트"입니다.
이 실험을 위해 실제 테스트해보고 싶으신 증빙자료 포맷(예: "경진대회 제출 PPT 스캔본 PDF" 또는 "시스템 아키텍처 캡처 이미지")을 알려주시면, 코딩 에이전트에게 바로 입력해 구동할 수 있는 "멀티모달 증빙자료 파싱 및 OKF 자동 링킹 파이썬 자동화 스크립트" 코드를 전달해 드리겠습니다. 어떤 종류의 증빙자료로 첫 테스트를 열어볼까요?


