from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from db import get_conn

app = FastAPI(
    title="DB Service",
    description="학생 관찰일지용 MySQL DB 서비스",
    version="1.0.0"
)

# 입력 모델 정의
class KeywordQuery(BaseModel):
    name: str
    grade: Optional[str] = None
    subject: str
    category: str

class RecordInput(BaseModel):
    name: str
    grade: str
    subject: str
    field: str
    keyword: str
    category: str
    date: str
    ts: str | None = None


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "db_service"}


@app.post("/keywords")
def get_keywords(data: KeywordQuery):
    """조건(name, subject, category 등)에 맞는 키워드 리스트 반환"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        sql = """
            SELECT f.name AS field, r.keyword, r.date, r.ts
            FROM record r
            JOIN student s ON r.student_id = s.student_id
            JOIN subject subj ON r.subject_id = subj.subject_id
            JOIN field f ON r.field_id = f.field_id
            WHERE s.name=%s AND subj.name=%s AND subj.category=%s
        """
        params = [data.name, data.subject, data.category]

        if data.grade:
            sql += " AND s.grade=%s"
            params.append(data.grade)

        if data.fields:
            placeholders = ",".join(["%s"] * len(data.fields))
            sql += f" AND f.name IN ({placeholders})"
            params.extend(data.fields)

        if data.date:
            sql += " AND r.date LIKE %s"
            params.append(data.date[:7] + "%")

        cur.execute(sql, params)
        results = cur.fetchall()
        cur.close()
        conn.close()

        # DictCursor 덕분에 dict 형태 반환됨
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/insert")
def insert_record(r: RecordInput):
    try:
        conn = get_conn()
        cur = conn.cursor()

        # 1) 기준 테이블 upsert (없으면 생성)
        cur.execute("INSERT IGNORE INTO student(name, grade) VALUES (%s, %s)", (r.name, r.grade))
        cur.execute("INSERT IGNORE INTO subject(name, category) VALUES (%s, %s)", (r.subject, r.category))
        cur.execute("INSERT IGNORE INTO `field`(name, category) VALUES (%s, %s)", (r.field, r.category))

        # 2) FK id 조회
        cur.execute("SELECT student_id FROM student WHERE name=%s AND grade=%s", (r.name, r.grade))
        sid = cur.fetchone()["student_id"]
        cur.execute("SELECT subject_id FROM subject WHERE name=%s AND category=%s", (r.subject, r.category))
        subid = cur.fetchone()["subject_id"]
        cur.execute("SELECT field_id FROM `field` WHERE name=%s AND category=%s", (r.field, r.category))
        fid = cur.fetchone()["field_id"]

        # 3) record 저장
        ts = r.ts or "NOW()"
        if ts == "NOW()":
            sql = """
              INSERT INTO record(student_id, subject_id, field_id, keyword, date, ts)
              VALUES (%s, %s, %s, %s, %s, NOW())
            """
            params = (sid, subid, fid, r.keyword, r.date)
            cur.execute(sql, params)
        else:
            sql = """
              INSERT INTO record(student_id, subject_id, field_id, keyword, date, ts)
              VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (sid, subid, fid, r.keyword, r.date, r.ts)
            cur.execute(sql, params)

        conn.commit()
        cur.close(); conn.close()
        return {"status": "ok"}

    except Exception as e:
        # 상세 원인 보기 위해 메시지 그대로 전달
        raise HTTPException(status_code=500, detail=f"DB insert error: {e}")