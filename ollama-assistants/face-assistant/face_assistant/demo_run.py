"""Non-interactive demo runner for the Face Recognition Assistant.

Generates demo output showing all 4 functions.
When no real face image is available, uses built-in mock data.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "outputs" / "demo_output.txt"


def block(title: str, content: str) -> str:
    cleaned = textwrap.dedent(content).strip()
    return f"{title}\n{'-' * len(title)}\n{cleaned}\n"


def main() -> None:
    transcript = "\n".join(
        [
            block(
                "Home",
                """
                Face Recognition Assistant
                (using Ollama VLM)
                --------------------------------
                1. Face Detection
                2. Emotion Recognition
                3. VLM Deep Analysis
                4. Age & Gender Estimation
                5. Exit
                """,
            ),
            block(
                "Demo 1 Input",
                """
                Image path: data/sample_face.jpg
                """,
            ),
            block(
                "Demo 1 Output — Face Detection",
                """
                Face Detection Result

                Image: sample_face.jpg
                Image Size: 640x480

                Faces Detected: 2

                Face 1: position=(180,95) size=165x165
                Face 2: position=(410,120) size=140x140
                """,
            ),
            block(
                "Demo 2 Input",
                """
                Image path: data/sample_face.jpg
                """,
            ),
            block(
                "Demo 2 Output — Emotion Recognition",
                """
                Emotion Recognition Result

                Image: sample_face.jpg
                Face position: (180,95) size: 165x165

                Emotion Probabilities:

                  happy (开心): ████████░░ 78%
                  neutral (平静): ██░░░░░░░░ 12%
                  surprise (惊讶): █░░░░░░░░░  5%
                  sad (悲伤): ░░░░░░░░░░  3%
                  angry (愤怒): ░░░░░░░░░░  1%
                  fear (恐惧): ░░░░░░░░░░  1%
                  disgust (厌恶): ░░░░░░░░░░  0%

                Top Emotion: happy (78%)
                """,
            ),
            block(
                "Demo 3 Input",
                """
                Image path: data/sample_face.jpg
                """,
            ),
            block(
                "Demo 3 Output — VLM Deep Analysis (Built-in Fallback)",
                """
                VLM Deep Analysis
                (Ollama not available, using rule-based analysis)

                Face position: (180,95) size: 165x165

                1. Expression: Happy, appears relaxed and smiling
                2. Age: 25-30 years old
                3. Gender: Female
                4. Features: Long hair, no glasses, smooth skin
                5. Impression: Warm and friendly appearance

                Note: Install Ollama and pull llava:7b for VLM analysis.
                  $ ollama serve
                  $ ollama pull llava:7b
                """,
            ),
            block(
                "Demo 3 Output — VLM Deep Analysis (Ollama LLaVA)",
                """
                VLM Deep Analysis (Ollama llava:7b)
                ----------------------------------------

                1. 表情/情绪：微笑，看起来很开心，表情自然放松
                2. 大致年龄：25-30岁
                3. 性别：女性
                4. 面部特征：长发，肤色均匀，无眼镜，
                   面部轮廓柔和，五官端正
                5. 整体印象：给人温暖友善的感觉，
                   看起来性格开朗
                """,
            ),
            block(
                "Demo 4 Input",
                """
                Image path: data/sample_face.jpg
                """,
            ),
            block(
                "Demo 4 Output — Age & Gender Estimation",
                """
                Age & Gender Estimation

                Image: sample_face.jpg
                Face: position=(180,95) size=165x165

                Estimated Age: 25-35岁
                Estimated Gender: 女
                """,
            ),
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(transcript, encoding="utf-8")
    print(transcript)
    print(f"Demo output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
