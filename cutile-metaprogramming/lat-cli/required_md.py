"""lat.md 필수 마크다운 파일 존재 여부 검증기"""
from pathlib import Path
from typing import List, Tuple

# lat.md/ 아래 반드시 존재해야 하는 파일 목록 (프로젝트 루트 기준 상대 경로)
REQUIRED_MD_FILES: List[str] = [
    "lat.md/architecture.md",
    "lat.md/outcomes.md",
    "lat.md/tests/migration-pass-criteria.md",
    # patterns 디렉토리에는 최소 1개 이상의 .md 파일이 있어야 함
]

REQUIRED_DIRS: List[str] = [
    "lat.md/patterns",
    "lat.md/retrospectives",
    "lat.md/tests",
    "lat.md/.cache",
]


def check_required_files(project_root: Path) -> Tuple[bool, List[str]]:
    """
    필수 마크다운 파일과 디렉토리 존재 여부를 검증한다.
    
    Returns:
        (성공 여부, 누락된 항목의 사용자 친화적 메시지 리스트)
    """
    missing: List[str] = []
    lat_md_dir = project_root / "lat.md"

    # 1. 기본 디렉토리 존재 여부
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing.append(f"[MISSING DIRECTORY] {dir_path}/ (mkdir -p {dir_path})")

    # 2. 필수 파일 존재 여부
    for file_path in REQUIRED_MD_FILES:
        full_path = project_root / file_path
        if not full_path.is_file():
            missing.append(f"[MISSING FILE] {file_path}")

    # 3. patterns/ 디렉토리 안에 최소 1개의 .md 파일이 있는지
    patterns_dir = lat_md_dir / "patterns"
    if patterns_dir.is_dir():
        pattern_files = list(patterns_dir.rglob("*.md"))
        if not pattern_files:
            missing.append(
                "[EMPTY DIRECTORY] lat.md/patterns/ — "
                "최소 1개의 설계 패턴 .md 파일이 필요합니다 (예: online-softmax.md)"
            )
    else:
        missing.append("[MISSING DIRECTORY] lat.md/patterns/")

    # 4. tests/ 디렉토리 안에 최소 1개의 .md 파일이 있는지
    tests_dir = lat_md_dir / "tests"
    if tests_dir.is_dir():
        test_files = list(tests_dir.rglob("*.md"))
        if not test_files:
            missing.append(
                "[EMPTY DIRECTORY] lat.md/tests/ — "
                "최소 1개의 테스트 명세 .md 파일이 필요합니다"
            )

    success = len(missing) == 0
    return success, missing


def print_missing_report(project_root: Path) -> int:
    """
    필수 파일 검증 결과를 터미널에 출력하고 종료 코드를 반환한다.
    사용법: python lat-cli/cli.py check-required
    """
    success, missing = check_required_files(project_root)

    if success:
        print("✅ 모든 필수 lat.md 파일과 디렉토리가 존재합니다.")
        print("   lat check 를 실행할 수 있습니다.")
        return 0
    else:
        print("❌ lat.md/ 아래 필수 구성요소가 누락되었습니다:\n")
        for item in missing:
            print(f"  • {item}")
        print(f"\n총 {len(missing)}개 항목이 누락되었습니다.")
        print("위 항목들을 생성한 후 lat check 를 실행하세요.")
        return 1