# AGENTS.md — cuTile 메타프로그래밍 프로젝트

## 프로젝트 정체성
Coding agent와 함께 Pytorch/Triton 기반으로 작성된 2개의 코드베이스(llm-from-scratch, nano-vllm)를 **cuTile Python DSL**로 변환시키는 작업을 통해, 단순한 코드 재작성이 아니라 **메타프로그래밍 체계**를 구축합니다.  
**마크다운 기반 Semiformal Design Documents**가 단순한 문서가 아니라, 코드를 인과적으로 제약하는 **실행 가능한 메타 표현**임을 실증하고, 논문을 작성하는 것이 궁극적 목표입니다.

## 디렉토리 구조
```
cutile-metaprogramming/
├── AGENTS.md                  # 에이전트 진입점 (이 파일)
├── .skills/                   # 스킬 정의
├── lat.md/                    # 지식 그래프 & 메타문서 (읽기 전용)
│   ├── architecture.md        # nano‑vLLM 원본 아키텍처
│   ├── outcomes.md            # cuTile 변환 목표
│   ├── rules/                 # 반정형 설계 규칙 (Semiformal Rules)
│   ├── patterns/              # (레거시) 설계 패턴 → rules/로 대체 중
│   ├── retrospectives/        # 변환 세션 회고 (복리 축적)
│   └── tests/                 # 테스트 명세 (Markdown)
├── src/                       # cuTile 변환 대상 코드
├── nano-vllm/                 # 원본 nano‑vLLM (읽기 전용)
├── TileGym/                   # cuTile 참조 예제 (읽기 전용)
├── lat-cli/                   # 지식 그래프 도구 (Python)
└── logs/                      # 규칙 적용 로그, 성능 추적
```

## 핵심 원칙 (반드시 준수)
1. **Pure cuTile Forward Path**: 모든 GPU 연산은 `@ct.kernel` + `ct.launch`를 통과해야 합니다. `nn.Linear`, `F.scaled_dot_product_attention`, Triton 커널 호출은 금지됩니다.
2. **Tile Dimensions Power‑of‑2**: 모든 타일 크기는 2의 거듭제곱이어야 합니다. `BLOCK_M`, `BLOCK_K` 등.
3. **All Constants Typed**: `BLOCK: ct.Constant[int]` 등 타입 어노테이션 필수.
4. **Single File per Kernel**: 각 커널은 하나의 `.py` 파일에 구현, 검증, 테스트를 포함합니다.
5. **No Source Citations**: 코드 내에 TileGym 파일명 등 참조 경로를 주석으로 남기지 마세요.

## 워크플로우 (단계적 검증 게이트)
모든 작업은 아래 순서를 따릅니다. 각 단계 통과 전까지 다음 단계로 진행하지 않습니다.

1. **Architect Phase**: 메타문서(`rules/`, `outcomes.md`)를 작성/수정 → `lat check`로 무결성 확인
2. **Rule Extraction**: `lat rules extract --target <target>`으로 규칙 추출
3. **Executor Phase**: `lat expand --include-rules`로 규칙 포함 프롬프트 생성 → 코드 생성 → `@rule:` 주석 기입
4. **Rule Logging**: `logs/rule_application.jsonl`에 규칙 적용 여부 기록 (하단 템플릿 참조)
5. **Verification**: `lat rules verify` + `pytest` + `lat check` → 실패 시 최대 3회 자동 수정
6. **Retrospective**: `lat.md/retrospectives/`에 회고 기록 → 복리 자산화

## 도구 사용법 (lat‑cli)
`lat‑cli/`는 표준 `lat` 명령어와 호환되는 자체 구현 CLI입니다. Python만으로 동작하며, Ollama API 호출은 `lat search`에만 사용됩니다.

| 명령어 | 용도 |
|--------|------|
| `python lat-cli/cli.py check` | `[[wiki link]]`와 `@lat:` 주석의 참조 무결성 검증 |
| `python lat-cli/cli.py rules extract --target <file/id>` | 지정된 메타문서에서 규칙을 JSON으로 추출 |
| `python lat-cli/cli.py rules verify logs/rule_application.jsonl` | 규칙 적용 로그와 실제 코드 정합성 검증 |
| `python lat-cli/cli.py gap` | `outcomes.md`와 현재 코드 간 차이 분석 (Seam 식별) |
| `python lat-cli/cli.py meta-status` | 현재 메타프로그램 상태 출력 |
| `python lat-cli/cli.py meta-diff --before <ver> --after <ver>` | 메타문서 변경 전후의 규칙 차이 및 코드 영향 예측 |

## 규칙과 로깅
### 규칙 정의 (rules/*.md)
모든 규칙은 YAML 프론트매터에 정의합니다:
```yaml
rules:
  - id: UNIQUE-RULE-ID
    description: "규칙 설명"
    constraint: "코드에 적용될 구체적 제약"
    enforcement: hard 또는 soft
    condition: null 또는 {커널_타입: flash_attention}
```

### 규칙 적용 로그 (logs/rule_application.jsonl)
Executor는 코드 생성 후 반드시 아래 형식으로 로그를 남깁니다:
```jsonl
{"timestamp": "ISO8601", "rule_id": "규칙 ID", "applied": true/false, "location": "파일:라인", "decision": "APPLIED 또는 NOT_APPLICABLE 또는 DEFERRED", "reason": "미적용 사유"}
```

## 커뮤니케이션 프로토콜
- **모호한 작업일 때**: 2‑3가지 접근법을 제시하고 인간의 선택을 기다립니다.
- **오류 발생 시**: 최대 3회 자체 수정 시도 후, 실패하면 분석과 함께 보고합니다.
- **규칙 충돌 시**: 충돌하는 규칙과 이유를 명시하고 인간에게 해결을 요청합니다.
- **새로운 패턴 발견 시**: `lat.md/retrospectives/`에 초안을 작성하고, 인간이 검증 후 `rules/`로 승격합니다.

## 성공 지표
1. 모든 커널이 Pure cuTile Forward Path를 만족
2. `lat check`와 `lat rules verify` 통과
3. Parity test 전면 통과 (FP16 기준 1e-2 rtol)
4. 성능이 Triton 기준 0.95x 이상
5. 규칙 적용 로그가 모든 변환을 추적

## 결론
이 `AGENTS.md`를 프로젝트 루트에 저장하면, Coding Agent는 작업 시작 시 이 파일을 자동으로 읽고 프로젝트의 전체 철학과 제약, 워크플로우를 이해한 상태에서 행동하게 됩니다. 이것이 바로 우리가 설계한 "실행 가능한 메타문서" 체계의 첫 관문입니다.

## References
- lat.md github repo: https://github.com/1st1/lat.md
- llm-from-scratch repo: https://github.com/angelos-p/llm-from-scratch
- TileGym repo: https://github.com/NVIDIA/TileGym
- nano-vllm repo: https://github.com/GeeeekExplorer/nano-vllm