import os
import shutil
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from google import genai
from google.genai import types

# ==============================================================================
# 설정 (Configuration)
# ==============================================================================
API_KEY = "AIzaSyA3pAbFkVboZ4rD6xUyTSROTbw9VhAj0wE"  # 제공해주신 API 키
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-flash-lite-latest"

BATCH_SIZE = 10
MAX_CHARS = 1000

CATEGORIES = ["업무", "개인"]

def select_target_directory() -> Path:
    """Tkinter를 사용하여 사용자에게 분류할 대상 폴더를 선택하게 합니다."""
    root = tk.Tk()
    root.withdraw() # 메인 윈도우 숨기기
    root.attributes('-topmost', True) # 창을 최상단에 띄우기
    
    print("분류할 대상 폴더를 선택해 주세요...")
    directory = filedialog.askdirectory(title="분류할 대상 폴더를 선택하세요")
    
    root.destroy()
    return Path(directory) if directory else None

def get_unique_path(target_folder: Path, filename: str) -> Path:
    target_path = target_folder / filename
    if not target_path.exists():
        return target_path
    
    stem = target_path.stem
    suffix = target_path.suffix
    counter = 1
    while True:
        new_name = f"{stem}({counter}){suffix}"
        new_path = target_folder / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def read_file_preview(filepath: Path, max_chars: int = 1000) -> str:
    """파일의 앞부분 1000자를 읽어옵니다. 텍스트 파일이 아닐 경우 오류 없이 넘깁니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(max_chars)
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='cp949') as f:
                return f.read(max_chars)
        except Exception:
            return "[바이너리 파일이거나 읽을 수 없는 인코딩입니다. 이름으로 유추하세요.]"
    except Exception as e:
         return f"[파일 읽기 오류: {e}]"

def classify_batch(files_slice, target_dir):
    """파일 10개를 묶어 Gemini API에 분류를 요청합니다."""
    if not files_slice:
        return
    
    file_data_list = []
    for f in files_slice:
        preview = read_file_preview(f, MAX_CHARS)
        file_data_list.append(f"파일명: {f.name}\n내용 미리보기:\n{preview[:MAX_CHARS]}\n---")

    combined_text = "\n".join(file_data_list)
    
    prompt = f"""
당신은 사용자의 스토리지에서 파일을 분류하는 자동화 AI입니다.
주어진 각각의 파일명과 파일 내용 조금(미리보기)을 분석해서, 이 파일이 "업무" 용도인지 "개인" 용도인지 판별하세요.
애매한 파일은 "기타"로 분류하세요.

반드시 다음 형식의 JSON 객체로만 응답하세요(다른 말은 절대 하지 마세요):
{{
    "파일명1.txt": "업무",
    "파일명2.pdf": "개인",
    "파일명3.jpg": "기타"
}}

분석할 파일들:
{combined_text}
"""
    
    print(f"🔄 LLM에 {len(files_slice)}개 파일 분류 요청 중...")
    try:
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        # JSON 응답 강제 설정
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )

        # 모델 호출 (gemini-flash-lite-latest 사용)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config,
        )
        
        result_json = response.text
        classifications = json.loads(result_json)
        
        for f in files_slice:
            category = classifications.get(f.name, "기타")
            
            if category in CATEGORIES:
                dest_dir = target_dir / category
            else:
                dest_dir = target_dir / "기타"
                
            dest_dir.mkdir(exist_ok=True)
            new_path = get_unique_path(dest_dir, f.name)
            
            try:
                shutil.move(str(f), str(new_path))
                print(f"✅ 이동 완료: {f.name} -> {category}/")
            except Exception as e:
                print(f"❌ 이동 실패 ({f.name}): {e}")

    except Exception as e:
        print(f"API 호출 또는 JSON 파싱 중 오류 발생: {e}")

def main():
    target_dir = select_target_directory()
    if not target_dir:
        print("폴더 선택이 취소되었습니다.")
        return

    print(f"=== AI 스마트 파일 분류기 시작: {target_dir.name} ===")
    
    target_files = []
    for item in target_dir.iterdir():
        if item.is_file():
            target_files.append(item)
            
    if not target_files:
        print(f"'{target_dir}' 폴더 안에 분류할 파일이 없습니다.")
        return

    for i in range(0, len(target_files), BATCH_SIZE):
        batch = target_files[i:i + BATCH_SIZE]
        classify_batch(batch, target_dir)
        
    print("=== 모든 처리 완료! ===")

if __name__ == "__main__":
    main()
