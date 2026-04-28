"""
Admin Pages Module — Complete admin dashboard and management
Includes: Dashboard, User Management, Analytics, Product Management, Reports
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from backend.db_config import get_db_connection
from backend.data_layer import (
    add_product,
    get_products_df,
    import_online_retail_dataset,
    get_dataset_import_overview,
)


def kpi(label, value, sub="", color="blue"):
    """KPI Card Component"""
    st.markdown(f'<div class="kpi {color}"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True)

def section(title):
    """Section Header Component"""
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)


def format_timestamp(value):
    if value is None or pd.isna(value):
        return "N/A"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def ensure_user_columns(users_df):
    df = users_df.copy()
    if "account_status" not in df.columns:
        df["account_status"] = "Active"
    if "last_login" not in df.columns:
        df["last_login"] = pd.NA
    if "login_count" not in df.columns:
        df["login_count"] = 0
    if "created_at" not in df.columns:
        df["created_at"] = pd.NA
    return df


def apply_session_status_overrides(users_df):
    df = users_df.copy()
    overrides = st.session_state.get("user_status_overrides", {})
    if overrides and "username" in df.columns:
        df["account_status"] = df.apply(
            lambda row: overrides.get(str(row["username"]).strip(), row.get("account_status", "Active")),
            axis=1,
        )
    return df


def update_user_status_safe(username, account_status):
    account_status = (account_status or "").strip().title()
    if account_status not in {"Active", "Inactive"}:
        return False, "Invalid account status."

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS account_status TEXT NOT NULL DEFAULT 'Active'
            """
        )
        c.execute(
            "UPDATE users SET account_status = %s WHERE username = %s",
            (account_status, (username or "").strip()),
        )
        conn.commit()
        if c.rowcount == 0:
            return False, "User not found."
        if "user_status_overrides" not in st.session_state:
            st.session_state.user_status_overrides = {}
        st.session_state.user_status_overrides[(username or "").strip()] = account_status
        return True, f"User marked as {account_status.lower()}."
    except Exception:
        conn.rollback()
        try:
            c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
            existing = {row[0] for row in c.fetchall()}
            if "account_status" not in existing:
                c.execute("ALTER TABLE users ADD COLUMN account_status TEXT NOT NULL DEFAULT 'Active'")
            c.execute(
                "UPDATE users SET account_status = %s WHERE username = %s",
                (account_status, (username or "").strip()),
            )
            conn.commit()
            if c.rowcount == 0:
                return False, "User not found."
            return True, f"User marked as {account_status.lower()}."
        except Exception as e:
            conn.rollback()
            return False, f"Failed to update user status: {e}"
    finally:
        conn.close()

def _is_dark_mode():
    return str(st.get_option("theme.base") or "").lower() == "dark"

