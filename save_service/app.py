from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import httpx

app = FastAPI(title="Record Save Service", version="2.0.0")

DB_SERVICE_URL = "http://localhost:8002"  # db_service 주소

class RecordInput(BaseModel):
    name: str = Field(..., min_length=1)
    grade: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)   # 교과 / 자율·봉사·진로·동아리
    field: str = Field(..., min_length=1)     # 수업태도/탐구/책임감/...
    keyword: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)  # 세특/행발/창체
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

@app.get("/health")
def health():
    return {"status": "ok", "service": "save_service"}

@app.post("/save")
async def save_record(data: RecordInput):
    """입력 → db_service(/insert)로 저장 요청을 프록시"""
    payload = data.model_dump()
    payload["ts"] = datetime.now().isoformat(timespec="seconds")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{DB_SERVICE_URL}/insert", json=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"db_service /insert error: {r.text}")
        return {"status": "success", "db_service": r.json(), "timestamp": payload["ts"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"proxy error: {e}")
