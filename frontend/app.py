"""
IntelliGrocery Analytics — Full MBA Platform
Integrates every section of the MBA_ECommerce_Apriori notebook as interactive Streamlit pages.
"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter, defaultdict

from backend.data_layer  import (init_db, get_df, get_all_df, get_monthly_revenue,
                                  get_hourly_orders, get_basket_sizes, get_top_products,
                                  get_category_revenue, build_transactions,
                                  insert_rt_transaction, ALL_ITEMS, PATTERNS, PRICE_MAP, CAT_MAP,
                                  create_user, authenticate_user, get_users_df,
                                  record_user_purchase, get_user_purchases_df)
from backend.apriori_engine import AprioriEngine
from backend.data_layer import add_product, get_products_df, get_product_prices, get_product_categories, get_all_product_names

from frontend.pages_user import (render_profile_page, render_shop_page, 
                                 render_recommendations_page, render_wishlist_page, 
                                 render_settings_page)
from frontend.pages_admin import (render_admin_dashboard, render_user_management, 
                                  render_analytics_page, render_product_management,
                                  render_system_settings)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="IntelliGrocery MBA", page_icon="🛒",
                   layout="wide", initial_sidebar_state="expanded")

# ── COLOUR PALETTE (notebook-matching) ────────────────────────────────────────
BLUE   = "#2D5BE3"
GREEN  = "#1A7A4A"
ORANGE = "#E35D2D"
PURPLE = "#9A3DD4"
AMBER  = "#C0831A"
TEAL   = "#2D9DC0"
PALETTE = [BLUE, GREEN, ORANGE, PURPLE, AMBER, TEAL]

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f172a 0%,#1e293b 100%);}
[data-testid="stSidebar"] *{color:#e2e8f0 !important;}
[data-testid="stSidebar"] hr{border-color:#334155;}

.kpi{background:#fff;border-radius:14px;padding:1.1rem 1.4rem;
     box-shadow:0 1px 4px rgba(0,0,0,.08);border-left:4px solid;}
.kpi.blue  {border-color:#2D5BE3}
.kpi.green {border-color:#1A7A4A}
.kpi.orange{border-color:#E35D2D}
.kpi.purple{border-color:#9A3DD4}
.kpi.amber {border-color:#C0831A}
.kpi.teal  {border-color:#2D9DC0}
.kpi-label{font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.6px}
.kpi-value{font-size:26px;font-weight:700;color:#0f172a;margin:3px 0}
.kpi-sub  {font-size:11px;color:#94a3b8}

.section-hdr{font-size:17px;font-weight:600;color:#1e293b;
             border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin:1.4rem 0 .9rem}

.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600}
.high  {background:#dcfce7;color:#166534}
.med   {background:#fef9c3;color:#854d0e}
.low   {background:#fee2e2;color:#991b1b}

.rec-card{background:linear-gradient(135deg,#1e3a5f,#2d5be3);
          border-radius:10px;padding:10px 14px;color:#fff;margin-bottom:7px;font-size:13px}
.rec-card b{font-size:14px}

.rt-log{background:#0f172a;border-radius:10px;padding:1rem;
        font-family:monospace;font-size:12px;color:#4ade80;
        max-height:280px;overflow-y:auto;line-height:1.8}

.opt-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
          padding:12px 16px;margin-bottom:8px}
.opt-title{font-weight:600;font-size:14px;color:#1e293b}
.opt-desc {font-size:12px;color:#64748b;margin-top:3px}
.opt-badge{float:right;font-size:11px;font-weight:600;
           background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:8px}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INIT DB
# ══════════════════════════════════════════════════════════════════════════════
try:
    init_db()
except Exception as db_err:
    st.error("PostgreSQL connection failed. Update DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME in your environment.")
    st.code(str(db_err))
    st.stop()

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "user_page" not in st.session_state:
    st.session_state.user_page = "🛒 Shop"

auth_user = st.session_state.get("auth_user")

if auth_user is None:
    st.markdown("## 🔐 Welcome to IntelliGrocery")
    st.caption("Customers can create accounts and sign in. Admin portal is restricted to admin accounts only.")

    tab_user_login, tab_user_signup, tab_admin = st.tabs(["👤 User Login", "📝 User Sign Up", "🛡️ Admin Login"])

    with tab_user_login:
        with st.form("user_login_form"):
            user_name = st.text_input("User Username")
            user_pass = st.text_input("User Password", type="password")
            do_user_login = st.form_submit_button("Login as User", width="stretch")
        if do_user_login:
            auth = authenticate_user(user_name, user_pass)
            if auth and auth["role"] == "user":
                st.session_state.auth_user = auth
                st.session_state.user_page = "🛒 Shop"
                st.success(f"Welcome {auth['username']}.")
                st.rerun()
            elif auth:
                st.error("This account is not a user account. Use Admin Login.")
            else:
                st.error("Invalid user credentials.")

    with tab_user_signup:
        with st.form("user_signup_form"):
            signup_username = st.text_input("Choose Username", placeholder="e.g., john_doe")
            signup_password = st.text_input("Choose Password", type="password")
            signup_confirm = st.text_input("Confirm Password", type="password")
            do_user_signup = st.form_submit_button("Create User Account", width="stretch")

        if do_user_signup:
            if len((signup_username or "").strip()) < 3:
                st.error("Username must be at least 3 characters.")
            elif len(signup_password or "") < 6:
                st.error("Password must be at least 6 characters.")
            elif signup_password != signup_confirm:
                st.error("Password and confirm password do not match.")
            else:
                ok, msg = create_user(signup_username, signup_password, "user")
                if ok:
                    st.success("Account created successfully. Please login from User Login tab.")
                else:
                    st.error(msg)

    with tab_admin:
        with st.form("admin_login_form"):
            admin_name = st.text_input("Admin Username")
            admin_pass = st.text_input("Admin Password", type="password")
            do_admin_login = st.form_submit_button("Login as Admin", width="stretch")
        if do_admin_login:
            auth = authenticate_user(admin_name, admin_pass)
            if auth and auth["role"] == "admin":
                st.session_state.auth_user = auth
                st.success(f"Welcome admin {auth['username']}.")
                st.rerun()
            elif auth:
                st.error("This account is not an admin account. Use User Login.")
            else:
                st.error("Invalid admin credentials.")

    st.stop()
    raise SystemExit(0)

current_user = auth_user["username"]
is_admin = auth_user["role"] == "admin"

admin_only_pages = {
    "📊 Dashboard",
    "📈 Analytics",
    "👥 User Mgmt",
    "📦 Products",
    "🔬 Algorithms",
    "📊 Exploratory Analysis",
    "🔢 Transaction Encoding",
    "⚙️ Apriori Mining",
    "🔄 Incremental Learning",
    "⚡ Real-Time Simulation",
    "🏆 Optimization Summary",
}

admin_algorithm_pages = [
    "📊 Exploratory Analysis",
    "🔢 Transaction Encoding",
    "⚙️ Apriori Mining",
    "🔄 Incremental Learning",
    "⚡ Real-Time Simulation",
    "🏆 Optimization Summary",
]

removed_admin_algorithm_pages = {
    "📐 Rules Analysis",
    "🎯 Recommendation Engine",
    "🔬 Sensitivity Analysis",
}

user_nav_pages = [
    "🛒 Shop",
    "👤 My Profile",
    "🧺 My Cart",
    "📜 My Orders",
    "⚙️ Settings",
]

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🛒 IntelliGrocery")
    st.markdown(f"**Signed in as:** {current_user}")
    st.markdown(f"**Role:** {'🛡️ Admin' if is_admin else '👤 User'}")
    st.markdown("---")

    if is_admin:
        section = st.radio("Section", [
            "📊 Dashboard",
            "📈 Analytics",
            "👥 User Mgmt",
            "📦 Products",
            "⚙️ Settings",
            "🔬 Algorithms"
        ], label_visibility="collapsed")
        
        st.markdown("---")
        
        if section == "🔬 Algorithms":
            page = st.radio("Algorithm Pages", admin_algorithm_pages, label_visibility="collapsed")
        else:
            page = section

        st.markdown("---")
        st.markdown("**⚙️ Apriori Parameters**")
        min_sup  = st.slider("Min Support",    0.005, 0.10, 0.02,  0.005, format="%.3f")
        min_conf = st.slider("Min Confidence", 0.05,  0.90, 0.15,  0.05,  format="%.2f")
        min_lift = st.slider("Min Lift",       1.0,   6.0,  1.5,   0.1,   format="%.1f")
        max_len  = st.slider("Max Itemset Len",2,     5,    4,     1)

        st.markdown("---")
        if st.button("🔄 Refresh", width="stretch"):
            st.cache_data.clear()
            st.rerun()

        if st.button("🚪 Logout", width="stretch"):
            st.session_state.auth_user = None
            st.session_state.cart = {}
            st.session_state.user_page = "🛒 Shop"
            st.rerun()

        st.markdown("---")
    else:
        page = st.session_state.get("user_page", "🛒 Shop")
        if page not in user_nav_pages:
            page = "🛒 Shop"
            st.session_state.user_page = page
        st.caption("Shopping mode")
        min_sup, min_conf, min_lift, max_len = 0.02, 0.15, 1.5, 4

    st.markdown('<div style="font-size:11px;color:#475569;margin-top:1rem">v3.0 · Apriori + Shopping<br>Full MBA Platform</div>',
                unsafe_allow_html=True)

if (not is_admin) and (page in admin_only_pages):
    st.error("Access denied. Admin pages are restricted to authorized admin accounts only.")
    st.stop()

if is_admin and page in removed_admin_algorithm_pages:
    page = "📊 Exploratory Analysis"

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def load():
    return get_df()

@st.cache_data(ttl=300, show_spinner=False)
def load_all():
    # get_all_df() and get_df() both read the same transactions table.
    # Reusing load() avoids a second full-table query on each rerun.
    return load()


def _empty_txn_df():
    return pd.DataFrame(columns=["BillNo", "Itemname", "Quantity", "Price", "Date", "Country", "Category", "Revenue"])


@st.cache_data(ttl=300, show_spinner=False)
def load_product_catalog():
    """Load the current product catalog from the database."""
    products_df = get_products_df()

    if products_df.empty:
        return sorted(ALL_ITEMS), dict(PRICE_MAP), dict(CAT_MAP)

    items = products_df["name"].dropna().astype(str).tolist()
    prices = dict(zip(products_df["name"], products_df["price"]))
    categories = dict(zip(products_df["name"], products_df["category"]))
    return sorted(items), prices, categories


live_items, live_price_map, live_cat_map = load_product_catalog()

heavy_data_pages = {
    "📊 Dashboard",
    "📈 Analytics",
    "📊 Exploratory Analysis",
    "🔢 Transaction Encoding",
    "⚙️ Apriori Mining",
    "📐 Rules Analysis",
    "🏆 Optimization Summary",
    "⚡ Real-Time Simulation",
}

engine_pages = {
    "🔢 Transaction Encoding",
    "⚙️ Apriori Mining",
    "📐 Rules Analysis",
    "🎯 Recommendation Engine",
    "🔄 Incremental Learning",
    "🔬 Sensitivity Analysis",
    "🏆 Optimization Summary",
}

if page in heavy_data_pages or page in engine_pages:
    df = load()
    df_all = load_all()
else:
    df = _empty_txn_df()
    df_all = _empty_txn_df()

# ── Build engine (cached by params) ─────────────────────────────────────────
@st.cache_resource(ttl=60)
def get_engine(sup, conf, lift, mlen):
    _df    = load()
    txns   = build_transactions(_df)
    engine = AprioriEngine(min_support=sup, min_confidence=conf,
                           min_lift=lift, max_len=mlen)
    engine.load_transactions(txns).fit(verbose=False).generate_rules(verbose=False)
    return engine, txns

engine = None
transactions = []
rules_df = pd.DataFrame()
freq_df = pd.DataFrame()
pass_stats = pd.DataFrame()

if is_admin and page in engine_pages:
    engine, transactions = get_engine(min_sup, min_conf, min_lift, max_len)
    rules_df = engine.rules_df
    freq_df = engine.get_frequent_sets_df()
    pass_stats = engine.get_pass_stats_df()

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def kpi(label, value, sub="", color="blue"):
    st.markdown(f'<div class="kpi {color}"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)

def lift_badge(v):
    if v >= 3:   return "🟢 High"
    elif v >= 2: return "🟡 Medium"
    return "🔴 Low"

def plot_cfg(fig, h=340):
    dark = str(st.get_option("theme.base") or "").lower() == "dark"
    text_color = "#e5e7eb" if dark else "#0f172a"
    grid_color = "rgba(148,163,184,0.22)" if dark else "#e2e8f0"
    bg_color = "#0f172a" if dark else "white"

    fig.update_layout(
        height=h,
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        margin=dict(l=0, r=0, t=30, b=0),
        font=dict(family="Inter", color=text_color),
        title_font=dict(color=text_color),
        xaxis=dict(title_font=dict(color=text_color), tickfont=dict(color=text_color), gridcolor=grid_color, zerolinecolor=grid_color),
        yaxis=dict(title_font=dict(color=text_color), tickfont=dict(color=text_color), gridcolor=grid_color, zerolinecolor=grid_color),
    )
    return fig


def product_discount_pct(item_name):
    # Deterministic pseudo-discount to emulate storefront promotions.
    return (sum(ord(c) for c in item_name) % 4) * 5


TAG_KEYWORDS = {
    "protein": ["protein", "egg", "milk", "yogurt", "cheese", "peanut", "nut", "bean", "lentil"],
    "healthy": ["healthy", "fresh", "natural", "organic", "light", "diet"],
    "snack": ["snack", "chips", "bar", "biscuit", "cookie", "cracker"],
    "fruit": ["fruit", "banana", "apple", "orange", "mango", "berry", "grape", "pineapple"],
    "vegetable": ["vegetable", "veggie", "spinach", "tomato", "potato", "onion", "carrot", "broccoli"],
    "drink": ["drink", "juice", "tea", "coffee", "water", "soda"],
}


def infer_product_tags(item_name, category_name):
    text = f"{item_name} {category_name}".lower()
    tags = set()

    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            tags.add(tag)

    if category_name:
        tags.add(str(category_name).strip().lower())

    return tags


def get_cart_recommendations(cart_map, item_names, category_map, top_n=6):
    if not cart_map:
        return []

    cart_items = {str(item) for item in cart_map.keys()}
    cart_categories = {
        str(category_map.get(item, "Other")).strip().lower()
        for item in cart_items
    }
    cart_tags = set()
    for item in cart_items:
        cart_tags.update(infer_product_tags(item, category_map.get(item, "Other")))

    ranked = []
    for item in item_names:
        if item in cart_items:
            continue

        category_name = category_map.get(item, "Other")
        item_tags = infer_product_tags(item, category_name)
        category_score = 2 if str(category_name).strip().lower() in cart_categories else 0
        tag_overlap = len(item_tags & cart_tags)
        score = category_score + (tag_overlap * 3)

        if score <= 0:
            continue

        ranked.append({
            "item": item,
            "category": category_name,
            "score": score,
            "tag_overlap": tag_overlap,
        })

    ranked.sort(key=lambda x: (-x["score"], -x["tag_overlap"], x["item"]))
    return ranked[:max(4, min(6, int(top_n)))]


def _sum_first_available(df, column_names):
    for column_name in column_names:
        if column_name in df.columns:
            return pd.to_numeric(df[column_name], errors="coerce").fillna(0).sum()
    return 0


def render_user_top_menu(current_page):
    """BigBasket-style user navigation: shop-first with profile menu."""
    options = user_nav_pages
    safe_current_page = current_page if current_page in options else "🛒 Shop"

    c1, c2 = st.columns([9, 1])
    with c1:
        st.caption("🛒 Shopping")
    with c2:
        with st.popover("👤", help="Profile & account"):
            selected = st.radio("Open page", options, index=options.index(safe_current_page))
            if selected != safe_current_page:
                st.session_state.user_page = selected
                st.rerun()
            if st.button("🚪 Logout", width="stretch"):
                st.session_state.auth_user = None
                st.session_state.cart = {}
                st.session_state.user_page = "🛒 Shop"
                st.rerun()

    st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER — DISPATCH TO PAGES
# ══════════════════════════════════════════════════════════════════════════════

# ── USER PAGES ─────────────────────────────────────────────────────────────────
if not is_admin:
    render_user_top_menu(page)

if page == "👤 My Profile":
    render_profile_page(current_user, get_users_df, None)

elif page == "🛒 Shop":
    render_shop_page(live_items, live_price_map, live_cat_map)

elif page == "🎯 Recommendations":
    render_recommendations_page(rules_df if is_admin else pd.DataFrame(), 
                               engine if is_admin else None, live_items, live_price_map, live_cat_map)

elif page == "❤️ Wishlist":
    render_wishlist_page(live_items, live_price_map, live_cat_map)

elif page == "⚙️ Settings":
    render_settings_page()

# ── ADMIN PAGES ────────────────────────────────────────────────────────────────
elif page == "📊 Dashboard":
    render_admin_dashboard(get_users_df, get_user_purchases_df, get_all_df, get_df)

elif page == "📈 Analytics":
    render_analytics_page(get_all_df, get_df)

elif page == "👥 User Mgmt":
    render_user_management(get_users_df, create_user)

elif page == "📦 Products":
    render_product_management(live_items, live_price_map, live_cat_map)

elif page == "⚙️ Settings":
    render_system_settings()

# ── LEGACY ALGORITHM PAGES (existing code continues below) ──────────────────────
elif page == "🧺 My Cart":
    st.markdown("## 🧺 My Cart")
    st.caption("Review your cart, update quantities, and checkout")

    if not st.session_state.cart:
        st.info("Your cart is empty. Add products from Shop.")
    else:
        catalog_df = pd.DataFrame({
            "Item": sorted(live_items),
            "Price": [round(float(live_price_map.get(i, PRICE_MAP.get(i, 0.0))), 2) for i in sorted(live_items)],
        })
        catalog_df["DiscountPct"] = catalog_df["Item"].apply(product_discount_pct)
        catalog_df["FinalPrice"] = (catalog_df["Price"] * (1 - catalog_df["DiscountPct"] / 100)).round(2)
        final_price_map = {row.Item: row.FinalPrice for row in catalog_df.itertuples()}

        rows = []
        for item, qty in st.session_state.cart.items():
            unit = float(final_price_map.get(item, PRICE_MAP.get(item, 0.0)))
            rows.append({
                "Item": item,
                "Qty": int(qty),
                "Unit Price": round(unit, 2),
                "Subtotal": round(unit * int(qty), 2),
            })
        cart_df = pd.DataFrame(rows).sort_values("Item")

        st.dataframe(cart_df, width="stretch", height=320)

        st.markdown("### You may also like")
        recs = get_cart_recommendations(
            st.session_state.cart,
            live_items,
            live_cat_map,
            top_n=6,
        )

        if recs:
            rec_cols = st.columns(3)
            for idx, rec in enumerate(recs):
                with rec_cols[idx % 3]:
                    rec_item = rec["item"]
                    rec_category = rec["category"]
                    rec_price = float(final_price_map.get(rec_item, live_price_map.get(rec_item, 0.0)))

                    st.markdown(
                        f"""
                        <div style=\"background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:10px;margin-bottom:8px;min-height:132px\">
                            <div style=\"font-weight:700;color:#0f172a;font-size:13px;line-height:1.3\">{rec_item}</div>
                            <div style=\"font-size:10px;color:#7c3aed;text-transform:uppercase;letter-spacing:.5px;margin-top:4px;font-weight:600\">{rec_category}</div>
                            <div style=\"margin-top:8px;font-size:18px;font-weight:700;color:#1a7a4a\">£{rec_price:.2f}</div>
                            <div style=\"font-size:10px;color:#64748b;margin-top:4px\">Related by category/tags</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button("➕ Add", key=f"rec_add_{idx}_{rec_item}", width="stretch"):
                        st.session_state.cart[rec_item] = st.session_state.cart.get(rec_item, 0) + 1
                        st.success(f"Added 1x {rec_item}")
                        st.rerun()
        else:
            st.caption("No related products found yet for your cart.")

        total_amount = float(cart_df["Subtotal"].sum())
        delivery_fee = 0.0 if total_amount >= 40 else 2.99
        payable = total_amount + delivery_fee

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi("Cart Total", f"£{total_amount:,.2f}", "Products", "blue")
        with c2:
            kpi("Delivery", f"£{delivery_fee:,.2f}", "Free above £40", "green")
        with c3:
            kpi("Payable", f"£{payable:,.2f}", "At checkout", "orange")

        with st.form("checkout_form"):
            payment_method = st.selectbox("Payment Method", ["Cash on Delivery", "Card on Delivery", "UPI"])
            place_order = st.form_submit_button("✅ Checkout", width="stretch")

        if place_order:
            bill = record_user_purchase(current_user, st.session_state.cart)
            if bill:
                st.success(f"Order confirmed. Bill No: {bill} | Payment: {payment_method}")
                st.session_state.cart = {}
                st.cache_data.clear()
            else:
                st.error("Could not place order. Please review cart quantities.")

        if st.button("🗑 Clear Cart", width="stretch"):
            st.session_state.cart = {}
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# USER PAGE — ORDER HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📜 My Orders":
    st.markdown("## 📜 My Orders")
    st.caption("Your past purchases")

    user_orders = get_user_purchases_df(current_user)
    if user_orders.empty:
        st.info("No orders found yet. Place an order from the Buy Products page.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            kpi("Orders", f"{len(user_orders):,}", "Purchase count", "blue")
        with c2:
            item_total = _sum_first_available(user_orders, ["ItemCount", "Quantity", "quantity"])
            kpi("Items Bought", f"{int(item_total):,}", "Total quantity", "green")
        with c3:
            spent_total = _sum_first_available(user_orders, ["TotalAmount", "total_amount", "Amount"])
            kpi("Spent", f"£{spent_total:,.2f}", "Total amount", "orange")

        st.dataframe(user_orders, width="stretch", height=420)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PAGE — USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 User Management":
    st.markdown("## 👥 User Management")
    st.caption("Admin page — create and review platform users")

    with st.form("create_user_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("Username")
            new_role = st.selectbox("Role", ["user", "admin"])
        with c2:
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
        create_user_btn = st.form_submit_button("Create User", width="stretch")

    if create_user_btn:
        if new_password != confirm_password:
            st.error("Password confirmation does not match.")
        else:
            ok, msg = create_user(new_username, new_password, new_role)
            if ok:
                st.success(msg)
                st.cache_data.clear()
            else:
                st.error(msg)

    st.markdown("### Existing Users")
    users_df = get_users_df()
    st.dataframe(users_df, width="stretch", height=420)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXPLORATORY ANALYSIS  (Notebook Section 2)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Exploratory Analysis":
    st.markdown("## 📊 Exploratory Data Analysis")
    st.caption("dataset overview & visual exploration")

    # KPIs
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Total Rows",   f"{len(df_all):,}",  "Raw records",       "blue")
    with c2: kpi("Invoices",     f"{df['BillNo'].nunique():,}",  "Unique orders", "green")
    with c3: kpi("Products",     f"{df['Itemname'].nunique():,}", "Unique SKUs",  "orange")
    with c4: kpi("Total Revenue",f"£{df['Revenue'].sum():,.0f}", "All time",      "amber")
    with c5: kpi("Avg Basket",   f"{df.groupby('BillNo')['Itemname'].nunique().mean():.1f}","Items/order","teal")

    # Row 1
    col1, col2 = st.columns(2)
    with col1:
        section("🥇 Top 15 Products by Frequency")
        item_freq = df["Itemname"].value_counts().head(15).reset_index()
        item_freq.columns = ["Itemname","Count"]
        fig2 = px.bar(item_freq, x="Count", y="Itemname", orientation="h",
                      color="Count", color_continuous_scale="Greens")
        fig2.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(plot_cfg(fig2, 360), use_container_width=True)
    with col2:
        section("📱 Top 15 Categories by Revenue")
        cat_rev = df.groupby("Category")["Revenue"].sum().nlargest(15).reset_index()
        fig_cat = px.bar(cat_rev, x="Revenue", y="Category", orientation="h",
                         color="Revenue", color_continuous_scale="Oranges")
        fig_cat.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(plot_cfg(fig_cat, 360), use_container_width=True)

    # Row 2 — Monthly Revenue (notebook axes[0,2])
    section("📈 Monthly Revenue Trend")
    mrev = get_monthly_revenue(df)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=mrev["Month"], y=mrev["Revenue"],
                              mode="lines+markers",
                              line=dict(color=ORANGE, width=2.5),
                              fill="tozeroy", fillcolor="rgba(227,93,45,.1)",
                              name="Revenue £"))
    st.plotly_chart(plot_cfg(fig3, 280), use_container_width=True)

    # Row 3 — Basket size, Quantity dist, Hourly orders
    col1, col2, col3 = st.columns(3)
    with col1:
        section("🧺 Basket Size Distribution")
        bs = get_basket_sizes(df)
        bs_clip = bs[bs["basket_size"] <= 80]
        fig4 = px.histogram(bs_clip, x="basket_size", nbins=40, color_discrete_sequence=[PURPLE])
        fig4.add_vline(x=bs_clip["basket_size"].median(), line_dash="dash",
                       line_color="red", annotation_text=f"Median: {bs_clip['basket_size'].median():.0f}")
        st.plotly_chart(plot_cfg(fig4, 280), use_container_width=True)
    with col2:
        section("📦 Quantity per Line Item")
        qty = df[(df["Quantity"] > 0) & (df["Quantity"] <= 200)]["Quantity"]
        fig5 = px.histogram(qty, nbins=50, color_discrete_sequence=[TEAL])
        st.plotly_chart(plot_cfg(fig5, 280), use_container_width=True)
    with col3:
        section("🕐 Orders by Hour of Day")
        hourly = get_hourly_orders(df)
        fig6 = px.bar(hourly, x="Hour", y="Orders", color_discrete_sequence=[AMBER])
        st.plotly_chart(plot_cfg(fig6, 280), use_container_width=True)

    # Category revenue
    section("🏷️ Revenue by Category")
    catdf = get_category_revenue(df)
    fig7 = px.pie(catdf, values="Revenue", names="Category",
                  color_discrete_sequence=PALETTE, hole=0.4)
    fig7.update_layout(height=320, paper_bgcolor="white", margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig7, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — TRANSACTION ENCODING  (Notebook Section 3)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔢 Transaction Encoding":
    st.markdown("## 🔢 Transaction Encoding & Preprocessing")
    st.caption("data cleaning, basket building, sparse matrix visualisation")

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("Raw Transactions", f"{len(transactions):,}", "After cleaning","blue")
    with c2: kpi("Unique Items", f"{len(set(i for t in transactions for i in t)):,}","SKUs in baskets","green")
    with c3: kpi("Avg Items/Basket", f"{np.mean([len(t) for t in transactions]):.2f}","Mean basket size","orange")
    with c4: kpi("Max Basket", f"{max(len(t) for t in transactions)}","Largest basket","purple")

    section("🗂️ Preprocessing Steps Applied")
    steps = [
        ("Remove null Itemnames",  "Dropped rows where Itemname is null",         "Critical"),
        ("Remove returns (Qty≤0)", "Cancellations have negative quantity",         "Critical"),
        ("Remove invalid prices",  "Zero/negative prices are data errors",         "Critical"),
        ("Strip & uppercase items","Normalises 'white HEART' = 'WHITE HEART'",     "Quality"),
        ("Filter basket size 2–100","Single-item baskets give no rules",           "MBA"),
        ("Frozenset encoding",     "Sparse boolean — 10× less memory than dense", "Optimisation"),
    ]
    for step, desc, badge in steps:
        col = "high" if badge == "Critical" else ("med" if badge == "MBA" else "low")
        st.markdown(f'<div class="opt-card"><span class="opt-badge">{badge}</span>'
                    f'<div class="opt-title">{step}</div>'
                    f'<div class="opt-desc">{desc}</div></div>', unsafe_allow_html=True)

    # Sparse matrix heatmap (top-20 items, first 30 baskets)
    section("🔥 Sparse Transaction–Item Matrix (first 30 baskets × top 20 items)")
    top20 = [item for item, _ in Counter(i for t in transactions for i in t).most_common(20)]
    sample_txns = transactions[:30]
    matrix = np.array([[1 if item in set(t) else 0 for item in top20] for t in sample_txns])
    fig_hm = px.imshow(matrix,
                       x=[i[:22] for i in top20],
                       y=[f"T{i+1}" for i in range(len(sample_txns))],
                       color_continuous_scale="Blues",
                       labels=dict(x="Item", y="Transaction", color="Present"),
                       aspect="auto")
    fig_hm.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig_hm.update_layout(height=440, paper_bgcolor="white",
                         margin=dict(l=0,r=0,t=20,b=80),
                         coloraxis_showscale=False)
    st.plotly_chart(fig_hm, use_container_width=True)

    # Item frequency bar with support colour coding
    section("📊 Item Frequency with Support Tier Colouring")
    item_cnt = Counter(i for t in transactions for i in t)
    n_txns   = len(transactions)
    top_items = dict(sorted(item_cnt.items(), key=lambda x: -x[1])[:20])
    supports  = {k: v/n_txns for k, v in top_items.items()}
    colors_bar = [BLUE if v >= 0.05 else (GREEN if v >= 0.03 else ORANGE)
                  for v in supports.values()]
    fig_freq = go.Figure(go.Bar(
        x=list(top_items.values()),
        y=[k[:32] for k in top_items.keys()],
        orientation="h",
        marker_color=colors_bar,
        text=[f"{v:.1%}" for v in supports.values()],
        textposition="outside",
    ))
    fig_freq.update_layout(height=460, plot_bgcolor="white", paper_bgcolor="white",
                           yaxis=dict(autorange="reversed"),
                           margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig_freq, use_container_width=True)
    st.caption("🔵 Blue = support ≥5%  |  🟢 Green = 3–5%  |  🟠 Orange = <3%")

    section("💾 Memory Efficiency — Sparse vs Dense Encoding")
    import sys as _sys
    sparse_mem = sum(_sys.getsizeof(frozenset(t)) for t in transactions)
    all_items_set = set(i for t in transactions for i in t)
    dense_est = len(transactions) * len(all_items_set)
    col1, col2, col3 = st.columns(3)
    with col1: kpi("Sparse (frozenset)", f"{sparse_mem/1024:.0f} KB", "Actual usage", "green")
    with col2: kpi("Dense (matrix est.)", f"{dense_est/1024:.0f} KB", "If stored as 0/1 matrix", "orange")
    with col3: kpi("Memory Saving", f"{(1-sparse_mem/max(dense_est,1))*100:.0f}%", "Reduction achieved", "blue")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — APRIORI MINING  (Notebook Section 4 & 5)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Apriori Mining":
    st.markdown("## ⚙️ Apriori Algorithm Mining")
    st.caption("pass-by-pass trace, pruning efficiency, frequent itemsets")

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("Transactions",    f"{engine._stats['n_transactions']:,}", "Input",     "blue")
    with c2: kpi("Frequent Sets",   f"{engine._stats['n_frequent_sets']:,}","Discovered","green")
    with c3: kpi("Rules Mined",     f"{len(rules_df):,}",                  "Generated", "orange")
    with c4: kpi("Fit Time",        f"{engine._stats['fit_time_s']}s",     "Wall clock","purple")

    # Algorithm flow diagram
    section("🔄 Apriori Algorithm Flow")
    algo_steps = [
        ("Pass 1","Count 1-itemsets","Prune < min_support → L₁"),
        ("Pass 2","Self-join L₁ → C₂","Count & prune → L₂"),
        ("Pass 3","Self-join L₂ → C₃","Count & prune → L₃"),
        ("Rules","For each Lₖ (k≥2)","Generate A→B, filter conf & lift"),
    ]
    cols = st.columns(4)
    for col, (step, action, result) in zip(cols, algo_steps):
        with col:
            st.markdown(f"""<div style="background:#1e3a5f;border-radius:10px;padding:12px;
                            text-align:center;color:white">
                <div style="font-size:13px;font-weight:700;color:#93c5fd">{step}</div>
                <div style="font-size:11px;margin:6px 0">{action}</div>
                <div style="font-size:10px;color:#6ee7b7">{result}</div></div>""",
                         unsafe_allow_html=True)

    if not pass_stats.empty:
        section("📊 Pass-by-Pass Statistics")
        col1, col2, col3 = st.columns(3)

        # (a) Candidates vs Frequent
        with col1:
            fig_a = go.Figure()
            fig_a.add_trace(go.Bar(x=[f"Pass {p}" for p in pass_stats["pass"]],
                                   y=pass_stats["candidates"], name="Candidates",
                                   marker_color=BLUE, opacity=0.85))
            fig_a.add_trace(go.Bar(x=[f"Pass {p}" for p in pass_stats["pass"]],
                                   y=pass_stats["frequent"], name="Frequent",
                                   marker_color=GREEN, opacity=0.85))
            fig_a.update_layout(barmode="group", height=300,
                                plot_bgcolor="white", paper_bgcolor="white",
                                margin=dict(l=0,r=0,t=30,b=0),
                                title="(a) Candidates vs Frequent")
            st.plotly_chart(fig_a, use_container_width=True)

        # (b) Pruning rate
        with col2:
            pass_stats["pruning_rate"] = (
                1 - pass_stats["frequent"] / pass_stats["candidates"].replace(0,1)
            ) * 100
            fig_b = px.bar(pass_stats, x=pass_stats["pass"].apply(lambda x: f"Pass {x}"),
                           y="pruning_rate", text="pruning_rate",
                           color_discrete_sequence=[ORANGE])
            fig_b.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_b.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                                margin=dict(l=0,r=0,t=30,b=0), yaxis_range=[0,105],
                                title="(b) Anti-Monotone Pruning Rate")
            st.plotly_chart(fig_b, use_container_width=True)

        # (c) Frequent sets by size
        with col3:
            if not freq_df.empty:
                size_counts = freq_df.groupby("length").size().reset_index(name="count")
                size_counts["label"] = size_counts["length"].apply(lambda x: f"{x}-itemset")
                fig_c = px.bar(size_counts, x="label", y="count", text="count",
                               color_discrete_sequence=[PURPLE])
                fig_c.update_traces(textposition="outside")
                fig_c.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                                    margin=dict(l=0,r=0,t=30,b=0),
                                    title="(c) Frequent Itemsets by Size")
                st.plotly_chart(fig_c, use_container_width=True)

    section("📋 Frequent Itemsets Table")
    st.dataframe(freq_df.head(50), use_container_width=True, height=340)
    if not freq_df.empty:
        st.download_button("⬇ Download Frequent Itemsets", freq_df.to_csv(index=False),
                           "frequent_itemsets.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — RULES ANALYSIS  (Notebook Section 6)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📐 Rules Analysis":
    st.markdown("## 📐 Association Rules Analysis")
    st.caption("support/confidence/lift landscape (Figs A–F)")

    if rules_df.empty:
        st.warning("⚠️ No rules found. Lower the thresholds in the sidebar.")
        st.stop()

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Total Rules",  f"{len(rules_df):,}",                "Mined",        "blue")
    with c2: kpi("Avg Lift",     f"{rules_df['lift'].mean():.2f}",    "Mean",         "green")
    with c3: kpi("Max Lift",     f"{rules_df['lift'].max():.2f}",     "Best rule",    "orange")
    with c4: kpi("Avg Conf",     f"{rules_df['confidence'].mean():.1%}","Mean",       "purple")
    with c5: kpi("Lift > 2",     f"{(rules_df['lift']>2).sum():,}",   "Strong rules", "amber")

    tab1, tab2, tab3 = st.tabs(["📊 Visualisations", "📋 Rules Table", "📤 Export"])

    with tab1:
        # (A) Support vs Confidence coloured by Lift
        section("(A) Support vs Confidence — coloured by Lift")
        rd = rules_df.copy()
        rd["ant_str"] = rd["antecedent"].apply(lambda x: " + ".join(x))
        rd["con_str"] = rd["consequent"].apply(lambda x: " + ".join(x))
        fig_a = px.scatter(rd, x="support", y="confidence", color="lift",
                           color_continuous_scale="RdYlGn",
                           hover_data=["ant_str","con_str","lift"],
                           size="lift", size_max=18,
                           labels={"support":"Support","confidence":"Confidence","lift":"Lift"})
        fig_a.add_hline(y=min_conf, line_dash="dash", line_color="gray",
                        annotation_text=f"min_conf={min_conf:.0%}")
        fig_a.add_vline(x=min_sup, line_dash="dot", line_color="gray",
                        annotation_text=f"min_sup={min_sup:.1%}")
        fig_a.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                            margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig_a, use_container_width=True)

        # (B) + (D) Lift & Confidence distributions
        col1, col2, col3 = st.columns(3)
        with col1:
            section("(B) Lift Distribution")
            fig_b = px.histogram(rules_df, x="lift", nbins=30, color_discrete_sequence=[TEAL])
            fig_b.add_vline(x=rules_df["lift"].median(), line_dash="dash", line_color="red",
                            annotation_text=f"Median {rules_df['lift'].median():.2f}")
            st.plotly_chart(plot_cfg(fig_b, 260), use_container_width=True)
        with col2:
            section("(D) Confidence Distribution")
            fig_d = px.histogram(rules_df, x="confidence", nbins=25, color_discrete_sequence=[AMBER])
            fig_d.add_vline(x=rules_df["confidence"].median(), line_dash="dash", line_color="red")
            st.plotly_chart(plot_cfg(fig_d, 260), use_container_width=True)
        with col3:
            section("(F) Leverage Distribution")
            fig_f = px.histogram(rules_df, x="leverage", nbins=25, color_discrete_sequence=[PURPLE])
            fig_f.add_vline(x=0, line_color="black")
            st.plotly_chart(plot_cfg(fig_f, 260), use_container_width=True)

        # (C) Top 20 rules by lift
        section("(C) Top 20 Rules by Lift")
        top20 = rules_df.nlargest(20, "lift").copy()
        top20["rule"] = (top20["antecedent"].apply(lambda x: " + ".join(x)) +
                         " → " + top20["consequent"].apply(lambda x: " + ".join(x)))
        top20["rule_short"] = top20["rule"].str[:68] + "…"
        fig_c = px.bar(top20, x="lift", y="rule_short", orientation="h",
                       color="confidence", color_continuous_scale="Blues",
                       text="lift")
        fig_c.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_c.update_layout(height=560, plot_bgcolor="white", paper_bgcolor="white",
                            yaxis=dict(autorange="reversed"),
                            margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_c, use_container_width=True)

        # Co-occurrence heatmap
        section("🔥 Product Co-occurrence Heatmap (Top 12 Items)")
        top_prods = df["Itemname"].value_counts().head(12).index.tolist()
        txn_sets = [frozenset(t) for t in transactions]
        co_mat = np.zeros((len(top_prods), len(top_prods)), dtype=int)
        for i, p1 in enumerate(top_prods):
            for j, p2 in enumerate(top_prods):
                if i != j:
                    co_mat[i, j] = sum(1 for t in txn_sets if p1 in t and p2 in t)
        fig_co = px.imshow(co_mat, x=[p[:20] for p in top_prods], y=[p[:20] for p in top_prods],
                           color_continuous_scale="Blues", text_auto=True, aspect="auto")
        fig_co.update_xaxes(tickangle=45, tickfont=dict(size=9))
        fig_co.update_layout(height=440, paper_bgcolor="white", margin=dict(l=0,r=0,t=20,b=80))
        st.plotly_chart(fig_co, use_container_width=True)

        # (E) Conviction distribution
        section("(E) Conviction Distribution")
        conv_clip = rules_df[rules_df["conviction"] < rules_df["conviction"].quantile(0.95)]["conviction"]
        fig_e = px.histogram(conv_clip, nbins=25, color_discrete_sequence=[GREEN])
        st.plotly_chart(plot_cfg(fig_e, 240), use_container_width=True)

    with tab2:
        section("All Association Rules")
        search = st.text_input("🔍 Filter by antecedent or consequent")
        disp = rules_df.copy()
        if search:
            mask = (disp["antecedent"].astype(str).str.contains(search, case=False) |
                    disp["consequent"].astype(str).str.contains(search, case=False))
            disp = disp[mask]
        disp["strength"] = disp["lift"].apply(lift_badge)
        disp["ant"] = disp["antecedent"].apply(lambda x: " + ".join(x))
        disp["con"] = disp["consequent"].apply(lambda x: " + ".join(x))
        st.dataframe(disp[["ant","con","support","confidence","lift","conviction","leverage","strength"]],
                     use_container_width=True, height=440)
        st.caption(f"Showing {len(disp)} / {len(rules_df)} rules")

    with tab3:
        exp = rules_df.copy()
        exp["antecedent"] = exp["antecedent"].apply(lambda x: " + ".join(x))
        exp["consequent"] = exp["consequent"].apply(lambda x: " + ".join(x))
        st.download_button("⬇ Download All Rules (CSV)", exp.to_csv(index=False),
                           "association_rules_final.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — RECOMMENDATION ENGINE  (Notebook Section 7)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Recommendation Engine":
    st.markdown("## 🎯 Adaptive Recommendation Engine")
    st.caption("Notebook Section 7 — coverage-weighted scoring, top-N recommendations")

    st.info("**Scoring formula:** score(item) = Σ lift × confidence × (1 + |antecedent| / |cart|)")

    if rules_df.empty:
        st.warning("No rules available. Lower thresholds in sidebar.")
        st.stop()

    # Preset test carts from notebook
    preset = {
        "Cart A — Heart T-Light + Jumbo Bag": ["WHITE HANGING HEART T-LIGHT HOLDER","JUMBO BAG RED RETROSPOT"],
        "Cart B — Regency Cakestand":         ["REGENCY CAKESTAND 3 TIER"],
        "Cart C — Bunting + Lunch Bag + Bird":["PARTY BUNTING","LUNCH BAG RED RETROSPOT","ASSORTED COLOUR BIRD ORNAMENT"],
        "Cart D — Cake Tins":                 ["SET OF 3 CAKE TINS PANTRY DESIGN"],
        "Custom (pick below)":                [],
    }
    choice = st.selectbox("Choose a test cart (matches notebook test cases):", list(preset.keys()))
    if choice == "Custom (pick below)":
        cart_items = st.multiselect("Pick items:", ALL_ITEMS, max_selections=8)
    else:
        cart_items = preset[choice]
        st.markdown(f"**Cart contents:** {' | '.join(cart_items)}")

    top_n = st.slider("Top-N recommendations", 3, 10, 6)

    if cart_items:
        recs = engine.recommend(cart_items, top_n=top_n)
        if recs:
            section(f"🎯 Top {top_n} Recommendations")
            for i, r in enumerate(recs, 1):
                conf_pct = round(r["best_conf"] * 100, 1)
                lift_val = round(r["best_lift"], 2)
                score    = round(r["score"], 3)
                badge    = "🟢" if lift_val >= 3 else ("🟡" if lift_val >= 2 else "🔴")
                st.markdown(f'<div class="rec-card">'
                            f'<b>#{i} &nbsp; {badge} &nbsp; {r["item"]}</b>'
                            f'&nbsp;&nbsp;|&nbsp; Confidence: {conf_pct}%'
                            f'&nbsp;|&nbsp; Lift: {lift_val}×'
                            f'&nbsp;|&nbsp; Rules hit: {r["rules_hit"]}'
                            f'&nbsp;|&nbsp; Score: {score}</div>', unsafe_allow_html=True)

            # Bar chart
            items_  = [r["item"][:30] for r in recs]
            scores_ = [r["score"] for r in recs]
            confs_  = [r["best_conf"] for r in recs]
            lifts_  = [r["best_lift"] for r in recs]
            fig_rec = go.Figure(go.Bar(
                x=scores_, y=items_, orientation="h",
                marker=dict(color=lifts_, colorscale="RdYlGn", showscale=True,
                            colorbar=dict(title="Lift")),
                text=[f"conf={c:.0%} lift={l:.1f}×" for c,l in zip(confs_, lifts_)],
                textposition="outside",
            ))
            fig_rec.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white",
                                  yaxis=dict(autorange="reversed"),
                                  xaxis_title="Recommendation Score",
                                  margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_rec, use_container_width=True)
        else:
            st.info("No strong recommendations for this cart with current thresholds.")

    # Multi-cart comparison (notebook Fig 7)
    section("📊 Multi-Cart Recommendation Comparison")
    cols = st.columns(3)
    for col, (label, items) in zip(cols, list(preset.items())[:3]):
        with col:
            recs = engine.recommend(items, top_n=5)
            if recs:
                fig_mc = px.bar(
                    x=[r["score"] for r in recs],
                    y=[r["item"][:22] for r in recs],
                    orientation="h", color_discrete_sequence=[BLUE],
                    title=label.split("—")[0].strip()
                )
                fig_mc.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                                     yaxis=dict(autorange="reversed"),
                                     margin=dict(l=0,r=0,t=40,b=0), showlegend=False)
                st.plotly_chart(fig_mc, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — INCREMENTAL LEARNING  (Notebook Section 8)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔄 Incremental Learning":
    st.markdown("## 🔄 Incremental Learning Simulation")
    st.caption("simulate new purchases, track rule evolution")

    st.info("""When a customer completes a purchase the engine:
1. Appends the transaction   2. Refits Apriori   3. Regenerates all rules   4. New rules activate immediately""")

    NEW_PURCHASES = [
        ["WHITE HANGING HEART T-LIGHT HOLDER","REGENCY CAKESTAND 3 TIER","LUNCH BAG RED RETROSPOT","JUMBO BAG RED RETROSPOT"],
        ["PARTY BUNTING","SET OF 3 CAKE TINS PANTRY DESIGN","PACK OF 72 RETROSPOT CAKE CASES","NATURAL SLATE HEART CHALKBOARD"],
        ["JUMBO BAG PINK POLKADOT","LUNCH BAG  BLACK SKULL.","HEART OF WICKER SMALL","JUMBO STORAGE BAG SUKI"],
        ["ASSORTED COLOUR BIRD ORNAMENT","WHITE HANGING HEART T-LIGHT HOLDER","JUMBO BAG RED RETROSPOT","REGENCY CAKESTAND 3 TIER"],
        ["PARTY BUNTING","JUMBO SHOPPER VINTAGE RED PAISLEY","SET OF 3 CAKE TINS PANTRY DESIGN"],
    ]
    TEST_CART = ["WHITE HANGING HEART T-LIGHT HOLDER","JUMBO BAG RED RETROSPOT"]

    if st.button("▶ Run Incremental Simulation (5 new purchases)", use_container_width=True):
        with st.spinner("Simulating incremental updates..."):
            import copy
            sim_engine = AprioriEngine(min_support=min_sup, min_confidence=min_conf,
                                      min_lift=min_lift, max_len=max_len)
            sim_engine.load_transactions(transactions).fit(verbose=False).generate_rules(verbose=False)

            base_rules = len(sim_engine.rules)
            base_txns  = len(sim_engine.transactions)
            recs_before = sim_engine.recommend(TEST_CART, top_n=3)

            history = []
            for i, purchase in enumerate(NEW_PURCHASES, 1):
                t0 = time.time()
                sim_engine.update(purchase)
                elapsed = time.time() - t0
                recs = sim_engine.recommend(TEST_CART, top_n=3)
                history.append({
                    "Purchase #": i,
                    "New Item (first)": purchase[0][:35],
                    "Total Txns": len(sim_engine.transactions),
                    "Total Rules": len(sim_engine.rules),
                    "Update Time (s)": round(elapsed, 3),
                    "Top Rec": recs[0]["item"][:30] if recs else "—",
                    "Top Lift": round(recs[0]["best_lift"], 2) if recs else 0,
                })

            hist_df = pd.DataFrame(history)
            st.dataframe(hist_df, use_container_width=True)

            # Plots — notebook Fig 8a, 8b, 8c
            section("📈 Rule Evolution Charts")
            c1, c2, c3 = st.columns(3)
            x = hist_df["Purchase #"]

            with c1:
                fig_8a = go.Figure()
                fig_8a.add_trace(go.Scatter(
                    x=["Base"] + [f"P{i}" for i in x],
                    y=[base_rules] + list(hist_df["Total Rules"]),
                    mode="lines+markers+text",
                    line=dict(color=BLUE, width=2.5),
                    marker=dict(size=9),
                    text=[str(v) for v in [base_rules] + list(hist_df["Total Rules"])],
                    textposition="top center",
                    fill="tozeroy", fillcolor="rgba(45,91,227,.1)"
                ))
                fig_8a.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                                     title="(a) Rule Count Evolution",
                                     margin=dict(l=0,r=0,t=40,b=0))
                st.plotly_chart(fig_8a, use_container_width=True)

            with c2:
                fig_8b = px.bar(hist_df, x=[f"P{i}" for i in x],
                                y="Update Time (s)", text="Update Time (s)",
                                color_discrete_sequence=[GREEN])
                fig_8b.update_traces(texttemplate="%{text:.3f}s", textposition="outside")
                fig_8b.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                                     title="(b) Rebuild Time per Purchase",
                                     margin=dict(l=0,r=0,t=40,b=0))
                st.plotly_chart(fig_8b, use_container_width=True)

            with c3:
                fig_8c = go.Figure()
                baseline_lift = recs_before[0]["best_lift"] if recs_before else 0
                fig_8c.add_trace(go.Scatter(
                    x=["Base"] + [f"P{i}" for i in x],
                    y=[baseline_lift] + list(hist_df["Top Lift"]),
                    mode="lines+markers",
                    line=dict(color=ORANGE, width=2.5),
                    marker=dict(size=9),
                ))
                fig_8c.add_hline(y=min_lift, line_dash="dash", line_color="red",
                                 annotation_text=f"min_lift={min_lift}")
                fig_8c.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                                     title="(c) Top Recommendation Lift",
                                     margin=dict(l=0,r=0,t=40,b=0))
                st.plotly_chart(fig_8c, use_container_width=True)
    else:
        st.markdown("Click the button above to run the simulation.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — SENSITIVITY ANALYSIS  (Notebook Section 9)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔬 Sensitivity Analysis":
    st.markdown("## 🔬 Sensitivity Analysis — Threshold Impact")
    st.caption("Notebook Section 9 — heatmaps of rules vs support/confidence grid")

    st.warning("⏳ This sweeps multiple Apriori runs — takes ~30–60 seconds. Click to start.")

    support_vals    = [0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05]
    confidence_vals = [0.10, 0.15, 0.20, 0.25, 0.30]

    if st.button("▶ Run Sensitivity Sweep", use_container_width=True):
        results = []
        bar = st.progress(0)
        total = len(support_vals) * len(confidence_vals)
        done  = 0
        for sup in support_vals:
            for conf in confidence_vals:
                e_tmp = AprioriEngine(min_support=sup, min_confidence=conf,
                                     min_lift=1.5, max_len=3)
                e_tmp.load_transactions(transactions).fit(verbose=False).generate_rules(verbose=False)
                results.append({
                    "min_support":    sup,
                    "min_confidence": conf,
                    "n_freq_sets":    e_tmp._stats["n_frequent_sets"],
                    "n_rules":        len(e_tmp.rules),
                })
                done += 1
                bar.progress(done / total)

        sens_df = pd.DataFrame(results)
        pivot_r = sens_df.pivot(index="min_confidence", columns="min_support", values="n_rules")
        pivot_f = sens_df.pivot(index="min_confidence", columns="min_support", values="n_freq_sets")

        col1, col2 = st.columns(2)
        with col1:
            section("(A) Rules Generated — rows=conf, cols=support")
            fig_a = px.imshow(pivot_r, text_auto=True, color_continuous_scale="Blues",
                              x=[f"{v:.1%}" for v in support_vals],
                              y=[f"{v:.0%}" for v in confidence_vals],
                              labels=dict(x="Min Support", y="Min Confidence", color="Rules"),
                              aspect="auto")
            fig_a.update_layout(height=320, paper_bgcolor="white", margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_a, use_container_width=True)

        with col2:
            section("(B) Frequent Itemsets Found")
            fig_b = px.imshow(pivot_f, text_auto=True, color_continuous_scale="Greens",
                              x=[f"{v:.1%}" for v in support_vals],
                              y=[f"{v:.0%}" for v in confidence_vals],
                              labels=dict(x="Min Support", y="Min Confidence", color="Itemsets"),
                              aspect="auto")
            fig_b.update_layout(height=320, paper_bgcolor="white", margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig_b, use_container_width=True)

        # Line chart — rules vs support for each confidence level
        section("📈 Rules vs Support (per confidence level)")
        fig_line = go.Figure()
        for conf in confidence_vals:
            sub = sens_df[sens_df["min_confidence"] == conf]
            fig_line.add_trace(go.Scatter(x=sub["min_support"]*100, y=sub["n_rules"],
                                         mode="lines+markers", name=f"conf={conf:.0%}"))
        fig_line.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                               xaxis_title="Min Support (%)", yaxis_title="Number of Rules",
                               margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_line, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8 — REAL-TIME SIMULATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚡ Real-Time Simulation":
    st.markdown("## ⚡ Real-Time Transaction Simulation")
    st.caption("Insert live transactions and watch the rule engine update")

    if "rt_log" not in st.session_state:
        st.session_state.rt_log = []

    col1, col2 = st.columns([1, 2])
    with col1:
        mode = st.radio("Basket mode", ["Random","Pattern-based","Custom"])
        if mode == "Custom":
            sel_items = st.multiselect("Pick items:", ALL_ITEMS, default=ALL_ITEMS[:3])
        else:
            sel_items = None
        n_txn = st.number_input("Transactions to generate", 1, 50, 1)

        if st.button("🚀 Generate & Insert", use_container_width=True):
            for _ in range(int(n_txn)):
                if mode == "Random":
                    basket = random.sample(ALL_ITEMS, k=random.randint(2,6))
                elif mode == "Pattern-based":
                    p = random.choice(PATTERNS)
                    basket = p[:random.randint(2, len(p))]
                else:
                    basket = sel_items or ALL_ITEMS[:2]
                bill = insert_rt_transaction(basket)
                st.session_state.rt_log.insert(0,
                    f"[{time.strftime('%H:%M:%S')}] {bill} → {', '.join(basket[:4])}{'…' if len(basket)>4 else ''}")
            st.success(f"✅ {n_txn} transaction(s) inserted!")
            st.cache_data.clear()

        if st.button("🤖 Auto 10 Random", use_container_width=True):
            for _ in range(10):
                basket = random.sample(ALL_ITEMS, k=random.randint(2,5))
                bill = insert_rt_transaction(basket)
                st.session_state.rt_log.insert(0, f"[{time.strftime('%H:%M:%S')}] {bill} → {', '.join(basket[:3])}…")
            st.success("✅ 10 transactions inserted!")
            st.cache_data.clear()

        if st.button("🗑 Clear Log"):
            st.session_state.rt_log = []

    with col2:
        st.markdown("### Live Transaction Log")
        log = "\n".join(st.session_state.rt_log[:60]) or "No transactions yet…"
        st.markdown(f'<div class="rt-log">{log}</div>', unsafe_allow_html=True)

        fresh = get_all_df()
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Records",  f"{len(fresh):,}")
        c2.metric("Total Invoices", f"{fresh['BillNo'].nunique():,}")
        c3.metric("Revenue",        f"£{fresh['Revenue'].sum():,.0f}")

        st.markdown("**Last 10 Transactions**")
        last10 = fresh.sort_values("Date",ascending=False).drop_duplicates("BillNo").head(10)
        st.dataframe(last10[["BillNo","Itemname","Quantity","Revenue","Date"]],
                     use_container_width=True, height=240)

    # Revenue gauge
    section("📊 Revenue Gauge")
    total_rev = get_all_df()["Revenue"].sum()
    target = 50000
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_rev,
        delta={"reference": target*0.7},
        title={"text": f"Revenue vs £{target:,} Target"},
        gauge={
            "axis": {"range": [0, target]},
            "bar":  {"color": BLUE},
            "steps": [
                {"range": [0, target*0.5],  "color": "#fee2e2"},
                {"range": [target*0.5, target*0.8], "color": "#fef9c3"},
                {"range": [target*0.8, target], "color": "#dcfce7"},
            ],
            "threshold": {"line": {"color": GREEN,"width": 4}, "value": target*0.9}
        }
    ))
    fig_g.update_layout(height=280, paper_bgcolor="white", margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig_g, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 9 — OPTIMISATION SUMMARY  (Notebook Sections 10 & 11)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Optimization Summary":
    st.markdown("## 🏆 Optimization Summary Dashboard")
    st.caption("all 9 optimisations + project summary charts")

    OPTIMISATIONS = [
        ("Anti-monotone pruning",     "Apriori property eliminates 90–99%+ of candidates",      "95.2%", "Candidates reduced"),
        ("Self-join candidate gen",   "Merge itemsets sharing first k-1 items; avoids O(nᵏ)",    "O(n²)","Complexity"),
        ("Dict-based counting",       "Hash lookup O(1) per pair; 3× faster than list scan",     "3×",   "Speed boost"),
        ("Sparse frozenset encoding", "Only store present items; ~10× less memory",               "88.7%","Memory saving"),
        ("Dual quality filter",       "Confidence AND Lift — removes misleading high-conf rules", "72%",  "Spurious rules cut"),
        ("Conviction + Leverage",     "Multi-metric ranking for diverse recommendations",         "+",    "Diversity"),
        ("Incremental update",        "Append-only; no full reload on new transactions",          "<1s",  "Update time"),
        ("Coverage-weighted scoring", "Longer-context rules score higher → targeted recs",        "+",    "Personalisation"),
        ("Top-N deduplication",       "Best-rule-per-item before ranking; no redundant output",   "✓",    "Quality"),
    ]
    for i, (name, desc, metric, unit) in enumerate(OPTIMISATIONS):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f'<div class="opt-card">'
                        f'<span class="opt-badge">#{i+1}</span>'
                        f'<div class="opt-title">{name}</div>'
                        f'<div class="opt-desc">{desc}</div></div>',
                        unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="text-align:center;padding-top:20px">'
                        f'<div style="font-size:22px;font-weight:700;color:{PALETTE[i%6]}">{metric}</div>'
                        f'<div style="font-size:11px;color:#64748b">{unit}</div></div>',
                        unsafe_allow_html=True)

    # Project summary dashboard (Notebook Section 11.1)
    section("📊 Project Summary Dashboard ")

    col1, col2 = st.columns(2)

    # (A) Frequent itemset support distribution
    with col1:
        if not freq_df.empty:
            fig_a = px.histogram(freq_df, x="support", nbins=30,
                                 color_discrete_sequence=[BLUE])
            fig_a.add_vline(x=min_sup, line_dash="dash", line_color="red",
                            annotation_text=f"min_sup={min_sup:.1%}")
            fig_a.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                                title="(A) Frequent Itemset Support Distribution",
                                margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_a, use_container_width=True)

    # (B) Most frequently recommended items (as consequent)
    with col2:
        if not rules_df.empty:
            all_cons = Counter(item for r in engine.rules for item in r["consequent"])
            top_cons = pd.DataFrame(all_cons.most_common(12), columns=["Item","Count"])
            fig_b = px.bar(top_cons, x="Count", y="Item", orientation="h",
                           color_discrete_sequence=[GREEN])
            fig_b.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                                yaxis=dict(autorange="reversed"),
                                title="(B) Most Frequently Recommended Items",
                                margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_b, use_container_width=True)

    col1, col2 = st.columns(2)

    # (C) Optimisation impact bar
    with col1:
        opt_metrics = {"Anti-monotone\npruning": 95.2, "Memory\nreduction": 88.7,
                       "Dual-filter\nquality": 72.0, "Coverage\nscoring": 100.0}
        fig_c = px.bar(x=list(opt_metrics.keys()), y=list(opt_metrics.values()),
                       text=list(opt_metrics.values()),
                       color=list(opt_metrics.keys()),
                       color_discrete_sequence=PALETTE)
        fig_c.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_c.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                            yaxis_range=[0, 115], showlegend=False,
                            title="(C) Optimisation Impact Metrics",
                            margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_c, use_container_width=True)

    # (D) Metric correlation heatmap
    with col2:
        if not rules_df.empty:
            corr = rules_df[["support","confidence","lift","conviction","leverage"]].corr()
            fig_d = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                              aspect="auto", zmin=-1, zmax=1)
            fig_d.update_layout(height=300, paper_bgcolor="white",
                                title="(D) Metric Correlation Matrix",
                                margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_d, use_container_width=True)

    # Final stats panel
    section("✅ Final Project Statistics")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: kpi("Transactions",   f"{engine._stats['n_transactions']:,}", "UK baskets",    "blue")
    with c2: kpi("Unique Items",   f"{len(set(i for t in transactions for i in t)):,}","SKUs","green")
    with c3: kpi("Frequent Sets",  f"{engine._stats['n_frequent_sets']:,}","Discovered",   "orange")
    with c4: kpi("Rules Mined",    f"{len(rules_df):,}",                  "Generated",    "purple")
    with c5: kpi("Best Lift",      f"{rules_df['lift'].max():.3f}×" if not rules_df.empty else "—","Top rule","amber")
    with c6: kpi("Fit Time",       f"{engine._stats['fit_time_s']}s",     "Wall clock",   "teal")

    if not rules_df.empty:
        exp = rules_df.copy()
        exp["antecedent"] = exp["antecedent"].apply(lambda x: " + ".join(x))
        exp["consequent"] = exp["consequent"].apply(lambda x: " + ".join(x))
        st.download_button("⬇ Download Final Rules CSV",
                           exp.to_csv(index=False),
                           "association_rules_final.csv", "text/csv")
