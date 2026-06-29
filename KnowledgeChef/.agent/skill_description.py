#!/usr/bin/env python3
"""
SKILL.md 파일에 누락된 description 필드를 추가합니다.
.agent/skills/ 하위의 모든 SKILL.md를 검사하여 수정합니다.
"""

import os
import re
import yaml
from pathlib import Path

# 스킬별 추천 description 매핑
RECOMMENDED_DESCRIPTIONS = {
    "brain": "Persistent memory and knowledge management for Codex",
    "data-flywheel": "Convert approved execution records into reusable artifacts",
    "data-layer": "Agent activity dashboard and data layer monitoring",
    "debug-investigator": "Debug and investigate issues in the codebase",
    "deploy-checklist": "Generate deployment readiness checklists",
    "design-md": "Create design documents in markdown format",
    "git-proxy": "Git operations and repository management",
    "memory-manager": "Manage agent memory and recall",
    "skillforge": "Create and manage Codex skills",
    "tldraw": "Create diagrams and visualizations",
    "kdqe": "Unified schema and instructions for querying the TechShop e-commerce database",
    # 필요에 따라 추가
}

def get_skill_name_from_path(skill_dir: Path) -> str:
    """스킬 디렉토리 이름을 반환 (예: 'data-layer')"""
    return skill_dir.name

def extract_frontmatter(content: str) -> tuple:
    """
    SKILL.md 내용에서 frontmatter와 본문을 분리합니다.
    반환: (frontmatter_yaml, body, has_frontmatter)
    """
    frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    match = frontmatter_pattern.match(content)
    if match:
        yaml_part = match.group(1)
        body = content[match.end():]
        return yaml_part, body, True
    else:
        return "", content, False

def add_description_to_frontmatter(yaml_str: str, skill_name: str) -> str:
    """
    YAML frontmatter 문자열에 description 필드를 추가합니다.
    이미 description이 있으면 그대로 반환합니다.
    """
    try:
        data = yaml.safe_load(yaml_str)
        if not data:
            data = {}
        if "description" in data and data["description"]:
            # 이미 description이 있으면 그대로 반환
            return yaml_str
        # description 추가
        desc = RECOMMENDED_DESCRIPTIONS.get(skill_name, f"{skill_name} skill for Codex")
        data["description"] = desc
        # 다시 YAML 문자열로 변환
        new_yaml = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
        return new_yaml.rstrip('\n')
    except yaml.YAMLError:
        # 파싱 실패 시, 간단히 추가 (원본 유지하며 description만 삽입)
        # 여기서는 그냥 기존 yaml_str에 description 줄을 추가
        lines = yaml_str.splitlines()
        if lines and lines[0].strip() == "":
            lines.insert(0, f"description: {RECOMMENDED_DESCRIPTIONS.get(skill_name, f'{skill_name} skill for Codex')}")
        else:
            # 첫 줄이 key: value 형태라고 가정
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    # 첫 번째 실제 라인 앞에 삽입
                    lines.insert(i, f"description: {RECOMMENDED_DESCRIPTIONS.get(skill_name, f'{skill_name} skill for Codex')}")
                    break
            else:
                lines.append(f"description: {RECOMMENDED_DESCRIPTIONS.get(skill_name, f'{skill_name} skill for Codex')}")
        return "\n".join(lines)

def process_skill_file(skill_md_path: Path) -> bool:
    """
    SKILL.md 파일을 처리합니다.
    description이 없으면 추가하고 파일을 덮어씁니다.
    변경이 있었으면 True 반환.
    """
    content = skill_md_path.read_text(encoding='utf-8')
    yaml_str, body, has_frontmatter = extract_frontmatter(content)
    
    if not has_frontmatter:
        print(f"⚠️  {skill_md_path}: frontmatter가 없습니다. 건너뜁니다.")
        return False
    
    skill_name = get_skill_name_from_path(skill_md_path.parent)
    new_yaml = add_description_to_frontmatter(yaml_str, skill_name)
    
    if new_yaml == yaml_str:
        # 변경 사항 없음
        return False
    
    # 새 내용 조합
    new_content = f"---\n{new_yaml}\n---\n{body}"
    skill_md_path.write_text(new_content, encoding='utf-8')
    return True

def main():
    # 현재 디렉토리 기준 .agent/skills 경로
    skills_dir = Path(".agent/skills")
    if not skills_dir.exists():
        print(f"❌ {skills_dir} 디렉토리를 찾을 수 없습니다.")
        print("이 스크립트는 프로젝트 루트(4-KDQE)에서 실행해주세요.")
        return
    
    # 모든 SKILL.md 파일 찾기
    skill_files = list(skills_dir.rglob("SKILL.md"))
    if not skill_files:
        print("⚠️  SKILL.md 파일을 찾을 수 없습니다.")
        return
    
    modified_count = 0
    for skill_file in skill_files:
        print(f"📄 처리 중: {skill_file}")
        if process_skill_file(skill_file):
            modified_count += 1
            print(f"   ✅ description 추가 완료")
        else:
            print(f"   ℹ️  이미 description이 있거나 변경 불필요")
    
    print(f"\n✅ 완료: {modified_count}개 파일을 수정했습니다.")

if __name__ == "__main__":
    main()