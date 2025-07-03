from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time

app = FastAPI(title="User Service", version="1.0.0")

# Prometheus metrics
REQUEST_COUNT = Counter('user_service_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('user_service_request_duration_seconds', 'Request duration')

# In-memory database simulation
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
]

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str

@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

@app.get("/")
async def root():
    return {"message": "User Service is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

@app.get("/users", response_model=List[User])
async def get_users():
    return users_db

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=User)
async def create_user(user: User):
    user.id = len(users_db) + 1
    users_db.append(user.dict())
    return user

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
