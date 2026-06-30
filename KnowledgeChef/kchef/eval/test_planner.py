import pytest
import yaml
import glob
import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Make debug output safe on Windows consoles that default to cp949.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# standalone planner implementation import
from kchef.planner_agent import PlannerPipeline, load_system_model
from kchef.eval.scorer import PlanningScorer

# ========== 디버깅 출력 ==========
print("=" * 60)
print("🔍 test_planner.py 디버깅 정보")
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"스크립트 위치: {__file__}")

# 벤치마크 파일 검색 경로 (현재 파일 기준으로 상대 경로 설정)
base_dir = Path(__file__).parent  # kchef/eval/
benchmark_pattern = str(base_dir / "benchmark" / "q*.yaml")
print(f"벤치마크 패턴: {benchmark_pattern}")

# glob로 파일 목록 확인
file_list = glob.glob(benchmark_pattern)
print(f"발견된 YAML 파일: {file_list}")

# ========== 벤치마크 로딩 ==========
BENCHMARKS = []
for path in sorted(file_list):
    print(f"📄 로딩 중: {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            data["_benchmark_path"] = str(Path(path))
            BENCHMARKS.append(data)
            print(f"   ✅ 로드 성공: {data.get('id', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 로드 실패: {e}")

print(f"📊 총 {len(BENCHMARKS)}개의 벤치마크 케이스 로드됨")
print("=" * 60)

# BENCHMARKS가 비어 있으면 테스트가 모두 SKIP 됨 → 경고
if not BENCHMARKS:
    print("⚠️ 벤치마크 파일이 없습니다. 테스트가 모두 SKIP됩니다.")

scorer = PlanningScorer()


def _export_ir(case, actual_ir):
    benchmark_path = Path(case["_benchmark_path"])
    output_path = benchmark_path.with_suffix(".json")
    output_path.write_text(
        json.dumps(actual_ir.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"   IR 저장됨: {output_path}")


@pytest.fixture
def planner():
    """PlannerPipeline fixture"""
    print("🔧 PlannerPipeline fixture 생성 중...")
    system_model = load_system_model(Path("data/techshop.db"))
    print(f"   시스템 모델 로드 완료: tables={len(system_model.get('tables', {}))}개")
    return PlannerPipeline(system_model, skills_dir="kchef")


@pytest.mark.parametrize("case", BENCHMARKS, ids=[b.get("id", "unknown") for b in BENCHMARKS])
def test_planner_ir_quality(planner, case):
    """각 벤치마크 질의에 대해 Planner IR 품질을 검증한다."""
    print(f"\n🧪 테스트 실행: {case.get('id')}")
    print(f"   질문: {case.get('question')}")

    actual_ir = planner.plan(case["question"])
    print(f"   생성된 IR intent: {actual_ir.intent}")
    print(f"   생성된 IR steps: {len(actual_ir.steps)}개")
    print("   생성된 IR:")
    print(json.dumps(actual_ir.to_dict(), ensure_ascii=False, indent=2))
    _export_ir(case, actual_ir)

    score = scorer.score(actual_ir.to_dict(), case["expected_ir"])
    print(f"   점수: schema_valid={score.schema_valid}, intent_correct={score.intent_correct}, "
          f"source_correct={score.source_correct}, overall_f1={score.overall_f1:.2f}")

    # 최소 기준
    assert score.schema_valid, f"[{case['id']}] IR이 스키마를 위반"
    assert score.intent_correct, f"[{case['id']}] Intent 불일치"
    assert score.source_correct, f"[{case['id']}] Source 불일치"
    assert score.overall_f1 >= 0.7, f"[{case['id']}] Overall F1 {score.overall_f1:.2f} < 0.70"


@pytest.mark.parametrize("case",
    [b for b in BENCHMARKS if b.get("ambiguity_type")],
    ids=[b.get("id", "unknown") for b in BENCHMARKS if b.get("ambiguity_type")]
)
def test_ambiguity_resolution(planner, case):
    """모호성이 있는 질의에 대해 해소 능력을 검증한다."""
    print(f"\n🧪 모호성 테스트 실행: {case.get('id')}")
    print(f"   질문: {case.get('question')}")
    print(f"   ambiguity_type: {case.get('ambiguity_type')}")

    actual_ir = planner.plan(case["question"])
    print("   생성된 IR:")
    print(json.dumps(actual_ir.to_dict(), ensure_ascii=False, indent=2))
    _export_ir(case, actual_ir)
    score = scorer.score(actual_ir.to_dict(), case["expected_ir"])

    print(f"   ambiguity_resolution_rate: {score.ambiguity_resolution_rate:.2f}")
    assert score.ambiguity_resolution_rate >= 0.8, \
        f"[{case['id']}] 모호성 해소율 {score.ambiguity_resolution_rate:.2f} < 0.80"


if __name__ == "__main__":
    raise SystemExit(pytest.main([str(Path(__file__)), "-p", "no:cacheprovider", *sys.argv[1:]]))
