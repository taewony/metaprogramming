from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

@dataclass
class PlanningScore:
    schema_valid: bool
    intent_correct: bool
    concept_precision: float
    concept_recall: float
    concept_f1: float
    source_correct: bool
    filter_f1: float
    projection_f1: float
    aggregation_correct: bool
    join_correct: bool
    ambiguity_resolution_rate: float
    overall_f1: float

class PlanningScorer:
    """Knowledge IR의 다차원 구조 비교 점수 산출"""

    def score(self, actual_ir: dict, expected_ir: dict) -> PlanningScore:
        # 1. Schema Validity
        schema_valid = self._validate_schema(actual_ir)

        # 2. Intent Accuracy
        intent_correct = actual_ir.get("intent") == expected_ir.get("intent")

        # 3. Concept F1
        actual_concepts = set(actual_ir.get("concepts", []))
        expected_concepts = set(expected_ir.get("concepts", []))
        cp, cr, cf = self._set_f1(actual_concepts, expected_concepts)

        # 4. Source Accuracy
        actual_sources = {s.get("source") for s in actual_ir.get("steps", [])}
        expected_sources = {s.get("source") for s in expected_ir.get("steps", [])}
        source_correct = actual_sources == expected_sources

        # 5. Filter F1
        actual_filters = self._extract_filter_set(actual_ir)
        expected_filters = self._extract_filter_set(expected_ir)
        _, _, filter_f1 = self._set_f1(actual_filters, expected_filters)

        # 6. Projection F1
        actual_proj = self._extract_projections(actual_ir)
        expected_proj = self._extract_projections(expected_ir)
        _, _, proj_f1 = self._set_f1(actual_proj, expected_proj)

        # 7. Aggregation Accuracy
        agg_correct = self._compare_aggregation(actual_ir, expected_ir)

        # 8. Join Accuracy
        join_correct = self._compare_joins(actual_ir, expected_ir)

        # 9. Ambiguity Resolution Rate
        amb_rate = self._ambiguity_score(actual_ir, expected_ir)

        # Overall F1 (weighted average)
        scores = [
            1.0 if intent_correct else 0.0,
            cf,
            1.0 if source_correct else 0.0,
            filter_f1,
            proj_f1,
            1.0 if agg_correct else 0.0,
            1.0 if join_correct else 0.0,
            amb_rate
        ]
        overall = sum(scores) / len(scores)

        return PlanningScore(
            schema_valid=schema_valid,
            intent_correct=intent_correct,
            concept_precision=cp, concept_recall=cr, concept_f1=cf,
            source_correct=source_correct,
            filter_f1=filter_f1,
            projection_f1=proj_f1,
            aggregation_correct=agg_correct,
            join_correct=join_correct,
            ambiguity_resolution_rate=amb_rate,
            overall_f1=overall
        )

    def _set_f1(self, actual: Set, expected: Set) -> Tuple[float, float, float]:
        if not expected and not actual:
            return 1.0, 1.0, 1.0
        if not expected or not actual:
            return 0.0, 0.0, 0.0
        tp = len(actual & expected)
        precision = tp / len(actual) if actual else 0
        recall = tp / len(expected) if expected else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        return precision, recall, f1

    def _extract_filter_set(self, ir: dict) -> Set[Tuple]:
        filters = set()
        for step in ir.get("steps", []):
            for f in step.get("filters", []) or []:
                filters.add((f["field"], f["operator"], str(f["value"])))
        return filters

    def _extract_projections(self, ir: dict) -> Set[str]:
        proj = set()
        for step in ir.get("steps", []):
            for p in step.get("projections", []) or []:
                proj.add(p)
        return proj

    def _compare_aggregation(self, actual: dict, expected: dict) -> bool:
        for a_step, e_step in zip(actual.get("steps", []), expected.get("steps", [])):
            a_agg = a_step.get("aggregation")
            e_agg = e_step.get("aggregation")
            if a_agg != e_agg:
                return False
        return True

    def _compare_joins(self, actual: dict, expected: dict) -> bool:
        for a_step, e_step in zip(actual.get("steps", []), expected.get("steps", [])):
            if a_step.get("join") != e_step.get("join"):
                return False
        return True

    def _ambiguity_score(self, actual: dict, expected: dict) -> float:
        expected_ambs = expected.get("ambiguity_resolutions_expected", [])
        if not expected_ambs:
            return 1.0
        actual_ambs = actual.get("ambiguity_resolutions", [])
        if not actual_ambs:
            return 0.0
        correct = 0
        for ea in expected_ambs:
            for aa in actual_ambs:
                if aa.get("element") == ea.get("element") and \
                   aa.get("selected") == ea.get("selected"):
                    correct += 1
                    break
        return correct / len(expected_ambs)

    def _validate_schema(self, ir: dict) -> bool:
        try:
            from kchef.schema.ir_schema import KnowledgeIR
            KnowledgeIR(**ir)
            return True
        except Exception:
            return False
