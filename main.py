from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from solver import optimize_invoices

app = FastAPI(title="Invoice Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    id: int
    name: str
    price: float
    quantity: int = 1
    cashback_eligible: bool         # counts toward cashback generation
    discount_eligible: bool = True  # counts toward $2,500 discount threshold


class OptimizeRequest(BaseModel):
    items: list[Item]


@app.post("/api/optimize")
def optimize(request: OptimizeRequest):
    items = [item.model_dump() for item in request.items]
    return optimize_invoices(items)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6969, reload=True)
