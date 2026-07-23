# Lightweight Ollama VLM Multimodal Repositories & Guides

Heavy한 PyTorch 설치 없이 **Python + OpenCV/Base64**만 사용하여 **Ollama VLM API**로 멀티모달(Vision-Language) 기능을 시험해볼 수 있는 대표적인 영문 GitHub 리포지토리 및 실습 가이드 모음입니다.

---

## 🌟 추천 영문 GitHub 리포지토리

### 1. 🚀 [menzHSE/vlm_live_demo](https://github.com/menzHSE/vlm_live_demo)
* **특징**: 웹캠/동영상 프레임을 OpenCV로 읽어와 Ollama VLM API(`llava`, `llama3.2-vision` 등)로 실시간 캡셔닝 및 텍스트 분석을 수행하는 **가장 직관적인 영문 라이브 데모 리포지토리**입니다.
* **주요 스택**: `Python`, `opencv-python`, `ollama` (PyTorch 미사용)
* **주요 기능**:
  - OpenCV로 카메라인풋 캡처 및 JPEG Base64 변환
  - Ollama REST API 호출 및 VLM 응답 스트리밍 처리

---

### 2. 📹 [codearrangertoo/ollama-vision](https://github.com/codearrangertoo/ollama-vision)
* **특징**: 로컬 이미지/동영상 파일을 입력받아 Ollama VLM API로 오브젝트 묘사, OCR, 씬 분석을 테스트하는 경량화 파이프라인 리포지토리입니다.
* **주요 스택**: `Python`, `opencv-python`, `Pillow`, `requests` / `ollama`
* **주요 기능**:
  - 로컬 이미지 파일 및 비디오 프레임 전처리
  - `llava`, `moondream`, `llama3.2-vision` 등 다양한 VLM 모델 테스트 지원

---

### 3. 📚 [ollama/ollama-python](https://github.com/ollama/ollama-python) (공식 SDK 예제)
* **특징**: Ollama 공식 Python 라이브러리의 GitHub 리포지토리로, `examples/multimodal` 디렉토리 아래에 PyTorch 없이 이미지를 VLM API로 다루는 가장 표준적인 소스코드가 포함되어 있습니다.

---

## 💡 PyTorch 없이 VLM API 다루기 (예제 코드)

Below is the standard minimal code snippet using OpenCV and Ollama Python SDK without PyTorch:

```python
import base64
import cv2
import ollama

# 1. OpenCV로 이미지 읽기 및 Base64 인코딩 (PyTorch 필요 없음)
img = cv2.imread('sample.jpg')
_, buffer = cv2.imencode('.jpg', img)
img_b64 = base64.b64encode(buffer).decode('utf-8')

# 2. Ollama VLM API 호출
response = ollama.chat(
    model='llava:7b',  # 또는 llama3.2-vision
    messages=[{
        'role': 'user',
        'content': 'Describe what you see in this image in one sentence.',
        'images': [img_b64]
    }]
)

print("VLM Response:", response['message']['content'])
```

---

## 📄 License & Notes
- 본 리포지토리는 PyTorch 없이 경량화된 OpenCV + Ollama API 조합으로 로컬 VLM 멀티모달 기능을 테스트하는 용도로 작성되었습니다.
