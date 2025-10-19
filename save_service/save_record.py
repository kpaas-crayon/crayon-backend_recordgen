# 2. 관찰일지 저장부 (저장 전용 API)
import requests
from datetime import datetime
from typing import Optional

# DB 서비스 주소 (Docker Compose 기준이면 서비스명으로 접근)
DB_SERVICE_URL = "http://db_service:8002"


ENCODING = "utf-8"
MAX_NEW_TOKENS = 256

# 분야 표준(정규화 대상)
FIELD_CANON = {

    # 세부 능력 및 특기 사항
    "수업태도": "수업태도",
    "과제":   "과제",
    "발표":   "발표",
    "탐구":   "탐구",

    # 행동 특성 및 종합 의견
    "책임감":    "책임감",
    "협업":     "협업",
    "자기관리":  "자기관리",
    "공감/배려":  "공감/배려",

    # 창의적 체험활동
    "기획":    "기획",
    "협업":     "협업",
    "문제해결":  "문제해결",
    "리더십":  "리더십"
}

def normalize_field(field: str) -> Optional[str]:
    f = (field or "").strip()
    if not f:
        return None
    if f in FIELD_CANON:
        return FIELD_CANON[f]
    f2 = f.replace(" ", "")
    if f2 in FIELD_CANON:
        return FIELD_CANON[f2]
    return None

def save_keyword_entry(name, grade, subject, field, keyword, category, date, ts):
    """DB 서비스로 저장 요청을 보냄"""
    payload = {
        "name": name,
        "grade": grade,
        "subject": subject,
        "field": field,
        "keyword": keyword,
        "category": category,
        "date": date,
        "ts": ts,
    }

    try:
        response = requests.post(DB_SERVICE_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    

# 5. 관찰일지 저장

# subject:
# 세부 능력 및 특기 사항: 국어, 수학, 사회, 과학 등 해당 교과목 입력
# 행동 특성 및 종합의견: '행발' 입력
# 창의적 체험활동: '자율', '봉사', '진로', '동아리' 증 1택

# fields:
# 세부 능력 및 특기 사항: 수업 태도, 과제, 발표, 탐구
# 행동 특성 및 종합의견: 책임감, 협업, 자기관리, 공감/배려
# 창의적 체험활동: 기획, 협업, 문제해결, 리더십


