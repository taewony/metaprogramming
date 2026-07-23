Python 3.13, CUDA 13.3 기반의 cuda-python (cuTile 포함), 그리고 차세대 패키지 관리자인 uv를 사용하여 CUDA Graph 기반 커널을 시험할 수 있는 가상환경 구축 가이드입니다 [cu13].
uv는 Rust 기반으로 작성되어 기존 pip나 conda보다 최대 10~100배 빠른 속도로 패키지를 관리할 수 있어 대용량 CUDA 라이브러리 설치에 매우 유리합니다. [1] 
------------------------------
## 1. Python 3.13 및 가상환경 생성 (uv)
먼저 프로젝트 디렉토리를 생성하고, uv를 통해 Python 3.13 버전이 적용된 격리된 가상환경을 구축합니다.

# 1. 프로젝트 폴더 생성 및 이동
mkdir cuda-graph-test && cd cuda-graph-test
# 2. Python 3.13 기반 가상환경 생성 (.venv 폴더가 생성됨)
uv venv --python 3.13
# 3. 가상환경 활성화# (Linux / macOS)
source .venv/bin/activate# (Windows PowerShell)# .venv\Scripts\Activate.ps1

------------------------------
## 2. CUDA Python 13.3 핵심 패키지 설치
cuda.core와 고성능 커널 오서링을 위한 cuTile 패키지는 NVIDIA 공식 PyPI 저장소 및 인덱스를 통해 배포됩니다. CUDA 13.3 드라이버와 완벽하게 호환되도록 [cu13] 메타패키지 접미사를 지정하여 종속성을 명확히 처리합니다 [cu13].

# 1. 공식 CUDA Python 핵심 패키지 설치 (cuda.core 포함)
uv pip install "cuda-python[cu13]"
# 2. 차세대 타일 기반 커널 작성을 위한 cuTile(cuda-tile) 및 수학 백엔드 설치
uv pip install cuda-tile nvmath-python

💡 참고: uv는 기본적으로 시스템의 PyPI 캐시를 강력하게 활용하므로, 동일한 바이너리가 머신에 있다면 수 초 내에 설치가 완료됩니다.

------------------------------
## 3. JIT 컴파일러 및 가속 생태계 추가 (선택)
CUDA Graph를 구축하고 커널을 동적으로 컴파일하려면 NVIDIA의 새로운 MLIR 백엔드를 지원하는 컴파일러와 수치 해석 도구가 함께 있으면 좋습니다.

# Numba의 신형 CUDA MLIR 백엔드 및 배열 제어를 위한 NumPy 설치
uv pip install numba-cuda-mlir numpy

------------------------------
## 4. 환경 변수 체크 및 설치 검증
설치가 완료되었다면 가상환경 내에서 CUDA 드라이버 및 cuda.core가 런타임을 정상적으로 추상화하는지 검증해야 합니다. 아래 스크립트를 작성하여 테스트해 보세요.

# test_env.pyimport sysfrom cuda.core import Device

print(f"현재 파이썬 버전: {sys.version}")
try:
    # 0번 GPU 로드 및 활성화
    dev = Device(0)
    dev.set_current()
    
    print(f"✅ 환경 구축 성공!")
    print(f" - GPU 장치명: {dev.to_system_device().name}")
    print(f" - Compute Capability: {dev.arch}")
    
    # cuTile 로드 확인
    import cuda.tile as tile
    print(f" - cuTile 모듈 로드 완료: {tile.__file__}")
except Exception as e:
    print(f"❌ 오류 발생. 시스템 환경 변수(CUDA_PATH 또는 LD_LIBRARY_PATH)를 확인하세요.")
    print(f" 에러 내용: {e}")

실행 명령어:

python test_env.py

------------------------------
## 5. uv 프로젝트 형태로 고도화하기 (권장)
만약 이 테스트 환경을 깃허브(GitHub)에 공유하거나 다른 시스템에서도 100% 동일하게 재현하고 싶다면, uv init을 통한 프로젝트 관리 방식을 사용하는 것이 좋습니다.

# 프로젝트 초기화 (pyproject.toml 자동 생성)
uv init
# 종속성을 pyproject.toml에 명시하며 설치 및 락(lock) 파일 생성
uv add "cuda-python[cu13]" cuda-tile nvmath-python numpy

이후에는 다른 컴퓨터에서 uv sync 명령어 한 줄만 입력하면 Python 3.13 버전을 자동으로 다운로드하고 모든 CUDA 바인딩 패키지까지 완벽하게 복원해 줍니다.
## ✅ 환경 요약

* 패키지 관리자: uv (Rust 기반 고속 패키징 도구)
* 런타임: Python 3.13 + CUDA 13.3 Driver 바인딩
* 주요 구성: cuda.core (컨텍스트 및 그래프 제어), cuda.tile (고성능 타일 커널 설계) [cu13]

이제 환경 준비가 끝났습니다. CUDA 13.3 환경에서 cuda.core.Graph 객체를 활용해 스트림 기록(Stream Capture) 방식으로 CUDA Graph를 정의하고 집행(Instantiation)하는 구체적인 커널 시험용 코드 템플릿이 필요하신가요? 원하신다면 즉시 이어서 안내해 드리겠습니다.

[1] [https://m.blog.naver.com](https://m.blog.naver.com/drvoss/224204489777)

https://wikidocs.net/book/18603