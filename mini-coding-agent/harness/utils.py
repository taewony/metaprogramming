# harness/utils.py
import re

def clip(text, limit):
    """긴 문자열을 앞부분만 잘라내고 ... 표시"""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + f"\n...[truncated {len(text) - limit} chars]"

def middle(text, limit):
    """문자열의 가운데 부분을 ...으로 축약"""
    # ...

def now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

# XML 파싱 헬퍼 (parse, extract, parse_xml_tool 등)