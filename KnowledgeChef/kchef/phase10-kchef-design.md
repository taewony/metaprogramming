대학이라는 명확한 도메인을 위한 **스노우볼형 지식베이스 구축 및 유지보수 시스템**을 설계해드리겠습니다.  
작은 지식 덩어리를 만들고, 합치고, 중복을 제거하며, 깨진 링크까지 자가 치유하는 **"KnowledgeChef" (또는 CKOS: Cognitive Knowledge Operating System)** 프로젝트를 착수하기 위한 종합 문서입니다.

---

# KnowledgeChef: A Snowball Knowledge Accumulation System for OKF-based Domain Knowledge

**프로젝트 요약**  
조직(대학)의 방대한 지식을 OKF(Open Knowledge Format) 기반의 계층적 지식베이스로 구축·확장·정제하는 에이전트 시스템.  
작은 지식 덩어리(Knowledge Snowball)를 만들고, 병합하며, 중복을 제거하고, 링크 무결성을 유지하는 전 과정을 자동화한다.

---

## 1. 개요 및 비전

### 1.1 등장 배경
대규모 OKF 번들을 한 번에 구축하는 것은 토큰 비용, 보안, 품질 관리 측면에서 어렵다.  
또한 지식은 한 번에 완성되지 않고, 여러 이해관계자, 여러 시점에 걸쳐 조금씩 생성·수정된다.

### 1.2 KnowledgeChef의 철학
**"작게 만들고, 반복해서 합치며, 끊임없이 정제한다."**  
눈덩이(Snowball)처럼 작은 지식 덩어리를 굴려 커다란 지식베이스를 만든다.

- **Knowledge Ingredient**: 한 사람, 한 부서, 한 프로젝트에서 만든 소규모 OKF 조각.
- **Knowledge Snowball**: 여러 Ingredient를 병합·정리한 중간 단위의 지식 덩어리.
- **Knowledge Base (Main Bundle)**: Snowball들을 최종 병합한 완성된 OKF 번들.

---

## 2. 핵심 요구사항

### 2.1 기능적 요구사항
| ID | 요구사항 | 설명 |
|----|--------|------|
| FR1 | **작은 덩어리 생성 (Ingredient Builder)** | 코딩 에이전트(또는 사람)가 특정 도메인의 작은 OKF 단위를 생성할 수 있어야 함 |
| FR2 | **스노우볼 병합 (Snowball Merger)** | 여러 Ingredient/스노우볼을 하나의 일관된 계층 구조로 병합 (concept, index.md, data) |
| FR3 | **중복 탐지 및 제거 (Deduplicator)** | 의미적으로 유사한 concept, 중복된 리소스(CSV 행, 문서)를 탐지하고 정리 |
| FR4 | **링크 무결성 관리 (Link Manager)** | 병합/삭제 후 참조 링크가 깨지지 않도록 자동 업데이트 |
| FR5 | **리뷰/승인 워크플로우** | 사람이 merge 전에 diff를 검토하고 승인할 수 있는 인터페이스 |
| FR6 | **버전 관리** | Git 기반의 변경 이력 및 스냅샷 관리 |
| FR7 | **계층적 index.md 자동 생성/갱신** | 디렉터리 구조 변경 시 index.md의 심볼 테이블을 자동 재생성 |

### 2.2 비기능적 요구사항
- **로컬 실행**: 병합 및 정제 작업은 토큰 비용과 데이터 유출 방지를 위해 로컬 LLM 또는 경량 규칙 기반으로 수행.
- **확장성**: 개념 수가 수천 개로 증가해도 선형 이하의 시간으로 처리 가능.
- **멱등성**: 동일한 병합 작업을 여러 번 수행해도 결과가 동일해야 함.

---

## 3. 아키텍처 설계

### 3.1 전체 구조

```
[KnowledgeChef System]
    │
    ├── Ingredient Builder (Cloud Coding Agent)
    │   - 소규모 OKF 조각 생성
    │   - 각 조각은 독립된 git branch
    │
    ├── Snowball Merger (Local Agent)
    │   ├── Structure Harmonizer   (디렉터리/파일 병합)
    │   ├── Deduplication Engine  (중복 제거)
    │   ├── Link Integrity Checker (깨진 링크 탐지)
    │   └── Index Generator       (index.md 재생성)
    │
    ├── Merge Review Dashboard (사람 개입)
    │
    └── Main Knowledge Repository (Git)
```

