# 🚀 Quick Start Guide - IntelliGrocery

## Prerequisites

- Python 3.8+
- Git
- Virtual Environment (recommended)

## Installation & Setup

### 1. Clone or Navigate to Project
```bash
cd IntelliGrocery2
```

### 2. Create Virtual Environment
```bash
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
The database is auto-created on first run. It includes:
- Pre-seeded transaction data (500K+ rows)
- Default admin account (admin/admin123)
- Default user accounts
- Product catalog (100+ items)

## Running the Application

### Start Streamlit Server
```bash
streamlit run frontend/app.py
```

The app will open at: **http://localhost:8501**

## Login Credentials

### User Account (Regular Shopper)
```
Username: testuser
Password: testpass
```

### Admin Account (Manager/Analytics)
```
Username: admin
Password: admin123
```

---

## 🎯 First Time User Walkthrough

### As a Regular User:
1. **Login** with testuser/testpass
2. **Browse Shop** - Explore 100+ products across 8 categories
3. **Add to Cart** - Click "Add to Cart" on any product
4. **View Cart** - Check quantities and totals in "My Cart"
5. **Checkout** - Select delivery country & payment method
6. **Order History** - View past purchases in "My Orders"
7. **Get Recommendations** - AI suggests items based on rules mining
8. **Save Wishlist** - Add favorites to wishlist for later

### As an Admin:
1. **Login** with admin/admin123
2. **View Dashboard** - See real-time KPIs and revenue trends
3. **Check Analytics** - Drill down into sales by product/region
4. **Manage Users** - Create new accounts and view user stats
5. **Manage Products** - View inventory and pricing
6. **Configure Settings** - Adjust system parameters
7. **Explore Algorithms** - Run MBA analysis on transaction data

---

## 📁 Project Structure

```
IntelliGrocery2/
├── frontend/
│   ├── app.py                 # Main Streamlit app (entry point)
│   ├── pages_user.py          # User page components
│   └── pages_admin.py         # Admin page components
│
├── backend/
│   ├── data_layer.py          # Database & auth functions
│   ├── apriori_engine.py      # MBA algorithm implementation
│   └── __pycache__/
│
├── data/
│   └── grocery.db             # SQLite database (auto-created)
│
├── requirements.txt           # Python dependencies
├── README.md                  # Original project README
└── ADMIN_USER_GUIDE.md        # Complete feature guide
```

---

## 🎨 Key Pages

### User Pages (7)
1. 👤 My Profile - Account settings
2. 🛒 Shop - Product catalog
3. 🎯 Recommendations - AI suggestions
4. ❤️ Wishlist - Saved items
5. 🧺 My Cart - Shopping cart
6. 📜 My Orders - Order history
7. ⚙️ Settings - Preferences

### Admin Pages (6)
1. 📊 Dashboard - Real-time metrics
2. 📈 Analytics - Sales & customer insights
3. 👥 User Mgmt - Account management
4. 📦 Products - Inventory management
5. ⚙️ Settings - System configuration
6. 🔬 Algorithms - MBA analysis tools

---

## 🛠️ Common Tasks

### Create a New User Account
1. Login as admin
2. Go to "👥 User Mgmt" → "➕ Create User"
3. Enter username, password, and role
4. Click "✅ Create User"

### View Sales Analytics
1. Login as admin
2. Click "📈 Analytics"
3. Switch between Sales/Customer/Product/Geography tabs
4. Charts auto-update with filtered data

### Browse Products (User)
1. Go to "🛒 Shop"
2. Use search box, category filters, price range
3. Sort by name, price, or discount
4. Click "🛒 Add" to purchase

### Set Product Discount
1. Login as admin
2. Go to "📦 Products" → "💰 Pricing"
3. Select category and discount percentage
4. Click "Apply Discount"

---

## ⚙️ Configuration

### Modify Apriori Parameters (Admin)
In the sidebar, when logged in as admin:
- **Min Support**: Lower = more rules (default 0.02)
- **Min Confidence**: Lower = weaker rules (default 0.15)
- **Min Lift**: Higher = only strong rules (default 1.5)
- **Max Itemset Len**: Max items per rule (default 4)

### Country Filter
Select country to view region-specific data:
- United Kingdom (default)
- Germany
- France
- All (all countries)

---

## 🔄 Troubleshooting

### Port Already in Use
If port 8501 is in use:
```bash
streamlit run frontend/app.py --server.port 8502
```

### Database Issues
If you get database errors:
1. Delete `data/grocery.db`
2. Restart the app (it will recreate the database)
3. Re-login

### Slow Performance
1. Lower the **Min Support** threshold (load fewer rules)
2. Reduce **Max Itemset Len** (fewer combinations)
3. Clear cache with "🔄 Refresh" button in sidebar

### Login Failed
- Verify username/password are correct
- Check you're using User Login for regular accounts
- Use Admin Login for admin accounts only

---

## 📊 Database

### Database File
- Location: `data/grocery.db`
- Type: SQLite3
- Auto-created on startup

### Tables
1. **transactions** - E-commerce transaction data
2. **users** - User accounts (admin/user)
3. **purchase_history** - User purchase records

### Seeded Data
- 500K+ transaction records
- 100+ products across 8 categories
- 3 countries (UK, Germany, France)
- 2+ years of transaction history

---

## 🔐 Security Notes

⚠️ **Development Only**: Change default passwords before deployment
- Update `admin/admin123` in `backend/data_layer.py`
- Use environment variables for credentials
- Enable HTTPS in production
- Add 2FA for admin accounts

---

## 📈 Performance Tips

1. **Caching**: Data is cached for 30 seconds (sidebar: "🔄 Refresh" to clear)
2. **Filters**: Use country/category filters to reduce data
3. **Parameters**: Increase support threshold for faster Apriori
4. **Charts**: Disable unnecessary visualizations for speed

---

## 🎓 Learning Resources

### Apriori Algorithm
- Frequent itemsets: Items bought together ≥2%
- Rules: If item A → likely to buy item B
- Lift: How much more likely (>1.0 = associated)
- Confidence: Probability of consequence

### Use Cases
- Product recommendations
- Cross-selling strategies
- Store layout optimization
- Seasonal bundle promotions

---

## 📞 Support & Issues

### Error: "No data found"
- Admin needs to run Apriori first
- Lower thresholds if no rules generated
- Check country filter is correct

### Chart Not Displaying
- Refresh cache: Sidebar "🔄 Refresh"
- Check data is loaded (see KPIs)
- Try adjusting parameters

### Slow Algorithm Execution
- Reduce dataset (filter by country)
- Increase Min Support (e.g., 0.05 instead of 0.02)
- Reduce Max Itemset Len (e.g., 3 instead of 4)

---

## 🚀 Next Steps

1. ✅ Install and run the app
2. ✅ Login as user - try shopping
3. ✅ Login as admin - explore analytics
4. ✅ Create new user account
5. ✅ Adjust parameters and see insights
6. ✅ Generate recommendations
7. ✅ View sales analytics

---

**Happy Shopping & Analyzing! 🛒📊**

For detailed feature documentation, see [ADMIN_USER_GUIDE.md](ADMIN_USER_GUIDE.md)
