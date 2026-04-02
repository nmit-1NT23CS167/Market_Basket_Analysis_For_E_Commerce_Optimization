"""
server.py
---------
FastAPI REST API for Market Basket Analysis.

Run with:
    pip install fastapi uvicorn
    python server.py

Endpoints:
    GET  /api/products        — list all known products
    POST /api/recommend       — get recommendations for a cart
    POST /api/transaction     — add new transaction & update rules
    GET  /api/rules           — view current rules (with optional filters)
    GET  /api/stats           — dashboard stats
    POST /api/rules/rebuild   — force rule rebuild
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json, time
import apriori_engine as engine

app = FastAPI(title="Market Basket Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# All known products with metadata
PRODUCT_CATALOG = [
    {"id":"P001","name":"whole milk","label":"Whole Milk","category":"dairy","icon":"🥛","price":1.99},
    {"id":"P002","name":"rolls/buns","label":"Rolls/Buns","category":"bakery","icon":"🥖","price":2.49},
    {"id":"P003","name":"other vegetables","label":"Mixed Vegetables","category":"produce","icon":"🥦","price":1.79},
    {"id":"P004","name":"soda","label":"Soda","category":"beverage","icon":"🥤","price":1.29},
    {"id":"P005","name":"yogurt","label":"Yogurt","category":"dairy","icon":"🫙","price":0.99},
    {"id":"P006","name":"bottled water","label":"Bottled Water","category":"beverage","icon":"💧","price":0.89},
    {"id":"P007","name":"root vegetables","label":"Root Vegetables","category":"produce","icon":"🥕","price":1.49},
    {"id":"P008","name":"tropical fruit","label":"Tropical Fruit","category":"produce","icon":"🍍","price":2.99},
    {"id":"P009","name":"shopping bags","label":"Shopping Bags","category":"other","icon":"🛍️","price":0.29},
    {"id":"P010","name":"pastry","label":"Pastry","category":"bakery","icon":"🥐","price":1.89},
    {"id":"P011","name":"citrus fruit","label":"Citrus Fruit","category":"produce","icon":"🍊","price":1.69},
    {"id":"P012","name":"canned beer","label":"Canned Beer","category":"beverage","icon":"🍺","price":3.49},
    {"id":"P013","name":"brown bread","label":"Brown Bread","category":"bakery","icon":"🍞","price":2.19},
    {"id":"P014","name":"margarine","label":"Margarine","category":"dairy","icon":"🧈","price":1.59},
    {"id":"P015","name":"butter","label":"Butter","category":"dairy","icon":"🫙","price":2.29},
    {"id":"P016","name":"newspapers","label":"Newspapers","category":"other","icon":"📰","price":0.79},
    {"id":"P017","name":"curd","label":"Curd","category":"dairy","icon":"🫙","price":1.09},
    {"id":"P018","name":"domestic eggs","label":"Eggs","category":"dairy","icon":"🥚","price":2.99},
    {"id":"P019","name":"fruit/vegetable juice","label":"Fruit Juice","category":"beverage","icon":"🧃","price":2.49},
    {"id":"P020","name":"whipped/sour cream","label":"Sour Cream","category":"dairy","icon":"🫙","price":1.39},
    {"id":"P021","name":"pip fruit","label":"Pip Fruit","category":"produce","icon":"🍏","price":1.99},
    {"id":"P022","name":"coffee","label":"Coffee","category":"beverage","icon":"☕","price":4.99},
    {"id":"P023","name":"frozen vegetables","label":"Frozen Vegetables","category":"produce","icon":"🧊","price":2.29},
    {"id":"P024","name":"pork","label":"Pork","category":"meat","icon":"🥩","price":4.49},
    {"id":"P025","name":"cream cheese","label":"Cream Cheese","category":"dairy","icon":"🧀","price":1.79},
    {"id":"P026","name":"sliced cheese","label":"Sliced Cheese","category":"dairy","icon":"🧀","price":2.49},
    {"id":"P027","name":"bottled beer","label":"Bottled Beer","category":"beverage","icon":"🍶","price":3.99},
    {"id":"P028","name":"pip fruit","label":"Apple","category":"produce","icon":"🍏","price":0.99},
]

PRODUCT_MAP = {p["name"]: p for p in PRODUCT_CATALOG}

class CartRequest(BaseModel):
    items: List[str]
    top_n: Optional[int] = 6

class TransactionRequest(BaseModel):
    items: List[str]
    session_id: Optional[str] = None

class RebuildRequest(BaseModel):
    min_support: Optional[float] = 0.03
    min_confidence: Optional[float] = 0.25
    min_lift: Optional[float] = 1.2

@app.on_event("startup")
def startup():
    if not os.path.exists(engine.RULES_FILE):
        print("No rules file found — building from seed data...")
        engine.rebuild_rules()
        print("Rules built.")

@app.get("/api/products")
def get_products():
    return {"products": PRODUCT_CATALOG}

@app.post("/api/recommend")
def recommend(req: CartRequest):
    if not req.items:
        raise HTTPException(400, "Cart is empty")
    normalized = [i.lower().strip() for i in req.items]
    recs = engine.recommend(normalized, top_n=req.top_n)
    enriched = []
    for r in recs:
        meta = PRODUCT_MAP.get(r["item"], {
            "label": r["item"].title(),
            "category": "other",
            "icon": "🛒",
            "price": 0.0
        })
        enriched.append({**r, **meta})
    return {
        "cart": req.items,
        "recommendations": enriched,
        "n_recommendations": len(enriched),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.post("/api/transaction")
def add_transaction(req: TransactionRequest):
    if len(req.items) < 2:
        raise HTTPException(400, "Transaction must contain at least 2 items")
    result = engine.add_transaction_and_update(req.items)
    return {
        "status": "ok",
        "message": f"Transaction saved. Rules updated: {result['n_rules']} rules from {result['n_transactions']} transactions.",
        **result
    }

@app.get("/api/rules")
def get_rules(
    min_support: float = 0.0,
    min_confidence: float = 0.0,
    min_lift: float = 0.0,
    limit: int = 50
):
    data = engine.load_rules()
    rules = data.get("rules", [])
    filtered = [r for r in rules
                if r["support"] >= min_support
                and r["confidence"] >= min_confidence
                and r["lift"] >= min_lift]
    return {
        "meta": {k: v for k, v in data.items() if k != "rules"},
        "rules": filtered[:limit],
        "total_filtered": len(filtered)
    }

@app.get("/api/stats")
def get_stats():
    data = engine.load_rules()
    rules = data.get("rules", [])
    txns = engine.load_transactions()
    avg_basket = sum(len(t) for t in txns) / len(txns) if txns else 0
    top_rules = sorted(rules, key=lambda r: -r["lift"])[:5]
    return {
        "n_transactions": len(txns),
        "n_rules": len(rules),
        "n_products": len(PRODUCT_CATALOG),
        "avg_basket_size": round(avg_basket, 2),
        "top_rules": top_rules,
        "generated_at": data.get("generated_at", "N/A")
    }

@app.post("/api/rules/rebuild")
def force_rebuild(req: RebuildRequest):
    meta = engine.rebuild_rules(req.min_support, req.min_confidence, req.min_lift)
    return {"status": "ok", "n_rules": meta["n_rules"], "n_transactions": meta["n_transactions"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)