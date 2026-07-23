"""Face Recognition Assistant using Ollama VLM.

Run:
    python main.py

Optional environment variables:
    OLLAMA_MODEL=llava:7b
    OLLAMA_HOST=http://localhost:11434
    FACE_USE_OLLAMA=auto|0|false|off
"""

from __future__ import annotations

import base64
import json
import os
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llava:7b")
DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# 情绪标签映射 (EN -> ZH)
EMOTION_ZH = {
    "angry": "愤怒",
    "disgust": "厌恶",
    "fear": "恐惧",
    "happy": "开心",
    "sad": "悲伤",
    "surprise": "惊讶",
    "neutral": "平静",
}


@dataclass
class OllamaClient:
    """Ollama API 客户端（视觉模型）"""

    model: str = DEFAULT_MODEL
    host: str = DEFAULT_HOST
    timeout: int = 60
    enabled: bool = True
    last_error: str = ""

    def __post_init__(self) -> None:
        mode = os.getenv("FACE_USE_OLLAMA", "auto").strip().lower()
        if mode in {"0", "false", "off", "no"}:
            self.enabled = False
        self.host = self.host.strip().rstrip("/")
        if self.host and not self.host.startswith(("http://", "https://")):
            self.host = "http://" + self.host

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            url = f"{self.host}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    self.last_error = f"Ollama HTTP {resp.status}"
                    return False
                
                body = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in body.get("models", [])]
                
                # Check if target model or model family exists in Ollama tags
                model_base = self.model.split(":")[0]
                has_model = any(m == self.model or m.startswith(f"{model_base}:") for m in models)
                
                if not has_model and models:
                    self.last_error = f"Model '{self.model}' not found in Ollama. Available: {', '.join(models)}"
                    return False
                elif not models:
                    self.last_error = "No models installed in Ollama."
                    return False

                return True
        except urllib.error.URLError as e:
            self.last_error = f"Cannot connect to Ollama at {self.host} ({e.reason})"
            return False
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def generate_vision(self, image_bgr: np.ndarray, prompt: str) -> Optional[str]:
        if not self.enabled:
            return None
        _, buf = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_b64 = base64.b64encode(buf).decode("utf-8")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 300},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            res = str(body.get("response", "")).strip()
            return res if res else None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self.last_error = f"Ollama generation error: {exc}"
            return None


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {path}")
    return img


