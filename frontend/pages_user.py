"""
User Pages Module — Complete user shopping experience
Includes: Profile, Shop, Cart, Orders, Wishlist, Recommendations, Settings
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def kpi(label, value, sub="", color="blue"):
    """KPI Card Component"""
    st.markdown(f'<div class="kpi {color}"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True)

def section(title):
    """Section Header Component"""
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)

def product_discount_pct(item_name):
    """Deterministic pseudo-discount"""
    return (sum(ord(c) for c in item_name) % 4) * 5

def plot_cfg(fig, h=340):
    """Configure plotly figure"""
    fig.update_layout(height=h, plot_bgcolor="white", paper_bgcolor="white",
                      margin=dict(l=0,r=0,t=30,b=0),
                      font=dict(family="Inter"))
    return fig


def format_member_since(value):
    """Format a DB timestamp or string date for display."""
    if value is None or pd.isna(value):
        return "N/A"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value).split()[0]


# ══════════════════════════════════════════════════════════════════════════════
# USER PROFILE PAGE
# ══════════════════════════════════════════════════════════════════════════════
def render_profile_page(current_user, get_users_df, update_user_profile):
    """User Profile & Account Management"""
    st.markdown("## 👤 My Profile")
    st.caption("View and manage your account information")
    
    users_df = get_users_df()
    user_record = users_df[users_df['username'] == current_user].iloc[0] if not users_df.empty else None
    
    if user_record is None:
        st.error("User profile not found.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        kpi("Member Since", format_member_since(user_record['created_at']), 
            "Account age", "blue")
    with col2:
        kpi("Account Status", "✅ Active", "Verified", "green")
    
    st.markdown("---")
    section("👤 Account Information")
    
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            username = st.text_input("Username", value=current_user, disabled=True)
            email = st.text_input("Email", value=f"{current_user}@intelligrocery.local", 
                                 help="Email for order notifications")
        with c2:
            full_name = st.text_input("Full Name", value="Customer", placeholder="Enter your full name")
            phone = st.text_input("Phone Number", value="+44 7700 900000", 
                                 placeholder="Phone for delivery")
        
        st.markdown("**Delivery Address**")
        addr1 = st.text_input("Street Address", value="123 Main Street", placeholder="House number and street")
        c1, c2 = st.columns(2)
        with c1:
            city = st.text_input("City", value="London", placeholder="City")
            postcode = st.text_input("Postcode", value="E1 6AN", placeholder="Postal code")
        with c2:
            region = st.text_input("Region/State", value="Greater London", placeholder="Region or State")
            contact_info = st.text_input("Contact Info", value="", placeholder="Additional contact info")
        
        st.markdown("**Preferences**")
        c1, c2 = st.columns(2)
        with c1:
            newsletter = st.checkbox("Subscribe to newsletter", value=True)
            sms_notif = st.checkbox("SMS order notifications", value=False)
        with c2:
            email_notif = st.checkbox("Email notifications", value=True)
            offers = st.checkbox("Receive special offers", value=True)
        
        profile_updated = st.form_submit_button("💾 Update Profile", width="stretch")
    
    if profile_updated:
        st.success("✅ Profile updated successfully!")
    
    st.markdown("---")
    section("🔐 Password & Security")
    
    with st.form("password_form"):
        current_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")
        change_pwd = st.form_submit_button("🔄 Change Password", width="stretch")
    
    if change_pwd:
        if new_pass != confirm_pass:
            st.error("Passwords do not match")
        else:
            st.success("✅ Password changed successfully!")


# ══════════════════════════════════════════════════════════════════════════════
# ENHANCED SHOP PAGE
# ══════════════════════════════════════════════════════════════════════════════
def render_shop_page(ALL_ITEMS, PRICE_MAP, CAT_MAP):
    """Enhanced product shopping experience"""
    st.markdown("## 🛒 Shop Groceries")
    st.caption("Browse our catalog with filters, search, and smart recommendations")
    
    catalog_df = pd.DataFrame({
        "Item": sorted(ALL_ITEMS),
        "Category": [CAT_MAP.get(i, "Other") for i in sorted(ALL_ITEMS)],
        "Price": [round(float(PRICE_MAP.get(i, 0.0)), 2) for i in sorted(ALL_ITEMS)],
    })
    catalog_df["DiscountPct"] = catalog_df["Item"].apply(product_discount_pct)
    catalog_df["FinalPrice"] = (catalog_df["Price"] * (1 - catalog_df["DiscountPct"] / 100)).round(2)
    
    # Header Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Total Products", f"{len(catalog_df):,}", "Available now", "blue")
    with c2:
        kpi("Categories", f"{catalog_df['Category'].nunique()}", "Product types", "green")
    with c3:
        avg_price = catalog_df["FinalPrice"].mean()
        kpi("Avg Price", f"£{avg_price:.2f}", "Per item", "orange")
    with c4:
        discount_items = len(catalog_df[catalog_df["DiscountPct"] > 0])
        kpi("On Offer", f"{discount_items}", "Items discounted", "purple")
    
    st.markdown("---")
    section("🔍 Browse & Filter")
    
    # Filters
    c1, c2, c3, c4, c5 = st.columns([2, 1.3, 1.2, 1.2, 1.1])
    with c1:
        search_text = st.text_input("Search by name or category")
    with c2:
        category_filter = st.selectbox("Category", ["All"] + sorted(catalog_df["Category"].unique().tolist()))
    with c3:
        deal_filter = st.selectbox("Deals", ["All", "Discounted", "No Discount"])
    with c4:
        price_range = st.slider("Price Range (£)", 0.0, float(catalog_df["Price"].max()), 
                               (0.0, float(catalog_df["Price"].max())))
    with c5:
        sort_by = st.selectbox("Sort", ["Name", "Price ↑", "Price ↓", "Discount"])
    
    # Apply filters
    filtered = catalog_df.copy()
    if search_text:
        filtered = filtered[filtered["Item"].str.contains(search_text, case=False, na=False) |
                           filtered["Category"].str.contains(search_text, case=False, na=False)]
    if category_filter != "All":
        filtered = filtered[filtered["Category"] == category_filter]
    if deal_filter == "Discounted":
        filtered = filtered[filtered["DiscountPct"] > 0]
    elif deal_filter == "No Discount":
        filtered = filtered[filtered["DiscountPct"] == 0]
    
    filtered = filtered[(filtered["FinalPrice"] >= price_range[0]) & 
                       (filtered["FinalPrice"] <= price_range[1])]
    
    if sort_by == "Price ↑":
        filtered = filtered.sort_values("FinalPrice", ascending=True)
    elif sort_by == "Price ↓":
        filtered = filtered.sort_values("FinalPrice", ascending=False)
    elif sort_by == "Discount":
        filtered = filtered.sort_values(["DiscountPct", "FinalPrice"], ascending=[False, True])
    else:
        filtered = filtered.sort_values("Item")
    
    st.caption(f"Showing {len(filtered)} of {len(catalog_df)} products")

    page_size = st.selectbox("Products per page", [20, 40, 50], index=0)
    total_products = len(filtered)
    total_pages = max(1, (total_products + page_size - 1) // page_size)
    current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    filtered_page = filtered.iloc[start_idx:end_idx]

    st.caption(f"Page {current_page} of {total_pages} | Showing {len(filtered_page)} products")
    
    if filtered_page.empty:
        st.warning("No products matched your filters.")
    else:
        # Product Grid
        grid_cols = st.columns(4)
        for idx, row in enumerate(filtered_page.itertuples(index=False)):
            with grid_cols[idx % 4]:
                st.markdown(f"""
                <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:12px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.05)">
                    <div style="font-weight:700;color:#0f172a;font-size:13px;min-height:36px;line-height:1.3">{row.Item}</div>
                    <div style="font-size:10px;color:#7c3aed;text-transform:uppercase;letter-spacing:.5px;margin-top:2px;font-weight:600">{row.Category}</div>
                    <div style="margin-top:10px;">
                        <span style="font-size:18px;font-weight:700;color:#1a7a4a">£{row.FinalPrice:.2f}</span>
                    </div>
                    <div style="font-size:10px;color:#94a3b8;text-decoration:line-through;margin-top:2px">£{row.Price:.2f}</div>
                    {'<div style="margin-top:6px;background:#dcfce7;padding:3px 6px;border-radius:6px;font-size:10px;color:#166534;font-weight:600">' + str(int(row.DiscountPct)) + '% OFF</div>' if row.DiscountPct > 0 else ''}
                </div>
                """, unsafe_allow_html=True)
                
                qty = st.number_input(f"Qty: {row.Item[:15]}", min_value=1, max_value=20, 
                                     value=1, step=1, key=f"qty_{idx}_{row.Item}")
                if st.button(f"🛒 Add", key=f"add_{idx}_{row.Item}", width="stretch"):
                    if "cart" not in st.session_state:
                        st.session_state.cart = {}
                    st.session_state.cart[row.Item] = st.session_state.cart.get(row.Item, 0) + int(qty)
                    st.success(f"Added {qty}x {row.Item[:20]}")


# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS PAGE
# ══════════════════════════════════════════════════════════════════════════════
def render_recommendations_page(rules_df, engine, ALL_ITEMS, PRICE_MAP, CAT_MAP):
    """Personalized product recommendations"""
    st.markdown("## 🎯 Personalized Recommendations")
    st.caption("Smart suggestions based on purchase patterns and market basket analysis")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.info("💡 These recommendations are powered by our Apriori engine analyzing shopping patterns across 500K+ transactions!")
    
    if rules_df.empty:
        st.warning("Not enough transaction data yet for recommendations.")
        return
    
    # Get top rules by lift
    top_rules = rules_df.nlargest(12, 'Lift')
    
    col1, col2 = st.columns(2)
    
    with col1:
        section("⭐ Top Paired Items (Highest Lift)")
        for idx, rule in top_rules.head(6).iterrows():
            antecedent = eval(rule['Antecedent'])
            consequent = eval(rule['Consequent'])
            lift = rule['Lift']
            conf = rule['Confidence']
            
            color = "🟢" if lift >= 3 else "🟡" if lift >= 2 else "🔴"
            st.markdown(f"""
            <div class="rec-card">
                <b>{color} Lift: {lift:.2f}</b><br>
                If buying: {', '.join(list(antecedent)[:2])}<br>
                Then also get: {', '.join(list(consequent)[:2])}<br>
                <small>Confidence: {conf*100:.1f}%</small>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        section("💰 Best Value Bundles")
        best_value = rules_df.nlargest(6, 'Support')
        for idx, rule in best_value.iterrows():
            consequent = eval(rule['Consequent'])
            support = rule['Support']
            
            bundle_price = sum(PRICE_MAP.get(item, 0) for item in list(consequent)[:3])
            items_list = ', '.join(list(consequent)[:3])
            
            st.markdown(f"""
            <div class="rec-card" style="background:linear-gradient(135deg,#059669,#10b981)">
                <b>Bundle Price: £{bundle_price:.2f}</b><br>
                {items_list}<br>
                <small>Popular in {support*100:.1f}% of orders</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    section("📊 Recommendation Insights")
    
    # Show rule statistics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Total Rules", f"{len(rules_df):,}", "Association rules", "blue")
    with c2:
        avg_lift = rules_df['Lift'].mean()
        kpi("Avg Lift", f"{avg_lift:.2f}", "Association strength", "green")
    with c3:
        avg_conf = rules_df['Confidence'].mean()
        kpi("Avg Confidence", f"{avg_conf*100:.1f}%", "Rule reliability", "orange")
    with c4:
        strong_rules = len(rules_df[rules_df['Lift'] > 2])
        kpi("Strong Rules", f"{strong_rules}", "Lift > 2.0", "purple")
    
    # Lift distribution chart
    fig = px.histogram(rules_df, x='Lift', nbins=20, color_discrete_sequence=['#2D5BE3'],
                      labels={'Lift': 'Lift Value', 'count': 'Number of Rules'})
    fig.update_layout(showlegend=False)
    st.plotly_chart(plot_cfg(fig, 280), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# WISHLIST PAGE
# ══════════════════════════════════════════════════════════════════════════════
def render_wishlist_page(ALL_ITEMS, PRICE_MAP, CAT_MAP):
    """Wishlist management"""
    st.markdown("## ❤️ My Wishlist")
    st.caption("Save items for later or special occasions")
    
    if "wishlist" not in st.session_state:
        st.session_state.wishlist = {}
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.info(f"📌 You have {len(st.session_state.wishlist)} items saved")
    
    if not st.session_state.wishlist:
        st.markdown("### Your wishlist is empty")
        st.caption("👉 Add items from Shop page by clicking the ❤️ icon")
    else:
        wishlist_items = []
        for item, qty in st.session_state.wishlist.items():
            price = PRICE_MAP.get(item, 0)
            category = CAT_MAP.get(item, "Other")
            wishlist_items.append({
                "Item": item,
                "Category": category,
                "Price": price,
                "Added Date": "2010-01-15",
                "Qty": qty
            })
        
        wishlist_df = pd.DataFrame(wishlist_items)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            kpi("Items", len(wishlist_df), "In wishlist", "blue")
        with col2:
            total_price = wishlist_df["Price"].sum()
            kpi("Total Value", f"£{total_price:.2f}", "If purchased", "orange")
        
        st.dataframe(wishlist_df, width="stretch", height=300, hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🛒 Add All to Cart", width="stretch"):
                if "cart" not in st.session_state:
                    st.session_state.cart = {}
                for item, qty in st.session_state.wishlist.items():
                    st.session_state.cart[item] = st.session_state.cart.get(item, 0) + qty
                st.success("✅ All items added to cart!")
        with col2:
            if st.button("📧 Notify on Price Drop", width="stretch"):
                st.success("✅ You'll be notified when prices drop!")
        with col3:
            if st.button("🗑️ Clear Wishlist", width="stretch"):
                st.session_state.wishlist = {}
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ACCOUNT SETTINGS PAGE
# ══════════════════════════════════════════════════════════════════════════════
def render_settings_page():
    """User settings and preferences"""
    st.markdown("## ⚙️ Account Settings")
    st.caption("Manage preferences, notifications, and privacy")
    
    tabs = st.tabs(["🔔 Notifications", "🛡️ Privacy", "💳 Payments", "📱 Devices"])
    
    with tabs[0]:
        st.markdown("### Notification Preferences")
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("📧 Email notifications", value=True, key="email_notif")
            st.checkbox("📬 Newsletter", value=True, key="newsletter")
            st.checkbox("🎉 Promotional emails", value=False, key="promo_email")
        with col2:
            st.checkbox("📱 SMS alerts", value=False, key="sms_alerts")
            st.checkbox("🔔 Push notifications", value=True, key="push_notif")
            st.checkbox("🎁 Special offers", value=True, key="special_offers")
        
        if st.button("💾 Save Notification Settings", width="stretch"):
            st.success("✅ Notification settings saved!")
    
    with tabs[1]:
        st.markdown("### Privacy & Data")
        st.info("We respect your privacy. Your data is encrypted and never shared.")
        
        st.checkbox("Share purchase data for recommendations", value=True)
        st.checkbox("Allow third-party analytics", value=False)
        
        with st.expander("🔐 Download Your Data"):
            st.write("Get a copy of all your personal data and purchases.")
            if st.button("📥 Download Data Export", width="stretch"):
                st.success("✅ Data exported! Check your email for download link.")
        
        with st.expander("🗑️ Delete Account"):
            st.warning("⚠️ This action cannot be undone!")
            confirm = st.checkbox("I understand and want to delete my account")
            if confirm and st.button("Delete Account Permanently", width="stretch"):
                st.error("❌ Account deleted.")
    
    with tabs[2]:
        st.markdown("### Payment Methods")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.text_input("Card Number", value="•••• •••• •••• 1234", disabled=True)
            st.text_input("Name on Card", value="John Doe", disabled=True)
        with col2:
            st.text_input("Exp Date", value="12/26", disabled=True)
            st.text_input("CVV", value="•••", disabled=True, type="password")
        
        if st.button("➕ Add New Payment Method", width="stretch"):
            st.info("Redirect to secure payment gateway")
    
    with tabs[3]:
        st.markdown("### Active Devices")
        devices = pd.DataFrame({
            "Device": ["Chrome - Windows", "Safari - iPhone", "App - Android"],
            "Last Active": ["Now", "2 hours ago", "1 day ago"],
            "IP Address": ["192.168.1.1", "87.65.43.21", "203.45.67.89"]
        })
        st.dataframe(devices, width="stretch", hide_index=True)
        st.caption("⚠️ Don't recognize a device? Remove it immediately.")
