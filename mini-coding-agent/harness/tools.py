# harness/tools.py

import shutil
import subprocess

from pathlib import Path

from harness.utils import clip
from harness.context import IGNORED_PATH_NAMES


# ------------------------------------------------------------
# 내부 함수
# ------------------------------------------------------------

def _safe_path(root, path):
    """
    workspace 내부의 안전한 경로 반환
    """

    root = Path(root).resolve()

    target = (root / path).resolve()

    if root not in target.parents and target != root:
        raise ValueError("Access outside workspace")

    return target


# ------------------------------------------------------------
# list_files
# ------------------------------------------------------------

def tool_list_files(root, path="."):
    """
    디렉터리 목록 반환
    """

    target = _safe_path(root, path)

    if not target.exists():
        return "Directory not found."

    if not target.is_dir():
        return "Not a directory."

    result = []

    for item in sorted(target.iterdir()):

        if item.name in IGNORED_PATH_NAMES:
            continue

        prefix = "[D]" if item.is_dir() else "[F]"

        result.append(f"{prefix} {item.name}")

    return "\n".join(result)


# ------------------------------------------------------------
# read_file
# ------------------------------------------------------------

def tool_read_file(root, path, start=1, end=200):
    """
    파일 일부 읽기
    """

    target = _safe_path(root, path)

    if not target.exists():
        return "File not found."

    lines = target.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines()

    start = max(start, 1)

    end = min(end, len(lines))

    output = []

    for number in range(start, end + 1):

        output.append(
            f"{number:4d}: {lines[number-1]}"
        )

    return clip("\n".join(output))


# ------------------------------------------------------------
# search
# ------------------------------------------------------------

def tool_search(root, pattern, path="."):
    """
    문자열 검색
    """

    base = _safe_path(root, path)

    results = []

    for file in base.rglob("*"):

        if not file.is_file():
            continue

        if any(part in IGNORED_PATH_NAMES for part in file.parts):
            continue

        try:

            lines = file.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines()

            for number, line in enumerate(lines, 1):

                if pattern.lower() in line.lower():

                    results.append(
                        f"{file.relative_to(root)}:{number}: {line.strip()}"
                    )

        except Exception:
            pass

    if not results:
        return "No matches."

    return clip("\n".join(results))


# ------------------------------------------------------------
# run_shell
# ------------------------------------------------------------

def tool_run_shell(root, command, timeout=20):
    """
    Shell 명령 실행
    """

    try:

        result = subprocess.run(

            command,

            cwd=root,

            shell=True,

            capture_output=True,

            text=True,

            timeout=timeout,

        )

        output = result.stdout

        if result.stderr:

            output += "\n" + result.stderr

        return clip(output)

    except subprocess.TimeoutExpired:

        return "Command timeout."

    except Exception as e:

        return str(e)


# ------------------------------------------------------------
# write_file
# ------------------------------------------------------------

def tool_write_file(root, path, content):
    """
    파일 저장
    """

    target = _safe_path(root, path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        content,
        encoding="utf-8",
    )

    return f"Saved: {path}"


# ------------------------------------------------------------
# patch_file
# ------------------------------------------------------------

def tool_patch_file(root, path, old_text, new_text):
    """
    문자열 치환
    """

    target = _safe_path(root, path)

    if not target.exists():
        return "File not found."

    text = target.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    if old_text not in text:
        return "Text not found."

    text = text.replace(
        old_text,
        new_text,
        1,
    )

    target.write_text(
        text,
        encoding="utf-8",
    )

    return f"Patched: {path}"