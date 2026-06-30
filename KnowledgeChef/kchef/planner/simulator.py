# kchef/planner/simulator.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..schema.ir_schema import KnowledgeIR, DataStep, DocumentStep, Filter


@dataclass
class ValidationResult:
    """정신적 시뮬레이션(검증) 결과"""
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MentalSimulator:
    """
    Knowledge IR을 Dry-run(정신적 시뮬레이션)하여 실행 가능성을 검증합니다.
    - 참조하는 테이블/파일이 존재하는지 확인
    - 필터 조건에 사용된 컬럼이 유효한지 확인
    - 조인 조건이 올바른지 검증
    """

    def __init__(self, system_model: dict):
        """
        Args:
            system_model: 스키마 정보를 포함하는 시스템 모델
                         {"schemas": {"customers": {"columns": {...}}}, ...}
        """
        self.system_model = system_model
        self.schemas = system_model.get("schemas", {})

    def validate(self, ir: KnowledgeIR) -> ValidationResult:
        """
        IR을 검증합니다.
        - 각 DataStep의 source가 system_model에 존재하는지
        - 각 필터의 field가 source의 컬럼에 포함되는지
        - 각 조인 조건이 유효한지
        - 각 그룹화/정렬 필드가 유효한지
        - DocumentStep의 source가 존재하는지
        """
        errors = []
        warnings = []

        if not ir.steps:
            errors.append("IR에 실행 단계(steps)가 없습니다.")
            return ValidationResult(passed=False, errors=errors)

        for i, step in enumerate(ir.steps):
            step_prefix = f"Step {i+1}"

            if isinstance(step, DataStep):
                # 1. Source 존재 여부 확인
                source = step.source
                if source not in self.schemas:
                    errors.append(
                        f"{step_prefix}: 데이터 소스 '{source}'가 스키마에 없습니다. "
                        f"가능한 소스: {list(self.schemas.keys())}"
                    )
                    # 더 이상 검증하지 않고 계속 (오류 수집)
                    continue

                schema_cols = set(self.schemas[source].get("columns", {}).keys())

                # 2. 필터 필드 유효성
                if step.filters:
                    for f in step.filters:
                        if f.field not in schema_cols:
                            errors.append(
                                f"{step_prefix}: 필터 필드 '{f.field}'가 '{source}'에 없습니다. "
                                f"사용 가능한 컬럼: {sorted(schema_cols)}"
                            )

                # 3. 그룹화 필드 유효성
                if step.group_by:
                    for g in step.group_by:
                        if g not in schema_cols:
                            errors.append(
                                f"{step_prefix}: GROUP BY 필드 '{g}'가 '{source}'에 없습니다."
                            )

                # 4. 정렬 필드 유효성
                if step.order_by:
                    for s in step.order_by:
                        if s.field not in schema_cols:
                            errors.append(
                                f"{step_prefix}: ORDER BY 필드 '{s.field}'가 '{source}'에 없습니다."
                            )

                # 5. 집계 필드 유효성 (aggregation.field가 존재하는지)
                if step.aggregation:
                    agg = step.aggregation
                    if agg.field != "*" and agg.field not in schema_cols:
                        errors.append(
                            f"{step_prefix}: 집계 필드 '{agg.field}'가 '{source}'에 없습니다."
                        )

                # 6. 조인 조건 유효성 (간단히: on 조건에 '.'이 포함되어 있는지 정도만 확인)
                if step.join:
                    join = step.join
                    if "=" not in join.on:
                        errors.append(
                            f"{step_prefix}: 조인 조건 '{join.on}'에 '='가 포함되어 있지 않습니다."
                        )
                    # 조인 대상이 존재하는지 확인 (with_resource가 schemas에 있는지)
                    if join.with_resource not in self.schemas:
                        errors.append(
                            f"{step_prefix}: 조인 대상 '{join.with_resource}'가 스키마에 없습니다."
                        )

            elif isinstance(step, DocumentStep):
                # DocumentStep: source가 파일 시스템에 존재하는지 단순 확인 (여기서는 경로만 체크)
                # 실제로는 파일 존재 여부를 확인하지만, 여기서는 단순히 source가 비어있지 않은지 확인
                if not step.source:
                    errors.append(f"{step_prefix}: 문서 소스 경로가 비어 있습니다.")
                # 추가: 확장자 검사 등은 생략

        # 경고: 예를 들어 limit이 없으면 많은 결과를 반환할 수 있음을 경고
        for i, step in enumerate(ir.steps):
            if isinstance(step, DataStep) and step.limit is None:
                warnings.append(f"Step {i+1}: LIMIT이 지정되지 않아 대량 결과가 반환될 수 있습니다.")

        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings)