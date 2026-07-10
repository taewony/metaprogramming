• 좋아요. 지금 CLI로 ActiveGraph 동작을 추적하려면 이렇게 보면 됩니다.

  핵심 모델
  현재 text-to-sql ask는 매 실행마다 새 Graph()를 만듭니다.

  실행 전 상태는 개념적으로:

  objects:   []
  relations: []
  events:    []
  behaviors: [
    parse_intent       on question.submitted -> creates question, intent
    compile_sql        on intent.created     -> creates sql_query
    execute_sql        on sql.generated      -> creates query_result
    synthesize_answer  on sql.executed       -> creates answer
  ]

  behavior 등록 위치는 여기입니다:

  activegraph/text-to-sql-agent/src/cli/text_to_sql.py

  1. 실행

  cd D:\code\metaprogramming\KnowledgeChef\activegraph\text-to-sql-agent
  $env:PYTHONPATH = "src"
  $env:PYTHONDONTWRITEBYTECODE = "1"

  python -m activegraph text-to-sql ask "의사는 모두 몇명이야?" --json

  출력에서 run_id, trace_file, graph_file을 확인합니다.

  2. Event Log 순서 보기

  $run = "<run_id>"

  Get-Content .tests/runs/$run/trace.jsonl |
    ForEach-Object {
      $_ | ConvertFrom-Json | Select-Object id,type,actor
    }

  성공 케이스에서는 대략 이런 흐름입니다:

  evt_001 question.submitted user
  evt_002 behavior.started   runtime
  evt_003 object.created     parse_intent
  evt_004 object.created     parse_intent
  evt_005 relation.created   parse_intent
  evt_006 intent.created     parse_intent
  evt_007 behavior.completed runtime
  evt_008 behavior.started   runtime
  evt_009 object.created     compile_sql
  evt_010 relation.created   compile_sql
  evt_011 sql.generated      compile_sql
  evt_013 behavior.started   runtime
  evt_014 object.created     execute_sql
  evt_016 patch.applied      execute_sql
  evt_017 sql.executed       execute_sql
  evt_019 behavior.started   runtime
  evt_020 object.created     synthesize_answer
  evt_022 answer.created     synthesize_answer
  evt_024 runtime.idle       runtime

  3. 최종 Graph 보기

  Get-Content .tests/runs/$run/graph.json |
    Select-Object -ExpandProperty objects |
    Select-Object id,type,data

  예상 object:
  intent#2        intent
  sql_query#3     sql_query
  query_result#4  query_result
  answer#5        answer

  Get-Content .tests/runs/$run/graph.json |
    ConvertFrom-Json |
    Select-Object -ExpandProperty relations |
    Select-Object id,source,target,type

  예상 relation:

  intent#2     -> question#1      derived_from
  sql_query#3  -> intent#2        derived_from
  sql_query#3  -> query_result#4  executed_as
  answer#5     -> query_result#4  derived_from

  4. 실패한 behavior만 보기
  예를 들어 "의사는 모두 몇명?"이 실패하면:

  python -m activegraph text-to-sql ask "의사는 모두 몇명?" --json

  그 run id로:

  Get-Content .tests/runs/$run/trace.jsonl |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object type -eq "behavior.failed" |
    ConvertTo-Json -Depth 20

  이걸 보면 어느 behavior가 실패했는지 나옵니다. 이 경우에는 보통 parse_intent가 실패하고, 개선 대상은
  deterministic_plan()의 한국어 intent matching rule입니다.

  지금 구조에서는 ask 실행 전/후 diff를 CLI가 직접 출력하진 않지만, trace.jsonl이 “변화 과정”, graph.json이 “최종 상
  태”입니다. 다음 개선으로 text-to-sql inspect-run <run_id> 같은 명령을 추가하면 object/relation/event를 한 화면에서 더
  쉽게 볼 수 있습니다.