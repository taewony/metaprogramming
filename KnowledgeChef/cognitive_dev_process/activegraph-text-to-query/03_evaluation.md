# 03 Evaluation

## Evaluation Goal

The next agent line is evaluated by whether it can preserve proven DB behavior while improving architecture.

## Frozen Baseline Evaluation

The frozen Text-to-SQL line has this last known verification:

```text
python -m pytest tests/test_activegraph_text_to_sql_tdd.py -q
63 passed
```

That result becomes the compatibility oracle for the new Text-to-Query line.

## Required Compatibility Evals

The new line should eventually pass:

```text
hospital consolidated eval
techshop consolidated eval
third-party pack import smoke
eval-run export smoke
eval-run attach-score smoke
inspect graph evidence smoke
```

## Evaluation Artifacts

Each eval should produce learning artifacts:

```text
.tests/eval-runs/<eval_run_id>/
  manifest.json
  summary.json
  eval_events.jsonl
  cases/<case_id>/
    result.json
    trace.jsonl
    graph.json
    scoring-input.json
```

## Learning Interpretation

Evaluation is not only pass/fail. It answers:

- Which behavior fired?
- Which graph object changed?
- Which assumption was recorded?
- Which SQL was generated?
- Which evidence supports the final answer?
- Which failure should become a new system-model rule or adaptation proposal?