### 3.2 Ingredient Builder (Coding Agent)
- **역할**: 특정 주제(예: "2026년 컴퓨터공학과 캡스톤")에 대한 OKF 조각 생성.
- **작업 지시 예**: "2026년 1학기 캡스톤 프로젝트 OKF를 생성해줘. 개념은 Project, Student, Course. index.md는 이 디렉터리에..."  
- **산출물**: `ingredients/2026_capstone/` 경로의 OKF 번들 (concept/, data/, index.md 등).
- **환경**: Gemini/GPT Code Execution (클라우드), 결과물은 Git branch로 push.

### 3.3 Snowball Merger (Local Agent)
**핵심 엔진**. 클라우드 Agent의 토큰 비용과 보안 이슈를 피하기 위해 **로컬 LLM (Ollama, Llama 3) + 규칙 기반 스크립트**로 구현.

#### 3.3.1 Structure Harmonizer
- 서로 다른 Ingredient들의 디렉터리 트리를 비교.
- **Concept 병합**: 동일 concept(예: `project.md`)에 여러 소스의 속성과 관계를 합침.
- **Data 병합**: 같은 스키마의 CSV/Excel 파일을 `concat`, 중복 행은 키(ID) 기준으로 제거.
- **Document 복사**: `documents/` 아래 파일명 규칙(`{project_id}_prd.docx`)에 따라 복사.

#### 3.3.2 Deduplication Engine
- **Concept 유사도 분석**: concept markdown 파일 간 cosine similarity (TF-IDF 또는 임베딩)를 계산하여 임계값 이상이면 사람에게 병합 제안.
- **데이터 레코드 중복**: 정확한 ID 매칭 뿐 아니라 fuzzy matching (이름, 날짜)으로 중복 의심 쌍 추출.
- **문서 중복**: 파일 해시 비교로 완전 동일 문서 제거.

#### 3.3.3 Link Integrity Checker
- OKF 내의 모든 Markdown 파일과 CSV 파일을 파싱하여 내부 링크 (`[text](path)`) 수집.
- 대상 파일/디렉터리 존재 여부 확인. 없으면 깨진 링크로 보고.
- 자동 수정 규칙:
  - 링크가 사라진 concept을 다른 concept에 흡수했다면, 링크를 새 concept으로 변경.
  - 데이터 파일 경로 변경 시, `index.md`의 심볼 테이블 업데이트.

#### 3.3.4 Index Generator
- 각 디렉터리마다 `index.md`를 재생성.
- 템플릿:
  ```markdown
  # {Directory Name}
  - Concepts: [list with links]
  - Data Files: [CSV path] (row count, columns)
  - Documents: [list with links and summaries]
  ```

---

## 4. 운용 시나리오 (Snowball Workflow)

### 4.1 초기 스노우볼 생성
1. **도메인 분석가**가 "2026년 1학기 전체 프로젝트"라는 대주제를 선정.
2. Ingredient Builder에 "컴공과 캡스톤", "전자과 경진대회", "산학협력 프로젝트" 등 3개의 작은 OKF 생성을 지시.
3. 각 Ingredient는 독립적인 Git 브랜치에 생성됨 (`ing/2026_cap_cse`, `ing/2026_contest_ee`, `ing/2026_industry`).

### 4.2 첫 번째 병합 (1차 스노우볼)
4. Snowball Merger가 `ing/2026_cap_cse`와 `ing/2026_contest_ee`를 병합:
   - Harmonizer가 두 Ingredient의 디렉터리 구조를 비교.
   - `project.md` concept 파일을 하나로 통합 (중복 필드 합침).
   - `projects.csv` 병합, 학생 데이터는 `project_participation.csv`로 별도 관리.
   - 인덱스 재생성.
5. 결과물을 `sb/2026_1st_semester` 브랜치에 저장.
6. 리뷰 대시보드에 diff 제시 → 승인.

### 4.3 두 번째 병합 (2차 스노우볼)
7. `ing/2026_industry`와 `sb/2026_1st_semester`를 병합.
8. 중복 제거 엔진이 유사한 concept(예: 두 Ingredient 모두 "참여 기업" concept 보유)을 감지하고 병합 제안.
9. 링크 무결성 검사 후 깨진 링크 자동 수정.
10. 최종 `main` 브랜치에 병합.

### 4.4 지속적 유지보수
- 새로운 학기, 새 프로젝트가 생기면 새로운 Ingredient를 생성하고 `main`에 계속 병합.
- 정기적으로 전체 OKF에 대해 Deduplication과 Link Checker를 실행하여 품질 유지.

---

## 5. 기술 스택 및 구현 전략

### 5.1 Ingredient Builder (Cloud Agent)
- **Google Gemini 2.5 Pro with Code Execution** 또는 GPT-4 with Code Interpreter
- **지시 프롬프트**에 AGENTS.md 또는 DESGIN.md를 제공하여 OKF 규격 준수하도록 함.
- 생성된 아티팩트는 GitHub API를 통해 자동으로 새 브랜치에 커밋.

