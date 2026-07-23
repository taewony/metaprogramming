import json
import os
from game.constants import BASE_DIR

import sys

class ScoreManager:
    def __init__(self):
        # 실행 파일 빌드 시, 점수 파일은 Temp 폴더가 아닌 실행 파일과 같은 위치에 저장되어야 함
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = BASE_DIR
            
        self.file_path = os.path.join(base_path, "scores.json")
        self.scores = self.load_scores()

    def load_scores(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_scores(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, indent=4)
        except IOError as e:
            print(f"Error saving scores: {e}")

    def add_score(self, name, score):
        self.scores.append({'name': name, 'score': score})
        # 점수 내림차순 정렬
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        # 상위 5개만 유지
        self.scores = self.scores[:5]
        self.save_scores()

    def get_top_scores(self):
        return self.scores
