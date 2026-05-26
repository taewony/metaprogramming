# Migration Pass Criteria

> **Purpose**: CI 및 수동 검증을 위한 통과 기준 체크리스트.  
> **Usage**: 각 항목은 `[[outcomes#...]]`의 해당 섹션에 대한 **검증 방법**을 기술한다.  
> **Constraint**: 초기 Phase 1 마이그레이션에서는 "Do not reinterpret the baseline architecture" 원칙을 준수하며, 아키텍처 재설계는 Phase 2 이후에 허용한다.

## 1. Functional Equivalence [[tests/migration-pass-criteria#Functional Equivalence]]
- Token logits: [[outcomes#pipeline]] 기준, FP 허용 오차 내 일치.
- Sampling: [[outcomes#batching]] 하에서 고정 시드 동작 동일.
- KV Cache: [[outcomes#kv-cache]] 업데이트가 decode iteration 간 올바른지 검증.

## 2. Attention Kernel Migration [[tests/migration-pass-criteria#Attention Migration]]
- [[outcomes#attention]]: 모든 Triton attention 경로가 cuTile로 대체되었는지 확인.
- Flash/Paged attention 로직 보존 여부 검증.

## 3. KV Cache Semantics [[tests/migration-pass-criteria#KV Cache Semantics]]
- [[outcomes#kv-cache]]: Paged KV layout, block indexing, gather/scatter, decode-time append 동작 검증.

## 4. Tensor Parallel Correctness [[tests/migration-pass-criteria#Tensor Parallel]]
- [[outcomes#tensor-parallel]]: Multi-GPU 실행 정합성, NCCL collective 동작, vocabulary-parallel LM head 검증.

## 5. Continuous Batching [[tests/migration-pass-criteria#Continuous Batching]]
- [[outcomes#batching]]: Heterogeneous sequence lengths, incremental decoding, dynamic batching, prefill+decode coexistence 검증.

## 6. No Fallback Regression [[tests/migration-pass-criteria#No Fallback]]
- [[outcomes#pipeline]]: Eager PyTorch, CPU 실행, deprecated Triton kernel로의 무단 fallback이 없는지 확인.

## 7. Performance [[tests/migration-pass-criteria#Performance]]
- [[outcomes#performance]]: Throughput, decode latency, GPU utilization이 기준선 대비 허용 범위 내인지 벤치마크.

## 8. Memory [[tests/migration-pass-criteria#Memory]]
- [[outcomes#memory]]: KV Cache fragmentation, peak VRAM, temporary allocation 압력 검증.

## 9. Build Reproducibility [[tests/migration-pass-criteria#Build]]
- [[outcomes#build]]: 문서화된 명령어로 설치-컴파일-실행-벤치마크가 재현 가능한지 확인.

## 10. Code Quality [[tests/migration-pass-criteria#Code Quality]]
- [[outcomes#code-quality]]: Modular kernel structure, readable DSL, minimal duplication, scheduler/runtime/kernel 분리 검증.

## 11. Documentation [[tests/migration-pass-criteria#Documentation]]
- [[outcomes#knowledge]]: cuTile migration rationale, architecture overview, execution flow, benchmark instructions, known limitations가 문서화되었는지 확인.

## 12. Report [[tests/migration-pass-criteria#Report]]
- `migration_report.md` 존재 여부 및 내용 검증.