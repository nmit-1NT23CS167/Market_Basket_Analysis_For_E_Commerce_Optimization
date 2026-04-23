# 🐘 PostgreSQL + pgAdmin4 Setup Guide

## Overview

The IntelliGrocery project now supports **dual database modes**:

| Feature | SQLite (Default) | PostgreSQL |
|---------|------------------|-----------|
| Setup | Auto (file-based) | Docker Compose |
| Management | Minimal | pgAdmin4 UI |
| Scalability | Single-user | Multi-user |
| Performance | Good | Excellent |
| Backups | Manual | Automated |
| Use Case | Development | Production |

---

## Option 1: Development (SQLite - Default)

**No setup required!** The app automatically creates `data/grocery.db` on first run.

```bash
streamlit run frontend/app.py
```

This is perfect for testing and local development.

---

## Option 2: Production (PostgreSQL + pgAdmin4)

### Prerequisites

- Docker & Docker Compose installed
- Port 5432 available (PostgreSQL)
- Port 5050 available (pgAdmin4)

### Quick Start

#### Step 1: Start Services

```bash
cd IntelliGrocery2
docker-compose up -d
```

This starts:
- 🐘 **PostgreSQL** on `localhost:5432`
- 🔧 **pgAdmin4** on `http://localhost:5050`

#### Step 2: Configure Environment

Create a `.env` file:

```bash
# .env
DB_TYPE=postgres
DB_HOST=localhost
DB_PORT=5432
DB_USER=intelligrocery
DB_PASSWORD=IntelliGrocery@2024
DB_NAME=intelligrocery
```

#### Step 3: Update Requirements

```bash
pip install -r requirements.txt
```

#### Step 4: Update app.py Imports

Edit `frontend/app.py` to use PostgreSQL:

```python
# OLD (SQLite):
from backend.data_layer import init_db, get_df, ...

# NEW (PostgreSQL):
from backend.db_config import DB_TYPE, get_db_connection
from backend.data_layer import init_db, get_df, ...
```

> The connection is auto-detected via `db_config.py`

#### Step 5: Run App

```bash
streamlit run frontend/app.py
```

✅ App now connects to PostgreSQL automatically!

---

## 🔧 pgAdmin4 Web Interface

### Access pgAdmin4

Open in browser: **http://localhost:5050**

### Login Credentials

```
Email:    admin@intelligrocery.local
Password: AdminPass@2024
```

### Connect to Database

1. **Left sidebar** → Right-click "Servers" → "Create" → "Server"
2. **General tab**: Name = "IntelliGrocery"
3. **Connection tab**:
   - Host: `postgres` (Docker network) or `localhost` (external)
   - Port: `5432`
   - User: `intelligrocery`
   - Password: `IntelliGrocery@2024`
   - Database: `intelligrocery`
4. Click **Save**

✅ Database automatically registered on container start!

---

## 📊 pgAdmin4 Features

### Query Execution

1. Click Database → Click Query Tool (⚙️ icon)
2. Write SQL and execute:

```sql
-- View all users
SELECT username, role, created_at FROM users;

-- Monthly revenue
SELECT * FROM monthly_revenue;

-- Top products
SELECT Itemname, COUNT(*) as sales, SUM(Revenue) as revenue
FROM transactions
GROUP BY Itemname
ORDER BY revenue DESC
LIMIT 10;
```

### Monitoring

- **Connections**: See active database connections
- **Locks**: Monitor query locks
- **Activity**: Real-time query execution
- **Logs**: Server and query logs

### Backup

1. Right-click Database → **Backup**
2. Choose format: Custom (recommended) or Tar
3. Saves to local system

### Restore

1. Right-click Database → **Restore**
2. Select backup file
3. Click Restore

---

## 🐳 Docker Commands

### View Logs

```bash
# PostgreSQL logs
docker logs intelligrocery_db

# pgAdmin logs
docker logs intelligrocery_pgadmin
```

### Stop Services

```bash
docker-compose down
```

### Remove Everything (Including Data!)

```bash
docker-compose down -v
```

### Rebuild Containers

```bash
docker-compose down
docker-compose up -d --build
```

---

## 🔄 Migrate from SQLite to PostgreSQL

### 1. Export SQLite Data

```python
import sqlite3
import pandas as pd

# Connect to SQLite
conn = sqlite3.connect('data/grocery.db')

# Export tables
transactions = pd.read_sql_query("SELECT * FROM transactions", conn)
users = pd.read_sql_query("SELECT * FROM users", conn)
purchase_history = pd.read_sql_query("SELECT * FROM purchase_history", conn)

# Save as CSV
transactions.to_csv('transactions.csv', index=False)
users.to_csv('users.csv', index=False)
purchase_history.to_csv('purchase_history.csv', index=False)

conn.close()
```