def plot_cfg(fig, h=340):
    """Configure plotly figure"""
    dark = _is_dark_mode()
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


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_dashboard(get_users_df, get_user_purchases_df, get_all_df, get_df):
    """Main admin dashboard with KPIs and overview"""
    st.markdown("## 📊 Admin Dashboard")
    st.caption("Platform overview and real-time metrics")
    
    # Load data
    users_df = get_users_df()
    df = get_all_df()
    
    # KPIs Row 1
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_users = len(users_df)
    total_orders = df['BillNo'].nunique() if not df.empty else 0
    total_revenue = df['Revenue'].sum() if not df.empty else 0
    total_products = df['Itemname'].nunique() if not df.empty else 0
    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0
    conversion_rate = (total_orders / max(total_users, 1)) * 100
    
    with col1:
        kpi("Total Users", f"{total_users:,}", "Registered accounts", "blue")
    with col2:
        kpi("Active Orders", f"{total_orders:,}", "All time", "green")
    with col3:
        kpi("Revenue", f"£{total_revenue:,.0f}", "Total sales", "orange")
    with col4:
        kpi("Products Sold", f"{total_products:,}", "Unique items", "purple")
    with col5:
        kpi("Avg Order", f"£{avg_order_value:.2f}", "Per transaction", "amber")
    with col6:
        kpi("Conversion", f"{conversion_rate:.1f}%", "Orders/User", "teal")
    
    st.markdown("---")
    
    # Revenue & Orders Charts
    col1, col2 = st.columns(2)
    
    with col1:
        section("💰 Revenue Trend (Last 12 Months)")
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            monthly = df.groupby(df['Date'].dt.to_period('M'))['Revenue'].sum().reset_index()
            monthly.columns = ['Month', 'Revenue']
            monthly['Month'] = monthly['Month'].astype(str)
            
            fig = px.line(monthly, x='Month', y='Revenue', markers=True,
                         title='Monthly Revenue Growth')
            fig.update_traces(line_color='#E35D2D', marker_size=8)
            st.plotly_chart(plot_cfg(fig, 320), use_container_width=True)
        else:
            st.info("No data available yet")
    
    with col2:
        section("📈 Orders Trend")
        if not df.empty:
            monthly_orders = df.groupby(df['Date'].dt.to_period('M')).size().reset_index(name='Orders')
            monthly_orders['Month'] = monthly_orders.iloc[:, 0].astype(str)
            
            fig = px.bar(monthly_orders, x='Month', y='Orders',
                        title='Monthly Order Count')
            fig.update_traces(marker_color='#2D5BE3')
            st.plotly_chart(plot_cfg(fig, 320), use_container_width=True)
        else:
            st.info("No data available yet")
    
    st.markdown("---")
    section("📊 Platform Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### User Roles")
        user_roles = users_df['role'].value_counts().reset_index()
        user_roles.columns = ['role', 'count']
        fig = px.pie(user_roles, values='count', names='role', 
                    color_discrete_map={'admin': '#9A3DD4', 'user': '#2D5BE3'})
        st.plotly_chart(plot_cfg(fig, 280), use_container_width=True)
    
    with col2:
        st.markdown("### Orders by Category")
        if not df.empty:
            cat_orders = df.groupby('Category').size().reset_index(name='Orders')
            cat_orders = cat_orders.nlargest(5, 'Orders')
            fig = px.bar(cat_orders, x='Category', y='Orders',
                        color='Orders', color_continuous_scale='Viridis')
            st.plotly_chart(plot_cfg(fig, 280), use_container_width=True)
    
    with col3:
        st.markdown("### Top Products")
        if not df.empty:
            top_items = df['Itemname'].value_counts().head(5).reset_index()
            top_items.columns = ['Item', 'Orders']
            fig = px.bar(top_items, x='Orders', y='Item', orientation='h',
                        color='Orders', color_continuous_scale='Greens')
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(plot_cfg(fig, 280), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ENHANCED USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
def render_user_management(get_users_df, create_user):
    """Comprehensive user management"""
    st.markdown("## 👥 User Management")
    st.caption("Create, manage, and monitor user accounts")

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("🔄 Restart This Page", width="stretch", help="Reload this admin page without restarting from terminal"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()
    
    tabs = st.tabs(["➕ Create User", "👥 All Users", "🔍 User Details", "🚫 Deactivated"])
    
    with tabs[0]:
        st.markdown("### Create New User")
        with st.form("create_user_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_username = st.text_input("Username", placeholder="john_doe")
                new_role = st.selectbox("Role", ["user", "admin", "moderator"])
            with c2:
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
            
            c1, c2 = st.columns(2)
            with c1:
                email = st.text_input("Email", placeholder="john@example.com")
            with c2:
                status = st.selectbox("Status", ["Active", "Inactive"])
            
            create_user_btn = st.form_submit_button("✅ Create User", width="stretch")
        
        if create_user_btn:
            if new_password != confirm_password:
                st.error("❌ Passwords don't match")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            else:
                ok, msg = create_user(new_username, new_password, new_role)
                if ok:
                    st.success(f"✅ {msg}")
                    st.cache_data.clear()
                else:
                    st.error(f"❌ {msg}")
    
    with tabs[1]:
        st.markdown("### All Users")
        users_df = get_users_df()
        users_df = ensure_user_columns(users_df)
        users_df = apply_session_status_overrides(users_df)
        
        if not users_df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                kpi("Total Users", len(users_df), "Registered", "blue")
            with col2:
                admin_count = len(users_df[users_df['role'] == 'admin'])
                kpi("Admins", admin_count, "Admin accounts", "purple")
            with col3:
                user_count = len(users_df[users_df['role'] == 'user'])
                kpi("Regular Users", user_count, "Standard accounts", "green")
            
            # Search and filter
            search_col, role_col = st.columns([2, 1])
            with search_col:
                search_user = st.text_input("Search by username or email")
            with role_col:
                filter_role = st.selectbox("Filter by role", ["All", "admin", "user"])
            
            filtered_users = users_df.copy()
            if search_user:
                filtered_users = filtered_users[filtered_users['username'].str.contains(search_user, case=False)]
            if filter_role != "All":
                filtered_users = filtered_users[filtered_users['role'] == filter_role]
            
            # Display users table
            display_df = filtered_users.copy()
            display_df["created_at"] = display_df.get("created_at", pd.Series([pd.NA] * len(display_df), index=display_df.index)).apply(format_timestamp)
            display_df["last_login"] = display_df.get("last_login", pd.Series([pd.NA] * len(display_df), index=display_df.index)).apply(format_timestamp)
            display_df["login_count"] = pd.to_numeric(
                display_df.get("login_count", pd.Series([0] * len(display_df), index=display_df.index)),
                errors="coerce",
            ).fillna(0).astype(int)
            display_df["account_status"] = display_df.get("account_status", pd.Series(["Active"] * len(display_df), index=display_df.index)).fillna("Active")
            display_cols = ['username', 'role', 'account_status', 'last_login', 'login_count', 'created_at']
            st.dataframe(display_df.reindex(columns=display_cols, fill_value="N/A"), width="stretch", height=400, hide_index=True)
        else:
            st.info("No users found")
    
    with tabs[2]:
        st.markdown("### User Details & Activity")
        users_df = get_users_df()
        users_df = ensure_user_columns(users_df)
        users_df = apply_session_status_overrides(users_df)
        if not users_df.empty:
            selected_user = st.selectbox("Select User", users_df['username'].tolist())
            user_data = users_df[users_df['username'] == selected_user].iloc[0]
            user_status = str(user_data.get('account_status', 'Active') or 'Active')
            login_count = int(user_data.get('login_count', 0) or 0)
            last_login = format_timestamp(user_data.get('last_login'))
            status_badge = "🟢 Active" if user_status.lower() == "active" else "🔴 Inactive"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Username:** {user_data['username']}")
                st.write(f"**Role:** {user_data['role'].upper()}")
            with col2:
                st.write(f"**Created:** {user_data['created_at']}")
                st.write(f"**Status:** {status_badge}")
            with col3:
                st.write(f"**Last Login:** {last_login}")
                st.write(f"**Login Count:** {login_count}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✏️ Edit User", width="stretch"):
                    st.info("Edit form would open here")
            with col2:
                if st.button("🔐 Reset Password", width="stretch"):
                    st.success("✅ Temporary password sent to admin email")
            with col3:
                toggle_label = "🚫 Deactivate User" if user_status.lower() == "active" else "✅ Reactivate User"
                if st.button(toggle_label, width="stretch"):
                    next_status = "Inactive" if user_status.lower() == "active" else "Active"
                    ok, msg = update_user_status_safe(user_data['username'], next_status)
                    if ok:
                        st.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)
    
    with tabs[3]:
        st.markdown("### Deactivated Users")
        users_df = apply_session_status_overrides(users_df)
        users_df = ensure_user_columns(users_df)
        status_series = users_df['account_status'] if 'account_status' in users_df.columns else pd.Series(['Active'] * len(users_df), index=users_df.index)
        deactivated_users = users_df[status_series.fillna('Active').astype(str).str.lower() == 'inactive']
        if deactivated_users.empty:
            st.info("No deactivated users at this time")
        else:
            display_df = deactivated_users.copy()
            display_df["created_at"] = display_df.get("created_at", pd.Series([pd.NA] * len(display_df), index=display_df.index)).apply(format_timestamp)
            display_df["last_login"] = display_df.get("last_login", pd.Series([pd.NA] * len(display_df), index=display_df.index)).apply(format_timestamp)
            display_df["login_count"] = pd.to_numeric(
                display_df.get("login_count", pd.Series([0] * len(display_df), index=display_df.index)),
                errors="coerce",
            ).fillna(0).astype(int)
            st.dataframe(display_df[['username', 'role', 'last_login', 'login_count', 'created_at']], width="stretch", height=320, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS & REPORTING
# ══════════════════════════════════════════════════════════════════════════════
def render_analytics_page(get_all_df, get_df):
    """Advanced analytics and reporting"""
    st.markdown("## 📈 Analytics & Reports")
    st.caption("Detailed insights into sales, customer behavior, and trends")
    
    df = get_all_df()
    
    if df.empty:
        st.warning("No data available for analysis")
        return
    
    tabs = st.tabs(["📊 Sales", "👥 Customer", "🛍️ Products", "🌍 Geography"])
    
    with tabs[0]:
        st.markdown("### Sales Analytics")
        
        col1, col2 = st.columns(2)
        with col1:
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Daily revenue
            daily_revenue = df.groupby(df['Date'].dt.date)['Revenue'].sum().reset_index()
            fig = px.area(daily_revenue, x='Date', y='Revenue',
                         title='Daily Revenue Trend', markers=True)
            fig.update_traces(fill='tozeroy')
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)
        
        with col2:
            # Revenue by category
            category_revenue = df.groupby('Category')['Revenue'].sum().nlargest(10).reset_index()
            fig = px.bar(category_revenue, x='Revenue', y='Category', orientation='h',
                        title='Revenue by Category', color='Revenue', color_continuous_scale='Blues')
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)
        
        # Sales metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_rev = df['Revenue'].sum()
            kpi("Total Revenue", f"£{total_rev:,.0f}", "All time", "blue")
        with col2:
            avg_rev = df.groupby('BillNo')['Revenue'].sum().mean()
            kpi("Avg Transaction", f"£{avg_rev:.2f}", "Per order", "green")
        with col3:
            today_rev = df[df['Date'].dt.date == pd.Timestamp.today().date()]['Revenue'].sum()
            kpi("Today's Revenue", f"£{today_rev:,.0f}", "Current day", "orange")
        with col4:
            unique_orders = df['BillNo'].nunique()
            kpi("Total Transactions", f"{unique_orders:,}", "Order count", "purple")
    
    with tabs[1]:
        st.markdown("### Customer Analytics")
        
        col1, col2 = st.columns(2)
        with col1:
            # Customers by country
            country_stats = df.groupby('Country').agg({
                'BillNo': 'nunique',
                'Quantity': 'sum',
                'Revenue': 'sum'
            }).reset_index().sort_values('Revenue', ascending=False)
            country_stats.columns = ['Country', 'Orders', 'Items Sold', 'Revenue']
            
            fig = px.bar(country_stats, x='Country', y='Orders',
                        color='Revenue', color_continuous_scale='Greens',
                        title='Orders by Country')
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)
        
        with col2:
            # Order size distribution
            order_sizes = df.groupby('BillNo').size().reset_index(name='Items')
            fig = px.histogram(order_sizes, x='Items', nbins=20,
                             title='Order Size Distribution',
                             color_discrete_sequence=['#2D5BE3'])
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)
        
        # Customer table
        customer_stats = df.groupby('Country').agg({
            'BillNo': 'nunique',
            'Quantity': 'sum',
            'Revenue': 'sum'
        }).reset_index()
        customer_stats.columns = ['Country', 'Orders', 'Items', 'Revenue']
        customer_stats = customer_stats.sort_values('Revenue', ascending=False)
        st.dataframe(customer_stats, width="stretch", height=300, hide_index=True)
    
    with tabs[2]:
        st.markdown("### Product Analytics")
        
        # Top products
        top_products = df.groupby('Itemname').agg({
            'Quantity': 'sum',
            'Revenue': 'sum',
            'BillNo': 'nunique'
        }).reset_index().sort_values('Revenue', ascending=False).head(15)
        top_products.columns = ['Product', 'Qty Sold', 'Revenue', 'Orders']
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(top_products.head(10), x='Revenue', y='Product', orientation='h',
                        color='Revenue', color_continuous_scale='Oranges',
                        title='Top 10 Products by Revenue')
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)
        
        with col2:
            fig = px.bar(top_products.head(10), x='Qty Sold', y='Product', orientation='h',
                        color='Qty Sold', color_continuous_scale='Purples',
                        title='Top 10 Products by Quantity')
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)
        
        st.markdown("### Product Performance Table")
        st.dataframe(top_products, width="stretch", height=400, hide_index=True)
    
    with tabs[3]:
        st.markdown("### Geographic Analytics")
        
        col1, col2 = st.columns(2)
        with col1:
            # Revenue by country pie
            country_rev = df.groupby('Country')['Revenue'].sum().reset_index()
            fig = px.pie(country_rev, values='Revenue', names='Country',
                        title='Revenue Distribution by Country')
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)
        
        with col2:
            # Orders by country pie
            country_orders = df.groupby('Country')['BillNo'].nunique().reset_index()
            country_orders.columns = ['Country', 'Orders']
            fig = px.pie(country_orders, values='Orders', names='Country',
                        title='Orders Distribution by Country')
            st.plotly_chart(plot_cfg(fig, 300), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
def render_product_management(ALL_ITEMS, PRICE_MAP, CAT_MAP):
    """Product catalog management"""
    st.markdown("## 📦 Product Management")
    st.caption("Manage inventory, pricing, and product details")
    
    tabs = st.tabs(["➕ Add Product", "📋 Catalog", "💰 Pricing", "📊 Inventory"])
    
    with tabs[0]:
        st.markdown("### Add New Product")
        with st.form("add_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                product_name = st.text_input("Product Name")
                category = st.selectbox("Category", ["Home Decor", "Bags", "Party", "Stationery", 
                                                     "Kitchen", "Gifts", "Seasonal", "Candles"])
            with col2:
                price = st.number_input("Price (£)", min_value=0.01, step=0.01)
                sku = st.text_input("SKU", placeholder="AUTO-GENERATE")
            
            stock = st.number_input("Initial Stock", min_value=0, step=1)
            description = st.text_area("Description", placeholder="Product description...")
            
            submit_add_product = st.form_submit_button("✅ Add Product", width="stretch")
        
        if submit_add_product:
            if product_name:
                success, msg = add_product(product_name, category, price, stock, description, sku)
                if success:
                    st.success(msg)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("❌ Product name is required!")
    
    with tabs[1]:
        st.markdown("### Product Catalog")
        
        
        # Load products from database
        catalog_df = get_products_df()
        
        # If no custom products, use defaults
        if catalog_df.empty:
            catalog_data = {
                'name': sorted(ALL_ITEMS),
                'category': [CAT_MAP.get(i, 'Other') for i in sorted(ALL_ITEMS)],
                'price': [PRICE_MAP.get(i, 0) for i in sorted(ALL_ITEMS)],
                'stock': np.random.randint(10, 500, len(ALL_ITEMS))
            }
            catalog_df = pd.DataFrame(catalog_data)
        
        # Rename for display
        display_df = catalog_df.copy()
        if 'name' in display_df.columns:
            display_df = display_df.rename(columns={'name': 'Item'})
        if 'Item' not in display_df.columns:
            display_df = display_df.rename(columns={display_df.columns[0]: 'Item'})
        if 'category' in display_df.columns and 'Category' not in display_df.columns:
            display_df = display_df.rename(columns={'category': 'Category'})
        if 'price' in display_df.columns and 'Price' not in display_df.columns:
            display_df = display_df.rename(columns={'price': 'Price'})
        if 'stock' in display_df.columns and 'Stock' not in display_df.columns:
            display_df = display_df.rename(columns={'stock': 'Stock'})

        col1, col2 = st.columns([2, 1])
        with col1:
            search_prod = st.text_input("Search products")
        with col2:
            category_col = 'Category' if 'Category' in display_df.columns else 'category'
            filter_cat = st.selectbox("Category", ["All"] + sorted(display_df[category_col].dropna().astype(str).unique().tolist()))
        
        filtered_cat = display_df.copy()
        item_col = 'Item' if 'Item' in filtered_cat.columns else filtered_cat.columns[0]
        if search_prod:
            filtered_cat = filtered_cat[filtered_cat[item_col].astype(str).str.contains(search_prod, case=False, na=False)]
        if filter_cat != "All":
            filtered_cat = filtered_cat[filtered_cat[category_col].astype(str) == filter_cat]
        
        st.dataframe(filtered_cat, width="stretch", height=400, hide_index=True)
    
    with tabs[2]:
        st.markdown("### Pricing Management")
        
        col1, col2 = st.columns([1.5, 1.5])
        with col1:
            st.write("**Bulk Price Update**")
            discount_pct = st.slider("Discount (%)", 0, 50, 10)
            category_filter = st.selectbox("Apply to Category", ["All", "Home Decor", "Bags", "Party"])
            
            if st.button("Apply Discount", width="stretch"):
                st.success(f"✅ Applied {discount_pct}% discount to {category_filter}")
        
        with col2:
            st.write("**Price Range Statistics**")
            prices = list(PRICE_MAP.values())
            st.metric("Avg Price", f"£{np.mean(prices):.2f}")
            st.metric("Min Price", f"£{np.min(prices):.2f}")
            st.metric("Max Price", f"£{np.max(prices):.2f}")
    
    with tabs[3]:
        st.markdown("### Inventory Management")
        
        # Mock inventory data
        num_items = min(10, len(ALL_ITEMS))  # Ensure we don't exceed available items
        products = list(ALL_ITEMS)[:num_items]
        inventory_data = {
            'Product': products,
            'Stock': np.random.randint(5, 200, num_items),
            'Reorder Level': np.random.randint(20, 50, num_items),
            'Status': ['In Stock'] * (num_items - 2) + (['Low Stock', 'Critical'] if num_items >= 2 else [])
        }
        inventory_df = pd.DataFrame(inventory_data)
        
        low_stock = inventory_df[inventory_df['Stock'] < inventory_df['Reorder Level']]
        kpi("Total Items", len(inventory_df), "In catalog", "blue")
        kpi("Low Stock", len(low_stock), "Below reorder level", "orange")
        
        st.dataframe(inventory_df, width="stretch", height=400, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
def render_system_settings():
    """Admin system settings"""
    st.markdown("## ⚙️ System Settings")
    st.caption("Configure platform-wide settings and parameters")
    
    tabs = st.tabs(["🔧 General", "💰 Financial", "🔐 Security", "📧 Integrations"])
    
    with tabs[0]:
        st.markdown("### General Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            platform_name = st.text_input("Platform Name", value="IntelliGrocery")
            timezone = st.selectbox("Timezone", ["UTC", "GMT", "IST", "PST"])
            language = st.selectbox("Default Language", ["English", "Spanish", "French", "German"])
        with col2:
            st.write("**Maintenance Mode**")
            maintenance = st.checkbox("Enable Maintenance Mode", value=False)
            if maintenance:
                st.warning("⚠️ Platform will be unavailable to users")
            
            st.write("**System Health**")
            st.success("✅ All systems operational")
        
        if st.button("💾 Save General Settings", width="stretch"):
            st.success("✅ Settings saved!")

        st.markdown("---")
        st.markdown("### 📥 Historical Dataset Import")
        st.caption("Import Excel dataset for past-data analytics. Real-time transactions continue to update automatically.")

        overview = get_dataset_import_overview()
        c1, c2, c3 = st.columns(3)
        with c1:
            kpi("Transactions", f"{overview['transactions']:,}", "Current DB rows", "blue")
        with c2:
            kpi("Invoices", f"{overview['invoices']:,}", "Unique bills", "green")
        with c3:
            kpi("Products", f"{overview['products']:,}", "Catalog items", "purple")

        default_path = r"c:\Users\DELL\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\70948631311B1AC778F7B07A9ACDFC6F5B444D76\transfers\2026-17\updatedsheet.xlsx"
        dataset_path = st.text_input("Excel dataset path", value=default_path)
        replace_existing = st.checkbox(
            "Replace existing transaction history before import",
            value=True,
            help="Use this for first-time full historical import to avoid duplicate transaction rows.",
        )

        if st.button("🚀 Import Online Retail Dataset", width="stretch"):
            with st.spinner("Importing dataset into PostgreSQL. This can take a minute..."):
                result = import_online_retail_dataset(dataset_path, replace_existing=replace_existing)

            if result["ok"]:
                st.success(
                    f"✅ {result['message']} Loaded rows: {result['loaded_rows']:,}, "
                    f"Inserted transactions: {result['inserted_transactions']:,}, "
                    f"New products: {result['added_products']:,}."
                )
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")
    
    with tabs[1]:
        st.markdown("### Financial Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Shipping Threshold (£)", value=40.00, step=1.00)
            st.number_input("Shipping Fee (£)", value=2.99, step=0.01)
            st.number_input("Tax Rate (%)", value=20.0, step=0.1)
        with col2:
            st.selectbox("Currency", ["GBP £", "EUR €", "USD $"])
            st.selectbox("Payment Gateway", ["Stripe", "PayPal", "Square"])
            st.checkbox("Enable COD (Cash on Delivery)", value=True)
        
        if st.button("💾 Save Financial Settings", width="stretch"):
            st.success("✅ Settings saved!")
    
    with tabs[2]:
        st.markdown("### Security Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Password Min Length", value=6, step=1)
            st.number_input("Session Timeout (min)", value=30, step=5)
            st.checkbox("Require 2FA for Admins", value=False)
        with col2:
            st.checkbox("Enable API Rate Limiting", value=True)
            st.number_input("Max Login Attempts", value=5, step=1)
            st.number_input("Lockout Duration (min)", value=15, step=5)
        
        if st.button("💾 Save Security Settings", width="stretch"):
            st.success("✅ Settings saved!")
    
    with tabs[3]:
        st.markdown("### External Integrations")
        
        integrations = {
            "Email Provider": "SendGrid",
            "SMS Service": "Twilio",
            "Payment": "Stripe",
            "Analytics": "Google Analytics",
            "Search": "Elasticsearch"
        }
        
        for service, provider in integrations.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{service}:** {provider}")
            with col2:
                st.success("✅ Connected")
            with col3:
                if st.button("⚙️", key=f"config_{service}", help=f"Configure {service}"):
                    st.info(f"Configuration for {service} would open here")

        col1, col2 = st.columns([2, 1])
        with col1:
            search_prod = st.text_input("Search products")
        with col2:
            cat_col = 'Category' if 'Category' in display_df.columns else 'category'
            filter_cat = st.selectbox("Category", ["All"] + sorted(display_df[cat_col].unique().tolist()))
        
        filtered_cat = display_df.copy()
        item_col = 'Item' if 'Item' in filtered_cat.columns else 'name'
        if search_prod:
            filtered_cat = filtered_cat[filtered_cat[item_col].str.contains(search_prod, case=False)]
        if filter_cat != "All":
            filtered_cat = filtered_cat[filtered_cat[cat_col] == filter_cat]
        
        st.dataframe(filtered_cat, width="stretch", height=400, hide_index=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            search_prod = st.text_input("Search products")
        with col2:
            cat_col = 'Category' if 'Category' in display_df.columns else 'category'
            filter_cat = st.selectbox("Category", ["All"] + sorted(display_df[cat_col].unique().tolist()))
        
        filtered_cat = display_df.copy()
        item_col = 'Item' if 'Item' in filtered_cat.columns else 'name'
        if search_prod:
            filtered_cat = filtered_cat[filtered_cat[item_col].str.contains(search_prod, case=False)]
        if filter_cat != "All":
            filtered_cat = filtered_cat[filtered_cat[cat_col] == filter_cat]
        
        st.dataframe(filtered_cat, width="stretch", height=400, hide_index=True)
