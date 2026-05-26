# nano-vllm 학습 가이드

> 초보자를 위한 대규모 언어 모델 **추론 엔진 학습 가이드**

## 개요

- [nano-vllm](https://github.com/GeeeekExplorer/nano-vllm) 전방위 학습 가이드
- nano-vllm은 DeepSeek 엔지니어 Yu Xingkai가 개발한 경량 vLLM 구현체로, 약 1,200줄의 파이썬 코드만으로 프로덕션급 추론 프레임워크의 핵심 기술을 구현했습니다.


## 학습 목표
- 대규모 언어 모델 추론 엔진의 핵심 원리를 처음부터 이해
- PagedAttention, 연속 배치 처리, 텐서 병렬 처리 등 핵심 기술 습득
- 바로 이력서에 활용할 수 있는 프로젝트 경험 확보

  
## nano-vllm 아키텍처 개요

```
사용자 요청 → LLM.generate()
              ↓
         LLMEngine.add_request()  → Tokenizer 인코딩
              ↓
         Scheduler.schedule()     → Prefill 우선 / Decode 라운드 로빈
              ↓
         ModelRunner.run()        → 입력 준비 → 모델 순전파 → 샘플링
              ↓
         Scheduler.postprocess()  → 토큰 추가 / 종료 판단
              ↓
         생성 결과 반환
```

## 학습 순서

### 토픽별 학습자료 (20강)

| 강의 | 주제 | 핵심 내용 |
|------|------|---------|
| [가이드](docs/00-nano-vllm-학습-개요.md) | 프로젝트 개요 | 학습 로드맵, nano-vllm 전체 구조 |
| [1강](docs/01-课程01-认识大模型推理.md) | 대규모 모델 추론 이해 | Prefill/Decode, 연산 병목 |
| [2강](docs/02-课程02-nano-vllm项目全景.md) | 프로젝트 전체 구조 | 디렉터리 구조, 아키텍처 계층 |
| [3강](docs/03-课程03-配置与入口.md) | 설정과 진입점 | Config, SamplingParams, example.py |
| [4강](docs/04-课程04-Tokenizer与Embedding.md) | Tokenizer와 Embedding | 어휘 병렬화, VocabParallelEmbedding |
| [5강](docs/05-课程05-Attention机制与FlashAttention.md) | Attention 메커니즘 | FlashAttention, Triton KV 저장 |
| [6강](docs/06-课程06-RoPE旋转位置编码.md) | RoPE 회전 위치 인코딩 | 수학적 유도, apply_rotary_emb |
| [7강](docs/07-课程07-LayerNorm与激活函数.md) | LayerNorm과 활성화 함수 | RMSNorm, SwiGLU, torch.compile |
| [8강](docs/08-课程08-Qwen3模型架构.md) | Qwen3 모델 아키텍처 | GQA, MLP, DecoderLayer |
| [9강](docs/09-课程09-KV-Cache原理与实现.md) | KV Cache 원리 | 메모리 계산, 캐시 재사용 |
| [10강](docs/10-课程10-PagedAttention与BlockManager.md) | PagedAttention | 블록 할당·회수, 프리픽스 캐싱 |
| [11강](docs/11-课程11-Sequence与请求管理.md) | Sequence 요청 관리 | 시퀀스 상태 머신, block_table |
| [12강](docs/12-课程12-Scheduler调度器.md) | Scheduler 스케줄러 | Prefill/Decode 스케줄링, 선점 |
| [13강](docs/13-课程13-连续批处理.md) | 연속 배치 처리 | 동적 배치, GPU 활용률 |
| [14강](docs/14-课程14-ModelRunner模型执行器.md) | ModelRunner 실행기 | KV Cache 할당, NCCL 통신 |
| [15강](docs/15-课程15-张量并行TP.md) | 텐서 병렬 처리 | 열/행 병렬, AllReduce |
| [16강](docs/16-课程16-CUDA-Graph优化.md) | CUDA Graph 최적화 | 그래프 캡처, replay 메커니즘 |
| [17강](docs/17-课程17-Triton-Kernel编写.md) | Triton Kernel | store_kvcache_kernel |
| [18강](docs/18-课程18-LLMEngine推理循环.md) | LLMEngine 추론 루프 | generate→step 전체 흐름 |
| [19강](docs/19-课程19-性能基准与优化.md) | 성능 벤치마크와 최적화 | bench.py, 처리량 테스트 |
| [20강](docs/20-课程20-完整项目串讲.md) | 전체 프로젝트 종합 | 엔드투엔드 흐름, 면접 포인트 |

### 면접 대비 자료

| 문서 | 내용 |
|------|------|
| [면접 빈출 문제 모음](docs/21-面试八股文大全.md) | 60개 이상의 면접 질문 + 상세 답변 |
| [프로젝트 이력서 작성 가이드](docs/22-项目简历撰写指南.md) | 이력서에 nano-vllm 프로젝트 기술하는 법 |
| [STAR 면접 스크립트](docs/23-STAR面试稿.md) | STAR 기법 자기소개 템플릿 |
| [면접 질문 전체 모음집](docs/24-面试问题全集-STAR回答.md) | 예상 질문 전체 + STAR 답변 |
| [채용 공고 요약](docs/25-岗位需求与招聘汇总.md) | 2026년 주요 기업 추론 엔지니어 채용 정보 |
| [학습 자료](docs/26-学习资源与参考.md) | 학습 로드맵, 참고 링크 |


## 핵심 기술 스택

| 기술 | nano-vllm 내 구현 | 해당 파일 |
|------|-------------------|---------|
| PagedAttention | BlockManager + xxhash 프리픽스 캐시 | `engine/block_manager.py` |
| 연속 배치 처리 | Scheduler Prefill/Decode 스케줄링 | `engine/scheduler.py` |
| FlashAttention | varlen_func + with_kvcache | `layers/attention.py` |
| 텐서 병렬 처리 | Column/Row/QKV ParallelLinear | `layers/linear.py` |
| CUDA Graph | capture + replay | `engine/model_runner.py` |
| Triton Kernel | store_kvcache_kernel | `layers/attention.py` |
| torch.compile | RMSNorm/RoPE/SiLU/Sampler | 각 layers 파일 |

## 성능 비교

RTX 4070 Laptop (Qwen3-0.6B, 256 시퀀스 길이) 기준:

| 추론 엔진 | 처리량 | GPU 메모리 사용량 | 시작 시간 |
|---------|--------|---------|---------|
| vLLM | 1361.84 tok/s | ~4.2GB | ~15s |
| nano-vllm | 1434.13 tok/s | ~3.8GB | ~3s |

## 빠른 시작

```bash
# 학습 가이드 저장소 클론
git clone https://github.com/bcefghj/learn-nano-vllm.git

# nano-vllm 소스 코드 클론
git clone https://github.com/GeeeekExplorer/nano-vllm.git

# 강의 순서대로 학습을 진행하세요
# docs/00-导读-项目概览.md 부터 시작합니다
```

## 대상 독자

- AI 추론 엔지니어 분야 취업 준비생
- 대규모 언어 모델 추론 엔진의 원리를 이해하고 싶은 초보자
- 이력서에 추론 엔진 프로젝트 경험을 효과적으로 담고 싶은 분

## 참고 자료

- [nano-vllm GitHub](https://github.com/GeeeekExplorer/nano-vllm)
- [블로그 코드 분석](https://www.cnblogs.com/cswuyg/p/19471225)
- [d.run 학습 튜토리얼](https://docs.d.run/blogs/2026/nano-vllm.html)
- [Flaneur2020 분석글](https://flaneur2020.github.io/posts/2025-10-12-nano-vllm/)

## 라이선스

MIT License