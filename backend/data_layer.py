"""
Data layer backed by PostgreSQL only.
"""
import random
import hashlib
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from backend.db_config import get_db_connection

# Product catalogue
CATALOGUE = {
    "Home Decor": [
        "WHITE HANGING HEART T-LIGHT HOLDER", "JUMBO BAG RED RETROSPOT",
        "REGENCY CAKESTAND 3 TIER", "NATURAL SLATE HEART CHALKBOARD",
        "HEART OF WICKER SMALL", "ASSORTED COLOUR BIRD ORNAMENT",
        "SET OF 3 CAKE TINS PANTRY DESIGN", "JUMBO STORAGE BAG SUKI",
        "PACK OF 72 RETROSPOT CAKE CASES", "PAPER CHAIN KIT 50'S CHRISTMAS",
    ],
    "Bags": [
        "LUNCH BAG RED RETROSPOT", "LUNCH BAG  BLACK SKULL.",
        "JUMBO BAG PINK POLKADOT", "JUMBO SHOPPER VINTAGE RED PAISLEY",
        "SHOPPING BAG WITH TROPICAL FLOWERS", "LUNCH BAG CARS BLUE",
    ],
    "Party": [
        "PARTY BUNTING", "PAPER BUNTING", "ASSORTED DESIGNS BUNTING",
        "PARTY BLOWERS", "PAPER CHAIN KIT VINTAGE CHRISTMAS",
    ],
    "Stationery": [
        "PACK OF 12 LONDON TISSUES", "SET OF 4 PANTRY JELLY MOULDS",
        "PACK OF 6 SKULL PAPER CUPS", "VINTAGE SEASIDE JIGSAW PUZZLES",
        "RED RETROSPOT MINI CASES SET OF 3",
    ],
    "Kitchen": [
        "PACK OF 72 RETROSPOT CAKE CASES", "PACK OF 60 MUSHROOM CAKE CASES",
        "CERAMIC STORAGE JAR WITH LID", "WOODEN PICTURE FRAME WHITE FINISH",
        "SET OF 3 WICKER OVAL BASKETS",
    ],
    "Gifts": [
        "MINI PAINT SET VINTAGE", "VINTAGE UNION JACK MEMOBOARD",
        "PACK OF 6 BIRDY GIFT TAGS", "VINTAGE DOILY GIFT BAG",
        "SET OF 4 KNICK KNACK TINS LONDON",
    ],
    "Seasonal": [
        "CHRISTMAS TREE HEART DECORATION", "SMALL CERAMIC TOP STORAGE JAR",
        "PAPER CHAIN KIT RETRO SPOT", "FELTCRAFT CUSHION OWL",
        "HAND WARMER UNION JACK",
    ],
    "Candles": [
        "HAND WARMER RED RETROSPOT", "SCENTED CANDLE JAR PINK GROVE",
        "TEA LIGHT CANDLES", "GLASS STAR FROSTED T-LIGHT HOLDER",
        "IVORY KNITTED MUG COSY",
    ],
}

ALL_ITEMS = [item for items in CATALOGUE.values() for item in items]
CAT_MAP = {item: cat for cat, items in CATALOGUE.items() for item in items}

PATTERNS = [
    ["WHITE HANGING HEART T-LIGHT HOLDER", "JUMBO BAG RED RETROSPOT", "REGENCY CAKESTAND 3 TIER"],
    ["LUNCH BAG RED RETROSPOT", "PARTY BUNTING", "ASSORTED COLOUR BIRD ORNAMENT"],
    ["JUMBO BAG RED RETROSPOT", "LUNCH BAG RED RETROSPOT", "JUMBO STORAGE BAG SUKI"],
    ["SET OF 3 CAKE TINS PANTRY DESIGN", "PACK OF 72 RETROSPOT CAKE CASES", "REGENCY CAKESTAND 3 TIER"],
    ["PARTY BUNTING", "PAPER BUNTING", "ASSORTED DESIGNS BUNTING", "PARTY BLOWERS"],
    ["NATURAL SLATE HEART CHALKBOARD", "HEART OF WICKER SMALL", "WHITE HANGING HEART T-LIGHT HOLDER"],
    ["JUMBO SHOPPER VINTAGE RED PAISLEY", "LUNCH BAG RED RETROSPOT", "LUNCH BAG  BLACK SKULL."],
    ["PAPER CHAIN KIT 50'S CHRISTMAS", "PARTY BUNTING", "PACK OF 72 RETROSPOT CAKE CASES"],
    ["REGENCY CAKESTAND 3 TIER", "SET OF 4 PANTRY JELLY MOULDS", "PACK OF 72 RETROSPOT CAKE CASES"],
    ["HAND WARMER RED RETROSPOT", "SCENTED CANDLE JAR PINK GROVE", "TEA LIGHT CANDLES"],
]

