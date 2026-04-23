# 🛒 IntelliGrocery - Complete User & Admin System

## 📋 System Overview

This is a complete e-commerce MBA Analytics platform with dual roles: **Users** (shoppers) and **Admins** (managers).

### Architecture
```
frontend/
  ├── app.py                 # Main router & Streamlit app
  ├── pages_user.py          # All user-facing pages
  ├── pages_admin.py         # All admin management pages
backend/
  ├── data_layer.py          # Database & auth functions  
  ├── apriori_engine.py      # MBA algorithm
data/
  └── grocery.db             # SQLite database
```

---

## 👤 USER PAGES (7 pages)

### 1. **👤 My Profile**
- View account information
- Edit delivery address
- Manage notification preferences
- Update account settings

### 2. **🛒 Shop** 
- Browse product catalog
- Advanced search & filtering
- Filter by category, price range, discounts
- Smart product grid with pricing display
- Add items to cart with quantity control

### 3. **🎯 Recommendations**
- AI-powered product suggestions using Apriori rules
- Personalized recommendations based on cart items
- Product co-occurrence heatmap
- Confidence & Lift scores for recommendations

### 4. **❤️ Wishlist**
- Save favorite items for later
- Track wishlist value
- Add all items to cart at once
- Price drop notifications

### 5. **🧺 My Cart**
- Review cart items
- Update quantities
- See item breakdown & totals
- Proceed to checkout
- Free delivery threshold (£40)
- Multiple payment methods (COD, Card, UPI)

### 6. **📜 My Orders**
- View purchase history
- Order statistics (count, items, spending)
- Download invoices
- Track order status

### 7. **⚙️ Settings**
- **Notifications**: Email, SMS, Push, Newsletter
- **Privacy**: Data sharing, analytics, account deletion  
- **Payments**: Manage saved cards
- **Devices**: View active login devices

---

## 🛡️ ADMIN PAGES (6 main sections)

### 1. **📊 Dashboard**
- Real-time KPIs (Users, Orders, Revenue, etc.)
- Monthly revenue & order trends
- User role distribution  
- Top products & countries
- Platform statistics

### 2. **📈 Analytics & Reports**
**Sales Tab:**
- Daily/monthly revenue trends
- Revenue by category
- Sales performance metrics

**Customer Tab:**
- Orders by geography
- Customer order size distribution
- Regional statistics

**Product Tab:**
- Top 15 products by revenue & quantity
- Product performance table
- Category breakdown

**Geography Tab:**
- Revenue & orders distribution
- Country-wise sales pie charts
- Regional insights

### 3. **👥 User Management**
- **Create User**: Add new accounts (user/admin/moderator roles)
- **All Users**: Search & filter by username/role
- **User Details**: View individual user profiles, login stats
- **Deactivated Users**: Manage suspended accounts

### 4. **📦 Product Management**
- **Add Product**: Create new inventory items
- **Catalog**: Browse all products with filters
- **Pricing**: Bulk price updates, apply discounts
- **Inventory**: Stock levels, reorder alerts

### 5. **⚙️ System Settings**
- **General**: Platform name, timezone, maintenance mode
- **Financial**: Shipping fees, tax rates, currency, payment gateway
- **Security**: Password policies, session timeouts, 2FA, rate limiting
- **Integrations**: Email, SMS, Payment, Analytics, Search services

### 6. **🔬 Algorithm Pages** (6 pages - existing MBA analysis)
- Exploratory Data Analysis
- Transaction Encoding & Sparse Matrix Visualization
- Apriori Mining with Pass Statistics
- Rules Analysis with Lift/Confidence Heatmaps
- Recommendation Engine (Coverage-weighted Scoring)
- Incremental Learning Simulation
- Sensitivity Analysis (Support×Confidence grid)
- Real-Time Transaction Simulation
- Optimization Summary (9 optimizations)

---

## 🔐 Authentication

### Default Credentials
```
User Account:
  Username: testuser
  Password: testpass

Admin Account:
  Username: admin
  Password: admin123
```

