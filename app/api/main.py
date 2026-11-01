import json, hashlib
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from redis import Redis
from app.config import ELASTIC_URL, REDIS_URL
from app.api.auth import authenticate_ldap

app = FastAPI(title="ENADE Distribuído API", version="1.0.0",
              description="Busca distribuída de questões do ENADE")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
es = Elasticsearch(ELASTIC_URL)
redis = Redis.from_url(REDIS_URL, decode_responses=True)
INDEX = "enade-questions"

@app.get("/health")
def health():
    checks = {}
    for name, fn in [("elasticsearch", lambda: es.ping()), ("redis", lambda: redis.ping())]:
        try: checks[name] = bool(fn())
        except Exception: checks[name] = False
    return {"status": "ok" if all(checks.values()) else "degraded", "services": checks}

@app.post("/auth/login")
def login(payload: dict):
    user = authenticate_ldap(payload.get("username",""), payload.get("password",""))
    if not user: raise HTTPException(401, "Credenciais inválidas")
    # Token de laboratório simplificado; substituir por JWT assinado antes de uso real.
    token = hashlib.sha256(f"{user['username']}:{user['role']}".encode()).hexdigest()
    redis.setex(f"token:{token}", 3600, json.dumps(user))
    return {"access_token": token, "token_type":"bearer", "user":user}

def current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Autenticação necessária")
    token = authorization.split(" ",1)[1]
    value = redis.get(f"token:{token}")
    if not value: raise HTTPException(401, "Sessão inválida")
    return json.loads(value)

@app.get("/questions")
def search_questions(q: str = "", area: str | None = None, course: str | None = None,
                     year: int | None = None, exam_type: str | None = None,
                     question_type: str | None = None, page: int = Query(1, ge=1),
                     size: int = Query(10, ge=1, le=100), authorization: str | None = Header(None)):
    user = current_user(authorization) if authorization else {"role":"ESTUDANTE"}
    cache_key = "search:" + hashlib.sha256(json.dumps([q,area,course,year,exam_type,question_type,page,size,user["role"]]).encode()).hexdigest()
    cached = redis.get(cache_key)
    if cached: return json.loads(cached)
    filters = []
    for field, value in [("area",area),("course",course),("year",year),("exam_type",exam_type),("question_type",question_type)]:
        if value is not None: filters.append({"term":{field:value}})
    # Estudante não recebe gabarito; professor precisa autenticar para vê-lo.
    body = {"query":{"bool":{"must":[{"multi_match":{"query":q,"fields":["statement^3","alternatives"],"type":"best_fields"}}] if q else [{"match_all":{}}],
                                "filter":filters}},
            "from":(page-1)*size,"size":size,
            "highlight":{"fields":{"statement":{}}}}
    result = es.search(index=INDEX, body=body)
    items = []
    for hit in result["hits"]["hits"]:
        source = hit["_source"]
        if user["role"] != "PROFESSOR": source.pop("answer_key", None)
        items.append({"id":hit["_id"],"score":hit["_score"],"question":source,
                      "highlight":hit.get("highlight",{})})
    response = {"total":result["hits"]["total"]["value"],"page":page,"size":size,"items":items}
    redis.setex(cache_key, 60, json.dumps(response, ensure_ascii=False))
    return response

@app.get("/questions/{question_id}")
def get_question(question_id: str, authorization: str | None = Header(None)):
    user = current_user(authorization) if authorization else {"role":"ESTUDANTE"}
    try: doc = es.get(index=INDEX,id=question_id)["_source"]
    except Exception: raise HTTPException(404,"Questão não encontrada")
    if user["role"] != "PROFESSOR": doc.pop("answer_key",None)
    return doc

@app.get("/analytics/courses")
def analytics_courses(authorization: str | None = Header(None)):
    user = current_user(authorization)
    if user["role"] != "PROFESSOR": raise HTTPException(403,"Acesso restrito a professores")
    r = es.search(index=INDEX, size=0, aggs={"courses":{"terms":{"field":"course","size":100}}})
    return [{"course":b["key"],"count":b["doc_count"]} for b in r["aggregations"]["courses"]["buckets"]]

@app.get("/analytics/competencies")
def analytics_competencies(authorization: str | None = Header(None)):
    user = current_user(authorization)
    if user["role"] != "PROFESSOR": raise HTTPException(403,"Acesso restrito a professores")
    r = es.search(index=INDEX,size=0,aggs={"competencies":{"terms":{"field":"competencies","size":100}}})
    return [{"competency":b["key"],"count":b["doc_count"]} for b in r["aggregations"]["competencies"]["buckets"]]

@app.post("/cart/{session_id}")
def add_cart(session_id: str, payload: dict):
    key=f"cart:{session_id}"
    redis.sadd(key, payload["question_id"]); redis.expire(key, 86400)
    return {"session_id":session_id,"items":sorted(redis.smembers(key))}

@app.get("/cart/{session_id}")
def get_cart(session_id: str):
    return {"session_id":session_id,"items":sorted(redis.smembers(f"cart:{session_id}"))}

@app.delete("/cart/{session_id}/{question_id}")
def remove_cart(session_id: str, question_id: str):
    redis.srem(f"cart:{session_id}",question_id)
    return {"items":sorted(redis.smembers(f"cart:{session_id}"))}