random.seed(42)
PRICE_MAP = {item: round(random.uniform(1.5, 15.0), 2) for item in ALL_ITEMS}


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _sqlite_db_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "grocery.db")


def _ensure_sqlite_tables(conn):
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account_status TEXT NOT NULL DEFAULT 'Active',
            last_login TIMESTAMP,
            login_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS purchase_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            BillNo TEXT NOT NULL,
            ItemCount INTEGER NOT NULL,
            TotalAmount REAL NOT NULL,
            PurchasedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _ensure_user_activity_columns(conn):
    c = conn.cursor()
    try:
        c.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS account_status TEXT NOT NULL DEFAULT 'Active'
        """)
        c.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS last_login TIMESTAMP
        """)
        c.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS login_count INTEGER NOT NULL DEFAULT 0
        """)
    except Exception:
        conn.rollback()
        c = conn.cursor()
        c.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
        )
        existing = {row[0] for row in c.fetchall()}
        if "account_status" not in existing:
            c.execute("ALTER TABLE users ADD COLUMN account_status TEXT NOT NULL DEFAULT 'Active'")
        if "last_login" not in existing:
            c.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        if "login_count" not in existing:
            c.execute("ALTER TABLE users ADD COLUMN login_count INTEGER NOT NULL DEFAULT 0")
    conn.commit()


def _ensure_sqlite_user_activity_columns(conn):
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in c.fetchall()}
    if "account_status" not in existing:
        c.execute("ALTER TABLE users ADD COLUMN account_status TEXT NOT NULL DEFAULT 'Active'")
    if "last_login" not in existing:
        c.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
    if "login_count" not in existing:
        c.execute("ALTER TABLE users ADD COLUMN login_count INTEGER NOT NULL DEFAULT 0")
    conn.commit()


def _mirror_user_to_sqlite(username, password_hash, role):
    try:
        path = _sqlite_db_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path)
        _ensure_sqlite_tables(conn)
        _ensure_sqlite_user_activity_columns(conn)
        c = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            """
            INSERT INTO users (username, password_hash, role, created_at, account_status, last_login, login_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash=excluded.password_hash,
                role=excluded.role
            """,
            (username, password_hash, role, created_at, "Active", None, 0),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _mirror_purchase_to_sqlite(username, bill_no, item_count, total_amount, purchased_at):
    try:
        path = _sqlite_db_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path)
        _ensure_sqlite_tables(conn)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO purchase_history (username, BillNo, ItemCount, TotalAmount, PurchasedAt)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, bill_no, int(item_count), float(total_amount), str(purchased_at)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _sync_users_to_sqlite(conn):
    try:
        c = conn.cursor()
        c.execute("SELECT username, password_hash, role FROM users")
        for username, password_hash, role in c.fetchall():
            _mirror_user_to_sqlite(username, password_hash, role)
    except Exception:
        pass


TRANSACTION_COLUMNS = ["id", "BillNo", "Itemname", "Quantity", "Price", "Date", "Country", "Category", "Revenue"]
TRANSACTION_COLUMN_ALIASES = {
    "billno": "BillNo",
    "itemname": "Itemname",
    "quantity": "Quantity",
    "price": "Price",
    "date": "Date",
    "country": "Country",
    "category": "Category",
}


def _empty_transactions_df():
    return pd.DataFrame(columns=TRANSACTION_COLUMNS)


def _normalize_transactions_df(df):
    if df is None or df.empty:
        return _empty_transactions_df()

    df = df.rename(columns={c: TRANSACTION_COLUMN_ALIASES.get(c, c) for c in df.columns})

    for column in TRANSACTION_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)
    df["Revenue"] = df["Quantity"] * df["Price"]
    return df


def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            BillNo TEXT,
            Itemname TEXT,
            Quantity INTEGER,
            Price NUMERIC(10,2),
            Date TIMESTAMP,
            Country TEXT,
            Category TEXT
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','user')),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS purchase_history (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            BillNo TEXT NOT NULL,
            ItemCount INTEGER NOT NULL,
            TotalAmount NUMERIC(12,2) NOT NULL,
            PurchasedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            price NUMERIC(10,2) NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            sku TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    _ensure_user_activity_columns(conn)

    c.execute("SELECT COUNT(*) FROM transactions")
    tx_count = c.fetchone()[0]
    if tx_count == 0:
        _seed(conn)

    _ensure_default_accounts(conn)
    _sync_users_to_sqlite(conn)
    conn.close()


def _ensure_default_accounts(conn):
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO users (username, password_hash, role, account_status, last_login, login_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        """,
        ("admin", _hash_password("admin123"), "admin", "Active", None, 0),
    )
    c.execute(
        """
        INSERT INTO users (username, password_hash, role, account_status, last_login, login_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        """,
        ("user", _hash_password("password"), "user", "Active", None, 0),
    )
    conn.commit()