def detect_faces(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Haar Cascade Multi-classifier face detection (Frontal + Profile)"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 1. Frontalface alt2
    cascade_alt2 = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_alt2.xml")
    clf_alt2 = cv2.CascadeClassifier(cascade_alt2)
    faces = clf_alt2.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
    if len(faces) > 0:
        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

    # 2. Frontalface default
    cascade_def = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    if os.path.exists(cascade_def):
        clf_def = cv2.CascadeClassifier(cascade_def)
        faces = clf_def.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
        if len(faces) > 0:
            return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

    # 3. Profileface
    cascade_prof = os.path.join(cv2.data.haarcascades, "haarcascade_profileface.xml")
    if os.path.exists(cascade_prof):
        clf_prof = cv2.CascadeClassifier(cascade_prof)
        faces = clf_prof.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
        if len(faces) > 0:
            return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

    return []


def get_face_detection_diagnostics(image: np.ndarray) -> list[str]:
    """Provide detailed diagnostic output explaining face detection failures"""
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_bright = float(np.mean(gray))
    std_contrast = float(np.std(gray))

    diags = []
    diags.append(f"• Image Resolution: {w}x{h} px")
    diags.append(f"• Average Brightness: {mean_bright:.1f} / 255")
    diags.append(f"• Contrast (StdDev): {std_contrast:.1f}")
    diags.append("")
    diags.append("Possible Reasons for OpenCV Detection Failure:")

    if mean_bright < 40:
        diags.append("  1. Low Brightness: Image is too dark to extract facial landmarks.")
    elif mean_bright > 215:
        diags.append("  1. High Brightness: Overexposure causes loss of facial features.")
    else:
        diags.append("  1. Lighting/Shadows: Strong directional light or harsh shadows.")

    if std_contrast < 20:
        diags.append("  2. Low Contrast: Low feature separation between face and background.")
    else:
        diags.append("  2. Pose/Angle: Non-frontal face orientation (profile, tilted, severe pitch).")

    if w < 100 or h < 100:
        diags.append("  3. Small Resolution: Face bounding box is below detection threshold.")
    else:
        diags.append("  3. Occlusion: Face is partially covered (mask, glasses, hair, hands).")

    diags.append("  4. Blur/Focus: Motion blur or poor focus reduces classifier accuracy.")

    return diags


def analyze_emotion_builtin(image: np.ndarray, face: tuple[int, int, int, int]) -> dict[str, float]:
    """Built-in emotion analysis"""
    x, y, w, h = face
    face_roi = image[y : y + h, x : x + w]
    if face_roi.size == 0:
        return {"neutral": 1.0}

    hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
    brightness = np.mean(hsv[:, :, 2])
    saturation = np.mean(hsv[:, :, 1])

    result = {"happy": 0.0, "sad": 0.0, "angry": 0.0, "surprise": 0.0, "fear": 0.0, "disgust": 0.0, "neutral": 0.0}

    if brightness > 150 and saturation > 50:
        result["happy"] = 0.7
        result["neutral"] = 0.2
        result["surprise"] = 0.1
    elif brightness < 100:
        result["sad"] = 0.5
        result["neutral"] = 0.3
        result["fear"] = 0.2
    elif saturation > 80:
        result["angry"] = 0.4
        result["surprise"] = 0.3
        result["neutral"] = 0.3
    else:
        result["neutral"] = 0.6
        result["happy"] = 0.2
        result["sad"] = 0.1
        result["surprise"] = 0.1
    return result


def analyze_age_gender_builtin(face_roi: np.ndarray) -> Tuple[str, str]:
    """Built-in age and gender analysis"""
    if face_roi.size == 0:
        return "未知", "未知"
    h, w = face_roi.shape[:2]
    area = w * h
    hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
    skin_brightness = np.mean(hsv[:, :, 2])

    if area > 40000:
        age = "30-45岁"
    elif area > 20000:
        age = "20-35岁"
    else:
        age = "15-25岁"

    gender = "女" if skin_brightness > 140 else "男"
    return age, gender


# ==================== 4 Demo Functions ====================


def demo_detect_faces(image_path: str) -> Tuple[str, bool]:
    """Demo 1: Face Detection"""
    img = load_image(image_path)
    faces = detect_faces(img)

    lines = [
        "Face Detection Result",
        "",
        f"Image: {os.path.basename(image_path)}",
        f"Image Size: {img.shape[1]}x{img.shape[0]}",
        "",
        f"Faces Detected: {len(faces)}",
        "",
    ]
    for i, (x, y, w, h) in enumerate(faces):
        lines.append(f"Face {i+1}: position=({x},{y}) size={w}x{h}")
    if not faces:
        lines.append("[Warning] No face detected by OpenCV Haar Cascade.")
        lines.append("")
        lines.extend(get_face_detection_diagnostics(img))

    return "\n".join(lines), False


def demo_emotion(image_path: str, client: Optional[OllamaClient] = None) -> Tuple[str, bool]:
    """Demo 2: Emotion Recognition"""
    img = load_image(image_path)
    faces = detect_faces(img)
    vlm_available = client is not None and client.is_available()

    if not faces:
        lines = [
            "Emotion Recognition Result",
            "",
            f"Image: {os.path.basename(image_path)}",
            "[Notice] OpenCV Haar Cascade failed to detect a face region.",
            "",
        ]
        if vlm_available:
            lines.append("Attempting VLM Full-Image Emotion Analysis...")
            vlm_result = client.generate_vision(
                img,
                "用中文一句话描述这张图片中人物的表情和情绪，不超过20字。",
            )
            if vlm_result:
                lines.append("")
                lines.append("VLM Enhanced Analysis (Full Image):")
                lines.append(vlm_result)
                return "\n".join(lines), True

        lines.extend(get_face_detection_diagnostics(img))
        return "\n".join(lines), False

    face = faces[0]
    x, y, w, h = face
    emotions = analyze_emotion_builtin(img, face)
    top_emotion = max(emotions.items(), key=lambda item: item[1])

    lines = [
        "Emotion Recognition Result",
        "",
        f"Image: {os.path.basename(image_path)}",
        f"Face position: ({x},{y}) size: {w}x{h}",
        "",
        "Emotion Probabilities (Built-in Rule):",
        "",
    ]
    for emotion, score in sorted(emotions.items(), key=lambda x: -x[1]):
        zh = EMOTION_ZH.get(emotion, emotion)
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        lines.append(f"  {emotion} ({zh}): {bar} {score:.0%}")

    lines.append("")
    lines.append(f"Top Emotion: {top_emotion[0]} ({top_emotion[1]:.0%})")

    # Try VLM enhancement
    if vlm_available:
        fh, fw = img.shape[:2]
        pad = int(max(w, h) * 0.3)
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(fw, x + w + pad), min(fh, y + h + pad)
        face_roi = img[y1:y2, x1:x2]

        vlm_result = client.generate_vision(
            face_roi,
            "用中文一句话描述这张人脸的表情和情绪，不超过20字。",
        )
        if vlm_result:
            lines.append("")
            lines.append("VLM Enhanced Analysis:")
            lines.append(vlm_result)
            return "\n".join(lines), True

    return "\n".join(lines), False


def demo_vlm_analysis(image_path: str, client: Optional[OllamaClient] = None) -> Tuple[str, bool]:
    """Demo 3: VLM Deep Analysis (Ollama)"""
    img = load_image(image_path)
    faces = detect_faces(img)
    vlm_available = client is not None and client.is_available()

    prompt = textwrap.dedent(
        """
        请分析这张图片中的人物/人脸，用中文简洁回答：
        1. 表情/情绪
        2. 大致年龄段
        3. 性别
        4. 面部特征（眼镜、发型等）
        5. 整体印象（一句话）
        每项一行。
        """
    ).strip()

    if not faces:
        if vlm_available:
            vlm_result = client.generate_vision(img, prompt)
            if vlm_result:
                lines = [
                    f"VLM Deep Analysis (Ollama {client.model}) [Full Image Fallback]",
                    f"{'-' * 40}",
                    "[Notice] OpenCV face detection found 0 faces. Analyzed full image directly with VLM.",
                    "",
                    vlm_result,
                ]
                return "\n".join(lines), True

        diag_text = "\n".join(get_face_detection_diagnostics(img))
        fallback = textwrap.dedent(
            f"""
            VLM Deep Analysis Failed
            {'-' * 40}
            [Warning] OpenCV failed to detect a face, and Ollama VLM is not available.

            {diag_text}

            Note: Install Ollama and pull llava:7b for deep analysis.
            """
        ).strip()
        return fallback, False

    face = faces[0]
    x, y, w, h = face
    # 40% margin crop for hair/accessories/posture
    pad = int(max(w, h) * 0.4)
    fh, fw = img.shape[:2]
    x1, y1 = max(0, x - pad), max(0, y - pad)
    x2, y2 = min(fw, x + w + pad), min(fh, y + h + pad)
    face_roi = img[y1:y2, x1:x2]

    if vlm_available:
        result = client.generate_vision(face_roi, prompt)
        if result:
            return f"VLM Deep Analysis (Ollama {client.model})\n{'-' * 40}\n\n{result}", True

    fallback = textwrap.dedent(
        f"""
        VLM Deep Analysis (Built-in Fallback)
        (Ollama not available, using rule-based analysis)

        Face position: ({x},{y}) size: {w}x{h}

        1. Expression: Neutral (rule-based)
        2. Age: {analyze_age_gender_builtin(face_roi)[0]}
        3. Gender: {analyze_age_gender_builtin(face_roi)[1]}
        4. Features: Face detected, detailed analysis requires VLM
        5. Impression: Unable to generate without VLM

        Note: Install Ollama and pull llava:7b for deep analysis.
        """
    ).strip()
    return fallback, False


def demo_age_gender(image_path: str, client: Optional[OllamaClient] = None) -> Tuple[str, bool]:
    """Demo 4: Age & Gender Estimation"""
    img = load_image(image_path)
    faces = detect_faces(img)
    vlm_available = client is not None and client.is_available()

    if not faces:
        lines = [
            "Age & Gender Estimation",
            "",
            f"Image: {os.path.basename(image_path)}",
            "[Notice] OpenCV Haar Cascade failed to detect a face region.",
            "",
        ]
        if vlm_available:
            lines.append("Attempting VLM Full-Image Estimation...")
            vlm_result = client.generate_vision(
                img,
                "用中文判断这张图片中人物的年龄和性别，各一句话。",
            )
            if vlm_result:
                lines.append("")
                lines.append("VLM Enhanced (Full Image):")
                lines.append(vlm_result)
                return "\n".join(lines), True

        lines.extend(get_face_detection_diagnostics(img))
        return "\n".join(lines), False

    face = faces[0]
    x, y, w, h = face
    face_roi = img[y : y + h, x : x + w]
    age, gender = analyze_age_gender_builtin(face_roi)

    lines = [
        "Age & Gender Estimation",
        "",
        f"Image: {os.path.basename(image_path)}",
        f"Face: position=({x},{y}) size={w}x{h}",
        "",
        f"Estimated Age (Built-in Rule): {age}",
        f"Estimated Gender (Built-in Rule): {gender}",
    ]

    if vlm_available:
        fh, fw = img.shape[:2]
        pad = int(max(w, h) * 0.3)
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(fw, x + w + pad), min(fh, y + h + pad)
        face_roi_pad = img[y1:y2, x1:x2]

        vlm_result = client.generate_vision(
            face_roi_pad,
            "用中文判断这张人脸的年龄和性别，各一句话。",
        )
        if vlm_result:
            lines.append("")
            lines.append("VLM Enhanced:")
            lines.append(vlm_result)
            return "\n".join(lines), True

    return "\n".join(lines), False


# ==================== UI ====================


def print_header(client: OllamaClient) -> None:
    print("Face Recognition Assistant")
    print("(using Ollama VLM)")
    print("--------------------------------")
    if client.enabled and client.is_available():
        print(f"Ollama VLM: {client.model} [connected]")
    elif client.enabled:
        reason = f" ({client.last_error})" if client.last_error else ""
        print(f"Ollama VLM: not connected{reason}")
    else:
        print("Ollama VLM: disabled, using built-in mode")
    print()


def print_menu() -> None:
    print("1. Face Detection")
    print("2. Emotion Recognition")
    print("3. VLM Deep Analysis")
    print("4. Age & Gender Estimation")
    print("5. Exit")


def show_output(text: str, used_vlm: bool, client: OllamaClient) -> None:
    print()
    print("VLM Output:" if used_vlm else "Output:")
    print(text)
    if not used_vlm and client.enabled and client.last_error:
        print()
        print("Note: Ollama was not available, built-in analysis was used.")
        print(f"Reason: {client.last_error}")
    print()


def ask_image_path(default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"Image path{suffix}: ").strip()
    path = raw or default
    if not os.path.exists(path):
        print(f"Warning: file not found: {path}")
    return path


def run_demo1(client: OllamaClient, image_path: str) -> None:
    print("Demo 1: Face Detection")
    text, _ = demo_detect_faces(image_path)
    show_output(text, False, client)


def run_demo2(client: OllamaClient, image_path: str) -> None:
    print("Demo 2: Emotion Recognition")
    text, used = demo_emotion(image_path, client)
    show_output(text, used, client)


def run_demo3(client: OllamaClient, image_path: str) -> None:
    print("Demo 3: VLM Deep Analysis")
    text, used = demo_vlm_analysis(image_path, client)
    show_output(text, used, client)


def run_demo4(client: OllamaClient, image_path: str) -> None:
    print("Demo 4: Age & Gender Estimation")
    text, used = demo_age_gender(image_path, client)
    show_output(text, used, client)


def main() -> None:
    client = OllamaClient()

    # 默认图片路径
    default_image = os.path.join(os.path.dirname(__file__), "data", "sample_face.jpg")
    if not os.path.exists(default_image):
        default_image = ""

    while True:
        print_header(client)
        print_menu()
        choice = input("Select function: ").strip().lower()
        print()

        if choice in {"5", "q", "quit", "exit"}:
            print("Bye.")
            break

        if choice not in {"1", "2", "3", "4"}:
            print("Invalid option. Please choose 1-5.")
            input("Press Enter to continue...")
            print()
            continue

        image_path = ask_image_path(default_image)
        if not image_path:
            print("No image path provided.")
            input("Press Enter to continue...")
            print()
            continue

        if choice == "1":
            run_demo1(client, image_path)
        elif choice == "2":
            run_demo2(client, image_path)
        elif choice == "3":
            run_demo3(client, image_path)
        elif choice == "4":
            run_demo4(client, image_path)

        input("Press Enter to return to menu...")
        print()


if __name__ == "__main__":
    main()
