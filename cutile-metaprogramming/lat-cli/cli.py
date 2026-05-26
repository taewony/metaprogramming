# lat-cli/cli.py (일부)
import argparse
from pathlib import Path
from required_md import print_missing_report

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # nano-vllm-cutile/
lat_md_dir = PROJECT_ROOT / "lat.md"

def main():
    parser = argparse.ArgumentParser(prog="lat", description="GPU Kernel Dev 지식 그래프 도구")
    subparsers = parser.add_subparsers(dest="command")

    # check-required
    subparsers.add_parser("check-required", help="lat.md 필수 파일 존재 여부 검증")

    # check
    subparsers.add_parser("check", help="[[wiki link]] 및 @lat: 참조 무결성 검증")

    # gap
    subparsers.add_parser("gap", help="outcomes.md 기반 차이 분석")

    # help (기타 명령어)
    subparsers.add_parser("help", help="...")
    
    args = parser.parse_args()

    if args.command == "check-required":
        exit_code = print_missing_report(PROJECT_ROOT)
        exit(exit_code)
    
    elif args.command == "check":
        from checker import print_check_report
        exit_code = print_check_report(lat_md_dir)
        exit(exit_code)
    # ...

if __name__ == "__main__":
    main()