import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import time
from datetime import datetime

def get_unique_path(target_folder: Path, filename: str) -> Path:
    """
    대상 폴더에 동일한 이름의 파일이 존재할 경우, 파일명 뒤에 (1), (2) 등을 붙여 고유한 경로를 반환합니다.
    """
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

def select_target_directory() -> str:
    """
    Tkinter를 사용하여 사용자에게 정리할 대상 폴더를 선택하게 합니다.
    """
    root = tk.Tk()
    root.withdraw() # 메인 윈도우 숨기기
    # 최상단에 창을 띄우기 위한 설정
    root.attributes('-topmost', True)
    
    print("정리할 대상 폴더를 선택해 주세요...")
    directory = filedialog.askdirectory(title="정리할 대상 폴더를 선택하세요")
    
    root.destroy()
    return directory

def organize_files(target_dir: str):
    """
    지정된 디렉터리의 파일들을 확장자에 따라 폴더별로 분류합니다.
    """
    TARGET_DIR = Path(target_dir)
    
    if not TARGET_DIR.exists() or not TARGET_DIR.is_dir():
        print(f"오류: '{target_dir}' 경로를 찾을 수 없거나 디렉터리가 아닙니다.")
        return

    # 폴더 이름 및 해당 확장자 매핑
    CATEGORY_MAPPING = {
        '이미지': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
        '문서': ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt', '.pptx', '.ppt', '.csv', '.hwp'],
        '영상': ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
    }

    # 확장자를 키로, 타겟 폴더 이름을 값으로 가지는 빠른 검색용 딕셔너리 생성
    extension_to_folder = {}
    for folder, extensions in CATEGORY_MAPPING.items():
        for ext in extensions:
            extension_to_folder[ext.lower()] = folder

    print(f"\n[{TARGET_DIR}] 폴더 정리를 시작합니다...")
    
    # 로그 설정
    now = datetime.now()
    log_dir = TARGET_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 주의: 윈도우 파일 시스템에서는 파일명에 ':' 문자를 사용할 수 없으므로 '-'로 대체합니다
    log_filename = now.strftime("%Y%m%d_%H-%M-%S_summary.txt")
    log_filepath = log_dir / log_filename
    
    log_entries = []
    log_entries.append(f"실행 일시: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    log_entries.append(f"대상 폴더: {TARGET_DIR}")
    log_entries.append("-" * 50)
    
    moved_count = 0
    skipped_count = 0
    dir_skipped_count = 0
    
    # logs 폴더 자체는 무시하기 위해 이름 예외 처리
    log_dir_name = log_dir.name

    # 폴더 내 모든 항목 순회
    for item in TARGET_DIR.iterdir():
        # 디렉터리는 이동 대상에서 무조건 제외 (보존)
        if item.is_dir():
            dir_skipped_count += 1
            if item.name == log_dir_name:
                dir_skipped_count -= 1 # logs 폴더 자체는 카운트에서 제외하는 것이 깔끔함
            continue
            
        # 1년이 지난 파일인지 확인 (365일)
        file_age_seconds = time.time() - item.stat().st_mtime
        is_old = file_age_seconds > 365 * 24 * 3600
        
        # 타겟 폴더 결정
        target_folder_name = None
        ext = item.suffix.lower()
        
        if is_old:
            target_folder_name = "oldfiles"
        elif ext in extension_to_folder:
            target_folder_name = extension_to_folder[ext]
        
        # 이동 대상인 경우 처리
        if target_folder_name:
            target_folder_path = TARGET_DIR / target_folder_name
            
            # 대상 폴더가 없으면 생성
            target_folder_path.mkdir(exist_ok=True)
            
            # 중복을 피한 고유한 파일 경로 획득
            unique_dest_path = get_unique_path(target_folder_path, item.name)
            
            # 파일 이동
            try:
                shutil.move(str(item), str(unique_dest_path))
                print(f"이동 완료: {item.name} -> {target_folder_name}/ ({unique_dest_path.name})")
                log_entries.append(f"[이동 완료] {item.name} -> {target_folder_name}/{unique_dest_path.name}")
                moved_count += 1
            except Exception as e:
                print(f"이동 실패: {item.name} (사유: {e})")
                log_entries.append(f"[이동 실패] {item.name} (사유: {e})")
        else:
            # 매핑에 없고 1년 이상 안 지난 파일은 그대로 둠
            skipped_count += 1

    print("\n--- 정리 완료 ---")
    print(f"총 이동된 파일 수: {moved_count}개")
    print(f"분류되지 않고 보존된 파일 수: {skipped_count}개")
    print(f"보존된 디렉터리 수: {dir_skipped_count}개")
    
    # 로그 요약 추가 및 저장
    log_entries.append("-" * 50)
    log_entries.append(f"총 이동된 파일 수: {moved_count}개")
    log_entries.append(f"분류되지 않고 보존된 파일 수: {skipped_count}개")
    log_entries.append(f"보존된 디렉터리 수: {dir_skipped_count}개")
    
    try:
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(log_entries) + "\n")
        print(f"\n로그 파일이 생성되었습니다: {log_filepath}")
    except Exception as e:
        print(f"\n로그 파일 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    try:
        selected_dir = select_target_directory()
        if selected_dir:
            organize_files(selected_dir)
        else:
            print("폴더 선택이 취소되었습니다.")
            
        # 단일 실행 파일일 때 결과를 볼 수 있도록 잠시 대기
        input("\n프로그램을 종료하려면 Enter 키를 누르세요...")
    except Exception as e:
        print(f"\n치명적인 오류 발생: {e}")
        input("\n오류 내용을 확인 후 Enter 키를 눌러 종료하세요...")
