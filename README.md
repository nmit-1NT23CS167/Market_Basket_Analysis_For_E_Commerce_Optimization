# 🛒 IntelliGrocery MBA — Notebook-Integrated Edition

Full MBA Analytics Platform built from `MBA_ECommerce_Apriori.ipynb`.
Every notebook section is a dedicated Streamlit page.

## ▶ Quick Start

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

## 📄 Pages (maps to notebook sections)

| Page | Notebook Section | Features |
|------|-----------------|----------|
| 📊 Exploratory Analysis | Section 2 | Country chart, product freq, monthly revenue, basket size, hourly orders |
| 🔢 Transaction Encoding | Section 3 | Sparse matrix heatmap, support tiers, memory comparison |
| ⚙️ Apriori Mining | Sections 4&5 | Pass trace, pruning rate, frequent itemsets table |
| 📐 Rules Analysis | Section 6 | Support/confidence scatter, lift bar, co-occurrence heatmap, distributions |
| 🎯 Recommendation Engine | Section 7 | Coverage-weighted scoring, multi-cart comparison |
| 🔄 Incremental Learning | Section 8 | 5-purchase simulation, rule evolution charts |
| 🔬 Sensitivity Analysis | Section 9 | Support×confidence grid heatmaps |
| ⚡ Real-Time Simulation | Bonus | Live transaction generator, revenue gauge |
| 🏆 Optimization Summary | Sections 10&11 | All 9 optimisations, project summary dashboard |

## 📁 Structure

```
IntelliGrocery2/
├── frontend/app.py          # 9-page Streamlit UI
├── backend/
│   ├── apriori_engine.py    # Pure-Python Apriori (from notebook)
│   └── data_layer.py        # SQLite seeder & query helpers
├── data/grocery.db          # Auto-created on first run
└── requirements.txt
```

## ⚙️ Algorithm Parameters (sidebar)

| Parameter | Default | Effect |
|-----------|---------|--------|
| Min Support | 0.02 | Lower = more rules, slower |
| Min Confidence | 0.15 | Lower = weaker rules included |
| Min Lift | 1.5 | Higher = only strong associations |
| Max Itemset Len | 4 | Higher = more complex bundles |

## 🔑 Key Optimisations (from notebook Section 10)

1. Anti-monotone pruning — 90–99% candidate reduction
2. Self-join candidate generation — O(n²) not O(nᵏ)
3. Dict-based counting — O(1) lookup
4. Sparse frozenset encoding — ~10× memory saving
5. Dual confidence+lift filter — removes spurious rules
6. Conviction + Leverage metrics — multi-metric ranking
7. Incremental update — no full rebuild on new data
8. Coverage-weighted scoring — personalised recs
9. Top-N deduplication — diverse output
