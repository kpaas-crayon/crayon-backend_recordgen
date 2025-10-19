import os
import requests
from openai import OpenAI
from typing import List, Dict, Optional
from prompt_system import get_prompt
from prompt_user import get_user_prompt

# -------------------------------
# 기본 설정
# -------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4o-mini"
DB_SERVICE_URL = "http://localhost:8002"  # db_service API 엔드포인트


# -------------------------------
# DB에서 키워드 가져오기 (REST 호출)
# -------------------------------
def load_keywords_by_meta(*, grade, subject, name, date=None, fields=None, category=None):
    """
    db_service로 HTTP 요청을 보내서 키워드 조회.
    """
    payload = {
        "grade": grade,
        "subject": subject,
        "name": name,
        "date": date,
        "fields": fields,
        "category": category,
    }
    resp = requests.post(f"{DB_SERVICE_URL}/keywords", json=payload, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"DB 서비스 오류: {resp.text}")
    return resp.json()  # [{field, keyword, date, ts}, ...]


# -------------------------------
# 1차: 분야별 문단 생성
# -------------------------------
def build_field_messages(*, grade: str, subject: str, name: str, date: Optional[str],
                         field: str, keywords: List[str], category: str) -> List[Dict]:
    system_prompt = get_prompt(category)
    user_prompt_template = get_user_prompt(category, "field")

    date_str = date if date else "(미지정)"
    kw_bullets = "\n".join(f"- {k}" for k in keywords) if keywords else "(키워드 없음)"

    user_prompt = user_prompt_template.format(
        grade=grade,
        subject=subject,
        name=name,
        date_str=date_str,
        field=field,
        kw_bullets=kw_bullets,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt.strip()},
    ]


def generate_paragraph_for_field(*, grade, subject, name, date, field, keywords, category):
    messages = build_field_messages(
        grade=grade, subject=subject, name=name, date=date, field=field, keywords=keywords, category=category
    )
    resp = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=400,
    )
    return resp.choices[0].message.content.strip()


# -------------------------------
# 2차: 통합 문단 생성
# -------------------------------
def build_final_messages(*, grade, subject, name, date, field_paragraphs, category):
    system_prompt = get_prompt(category)
    user_prompt_template = get_user_prompt(category, "final")

    date_str = date if date else "(미지정)"
    parts = []
    for f, para in field_paragraphs.items():
        if para.strip():
            parts.append(f"[{f}]\n{para.strip()}")
    field_block = "\n\n".join(parts) if parts else "(생성된 1차 문단 없음)"

    user_prompt = user_prompt_template.format(
        grade=grade,
        subject=subject,
        name=name,
        date_str=date_str,
        parts=field_block,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt.strip()},
    ]


def generate_final_from_field_paragraphs(*, grade, subject, name, date, field_paragraphs, category):
    messages = build_final_messages(
        grade=grade, subject=subject, name=name, date=date, field_paragraphs=field_paragraphs, category=category
    )
    resp = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=700,
    )
    return resp.choices[0].message.content.strip()


# -------------------------------
# 최종 통합 함수 (2단계 생성)
# -------------------------------
def generate_record_two_stage(*, grade, subject, name, date, fields, category):
    """
    DB에서 키워드 → 분야별 문단 → 통합 문단 순서로 생성
    """
    # 1️⃣ 키워드 수집
    entries = load_keywords_by_meta(
        grade=grade, subject=subject, name=name, date=date, fields=fields, category=category
    )

    by_field: Dict[str, List[str]] = {}
    for e in entries:
        f = e.get("field")
        kw = e.get("keyword")
        if f:
            by_field.setdefault(f, []).append(kw)

    # 2️⃣ 1차 생성
    per_field: Dict[str, str] = {}
    for f, kws in by_field.items():
        if not kws:
            continue
        per_field[f] = generate_paragraph_for_field(
            grade=grade, subject=subject, name=name, date=date, field=f, keywords=kws, category=category
        )

    # 3️⃣ 2차 통합
    final_para = ""
    if per_field:
        final_para = generate_final_from_field_paragraphs(
            grade=grade, subject=subject, name=name, date=date, field_paragraphs=per_field, category=category
        )

    return {"per_field": per_field, "final": final_para}
