# kchef/planner/pipeline.py
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
import re

from kchef.schema.ir_schema import KnowledgeIR
from kchef.planner.intent import IntentRecognizer
from kchef.planner.concept_matcher import ConceptMatcher
from kchef.planner.ambiguity import AmbiguityResolver
from kchef.planner.decomposer import GoalDecomposer
from kchef.planner.playbook import PlaybookEngine
from kchef.planner.simulator import MentalSimulator
from kchef.planner.compiler import RecipeCompiler

class PlannerPipeline:
    """
    Cognitive Planner: 자연어 질의 → Knowledge IR 변환 파이프라인.
    SQL을 생성하지 않는다. Knowledge IR만 생성한다.
    """
    def __init__(self, system_model: dict, skills_dir: str, llm_client=None):
        self.system_model = system_model     # 스키마 + 비즈니스 규칙
        self.intent_recognizer = IntentRecognizer(skills_dir)
        self.concept_matcher = ConceptMatcher(system_model)
        self.ambiguity_resolver = AmbiguityResolver(skills_dir)
        self.decomposer = GoalDecomposer()
        self.playbook_engine = PlaybookEngine(skills_dir)
        self.simulator = MentalSimulator(system_model)
        self.compiler = RecipeCompiler()
        self.llm = llm_client                # Optional: LLM fallback

    def plan(self, question: str, context: dict = None) -> KnowledgeIR:
        """
        메인 진입점: 질문을 Knowledge IR로 변환한다.

        Args:
            question: 사용자의 자연어 질의 (불완전·모호 가능)
            context: 대화 컨텍스트 (multi-turn 지원)

        Returns:
            KnowledgeIR: 검증된 실행 계획
        """
        # ① Intent 분석
        intent_result = self.intent_recognizer.recognize(question)

        # ② Concept Matching
        concepts = self.concept_matcher.match(question, intent_result)

        # ③ 모호성 해소 (핵심)
        resolved = self.ambiguity_resolver.resolve(
            question=question,
            intent=intent_result,
            concepts=concepts,
            context=context
        )

        # ④ Goal 분해 (복합 의도인 경우)
        sub_goals = self.decomposer.decompose(
            intent=resolved.intent,
            concepts=resolved.concepts,
            constraints=resolved.constraints
        )

        # ⑤ Playbook 선택
        playbook = self.playbook_engine.select(
            intent=resolved.intent,
            concepts=resolved.concepts
        )

        # ⑥ Mental Simulation (Dry-run)
        draft_ir = self.compiler.compile(
            resolved=resolved,
            sub_goals=sub_goals,
            playbook=playbook
        )
        validation = self.simulator.validate(draft_ir)

        if not validation.passed:
            # 검증 실패 시 대안 Playbook으로 재시도
            alt_playbook = self.playbook_engine.select_alternative(
                intent=resolved.intent,
                concepts=resolved.concepts,
                exclude=[playbook.id]
            )
            draft_ir = self.compiler.compile(
                resolved=resolved,
                sub_goals=sub_goals,
                playbook=alt_playbook
            )
            validation = self.simulator.validate(draft_ir)
            if not validation.passed:
                raise PlanningError(f"Mental Rehearsal 실패: {validation.errors}")

        # ⑦ Knowledge IR 최종 출력
        return draft_ir
        
def load_system_model(bundle_path: str = "wiki") -> Dict:
    """
    OKF 번들에서 시스템 모델 로드 (기본값: wiki 폴더)
    """
    bundle_path = Path(bundle_path)
    model = {"concepts": {}, "schemas": {}, "index": {}}
    
    # index.md 파싱
    index_file = bundle_path / "index.md"
    if index_file.exists():
        content = index_file.read_text(encoding='utf-8')
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for name, path in links:
            model["index"][name] = path
    else:
        print(f"⚠️ index.md를 찾을 수 없음: {index_file}")
    
    # concepts/*.md 파싱
    concepts_dir = bundle_path / "concepts"
    if concepts_dir.exists():
        for concept_file in concepts_dir.glob("*.md"):
            content = concept_file.read_text(encoding='utf-8')
            if content.startswith("---"):
                try:
                    _, fm, _ = content.split("---", 2)
                    meta = yaml.safe_load(fm)
                    model["concepts"][concept_file.stem] = meta
                except Exception as e:
                    print(f"⚠️ 파싱 오류: {concept_file} - {e}")
    
    return model