### 5.2 Snowball Merger (Local Engine)
- **Python 3.11+** 기반 스크립트.
- **로컬 LLM**: Ollama + Llama 3 8B (concept 유사도 판단, 요약 생성 등 경량 작업)
- **임베딩 모델**: `sentence-transformers/all-MiniLM-L6-v2` (중복 탐지용)
- **링크 분석**: `markdown` 파서, `BeautifulSoup`/regex 기반 링크 추출.
- **버전 관리**: `GitPython` 라이브러리로 자동 커밋, 병합.

### 5.3 Merge Review Dashboard
- **Streamlit** 혹은 **Gradio**로 간단한 웹 UI 구축.
- 병합 전후의 Concept Diff, Data Diff를 보여주고 승인/거절 버튼.

---

## 6. 중복 제거 및 링크 관리 상세

### 6.1 중복 Concept 처리
1. 모든 concept markdown 파일을 읽고 헤더와 내용 추출.
2. TF-IDF 벡터화 후 코사인 유사도 계산.
3. 유사도 > 0.7인 쌍을 "병합 후보"로 표시.
4. 로컬 LLM이 두 concept의 설명을 보고 "병합 가능", "개별 유지", "하나는 다른 하나의 subset" 등 판단.
5. 병합 시, 관계(필드, 참조)도 함께 병합.

### 6.2 데이터 중복 처리
- CSV 파일은 지정된 키(예: `project_id`)로 정렬 후 `drop_duplicates`.
- 키가 없는 경우, 여러 필드의 조합으로 해시를 생성하거나 로컬 LLM이 유사 레코드 판단.

### 6.3 링크 무결성 보장
- **링크 추출**: Markdown 파일에서 `[text](relative/path)` 패턴을 정규식으로 추출.
- **대상 존재 검사**: 파일 시스템에서 해당 경로가 실제 존재하는지 확인.
- **깨진 링크 자동 복구 규칙**:
  1. 대상 파일이 `documents/old/`로 이동 → 새 경로로 링크 업데이트.
  2. 대상 concept가 병합으로 사라짐 → 병합된 concept으로 링크 변경 (Merge Map 참조).
  3. 데이터 파일 이름 변경 → index.md의 심볼 테이블에서 매핑.

---

## 7. 프로젝트 로드맵 (12주 계획)

| 주차 | 목표 | 활동 |
|------|------|------|
| **1주** | 프로토타입 요구 분석 및 환경 세팅 | OKF 규격 정의, Git repo 구성, Ollama 설치 |
| **2주** | Ingredient Builder 연동 | Cloud Agent로 OKF 생성 자동화 스크립트 개발, GitHub 브랜치 자동 push 테스트 |
| **3주** | Structure Harmonizer | 디렉터리/파일 병합 로직 구현 (concept 합치기, CSV concat) |
| **4주** | Deduplication Engine | TF-IDF + 코사인 유사도로 concept 중복 검출, 로컬 LLM 연동 |
| **5주** | Link Integrity Checker | 링크 추출기, 깨진 링크 검출 및 자동 수정 규칙 구현 |
| **6주** | Index Generator | index.md 자동 생성기, 계층 템플릿 적용 |
| **7주** | Merge Review Dashboard | Streamlit UI 구축 (diff 보기, 승인/거절) |
| **8주** | 통합 테스트 (1차) | 3개의 수동 Ingredient로 Snowball 병합 시뮬레이션 |
| **9주** | 실제 대학 데이터로 파일럿 | 2026-1학기 실제 데이터 일부를 Ingredient로 변환 후 전체 파이프라인 테스트 |
| **10주** | 성능 최적화 및 보완 | 대량 데이터 처리 속도 개선, 링크 수정 규칙 보강 |
| **11주** | 문서화 및 사용자 매뉴얼 | 운영자 교육 자료, 시스템 아키텍처 문서 |
| **12주** | 최종 발표 및 배포 | CKOS v1.0 릴리스, 유지보수 계획 수립 |

---

## 8. 기대 효과 및 결론

KnowledgeChef는 기존의 수작업 지식 관리나 단일 에이전트 접근과 달리,  
**지식의 생성과 관리를 하나의 OS처럼 운영**할 수 있게 해줍니다.  
이는 대학뿐 아니라, 기업의 기술 문서, 연구소의 실험 기록 등 분명한 도메인을 가진 모든 조직에서 활용 가능한 **범용 지식 증식 프레임워크**입니다.

이 문서를 기반으로 프로젝트를 시작하시면,  
"Cognitive Knowledge Operating System"의 첫 번째 구현체를 탄탄하게 설계하실 수 있을 것입니다.