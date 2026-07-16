```
제 3자가 SQLite DB file 및 OKF bundle을 각각 하나씩 제공하고, 현재의 agent 시스템이 이를 분석해서 이에 대한 자연어 검
  색, 질의에 응답할 수 있는 시스템이 되도록 준비하고, 제3자가 준비한 eval 항목들을 수행한 후에 event log를 바탕으로 제
  3자가 평가점수를 매기는 절차를 수행하도록 하려면, 현재 system model v99 기준으로 잘 준비 된 것인지 분석 검토해줘.
```

현재 구조는 “제3자 DB+OKF를 수동으로 pack화해서 검증/평가하는 실험 기반”은 준비되어 있습니다. 하지만 “제3자가 DB/OKF/eval만 주면 agent가 자동 분석해서 범용 자연어 질의와 외부 채점 절차까지 안정적으로 수행”하는 수준
  은 아직 아닙니다.

  잘 준비된 부분

  - packs.yaml 기반으로 DB, event store, OKF bundle root, system-model을 pack 단위로 분리할 수 있습니다.
  - pack validate --all은 현재 통과합니다. DB readable, event-store parent writable, OKF schema projection, SQLite
    schema alignment까지 확인합니다.

  - pack schema <pack>로 OKF bundle의 table/column metadata를 graph projection으로 볼 수 있습니다.
  - text-to-sql eval은 pack별 eval file을 고르고 실행합니다.
  - 실행마다 SQLite event store, .tests/runs/<run_id>/trace.jsonl, graph.json이 남습니다.
  - inspect, adapt, adapt-accept로 실패 run을 분석하고 adaptation proposal/eval draft/patch hint를 만들 수 있습니다.

  부족한 부분

  - 제3자 pack을 자동 생성하는 pack import/pack scaffold-from-db-okf가 없습니다.
  - 임의 DB/OKF에서 system-model.<domain>.v11.yaml을 자동 생성하지 못합니다. 현재 자연어 질의는 RuleCatalog의
    declarative rules가 있어야 동작합니다.

  - generic NL-to-SQL planner는 아직 없습니다. sql_planner.py에는 VIP, 이번 달 매출, hospital appointment 같은 domain-
    specific logic이 남아 있습니다.

  - eval scoring은 CLI JSON payload에는 있지만, eval.scored 같은 first-class event로 event log에 저장되지는 않습니다.
  - 제3자가 event log만 보고 점수를 매기는 표준 export bundle이 아직 없습니다.
  - v99는 status: production_ready라고 쓰여 있지만 실제 roadmap상 v99_production_north_star는 aspirational이고,
    v12_okf_kb_ingestion, v13_sql_rag_parallelism은 deferred입니다. 현재 구현 상태와 문서 상태가 어긋납니다.

  제 생각
  현재 system은 **“pack-configurable deterministic text-to-SQL harness”**로는 꽤 건강합니다. 하지만 제3자 온보딩 목표에
  는 다음 4개가 필요합니다.

  1. pack import thirdparty --db ... --okf ... --evals ...
      - DB/OKF/eval/event-store path를 등록
      - OKF schema alignment 수행
      - eval manifest 자동 갱신

  2. system-model bootstrap
      - OKF schema에서 schema_projection 자동 생성
      - 기본 behavior_model, entity_validation_model, 빈 rule_catalog scaffold 생성
      - 이후 eval 실패를 통해 rules/adaptations를 쌓는 방식

  3. 외부 평가용 run bundle
      - eval_run_id
      - case별 run_id
      - prompt, answer, SQL, rows, event trace path
      - internal score와 third-party score를 분리 저장
      - eval.scored, external_judgment.recorded event 추가

  4. generic planner 전략 결정
      - 단기: eval 기반 deterministic rule induction
      - 중기: LLM planner advisor가 SQL을 직접 실행하지 않고 “candidate intent/rule patch”만 제안
      - 장기: OKF schema + constraints 기반 bounded SQL synthesis

  따라서 제 판단은: v99 기준의 방향성은 맞지만, 현재 구현은 v11 deterministic pack runtime 단계입니다. 제3자 평가 플랫폼
  으로 쓰려면 v12/RAG보다 먼저 “third-party pack onboarding + eval-run event protocol”을 v11.5 정도로 추가하는 게 맞습니
  다.
  
---

```
• design-spec.md 업데이트 완료했습니다.

  핵심 반영 내용:

  - v11 deterministic pack runtime 이후의 다음 단계로 v11.5 Third-Party Pack Onboarding And Eval-Run Protocol 추가
  - 제3자가 제공하는 입력을 SQLite DB + OKF schema bundle + eval JSONL로 명확화
  - pack import, pack validate, pack schema, text-to-sql eval, eval-run export, eval-run attach-score 흐름 정리
  - eval-run event protocol 정의: eval_run, eval_case, eval_case_result, eval_score, eval.started, eval.case_completed,
    eval.case_scored 등

  - 외부 평가자가 event log / graph / SQL / answer artifact를 기준으로 점수를 매기는 절차 추가
  - OKF KB ingestion, RAG query, sub-agent orchestration은 전부 Future Work로 이동
  - Near-Term Implementation Plan, Resolved Questions, Deferred Decisions, Design Rules를 v11.5 중심으로 정렬

  추가로 작업 메모리도 갱신했습니다:

  - .agent/memory/working/WORKSPACE.md
  - .agent/memory/episodic/AGENT_LEARNINGS.jsonl

  검증:

  - rg로 주요 섹션 존재 확인
  - git diff --check -- design-spec.md 통과
  - 변경 파일: design-spec.md, workspace memory, episodic memory
  ```