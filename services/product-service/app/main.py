from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time

app = FastAPI(title="Product Service", version="1.0.0")

# Prometheus metrics
REQUEST_COUNT = Counter('product_service_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('product_service_request_duration_seconds', 'Request duration')

# In-memory database simulation
products_db = [
    {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
    {"id": 2, "name": "Book", "price": 29.99, "category": "Education"}
]

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    category: str

@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

@app.get("/")
async def root():
    return {"message": "Product Service is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "product-service"}

@app.get("/products", response_model=List[Product])
async def get_products():
    return products_db

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=Product)
async def create_product(product: Product):
    product.id = len(products_db) + 1
    products_db.append(product.dict())
    return product

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
