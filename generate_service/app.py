from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import httpx
from generate_record import generate_record_two_stage

app = FastAPI(title="Generate Record Service", version="2.0.0")

DB_SERVICE_URL = "http://localhost:8002"   # db_service 조회용
SAVE_SERVICE_URL = "http://localhost:8001" # 저장 결과를 남기고 싶을 때 사용(선택)

class GenerateInput(BaseModel):
    name: str = Field(..., min_length=1)
    grade: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)

def out_field(category: str):
    mapping = {
        "세부능력및특기사항": ["수업태도", "과제", "발표", "탐구"],
        "행동특성및종합의견": ["책임감", "협업", "자기관리", "공감/배려"],
        "창의적체험활동":   ["기획", "협업", "문제해결", "리더십"],
    }
    return mapping.get(category, [])

@app.get("/health")
def health():
    return {"status": "ok", "service": "generate_service"}

@app.post("/generate")
async def generate(data: GenerateInput):
    """
    1) db_service /keywords 로 전체 날짜의 원시 키워드 조회
    2) LLM으로 1차(분야별) + 2차(통합) 생성
    3) (선택) save_service /save 로 생성 결과 요약 저장
    """
    # 1) 조회
    query = {
        "name": data.name,
        "grade": data.grade,
        "subject": data.subject,
        "category": data.category,
        # date, fields 없음 → 전체 기간 전부
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{DB_SERVICE_URL}/keywords", json=query)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"db_service /keywords error: {r.text}")
        rows = r.json()
        if not rows:
            raise HTTPException(status_code=404, detail="조건에 맞는 저장 데이터 없음")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"db lookup error: {e}")

    # 필드별 키워드 맵
    field_map = {}
    for row in rows:
        field_map.setdefault(row["field"], []).append(row["keyword"])

    # 2) 생성
    used_fields = out_field(data.category)
    result = generate_record_two_stage(
        grade=data.grade,
        subject=data.subject,
        name=data.name,
        date=None,             # 전체 기간
        fields=used_fields,
        category=data.category,
    )

    # 3) (선택) 생성 결과를 간단 요약으로 저장하고 싶으면 아래 주석 해제
    # save_payload = {
    #     "name": data.name,
    #     "grade": data.grade,
    #     "subject": data.subject,
    #     "field": ",".join(used_fields),
    #     "keyword": " | ".join(sum(field_map.values(), [])),  # 근거 키워드 합본
    #     "category": data.category,
    #     "date": datetime.now().strftime("%Y-%m-%d"),
    # }
    # async with httpx.AsyncClient(timeout=15) as client:
    #     s = await client.post(f"{SAVE_SERVICE_URL}/save", json=save_payload)
    # if s.status_code != 200:
    #     raise HTTPException(status_code=502, detail=f"save_service /save error: {s.text}")

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "keywords_count": len(rows),
        "fields_used": used_fields,
        "generated": result,  # {"per_field": {...}, "final": "..."}
    }
