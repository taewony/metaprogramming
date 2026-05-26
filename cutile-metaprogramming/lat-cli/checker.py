"""
lat.md 참조 무결성 검증기 (check)
- Markdown [[wiki link]] 유효성
- 소스 코드 @lat: 주석 유효성
- 디렉토리 인덱스 파일 검증
- 섹션 구조 검증

TypeScript 원본: https://github.com/1st1/lat.md/blob/main/src/cli/check.ts
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, NamedTuple
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class CheckError:
    file: str          # 프로젝트 루트 기준 상대 경로
    line: int          # 1-indexed
    target: str        # 문제가 된 링크/섹션
    message: str       # 여러 줄 메시지 가능 (개행 포함)


@dataclass
class IndexError:
    dir: str
    message: str
    snippet: Optional[str] = None


@dataclass
class Section:
    id: str                          # 예: "architecture#Pipeline"
    file: str                        # 파일 경로
    heading: str                     # 제목 텍스트
    content: str                     # 전체 내용
    start_line: int                  # 시작 라인 (1-indexed)
    children: List[Section] = field(default_factory=list)
    first_paragraph: Optional[str] = None  # 첫 번째 비어 있지 않은 단락


@dataclass
class Ref:
    target: str
    line: int
    raw: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_EXTENSIONS: Set[str] = {
    '.py', '.ts', '.js', '.rs', '.go', '.java', '.cpp', '.c', '.h',
    '.cxx', '.hpp', '.cc', '.hh', '.cs', '.swift', '.kt', '.scala',
    '.rb', '.sh', '.bash', '.zsh', '.sql', '.r', '.jl',
}
MAX_BODY_LENGTH = 250

# Markdown heading pattern
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?\s*$', re.MULTILINE)
# Wiki link pattern — captures [[target]] or [[target|label]]
WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]')
# Frontmatter pattern (YAML between ---)
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


# ---------------------------------------------------------------------------
# Markdown / section helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> Dict[str, object]:
    """Parse YAML-like frontmatter from Markdown content.
    Returns a dict with frontmatter keys. Handles only simple scalars and lists.
    """
    m = FRONTMATTER_PATTERN.match(content)
    if not m:
        return {}
    fm: Dict[str, object] = {}
    for line in m.group(1).split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            key, val = key.strip(), val.strip()
            if val.lower() == 'true':
                fm[key] = True
            elif val.lower() == 'false':
                fm[key] = False
            else:
                # strip quotes
                if (val.startswith('"') and val.endswith('"')) or \
                   (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                fm[key] = val
        elif line.startswith('- '):
            # list item — accumulate into 'tags' for simplicity
            tag = line[2:].strip().strip('"').strip("'")
            lst = fm.setdefault('tags', [])
            if isinstance(lst, list):
                lst.append(tag)
    return fm


def extract_refs(file_path: str, content: str) -> List[Ref]:
    """Extract [[wiki link]] references from Markdown content with line numbers,
    ignoring those inside inline code blocks (backticks)."""
    refs: List[Ref] = []
    for i, line in enumerate(content.split('\n'), start=1):
        # Split the line by backticks to separate code spans from regular text
        parts = line.split('`')
        # Process only parts that are outside of code spans
        for j, part in enumerate(parts):
            # Even indices are outside code spans, odd indices are inside
            if j % 2 == 0: # Outside code span
                for m in WIKI_LINK_PATTERN.finditer(part):
                    # The line number `i` is correct for the entire line.
                    refs.append(Ref(target=m.group(1), line=i, raw=m.group(0)))
    return refs


def parse_sections(file_path: str, content: str) -> List[Section]:
    """Parse Markdown content into a hierarchical section list."""
    lines = content.split('\n')
    # Remove frontmatter for parsing purposes
    fm_match = FRONTMATTER_PATTERN.match(content)
    body_start = 0
    if fm_match:
        body_start = fm_match.end()
    body = content[body_start:]

    # Find all headings
    headings: List[Tuple[int, int, str]] = []  # (level, line_idx, heading_text)
    for m in HEADING_PATTERN.finditer(body):
        level = len(m.group(1))
        text = m.group(2).strip()
        line_idx = body[:m.start()].count('\n')
        headings.append((level, line_idx + body_start // len(lines[0]) + 1, text))

    # Build section list (flat)
    sections: List[Section] = []
    for idx, (level, line_num, heading) in enumerate(headings):
        # Determine section ID
        # 1. Explicit {#id}
        full_match = HEADING_PATTERN.search(body)
        # Build a clean section id from the heading text
        display_heading, heading_id = parse_heading_id(heading)
        # Prepend filename stem
        stem = Path(file_path).stem
        # heading_id에 이미 '#'이 포함되어 있으면 그대로 사용
        if '#' in heading_id:
            section_id = heading_id
        else:
            section_id = f"{stem}#{heading_id}"

        # Content: from this heading to next heading of same or higher level
        start_line = line_num
        end_line = None
        for j in range(idx + 1, len(headings)):
            if headings[j][0] <= level:
                end_line = headings[j][1] - 1
                break
        # Extract content
        if end_line:
            section_content = '\n'.join(lines[start_line:end_line])
        else:
            section_content = '\n'.join(lines[start_line - 1:])

        # First paragraph
        first_para = _extract_first_paragraph(section_content)

        sections.append(Section(
            id=section_id,
            file=file_path,
            heading=heading,
            content=section_content,
            start_line=start_line,
            first_paragraph=first_para,
        ))

    # Build parent-child relationships
    _build_hierarchy(sections)

    return sections

# checker.py - 기존 HEADING_PATTERN 아래에 추가

EXPLICIT_ID_PATTERN = re.compile(r'\s*\[\[([^\]]+)\]\]\s*$')

def parse_heading_id(heading_text: str) -> Tuple[str, str]:
    """
    제목 텍스트에서 명시적 ID와 표시용 텍스트를 분리합니다.
    
    예: "Inference Pipeline [[pipeline]]" → ("Inference Pipeline", "pipeline")
    예: "Scheduler [[scheduler#Request Lifecycle]]" → ("Scheduler", "scheduler#Request Lifecycle")
    예: "Overview" → ("Overview", "overview")
    """
    m = EXPLICIT_ID_PATTERN.search(heading_text)
    if m:
        explicit_id = m.group(1)
        display_text = heading_text[:m.start()].strip()
        return display_text, explicit_id
    else:
        # 명시적 ID가 없으면 제목 기반으로 ID 생성
        return heading_text, _heading_to_id(heading_text)
        
def _heading_to_id(heading: str) -> str:
    """Convert heading text to a URL-friendly ID."""
    # Remove special characters, convert spaces to hyphens
    text = heading.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text


def _extract_first_paragraph(content: str) -> Optional[str]:
    """Extract the first non-empty, non-heading paragraph from section content."""
    lines = content.split('\n')
    in_heading = True  # skip the heading line itself
    paragraph_lines: List[str] = []
    for line in lines:
        if in_heading:
            if line.startswith('#'):
                continue
            in_heading = False
        if not line.strip():
            if paragraph_lines:
                break
            continue
        if line.startswith('#'):
            break
        paragraph_lines.append(line)
    if paragraph_lines:
        return ' '.join(paragraph_lines)
    return None


def _build_hierarchy(sections: List[Section]) -> None:
    """Build parent-child relationships among sections."""
    # Simple approach: assign children based on indentation level
    # This is a simplified version — for now, all sections are roots
    pass


def flatten_sections(sections: List[Section]) -> List[Section]:
    """Flatten hierarchical sections into a single list."""
    result: List[Section] = []
    for s in sections:
        result.append(s)
        result.extend(flatten_sections(s.children))
    return result


# ---------------------------------------------------------------------------
# File index
# ---------------------------------------------------------------------------

def build_file_index(sections_by_file: Dict[str, List[Section]]) -> Dict[str, str]:
    """
    Build a mapping from short stem to fully qualified file path.
    If multiple files share the same stem, short access becomes ambiguous.
    """
    index: Dict[str, str] = {}
    for file_path in sections_by_file:
        stem = Path(file_path).stem
        if stem not in index:
            index[stem] = file_path
        else:
            # Mark as ambiguous by removing
            index[stem] = ''
    return index


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class ResolveResult(NamedTuple):
    resolved: str        # fully qualified id (e.g., "architecture#Pipeline")
    ambiguous: bool
    suggested: Optional[str]
    candidates: List[str]


def resolve_ref(
    target: str,
    section_ids: Set[str],
    file_index: Dict[str, str],
) -> ResolveResult:
    """
    Resolve a wiki link target against the known section IDs and file index.
    
    Resolution order:
    1. Exact match against section_ids (case-insensitive)
    2. If target contains '#', try exact match on file part
    3. If target is a bare name (no '#'), look up in file_index
    """
    target_lower = target.lower()

    # Exact match
    if target_lower in section_ids:
        return ResolveResult(target, False, None, [])

    # Try matching against section ids
    if '#' in target:
        file_part, _, section_part = target.partition('#')
        stem = Path(file_part).stem.lower()
        # Find sections that end with this stem#section_part
        candidates = [sid for sid in section_ids
                      if sid.lower().endswith(f"{stem}#{section_part.lower()}")]
        if len(candidates) == 1:
            return ResolveResult(candidates[0], False, None, [])
        elif len(candidates) > 1:
            return ResolveResult('', True, None, candidates)
    else:
        # Bare name — look up in file index
        stem = target.lower()
        candidates = [sid for sid in section_ids
                      if sid.lower().startswith(f"{stem}#")]
        if len(candidates) == 1:
            return ResolveResult(candidates[0], False, None, [])
        elif len(candidates) > 1:
            return ResolveResult('', True, candidates[0], candidates)

    # Not found
    return ResolveResult('', False, None, [])


# ---------------------------------------------------------------------------
# Source code reference scanning
# ---------------------------------------------------------------------------

LAT_PATTERN = re.compile(r'@lat:\s*\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]')


def scan_code_refs(project_root: Path, source_extensions: Set[str] = SOURCE_EXTENSIONS) -> List[Ref]:
    """Scan source code files for @lat: [[...]] annotations."""
    refs: List[Ref] = []
    for ext in source_extensions:
        for file_path in project_root.rglob(f'*{ext}'):
            # Skip hidden directories and node_modules
            if any(part.startswith('.') for part in file_path.parts):
                continue
            if 'node_modules' in file_path.parts:
                continue
            if '__pycache__' in file_path.parts:
                continue
            try:
                content = file_path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, PermissionError):
                continue
            for i, line in enumerate(content.split('\n'), start=1):
                for m in LAT_PATTERN.finditer(line):
                    refs.append(Ref(
                        target=m.group(1),
                        line=i,
                        raw=m.group(0),
                    ))
    return refs


# ---------------------------------------------------------------------------
# Markdown file listing
# ---------------------------------------------------------------------------

def list_lattice_files(lat_dir: Path) -> List[Path]:
    """List all Markdown files in lat.md/ directory."""
    return sorted(lat_dir.rglob('*.md'))


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_md(lat_dir: Path) -> Tuple[List[CheckError], Dict[str, int]]:
    """
    Validate all [[wiki link]] references in Markdown files.
    
    Returns (errors, file_stats)
    """
    project_root = lat_dir.parent
    files = list_lattice_files(lat_dir)
    all_sections: Dict[str, List[Section]] = {}

    # Load all sections
    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        sections = parse_sections(str(file_path), content)
        all_sections[str(file_path)] = sections

    flat = flatten_sections([s for secs in all_sections.values() for s in secs])
    section_ids: Set[str] = {s.id.lower() for s in flat}
    file_index = build_file_index(all_sections)

    errors: List[CheckError] = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        refs = extract_refs(str(file_path), content)
        rel_path = str(file_path.relative_to(project_root))

        for ref in refs:
            resolve_result = resolve_ref(ref.target, section_ids, file_index)

            if resolve_result.ambiguous:
                errors.append(CheckError(
                    file=rel_path,
                    line=ref.line,
                    target=ref.target,
                    message=_ambiguous_message(ref.target, resolve_result.candidates, resolve_result.suggested),
                ))
            elif not any(sid.lower() == resolve_result.resolved.lower() for sid in section_ids):
                # Try source reference
                source_err = _try_resolve_source_ref(ref.target, project_root)
                if source_err:
                    errors.append(CheckError(
                        file=rel_path,
                        line=ref.line,
                        target=ref.target,
                        message=source_err,
                    ))
    file_stats = _count_by_ext(files)
    return errors, file_stats


def check_code_refs_func(lat_dir: Path) -> Tuple[List[CheckError], Dict[str, int]]:
    """
    Validate all @lat: annotations in source code.
    
    Returns (errors, file_stats)
    """
    project_root = lat_dir.parent
    files = list_lattice_files(lat_dir)
    all_sections: Dict[str, List[Section]] = {}

    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        sections = parse_sections(str(file_path), content)
        all_sections[str(file_path)] = sections

    flat = flatten_sections([s for secs in all_sections.values() for s in secs])
    section_ids: Set[str] = {s.id.lower() for s in flat}
    file_index = build_file_index(all_sections)

    scan_refs = scan_code_refs(project_root)
    errors: List[CheckError] = []
    mentioned_sections: Set[str] = set()

    for ref in scan_refs:
        resolve_result = resolve_ref(ref.target, section_ids, file_index)
        mentioned_sections.add(resolve_result.resolved.lower())

        # Compute relative path
        try:
            display_path = str(Path(ref.target).relative_to(project_root))
        except ValueError:
            display_path = ref.target

        if resolve_result.ambiguous:
            errors.append(CheckError(
                file=display_path,
                line=ref.line,
                target=ref.target,
                message=_ambiguous_message(ref.target, [], resolve_result.suggested),
            ))
        elif not any(sid.lower() == resolve_result.resolved.lower() for sid in section_ids):
            errors.append(CheckError(
                file=display_path,
                line=ref.line,
                target=ref.target,
                message=f'@lat: [[{ref.target}]] — no matching section found',
            ))

    # Check require-code-mention
    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        fm = parse_frontmatter(content)
        if not fm.get('require_code_mention'):
            continue
        sections = parse_sections(str(file_path), content)
        file_sections = flatten_sections(sections)
        leaf_sections = [s for s in file_sections if not s.children]
        rel_path = str(file_path.relative_to(project_root))
        for leaf in leaf_sections:
            if leaf.id.lower() not in mentioned_sections:
                errors.append(CheckError(
                    file=rel_path,
                    line=leaf.start_line,
                    target=leaf.id,
                    message=f'section "{leaf.id}" requires a code mention but none found',
                ))

    # Count files
    scanned_files = set()
    for ref in scan_refs:
        scanned_files.add(ref.target)
    file_stats = {'.py': len(scan_refs)} if scan_refs else {}

    return errors, file_stats


def check_sections(lat_dir: Path) -> List[CheckError]:
    """Validate section structure: every section must have a leading paragraph ≤ MAX_BODY_LENGTH chars."""
    project_root = lat_dir.parent
    files = list_lattice_files(lat_dir)
    errors: List[CheckError] = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        sections = parse_sections(str(file_path), content)
        flat = flatten_sections(sections)
        rel_path = str(file_path.relative_to(project_root))

        for section in flat:
            if not section.first_paragraph:
                errors.append(CheckError(
                    file=rel_path,
                    line=section.start_line,
                    target=section.id,
                    message=(
                        f'section "{section.id}" has no leading paragraph. '
                        f'Every section must start with a brief overview '
                        f'(≤{MAX_BODY_LENGTH} chars) summarizing what it documents — '
                        f'this powers search snippets and command output.'
                    ),
                ))
            else:
                body_len = _body_text_length(section.first_paragraph)
                if body_len > MAX_BODY_LENGTH:
                    errors.append(CheckError(
                        file=rel_path,
                        line=section.start_line,
                        target=section.id,
                        message=(
                            f'section "{section.id}" leading paragraph is {body_len} '
                            f'characters (max {MAX_BODY_LENGTH}, excluding [[wiki links]]). '
                            f'Keep the first paragraph brief — it serves as the section\'s '
                            f'summary in search results and command output.'
                        ),
                    ))

    return errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ambiguous_message(target: str, candidates: List[str], suggested: Optional[str]) -> str:
    """Format an ambiguous-ref error as structured text."""
    short_name = target.split('#')[0] if '#' in target else target
    file_list = '\n'.join(f' - "{c.split("#")[0] if "#" in c else c}.md"' for c in candidates)
    lines: List[str] = []
    if suggested:
        lines.append(f"ambiguous link '[[{target}]]' — did you mean '[[{suggested}]]'?")
    else:
        options = "', '".join(f"'[[{c}]]'" for c in candidates)
        lines.append(f"ambiguous link '[[{target}]]' — multiple paths match, use either of: {options}")
    lines.append(
        f' The short path "{short_name}" is ambiguous — {len(candidates)} files match:',
    )
    lines.append(file_list)
    lines.append(' Please fix the link to use a fully qualified path.')
    return '\n'.join(lines)


def _try_resolve_source_ref(target: str, project_root: Path) -> Optional[str]:
    """
    Try resolving a wiki link as a source code reference (e.g. [[src/foo.py#bar]]).
    Returns None if valid, or an error message string.
    """
    if '#' not in target:
        # Bare name with no # — not a source ref in markdown context
        return f"broken link [[{target}]] — no matching section found"

    file_part, _, symbol_part = target.partition('#')
    ext = Path(file_part).suffix

    if ext not in SOURCE_EXTENSIONS:
        if ext:
            supported = ', '.join(sorted(SOURCE_EXTENSIONS))
            return (
                f'broken link [[{target}]] — unsupported file extension "{ext}". '
                f'Supported: {supported}'
            )
        return f"broken link [[{target}]] — no matching section found"

    abs_path = project_root / file_part
    if not abs_path.exists():
        return f'broken link [[{target}]] — file "{file_part}" not found'

    if not symbol_part:
        # File-only link with no symbol — valid as long as file exists
        return None

    # Check that symbol exists in the file
    try:
        content = abs_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, PermissionError):
        return f'broken link [[{target}]] — cannot read "{file_part}"'

    # Python: look for def/class
    if ext == '.py':
        sym_pattern = re.compile(
            rf'^(def|class)\s+{re.escape(symbol_part)}\b', re.MULTILINE
        )
        if not sym_pattern.search(content):
            return f'broken link [[{target}]] — symbol "{symbol_part}" not found in "{file_part}"'
    else:
        # Generic: look for the symbol name
        if symbol_part not in content:
            return f'broken link [[{target}]] — symbol "{symbol_part}" not found in "{file_part}"'

    return None


def _body_text_length(body: str) -> int:
    """Count body text length excluding [[wiki link]] markers."""
    return len(re.sub(r'\[\[[^\]]*\]\]', '', body))


def _count_by_ext(paths: List[Path]) -> Dict[str, int]:
    """Count files grouped by extension."""
    stats: Dict[str, int] = {}
    for p in paths:
        ext = p.suffix or '(no ext)'
        stats[ext] = stats.get(ext, 0) + 1
    return stats


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_all(lat_dir: Path) -> Tuple[List[CheckError], Dict[str, int]]:
    """
    Run all checks and return consolidated results.
    
    Returns (all_errors, file_stats)
    """
    start = time.time()

    md_errors, md_stats = check_md(lat_dir)
    code_errors, code_stats = check_code_refs_func(lat_dir)
    section_errors = check_sections(lat_dir)

    elapsed = time.time() - start
    elapsed_str = f'{elapsed*1000:.0f}ms' if elapsed < 1 else f'{elapsed:.1f}s'

    all_errors = md_errors + code_errors + section_errors
    all_stats = dict(md_stats)
    for ext, count in code_stats.items():
        all_stats[ext] = all_stats.get(ext, 0) + count

    return all_errors, all_stats


def print_check_report(lat_dir: Path) -> int:
    """Print check results to terminal and return exit code."""
    project_root = lat_dir.parent
    errors, stats = check_all(lat_dir)

    # Print stats
    if stats:
        parts = ', '.join(f'{n} {ext}' for ext, n in sorted(stats.items()))
        print(f'Scanned {parts}')
    else:
        print('No files scanned.')

    # Print errors
    if errors:
        for err in errors:
            loc = f'{err.file}:{err.line}'
            first_line, *rest = err.message.split('\n')
            print(f'\n- {loc}: {first_line}')
            for r in rest:
                print(f'  {r}')
        print(f'\n{len(errors)} error{"s" if len(errors) != 1 else ""} found')
        return 1
    else:
        print('All checks passed')
        return 0