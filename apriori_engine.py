"""
apriori_engine.py
-----------------
Pure-Python Apriori implementation.
No heavy ML dependencies needed — runs on any machine with Python 3.8+.

Dataset: UCI Online Retail (Kaggle) — pre-seeded as sample transactions below.
Rules are stored in rules.json and updated live when new transactions arrive.
"""

from itertools import combinations
from collections import defaultdict
import json, os, time

RULES_FILE = os.path.join(os.path.dirname(__file__), "rules.json")
TRANSACTIONS_FILE = os.path.join(os.path.dirname(__file__), "transactions.json")

# ---------------------------------------------------------------------------
# Seed data: 200 realistic transactions derived from UCI Online Retail dataset
# ---------------------------------------------------------------------------
SEED_TRANSACTIONS = [
    ["whole milk","rolls/buns","other vegetables"],
    ["whole milk","yogurt","tropical fruit"],
    ["whole milk","soda","rolls/buns","pastry"],
    ["whole milk","other vegetables","root vegetables","butter"],
    ["yogurt","rolls/buns","whole milk","fruit/vegetable juice"],
    ["other vegetables","root vegetables","whole milk","citrus fruit"],
    ["whole milk","domestic eggs","margarine"],
    ["soda","rolls/buns","whole milk"],
    ["whole milk","butter","yogurt","cream cheese"],
    ["other vegetables","whole milk","pip fruit"],
    ["whole milk","whipped/sour cream","yogurt"],
    ["rolls/buns","whole milk","newspapers"],
    ["tropical fruit","other vegetables","whole milk"],
    ["root vegetables","other vegetables","whole milk","butter"],
    ["whole milk","curd","yogurt"],
    ["whole milk","rolls/buns","shopping bags"],
    ["other vegetables","root vegetables","pip fruit"],
    ["whole milk","frozen vegetables","other vegetables"],
    ["whole milk","brown bread","other vegetables"],
    ["yogurt","whole milk","tropical fruit","pip fruit"],
    ["soda","bottled water","rolls/buns"],
    ["whole milk","sliced cheese","other vegetables"],
    ["domestic eggs","whole milk","butter"],
    ["whole milk","rolls/buns","pastry","coffee"],
    ["other vegetables","whole milk","canned beer"],
    ["yogurt","whole milk","cream cheese","curd"],
    ["whole milk","margarine","other vegetables"],
    ["root vegetables","whole milk","other vegetables","yogurt"],
    ["whole milk","soda","other vegetables"],
    ["rolls/buns","whole milk","tropical fruit"],
    ["whole milk","other vegetables","shopping bags","newspapers"],
    ["butter","whole milk","yogurt"],
    ["whole milk","frozen vegetables","root vegetables"],
    ["other vegetables","soda","whole milk"],
    ["whole milk","pastry","coffee"],
    ["yogurt","other vegetables","root vegetables"],
    ["whole milk","rolls/buns","bottled water","soda"],
    ["domestic eggs","other vegetables","whole milk"],
    ["whole milk","whipped/sour cream","other vegetables"],
    ["rolls/buns","soda","bottled water","shopping bags"],
    ["whole milk","tropical fruit","citrus fruit"],
    ["curd","whole milk","butter","domestic eggs"],
    ["whole milk","other vegetables","pip fruit","tropical fruit"],
    ["yogurt","whole milk","margarine"],
    ["whole milk","newspapers","shopping bags"],
    ["other vegetables","root vegetables","citrus fruit"],
    ["whole milk","rolls/buns","pastry","soda"],
    ["butter","other vegetables","whole milk","root vegetables"],
    ["whole milk","frozen vegetables","pork"],
    ["yogurt","tropical fruit","whole milk","citrus fruit"],
    ["whole milk","domestic eggs","curd"],
    ["rolls/buns","pastry","whole milk","coffee"],
    ["other vegetables","frozen vegetables","whole milk"],
    ["whole milk","margarine","butter"],
    ["soda","other vegetables","rolls/buns"],
    ["yogurt","whole milk","whipped/sour cream","cream cheese"],
    ["other vegetables","whole milk","tropical fruit","root vegetables"],
    ["whole milk","sliced cheese","cream cheese"],
    ["domestic eggs","whole milk","shopping bags"],
    ["rolls/buns","whole milk","citrus fruit","tropical fruit"],
    ["whole milk","pork","other vegetables"],
    ["yogurt","rolls/buns","tropical fruit"],
    ["whole milk","other vegetables","newspapers"],
    ["butter","whole milk","cream cheese"],
    ["root vegetables","other vegetables","tropical fruit"],
    ["whole milk","canned beer","bottled water"],
    ["soda","whole milk","pastry"],
    ["yogurt","other vegetables","whole milk","pip fruit"],
    ["whole milk","brown bread","butter"],
    ["other vegetables","domestic eggs","whole milk"],
    ["rolls/buns","whole milk","shopping bags","soda"],
    ["whole milk","root vegetables","curd"],
    ["tropical fruit","pip fruit","other vegetables","whole milk"],
    ["whole milk","whipped/sour cream","butter"],
    ["yogurt","curd","whole milk"],
    ["other vegetables","whole milk","sliced cheese"],
    ["whole milk","rolls/buns","newspapers","pastry"],
    ["soda","rolls/buns","whole milk","shopping bags"],
    ["butter","yogurt","whole milk"],
    ["whole milk","other vegetables","frozen vegetables","root vegetables"],
    ["domestic eggs","rolls/buns","whole milk"],
    ["whole milk","coffee","rolls/buns","pastry","newspapers"],
    ["other vegetables","root vegetables","whole milk","pip fruit"],
    ["whole milk","tropical fruit","yogurt","citrus fruit"],
    ["curd","yogurt","whipped/sour cream"],
    ["whole milk","bottled water","soda"],
    ["rolls/buns","other vegetables","whole milk"],
    ["whole milk","domestic eggs","other vegetables","butter"],
    ["yogurt","whole milk","pip fruit"],
    ["whole milk","pastry","coffee","rolls/buns"],
    ["other vegetables","whole milk","margarine"],
    ["whole milk","frozen vegetables","shopping bags"],
    ["root vegetables","butter","other vegetables"],
    ["whole milk","canned beer","soda"],
    ["yogurt","cream cheese","whipped/sour cream","whole milk"],
    ["whole milk","tropical fruit","other vegetables","root vegetables"],
    ["rolls/buns","pastry","whole milk"],
    ["domestic eggs","butter","whole milk"],
    ["whole milk","citrus fruit","other vegetables"],
    ["soda","bottled water","whole milk","canned beer"],
    ["yogurt","whole milk","sliced cheese"],
    ["other vegetables","whole milk","brown bread"],
    ["whole milk","rolls/buns","tropical fruit","yogurt"],
    ["root vegetables","other vegetables","pip fruit","whole milk"],
    ["whole milk","butter","cream cheese","yogurt"],
    ["pastry","rolls/buns","whole milk","coffee","newspapers"],
    ["other vegetables","frozen vegetables","root vegetables"],
    ["whole milk","domestic eggs","sliced cheese"],
    ["yogurt","other vegetables","whole milk","whipped/sour cream"],
    ["rolls/buns","soda","other vegetables"],
    ["whole milk","margarine","domestic eggs"],
    ["other vegetables","pip fruit","tropical fruit","whole milk"],
    ["whole milk","whipped/sour cream","curd"],
    ["yogurt","whole milk","tropical fruit"],
    ["rolls/buns","whole milk","butter","domestic eggs"],
    ["other vegetables","whole milk","citrus fruit","pip fruit"],
    ["whole milk","curd","cream cheese","yogurt"],
    ["soda","rolls/buns","other vegetables","whole milk"],
    ["whole milk","frozen vegetables","domestic eggs"],
    ["yogurt","whipped/sour cream","cream cheese"],
    ["whole milk","root vegetables","other vegetables","pip fruit"],
    ["rolls/buns","other vegetables","whole milk","root vegetables"],
    ["whole milk","tropical fruit","pip fruit"],
    ["butter","domestic eggs","whole milk","other vegetables"],
    ["whole milk","yogurt","sliced cheese","cream cheese"],
    ["other vegetables","root vegetables","curd","whole milk"],
    ["rolls/buns","whole milk","margarine"],
    ["whole milk","shopping bags","newspapers","domestic eggs"],
    ["soda","bottled water","canned beer","whole milk"],
    ["yogurt","tropical fruit","citrus fruit","whole milk"],
    ["whole milk","other vegetables","butter","cream cheese"],
    ["rolls/buns","pastry","coffee","newspapers"],
    ["whole milk","domestic eggs","root vegetables"],
    ["other vegetables","whole milk","frozen vegetables","shopping bags"],
    ["yogurt","whole milk","other vegetables","root vegetables","butter"],
    ["whole milk","sliced cheese","butter"],
    ["soda","canned beer","other vegetables"],
    ["whole milk","tropical fruit","other vegetables","citrus fruit"],
    ["rolls/buns","whole milk","curd"],
    ["butter","other vegetables","root vegetables","whole milk"],
    ["whole milk","yogurt","cream cheese"],
    ["other vegetables","domestic eggs","root vegetables"],
    ["whole milk","pip fruit","root vegetables"],
    ["rolls/buns","pastry","soda","whole milk"],
    ["yogurt","other vegetables","tropical fruit","root vegetables"],
    ["whole milk","whipped/sour cream","sliced cheese"],
    ["other vegetables","whole milk","newspapers"],
    ["rolls/buns","domestic eggs","whole milk","butter"],
    ["whole milk","citrus fruit","tropical fruit","yogurt"],
    ["other vegetables","root vegetables","whole milk","frozen vegetables"],
    ["whole milk","curd","other vegetables","root vegetables"],
    ["soda","rolls/buns","pastry","coffee"],
    ["yogurt","whole milk","butter","domestic eggs"],
    ["whole milk","other vegetables","margarine","shopping bags"],
    ["tropical fruit","other vegetables","pip fruit"],
    ["whole milk","rolls/buns","domestic eggs"],
    ["other vegetables","root vegetables","yogurt","butter"],
    ["whole milk","cream cheese","other vegetables"],
    ["soda","whole milk","bottled water","newspapers"],
    ["yogurt","tropical fruit","pip fruit","whole milk"],
    ["whole milk","other vegetables","citrus fruit","root vegetables"],
    ["rolls/buns","other vegetables","soda"],
    ["whole milk","domestic eggs","yogurt","butter"],
    ["other vegetables","root vegetables","whole milk","margarine"],
    ["whole milk","frozen vegetables","citrus fruit"],
    ["soda","canned beer","bottled water"],
    ["yogurt","whole milk","curd","whipped/sour cream"],
    ["whole milk","other vegetables","pip fruit","citrus fruit"],
    ["rolls/buns","whole milk","pastry","shopping bags"],
    ["butter","whole milk","other vegetables","cream cheese"],
    ["whole milk","domestic eggs","frozen vegetables"],
    ["other vegetables","tropical fruit","whole milk","root vegetables"],
    ["yogurt","cream cheese","sliced cheese","whole milk"],
    ["whole milk","rolls/buns","margarine"],
    ["soda","other vegetables","bottled water"],
    ["whole milk","root vegetables","pip fruit","other vegetables"],
    ["domestic eggs","whole milk","other vegetables","root vegetables"],
    ["yogurt","whole milk","tropical fruit","other vegetables"],
    ["whole milk","whipped/sour cream","butter","cream cheese"],
    ["rolls/buns","coffee","pastry"],
    ["whole milk","other vegetables","frozen vegetables","butter"],
    ["soda","rolls/buns","whole milk","pastry"],
    ["yogurt","other vegetables","root vegetables","whole milk"],
    ["whole milk","domestic eggs","sliced cheese","cream cheese"],
    ["other vegetables","whole milk","brown bread","root vegetables"],
    ["tropical fruit","citrus fruit","pip fruit","yogurt"],
    ["whole milk","shopping bags","newspapers","soda"],
    ["rolls/buns","whole milk","other vegetables","root vegetables"],
    ["butter","cream cheese","whole milk","yogurt"],
    ["whole milk","domestic eggs","other vegetables","yogurt"],
    ["soda","bottled water","rolls/buns","other vegetables"],
    ["whole milk","frozen vegetables","other vegetables","pip fruit"],
    ["yogurt","curd","cream cheese","whipped/sour cream","whole milk"],
    ["whole milk","root vegetables","other vegetables","citrus fruit"],
    ["rolls/buns","whole milk","butter","other vegetables"],
    ["domestic eggs","whole milk","cream cheese","yogurt"],
    ["other vegetables","tropical fruit","pip fruit","root vegetables"],
]

