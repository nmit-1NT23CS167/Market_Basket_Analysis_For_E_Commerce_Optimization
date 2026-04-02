# BasketIQ — Market Basket Analysis

A full-stack Market Basket Analysis system using the **Apriori algorithm**,
seeded from the **UCI Online Retail dataset (Kaggle)**.

---

## Project Structure

```
market_basket/
├── frontend/
│   └── index.html          ← Standalone frontend (open directly in browser)
│
└── backend/
    ├── apriori_engine.py   ← Pure-Python Apriori + persistence logic
    ├── server.py           ← FastAPI REST API
    ├── requirements.txt    ← Python dependencies
    ├── rules.json          ← Auto-generated rules file (created on first run)
    └── transactions.json   ← Transaction log (created on first run)
```

---

## Quick Start — Frontend Only (no server needed)

1. Open `frontend/index.html` directly in any modern browser.
2. Select products → click "Get Recommendations".
3. Rules are stored in `localStorage`. New transactions update rules live.

---

## Full Stack — with Python backend

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Generate initial rules
```bash
python apriori_engine.py
```
Output:
```
Building rules from seed data...
Done — 88 rules from 197 transactions
```

### 3. Start the API server
```bash
python server.py
```
Server runs at: http://localhost:8000

API docs: http://localhost:8000/docs

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/products` | List all 28 products |
| POST | `/api/recommend` | Get recommendations for a cart |
| POST | `/api/transaction` | Save transaction + rebuild rules |
| GET | `/api/rules` | Get all rules (filterable) |
| GET | `/api/stats` | Dashboard stats |
| POST | `/api/rules/rebuild` | Force rule rebuild with new params |

### Example: Get recommendations
```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"items": ["whole milk", "rolls/buns"], "top_n": 5}'
```

### Example: Add new transaction
```bash
curl -X POST http://localhost:8000/api/transaction \
  -H "Content-Type: application/json" \
  -d '{"items": ["waffles", "coffee", "butter"]}'
```

---

## Algorithm Details

### Apriori — How it works

1. **Pass 1** — Scan all transactions, count single-item frequencies.
   Remove items with support < `min_support` (anti-monotone pruning).

2. **Pass 2** — Self-join frequent 1-itemsets → candidate 2-itemsets.
   Scan DB to count each candidate. Prune infrequent ones.

3. **Pass k** — Repeat until no new frequent k-itemsets found (max k=4).

4. **Rule generation** — For each frequent itemset {A,B,C}:
   Generate all non-empty subset rules: A→BC, B→AC, C→AB, AB→C, etc.
   Keep rules where:
   - `confidence = P(A∪B) / P(A) ≥ min_confidence`
   - `lift = confidence / P(B) ≥ min_lift` (lift > 1 = non-random association)

### Default thresholds
| Parameter | Default | Meaning |
|-----------|---------|---------|
| min_support | 3% | Item appears in ≥3% of transactions |
| min_confidence | 25% | Rule is correct ≥25% of the time |
| min_lift | 1.2 | 20% more likely than random co-occurrence |

### New transaction logic
When a user checks out with a cart:
1. The transaction is appended to the transaction log.
2. Rules are fully rebuilt (fast for <10k transactions).
3. New rules derived from the novel combination become immediately active.
4. The UI shows a "New rule learned" banner if no prior recommendations existed.

---

## Dataset

Seeded from **UCI Online Retail** dataset (available on Kaggle):
- Source: https://www.kaggle.com/datasets/vijayuv/onlineretail
- 541,909 real transactions from a UK e-commerce retailer
- 197 representative transactions embedded directly in the code

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS (zero dependencies, offline-capable) |
| Algorithm | Pure Python Apriori (no sklearn/mlxtend needed) |
| Backend | FastAPI + Uvicorn |
| Persistence | JSON files (rules.json, transactions.json) |
| Storage (FE) | localStorage (persists across browser sessions) |
