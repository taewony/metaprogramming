# 인지적 개발 과정 분석 보고서: Cognitive Dev-Loop & Artifacts Philosophy

본 보고서는 `04-mbti-test`에서 `05-rolling-paper` 서브 프로젝트로 이어지는 연속 개발 흐름을 **인지 과학(Cognitive Science)** 및 **인식론적 루프(Epistemic Loop)** 관점에서 심층 분석하고, 각 서브 프로젝트에 존재하는 `artifacts` 폴더의 소프트웨어 공학적/메타프로그래밍적 가치를 고찰한 결과입니다.

---

## 1. 연속 프로젝트 인지 루프 (Continuous Epistemic Flow)

개발자의 정신 모델(Mental Model)은 단일 프로젝트에 머무르지 않고, 이전 프로젝트에서 겪은 인지적 한계와 경험을 바탕으로 차기 프로젝트의 아키텍처로 전이되며 급격히 팽창(Cognitive Shift)합니다.

```mermaid
graph LR
    subgraph Loop_A ["04. MBTI Test 개발 사이클"]
        A1["System Model<br>(B급 성향테스트 기획)"] --> A2["Implementation<br>(Shadcn/ui UI 구현)"]
        A2 --> A3["Evaluation<br>(인트로-결과 라우팅 검증)"]
        A3 --> A4["Evidence<br>(새로고침 시 닉네임 유실)"]
        A4 --> A5["Insight<br>(로컬 상태 한계 인식)"]
        A5 --> A6["Decision<br>(클라우드 DB 기획 결의)"]
        A6 --> A7["Next System Model<br>(DB 확장 준비 아키텍처)"]
    end

    subgraph Bridge ["Epistemic Bridge (인지적 가교)"]
        T["지식의 수직 전이<br>(로컬 단독 실행 웹 ➔ 실시간 풀스택 웹/앱)"]
    end

    subgraph Loop_B ["05. Rolling Paper 개발 사이클"]
        B1["System Model<br>(1:N 관계형 테이블 설계)"] --> B2["Implementation<br>(Supabase SQL & Auth 연동)"]
        B2 --> B3["Evaluation<br>(포스트잇 드래그 DND 테스트)"]
        B3 --> B4["Evidence<br>(RLS 권한 에러 42501 발생)"]
        B4 --> B5["Insight<br>(웹소켓 기반 실시간 동기화 필요성)"]
        B5 --> B6["Decision<br>(RLS 정교화, Expo WebView 패키징)"]
        B6 --> B7["Next System Model<br>(실시간 하이브리드 분산 아키텍처)"]
    end

    A7 --> T
    T --> B1

    style Loop_A fill:#111c30,stroke:#06b6d4,stroke-width:1px,color:#fff
    style Loop_B fill:#181130,stroke:#8b5cf6,stroke-width:1px,color:#fff
    style Bridge fill:#050c18,stroke:#fff,stroke-dasharray: 5,5,color:#fff
```

---

## 2. 각 서브 프로젝트별 `artifacts/` 폴더가 가지는 메타적 의미

안티그래비티 도서의 모든 실습 폴더(`01-hello-antigravity`, `04-mbti-test`, `05-rolling-paper` 등) 밑에는 어김없이 `artifacts` 혹은 유사한 기록 보관용 디렉토리가 존재합니다. 이 폴더가 갖는 전문가 관점에서의 **3대 핵심적 의미**는 다음과 같습니다.

### ① 외부 장기 기억 장치 (Externalized Long-term Memory)
- **인지 과학적 현상**: LLM 에이전트와 인간 개발자 모두 대화 세션이 길어지거나 파일 수가 늘어날 때 **컨텍스트 유실(Context Decay)** 혹은 작동 기억(Working Memory) 오버플로우를 겪습니다.
- **해결적 의미**: `artifacts` 폴더는 현재 프로젝트가 도달한 기술적 합의점, 설계 규칙, 구현 스크린샷 등을 물리 파일(`implementation_plan.md`, `walkthrough.md`)로 외재화(Externalization)해 두는 **"하드웨어 기억 저장소"**입니다. 에이전트는 새로운 세션을 시작할 때 이 폴더를 파싱함으로써 이전 대화 기록을 일일이 읽지 않고도 단 1초 만에 인지 상태를 재동기화(Cognitive Synchronization)할 수 있습니다.

### ② 인식론적 닻 (Epistemic Anchors)
- **공학적 현상**: 개발 중 소스 코드가 복잡하게 얽히거나 버그가 연속적으로 터질 때, 개발자와 에이전트는 본래 만들고자 했던 설계 목표를 잃어버리는 인지 편향(Cognitive Drift)을 겪습니다.
- **해결적 의미**: `artifacts` 폴더 내부의 문서들은 현재 사이클이 정상 궤도에 있는지 붙잡아 주는 **인식론적 닻(Anchor)** 역할을 합니다. `Implementation Plan`은 최초의 기준점(Base Model)을 고정해주며, `Walkthrough`는 검증된 평가 결과(Evidence)를 영수증 형태로 서명 및 밀봉하여 개발의 진척 상황을 되돌릴 수 없는 안정된 상태로 고정(Consolidation)합니다.