def _seed(conn):
    c = conn.cursor()
    base = datetime(2010, 12, 1)
    rows = []

    for i in range(5000):
        bill = f"5{i:05d}"
        date = base + timedelta(
            days=random.randint(0, 364),
            hours=random.randint(8, 21),
            minutes=random.randint(0, 59),
        )
        country = random.choices(
            ["United Kingdom", "Germany", "France", "Netherlands", "Australia"],
            weights=[85, 5, 4, 3, 3],
        )[0]
        pattern = random.choice(PATTERNS)
        extras = random.sample(ALL_ITEMS, k=random.randint(0, 4))
        basket = list(set(pattern[: random.randint(2, len(pattern))] + extras))

        for item in basket:
            rows.append(
                (
                    bill,
                    item,
                    random.randint(1, 12),
                    float(PRICE_MAP[item]),
                    date,
                    country,
                    CAT_MAP[item],
                )
            )

    c.executemany(
        """
        INSERT INTO transactions (BillNo, Itemname, Quantity, Price, Date, Country, Category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    conn.commit()


def get_df():
    """Get all transactions globally (no country filtering)"""
    conn = get_db_connection()
    q = "SELECT BillNo, Itemname, Quantity, Price, Date, Country, Category FROM transactions"
    df = pd.read_sql(q, conn)
    conn.close()
    return _normalize_transactions_df(df)


def get_monthly_revenue(df):
    tmp = df.copy()
    tmp["Month"] = tmp["Date"].dt.to_period("M").astype(str)
    return tmp.groupby("Month")["Revenue"].sum().reset_index()


def get_hourly_orders(df):
    tmp = df.copy()
    tmp["Hour"] = tmp["Date"].dt.hour
    return tmp.groupby("Hour")["BillNo"].nunique().reset_index(name="Orders")


def get_basket_sizes(df):
    return df.groupby("BillNo")["Itemname"].nunique().reset_index(name="basket_size")


def get_top_products(df, n=15):
    return df.groupby("Itemname")["Revenue"].sum().nlargest(n).reset_index()


def get_category_revenue(df):
    return df.groupby("Category")["Revenue"].sum().sort_values(ascending=False).reset_index()


def build_transactions(df):
    baskets = df[df["Quantity"] > 0].groupby("BillNo")["Itemname"].apply(set)
    baskets = baskets[baskets.apply(lambda x: 2 <= len(x) <= 100)]
    return [list(b) for b in baskets]


def insert_rt_transaction(items):
    price_map = get_product_prices()
    category_map = get_product_categories()
    conn = get_db_connection()
    c = conn.cursor()
    bill = f"RT{int(datetime.now().timestamp())}"
    ts = datetime.now()

    # Choose a country for this real-time bill. If an imported dataset exists
    # use one of the countries present there; otherwise fall back to United Kingdom.
    try:
        c.execute("SELECT DISTINCT Country FROM transactions WHERE Country IS NOT NULL")
        countries = [row[0] for row in c.fetchall() if row[0]]
    except Exception:
        countries = []

    if countries:
        country_for_bill = random.choice(countries)
    else:
        country_for_bill = "United Kingdom"

    rows = [
        (
            bill,
            item,
            random.randint(1, 6),
            float(price_map.get(item, PRICE_MAP.get(item, 5.0))),
            ts,
            country_for_bill,
            category_map.get(item, CAT_MAP.get(item, "Other")),
        )
        for item in items
    ]

    c.executemany(
        """
        INSERT INTO transactions (BillNo, Itemname, Quantity, Price, Date, Country, Category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    conn.commit()
    conn.close()
    return bill


def get_all_df():
    # Keep behavior aligned with get_df() while avoiding duplicate query paths.
    return get_df()


def create_user(username, password, role="user"):
    username = (username or "").strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."
    if role not in {"admin", "user"}:
        return False, "Invalid role."

    conn = get_db_connection()
    c = conn.cursor()
    try:
        password_hash = _hash_password(password)
        c.execute(
            "INSERT INTO users (username, password_hash, role, account_status, last_login, login_count) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, password_hash, role, "Active", None, 0),
        )
        conn.commit()
        _mirror_user_to_sqlite(username, password_hash, role)
        return True, "User created successfully."
    except Exception as e:
        conn.rollback()
        if getattr(e, "pgcode", None) == "23505":
            return False, "Username already exists."
        return False, "Failed to create user."
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    _ensure_user_activity_columns(conn)
    c.execute(
        "SELECT username, role, account_status, login_count FROM users WHERE username = %s AND password_hash = %s",
        ((username or "").strip(), _hash_password(password or "")),
    )
    row = c.fetchone()

    if row and str(row[2]).lower() != "active":
        conn.close()
        return None

    if row:
        now = datetime.now()
        next_login_count = int(row[3] or 0) + 1
        c.execute(
            "UPDATE users SET last_login = %s, login_count = %s WHERE username = %s",
            (now, next_login_count, row[0]),
        )
        conn.commit()
        conn.close()
        return {"username": row[0], "role": row[1], "account_status": row[2], "login_count": next_login_count, "last_login": now}

    conn.close()

    if not row:
        return None


def set_user_status(username, account_status):
    account_status = (account_status or "").strip().title()
    if account_status not in {"Active", "Inactive"}:
        return False, "Invalid account status."

    conn = get_db_connection()
    c = conn.cursor()
    try:
        _ensure_user_activity_columns(conn)
        c.execute(
            "UPDATE users SET account_status = %s WHERE username = %s",
            (account_status, (username or "").strip()),
        )
        conn.commit()

        path = _sqlite_db_path()
        if os.path.exists(path):
            sqlite_conn = sqlite3.connect(path)
            _ensure_sqlite_tables(sqlite_conn)
            _ensure_sqlite_user_activity_columns(sqlite_conn)
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(
                "UPDATE users SET account_status = ? WHERE username = ?",
                (account_status, (username or "").strip()),
            )
            sqlite_conn.commit()
            sqlite_conn.close()

        return True, f"User marked as {account_status.lower()}."
    except Exception:
        conn.rollback()
        return False, "Failed to update user status."
    finally:
        conn.close()


def get_users_df():
    conn = get_db_connection()
    _ensure_user_activity_columns(conn)
    df = pd.read_sql(
        "SELECT username, role, created_at, COALESCE(account_status, 'Active') AS account_status, last_login, COALESCE(login_count, 0) AS login_count FROM users ORDER BY created_at DESC",
        conn,
    )
    conn.close()
    return df


def record_user_purchase(username, item_quantities):
    """Record user purchase - country is auto-set to default"""
    price_map = get_product_prices()
    category_map = get_product_categories()
    country = "Global"  # Default - works anywhere
    cleaned = {k: int(v) for k, v in (item_quantities or {}).items() if int(v) > 0}
    if not cleaned:
        return None

    conn = get_db_connection()
    c = conn.cursor()
    bill = f"USR{int(datetime.now().timestamp())}{random.randint(100, 999)}"
    ts = datetime.now()

    rows = []
    total_amount = 0.0
    total_items = 0
    for item, qty in cleaned.items():
        price = float(price_map.get(item, PRICE_MAP.get(item, 5.0)))
        total_amount += price * qty
        total_items += qty
        rows.append((bill, item, qty, price, ts, country, category_map.get(item, CAT_MAP.get(item, "Other"))))

    c.executemany(
        """
        INSERT INTO transactions (BillNo, Itemname, Quantity, Price, Date, Country, Category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        rows,
    )
    c.execute(
        """
        INSERT INTO purchase_history (username, BillNo, ItemCount, TotalAmount, PurchasedAt)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (username, bill, total_items, round(total_amount, 2), ts),
    )

    conn.commit()
    conn.close()
    _mirror_purchase_to_sqlite(username, bill, total_items, round(total_amount, 2), ts)
    return bill


def get_user_purchases_df(username):
    conn = get_db_connection()
    df = pd.read_sql(
        """
        SELECT BillNo, ItemCount, TotalAmount, PurchasedAt
        FROM purchase_history
        WHERE username = %s
        ORDER BY PurchasedAt DESC
        """,
        conn,
        params=((username or "").strip(),),
    )
    conn.close()
    if df is None or df.empty:
        return pd.DataFrame(columns=["BillNo", "ItemCount", "TotalAmount", "PurchasedAt"])

    df = df.rename(columns={
        "billno": "BillNo",
        "itemcount": "ItemCount",
        "totalamount": "TotalAmount",
        "purchasedat": "PurchasedAt",
    })

    for column in ["BillNo", "ItemCount", "TotalAmount", "PurchasedAt"]:
        if column not in df.columns:
            df[column] = pd.NA

    df["ItemCount"] = pd.to_numeric(df["ItemCount"], errors="coerce").fillna(0)
    df["TotalAmount"] = pd.to_numeric(df["TotalAmount"], errors="coerce").fillna(0)
    df["PurchasedAt"] = pd.to_datetime(df["PurchasedAt"], errors="coerce")
    return df


def add_product(name, category, price, stock=0, description="", sku=""):
    """Add a new product to the database"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO products (name, category, price, stock, description, sku)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name.strip(), category, float(price), int(stock), description, sku or f"SKU{int(datetime.now().timestamp())}"),
        )
        conn.commit()
        conn.close()
        return True, f"Product '{name}' added successfully!"
    except Exception as e:
        conn.close()
        return False, f"Error: {str(e)}"


def get_products_df():
    """Get all products from database"""
    conn = get_db_connection()
    df = pd.read_sql("SELECT name, category, price, stock, description, sku FROM products ORDER BY name", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["name", "category", "price", "stock", "description", "sku"])
    return df


def get_product_prices():
    """Get product prices as dictionary"""
    df = get_products_df()
    if df.empty:
        return PRICE_MAP  # Fallback to default
    return dict(zip(df['name'], df['price']))


def get_product_categories():
    """Get product categories mapping"""
    df = get_products_df()
    if df.empty:
        return CAT_MAP  # Fallback to default
    return dict(zip(df['name'], df['category']))


def get_all_product_names():
    """Get list of all product names"""
    df = get_products_df()
    if df.empty:
        return ALL_ITEMS  # Fallback to default
    return sorted(df['name'].tolist())


def _infer_category_from_description(description):
    text = (description or "").upper()
    if not text:
        return "Other"

    keyword_map = {
        "Home Decor": ["HEART", "LANTERN", "HOLDER", "WICKER", "FRAME", "DECOR", "CHALKBOARD"],
        "Bags": ["BAG", "SHOPPER", "LUNCH BAG", "TOTE"],
        "Party": ["PARTY", "BUNTING", "BALLOON", "CONFETTI", "CELEBRATION"],
        "Stationery": ["PAPER", "CARD", "PEN", "NOTE", "JOURNAL", "TISSUES", "TAGS"],
        "Kitchen": ["CAKE", "MUG", "JAR", "TIN", "KITCHEN", "CUP", "BOWL"],
        "Gifts": ["GIFT", "PRESENT", "MEMOBOARD", "PUZZLE", "SET OF"],
        "Seasonal": ["CHRISTMAS", "EASTER", "HALLOWEEN", "XMAS", "SEASON"],
        "Candles": ["CANDLE", "TEA LIGHT", "SCENTED", "WARMER"],
    }

    for category, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def get_dataset_import_overview():
    """Return current DB overview for admin import panel."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM transactions")
    txn_count = int(c.fetchone()[0])
    c.execute("SELECT COUNT(DISTINCT BillNo) FROM transactions")
    invoice_count = int(c.fetchone()[0])
    c.execute("SELECT COUNT(*) FROM products")
    product_count = int(c.fetchone()[0])
    conn.close()
    return {
        "transactions": txn_count,
        "invoices": invoice_count,
        "products": product_count,
    }


def import_online_retail_dataset(file_path, replace_existing=False):
    """Import Online Retail Excel data into transactions and products tables."""
    if not file_path or not os.path.exists(file_path):
        return {
            "ok": False,
            "message": f"Dataset file not found: {file_path}",
            "inserted_transactions": 0,
            "added_products": 0,
            "loaded_rows": 0,
        }

    try:
        raw_df = pd.read_excel(file_path)
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Failed to read Excel: {exc}",
            "inserted_transactions": 0,
            "added_products": 0,
            "loaded_rows": 0,
        }

    required = ["InvoiceNo", "Description", "Quantity", "InvoiceDate", "UnitPrice", "Country"]
    missing = [col for col in required if col not in raw_df.columns]
    if missing:
        return {
            "ok": False,
            "message": f"Missing required columns: {', '.join(missing)}",
            "inserted_transactions": 0,
            "added_products": 0,
            "loaded_rows": 0,
        }

    df = raw_df[required].copy()
    df["Description"] = df["Description"].astype(str).str.strip().str.upper()
    df["Country"] = df["Country"].astype(str).str.strip()
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    df = df.dropna(subset=["InvoiceNo", "Description", "InvoiceDate", "Quantity", "UnitPrice"])
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    df = df[df["Description"] != ""]
    if df.empty:
        return {
            "ok": False,
            "message": "No valid transactional rows found after cleaning.",
            "inserted_transactions": 0,
            "added_products": 0,
            "loaded_rows": 0,
        }

    df["Category"] = df["Description"].apply(_infer_category_from_description)

    conn = get_db_connection()
    c = conn.cursor()
    inserted_transactions = 0
    added_products = 0

    try:
        if replace_existing:
            c.execute("TRUNCATE TABLE transactions RESTART IDENTITY")

        transaction_rows = [
            (
                row.InvoiceNo,
                row.Description,
                int(row.Quantity),
                round(float(row.UnitPrice), 2),
                row.InvoiceDate.to_pydatetime() if hasattr(row.InvoiceDate, "to_pydatetime") else row.InvoiceDate,
                row.Country,
                row.Category,
            )
            for row in df.itertuples(index=False)
        ]

        chunk_size = 10000
        for i in range(0, len(transaction_rows), chunk_size):
            chunk = transaction_rows[i:i + chunk_size]
            c.executemany(
                """
                INSERT INTO transactions (BillNo, Itemname, Quantity, Price, Date, Country, Category)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                chunk,
            )
            inserted_transactions += len(chunk)

        product_df = (
            df.groupby(["Description", "Category"], as_index=False)
            .agg(avg_price=("UnitPrice", "mean"), total_qty=("Quantity", "sum"))
        )

        for row in product_df.itertuples(index=False):
            c.execute(
                """
                INSERT INTO products (name, category, price, stock, description, sku)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                """,
                (
                    row.Description,
                    row.Category,
                    round(float(row.avg_price), 2),
                    max(int(row.total_qty), 0),
                    "Imported from Online Retail dataset",
                    f"OR{abs(hash(row.Description)) % 100000000}",
                ),
            )
            if c.rowcount == 1:
                added_products += 1

        conn.commit()
        return {
            "ok": True,
            "message": "Dataset imported successfully.",
            "inserted_transactions": inserted_transactions,
            "added_products": added_products,
            "loaded_rows": len(df),
        }
    except Exception as exc:
        conn.rollback()
        return {
            "ok": False,
            "message": f"Import failed: {exc}",
            "inserted_transactions": 0,
            "added_products": 0,
            "loaded_rows": 0,
        }
    finally:
        conn.close()