### Login Flow
1. Two tabs: "👤 User Login" and "🛡️ Admin Login"
2. Role-based separation (users can't access admin pages)
3. Session management with logout
4. Password hashing with SHA256

---

## 🎨 Design System

### Color Palette
```python
BLUE   = "#2D5BE3"   # Primary (Charts, CTA)
GREEN  = "#1A7A4A"   # Success (Revenue, Stock)
ORANGE = "#E35D2D"   # Warning (Alerts, Discounts)
PURPLE = "#9A3DD4"   # Accent (Rules, Analytics)
AMBER  = "#C0831A"   # Secondary (Time, Metrics)
TEAL   = "#2D9DC0"   # Alternative (Trends)
```

### Components
- **KPI Card**: Colorful metric boxes with labels
- **Section Header**: Divider with title
- **Recommendation Card**: Gradient box with rule details
- **Product Grid**: 4-column responsive layout
- **Data Tables**: Sortable, filterable, exportable

---

## 🔄 Data Flow

```
User Action (Shop/Cart) 
  ↓
Session State Update (st.session_state)
  ↓
Database Write (record_user_purchase)
  ↓
Admin Views Updated (via @st.cache_data)
  ↓
Analytics Refresh (Revenue, Orders, Trends)
```

---

## 📦 Features by Role

### User Features
✅ Browse products (100+ items across 8 categories)  
✅ Advanced search & filtering  
✅ Smart recommendations (Apriori-powered)  
✅ Wishlist management  
✅ Shopping cart  
✅ Checkout (3 payment methods)  
✅ Order history  
✅ Account management  
✅ Notification preferences  

### Admin Features
✅ Comprehensive dashboard  
✅ User account management  
✅ Product & inventory management  
✅ Sales analytics (daily, monthly, by category)  
✅ Customer behavior analytics  
✅ Geographic sales breakdown  
✅ System configuration  
✅ Payment gateway integration  
✅ Security settings  
✅ Advanced MBA algorithms (Apriori, Rules mining)  

---

## 🚀 Deployment Checklist

- [ ] Configure `PRICE_MAP` in `data_layer.py` with real prices
- [ ] Update product categories in `CATALOGUE`
- [ ] Set up database backups (`.db` files)
- [ ] Configure email service for notifications
- [ ] Set payment gateway API keys in `.env`
- [ ] Test user registration flow
- [ ] Verify admin dashboard calculations
- [ ] Load historical transaction data
- [ ] Configure minimum thresholds (support, confidence)
- [ ] Set up analytics reports

---

## 📊 Algorithm Pipeline

1. **Apriori Mining**: Frequent itemsets with anti-monotone pruning
2. **Association Rules**: Support, Confidence, Lift, Conviction, Leverage
3. **Recommendations**: Coverage-weighted scoring algorithm
4. **Incremental Learning**: Real-time rule evolution
5. **Sensitivity Analysis**: Parameter impact visualization

---

## 🔗 API Integration Points

- **Authentication**: `create_user()`, `authenticate_user()`
- **Products**: `ALL_ITEMS`, `PRICE_MAP`, `CAT_MAP`
- **Orders**: `record_user_purchase()`, `get_user_purchases_df()`
- **Analytics**: `get_monthly_revenue()`, `get_country_counts()`
- **Recommendations**: `engine.recommend(cart_items, top_n)`

---

## 📱 Responsive Design

- Mobile-friendly layout with `st.columns()`
- Adaptive grid (3-column for desktop, 1 for mobile)
- Touch-friendly buttons (wide, well-spaced)
- Sidebar collapses on small screens
- Charts scale automatically

---

## 🎯 Next Steps

1. Add image uploads for products
2. Implement email notifications
3. Add real payment gateway
4. Multi-language support
5. Dark mode theme
6. Mobile app (React Native)
7. AI chatbot support
8. Advanced inventory forecasting

---

## 📞 Support

For issues or feature requests, contact the development team.

**Version**: 3.0  
**Last Updated**: 2024  
**Tech Stack**: Streamlit, Pandas, Plotly, SQLite, Apriori  