### ③ 인간-에이전트 간의 협업 승인 프로토콜 (Human-Agent Trust Gate)
- **조직적 현상**: 에이전트에게 자율적 코딩 권한을 모두 위임할 경우, 코드베이스 전체를 엉망으로 덮어쓰거나 보안 정책을 훼손하는 사고가 발생할 수 있습니다.
- **해결적 의미**: 에이전트가 실제 파일 변경을 가하기 전에 인간에게 사전에 계획을 보고하는 통제 게이트(`implementation_plan.md`)와 완료 후 최종 차이점을 투명하게 정렬하여 배포 빌드 검증을 서명받는 게이트(`walkthrough.md`)를 `artifacts`에 영속화함으로써 **예측 가능하고 안전한(Deterministic & Safe) 자율 협업 관계**를 형성합니다.

---

## 3. 04 & 05 프로젝트의 구체적 인지 흐름 분석

### 04. MBTI Test ➔ 05. Rolling Paper의 인지 진화 경로

| 개발 루프 단계 | 04. MBTI Test (로컬 샌드박스 웹) | ➔ ➔ ➔ **Epistemic Bridge** ➔ ➔ ➔ | 05. Rolling Paper (실시간 풀스택 웹/앱) |
| :--- | :--- | :--- | :--- |
| **1. System Model** <br>(추상 표상 설계) | **로컬 테스트 플로우 기획**: `mbti_content.md`에 B급 코딩 유머 문항 및 가중치 표상 설계. | ➔ 단일 사용자 UI 구조에서 다중 접속 영속 데이터 구조로 정신 모델 확장 | **관계형 DB 설계**: Supabase PostgreSQL 기반 `boards` 및 `messages` 테이블 스키마 설계. |
| **2. Implementation** <br>(모델의 외재화) | **디자인 컴포넌트 깎기**: React 프롭스 흐름 설계 및 Shadcn/ui 디자인 가이드라인 코딩. | ➔ 정적 Tailwind CSS/Shadcn 가이드 숙련도를 클라이언트의 껍데기 UI로 이식 | **인프라 통합**: Supabase Auth 로그인 기능 연동 및 테이블 마이그레이션 SQL 쿼리 적용. |
| **3. Evaluation** <br>(예측적 검증) | **라우팅 및 상태 확인**: 인트로 ➔ 질문 ➔ 결과 화면으로의 React State 전파도 검사. | ➔ 로컬 클라이언트 메모리 테스트에서 런타임 보안/물리 동작 검사로 전이 | **보안 및 상호작용 검사**: 로그인 세션별 방 개설 권한 및 포스트잇 드래그 DND 좌표 수집 테스트. |
| **4. Evidence** <br>(원시 데이터 포착) | **공유 오류 수집**: 카카오톡 SDK script 로딩 실패 및 새로고침 시 닉네임 상태 증발 에러 포착. | ➔ 단순 웹 브라우저 경고에서 RLS(행 수준 보안) 차단 및 웹소켓 단절 경고 획득 | **보안 거부 검출**: 비로그인 사용자의 Boards 쓰기 거부 `42501 (Permission Denied)` Postgres 로그 포착. |
| **5. Insight** <br>(스키마 재구성) | **로컬 상태의 한계 인식**: 로컬 브라우저 너머의 글로벌 통계 집계를 위해서는 백엔드가 필수적임을 통찰. | ➔ "정적 앱"에서 "실시간 다중 접속 데이터 허브"로 개발자의 인지적 스키마 팽창 | **웹소켓 및 모바일 필요성 획득**: REST 폴링 한계 극복을 위한 Realtime Channel 도입 및 모바일 앱 포팅 통찰. |
| **6. Decision** <br>(행동 계획 결정) | **백엔드 솔루션 검토**: 다음 프로젝트에 백엔드 인프라(Supabase) 및 인증, RLS 보안을 탑재하기로 확정. | ➔ 지름길 계획: Supabase DB + Expo WebView + Realtime을 다음 프로젝트에 전격 이식 | **풀스택 최적화 확정**: RLS `auth.uid()` 보강, `Subscribe Realtime` API 적용 및 Expo React Native WebView 제작 확정. |
| **7. Next Sys Model** <br>(지식 정착) | **클라우드 준비 상태**: UI/UX 가이드는 숙련되었으며, DB 확장 가능성을 품은 고도화 상태 요약 보존. | ➔ 한 차원 진화한 지식 뭉치(Schema Block)를 안착하여 새 루프 개시 | **완성형 분산 생태계**: Vercel(Client) + Supabase(DB/Realtime) + Expo(Mobile)가 융합된 최종 아키텍처 수립. |

---

## 4. 결론 및 메타프로그래밍적 시사점

각 서브 프로젝트의 `artifacts` 폴더에 축적되는 기록들은 개발이 진행될수록 층층이 쌓여가는 **지식의 나이테**와 같습니다. 

안티그래비티 에이전트는 이 나이테들을 추적하여 앞서 작성한 코드의 아키텍처적 맥락을 잊지 않고, 인간 개발자는 이 아티팩트의 승인 과정을 통해 에이전트의 작동 방식을 명확히 통제합니다. 이러한 인지적 가교(Bridge)가 존재하기 때문에 `04` 프로젝트의 UI 디자인 경험이 `05` 프로젝트의 고도화된 풀스택 롤링페이퍼 서비스의 밑거름으로 완벽히 전이될 수 있었습니다.