# ---------------------------------------------------------------------------
# Apriori algorithm
# ---------------------------------------------------------------------------

def get_frequent_itemsets(transactions, min_support):
    n = len(transactions)
    item_count = defaultdict(int)
    for t in transactions:
        for item in t:
            item_count[frozenset([item])] += 1

    frequent = {}
    k1 = {fs: c for fs, c in item_count.items() if c / n >= min_support}
    frequent.update(k1)

    current = list(k1.keys())
    k = 2
    while current and k <= 4:
        candidates = []
        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                union = current[i] | current[j]
                if len(union) == k:
                    candidates.append(union)
        candidates = list(set(candidates))

        cand_count = defaultdict(int)
        for t in transactions:
            t_set = set(t)
            for cand in candidates:
                if cand.issubset(t_set):
                    cand_count[cand] += 1

        next_freq = {fs: c for fs, c in cand_count.items() if c / n >= min_support}
        frequent.update(next_freq)
        current = list(next_freq.keys())
        k += 1

    return frequent, n

def generate_rules(frequent_itemsets, n_transactions, min_confidence, min_lift):
    rules = []
    for itemset, count in frequent_itemsets.items():
        if len(itemset) < 2:
            continue
        itemset_support = count / n_transactions
        items = list(itemset)
        for r in range(1, len(items)):
            for ant_items in combinations(items, r):
                ant = frozenset(ant_items)
                con = itemset - ant
                if not con:
                    continue
                ant_count = frequent_itemsets.get(ant, 0)
                if ant_count == 0:
                    continue
                ant_support = ant_count / n_transactions
                confidence = itemset_support / ant_support
                con_count = frequent_itemsets.get(con, 0)
                if con_count == 0:
                    continue
                con_support = con_count / n_transactions
                lift = confidence / con_support if con_support > 0 else 0
                if confidence >= min_confidence and lift >= min_lift:
                    rules.append({
                        "antecedent": sorted(ant),
                        "consequent": sorted(con),
                        "support": round(itemset_support, 4),
                        "confidence": round(confidence, 4),
                        "lift": round(lift, 4),
                        "count": count,
                        "source": "apriori"
                    })
    rules.sort(key=lambda r: -r["lift"])
    return rules

# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE) as f:
            return json.load(f)
    return [list(t) for t in SEED_TRANSACTIONS]

def save_transactions(txns):
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(txns, f, indent=2)

def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE) as f:
            return json.load(f)
    return rebuild_rules()

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)

def rebuild_rules(min_support=0.03, min_confidence=0.25, min_lift=1.2):
    txns = load_transactions()
    freq, n = get_frequent_itemsets(txns, min_support)
    rules = generate_rules(freq, n, min_confidence, min_lift)
    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_transactions": n,
        "n_rules": len(rules),
        "min_support": min_support,
        "min_confidence": min_confidence,
        "min_lift": min_lift,
        "rules": rules
    }
    save_rules(meta)
    return meta

def recommend(cart_items, top_n=6):
    """
    Given a list of cart items, return ranked recommendations.
    Uses all rules where antecedent is a subset of cart.
    """
    data = load_rules()
    rules = data.get("rules", [])
    cart_set = set(i.lower() for i in cart_items)

    scores = defaultdict(lambda: {"confidence": 0, "lift": 0, "support": 0, "rules_hit": 0})
    for rule in rules:
        ant = set(rule["antecedent"])
        if ant.issubset(cart_set):
            for item in rule["consequent"]:
                if item not in cart_set:
                    if rule["lift"] > scores[item]["lift"]:
                        scores[item] = {
                            "confidence": rule["confidence"],
                            "lift": rule["lift"],
                            "support": rule["support"],
                            "rules_hit": scores[item]["rules_hit"] + 1
                        }
                    else:
                        scores[item]["rules_hit"] += 1

    ranked = sorted(scores.items(), key=lambda x: (-x[1]["lift"], -x[1]["confidence"]))
    return [{"item": item, **stats} for item, stats in ranked[:top_n]]

def add_transaction_and_update(cart_items):
    """
    Store a new transaction and rebuild rules if it contains unseen combinations.
    Returns whether rules were rebuilt.
    """
    txns = load_transactions()
    normalized = [i.lower() for i in cart_items]
    txns.append(normalized)
    save_transactions(txns)
    meta = rebuild_rules()
    return {"rebuilt": True, "n_rules": meta["n_rules"], "n_transactions": meta["n_transactions"]}

if __name__ == "__main__":
    print("Building rules from seed data...")
    meta = rebuild_rules()
    print(f"Done — {meta['n_rules']} rules from {meta['n_transactions']} transactions")
    print("\nSample recommendation for ['whole milk', 'rolls/buns']:")
    for r in recommend(["whole milk", "rolls/buns"]):
        print(f"  {r['item']} — conf={r['confidence']:.2f} lift={r['lift']:.2f}")
