# harness/session.py
import json
from pathlib import Path

class SessionStore:
    """세션을 JSON 파일로 저장/불러오기"""
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, session):
        path = self.root / f"{session['id']}.json"
        path.write_text(json.dumps(session, indent=2), encoding="utf-8")
        return path

    def load(self, session_id):
        return json.loads(self.path(session_id).read_text(encoding="utf-8"))