### 2. Import to PostgreSQL

In pgAdmin4 Query Tool:

```sql
-- Disable constraints temporarily
ALTER TABLE purchase_history DISABLE TRIGGER ALL;

-- Import transactions
COPY transactions (BillNo, Itemname, Quantity, Price, Date, Country, Category)
FROM '/path/to/transactions.csv'
WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- Re-enable constraints
ALTER TABLE purchase_history ENABLE TRIGGER ALL;
```

### 3. Switch to PostgreSQL

Update `.env`:
```
DB_TYPE=postgres
DB_HOST=localhost
DB_PORT=5432
DB_USER=intelligrocery
DB_PASSWORD=IntelliGrocery@2024
DB_NAME=intelligrocery
```

---

## 🔐 Security Checklist

⚠️ **Before Production Deployment:**

- [ ] Change default passwords in `docker-compose.yml`
- [ ] Use strong passwords (20+ chars, mixed case, numbers, symbols)
- [ ] Store credentials in `.env` (add `.env` to `.gitignore`)
- [ ] Use environment variables instead of hardcoded values
- [ ] Enable SSL/TLS for connections
- [ ] Set up automated backups
- [ ] Restrict pgAdmin4 access (firewall, VPN)
- [ ] Enable PostgreSQL authentication (pg_hba.conf)
- [ ] Use read-only replicas for analytics

### .env File (Secure)

```bash
# .env - NEVER commit this!
DB_TYPE=postgres
DB_HOST=prod-postgres.internal
DB_PORT=5432
DB_USER=intelligrocery_prod
DB_PASSWORD=SecureP@ssw0rd2024!
DB_NAME=intelligrocery_prod
PGADMIN_DEFAULT_PASSWORD=AdminSecure@2024!
```

Add to `.gitignore`:
```
.env
.env.local
data/
```

---

## 📈 Performance Tuning

### PostgreSQL Configuration

Edit docker-compose.yml:

```yaml
postgres:
  environment:
    POSTGRES_INITDB_ARGS: >
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c work_mem=16MB
      -c max_connections=100
```

### Create Indexes

```sql
-- Add custom indexes for your queries
CREATE INDEX idx_transactions_date_country 
  ON transactions(Date, Country);

CREATE INDEX idx_purchase_history_user_date 
  ON purchase_history(username, PurchasedAt DESC);

-- Analyze for query planner
ANALYZE transactions;
ANALYZE users;
```

### Monitor Performance

In pgAdmin4:

1. **Tools** → **Server Activity**
2. Check CPU, Memory, Connections
3. Identify slow queries in Logs

---

## 🚨 Troubleshooting

### Error: Port Already in Use

```bash
# Find process on port 5432
lsof -i :5432

# Change port in docker-compose.yml
ports:
  - "5433:5432"
```

### Error: Connection Refused

```bash
# Check PostgreSQL container status
docker ps | grep intelligrocery_db

# View logs
docker logs intelligrocery_db
```

### Error: Database Already Exists

```bash
# Reset everything
docker-compose down -v
docker-compose up -d
```

### pgAdmin4 Not Loading

```bash
# Restart pgAdmin container
docker restart intelligrocery_pgadmin

# Check logs
docker logs intelligrocery_pgadmin
```

### Slow Queries

```sql
-- Find slow queries (log queries > 1 second)
SET log_min_duration_statement = 1000;

-- See query plans
EXPLAIN ANALYZE SELECT * FROM transactions WHERE Country = 'UK';
```

---

## 📚 Useful SQL Queries

### Database Info

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('intelligrocery'));

-- Table sizes
SELECT 
    schemaname, 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity;
```

### Maintenance

```sql
-- Vacuum & analyze (maintenance)
VACUUM ANALYZE;

-- Check table integrity
SELECT * FROM pg_stat_user_tables;

-- Kill long-running queries
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'intelligrocery' AND state = 'active';
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Database Tests

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        env:
          DB_HOST: postgres
          DB_USER: test
          DB_PASSWORD: test
        run: python -m pytest
```

---

## 📖 References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgAdmin4 Documentation](https://www.pgadmin.org/docs/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

---

## ✅ Summary

| Step | Command | Notes |
|------|---------|-------|
| 1. Start Docker | `docker-compose up -d` | Starts PostgreSQL + pgAdmin4 |
| 2. Create `.env` | Set `DB_TYPE=postgres` | Configure connection |
| 3. Install deps | `pip install -r requirements.txt` | Includes psycopg2 |
| 4. Access pgAdmin | `http://localhost:5050` | Manage database visually |
| 5. Run app | `streamlit run frontend/app.py` | Auto-connects to PostgreSQL |

🎉 **Your production database is ready!**
