# 🐘 PostgreSQL + pgAdmin4 Quick Reference

## 🚀 Quick Start (< 5 minutes)

### Windows
```batch
# Start services
docker-startup.bat start

# Stop services
docker-startup.bat stop

# View status
docker-startup.bat status
```

### Mac/Linux
```bash
chmod +x docker-startup.sh

# Start services
./docker-startup.sh start

# Stop services
./docker-startup.sh stop

# View status
./docker-startup.sh status
```

---

## 📍 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **pgAdmin4** | http://localhost:5050 | admin@intelligrocery.local / AdminPass@2024 |
| **PostgreSQL** | localhost:5432 | intelligrocery / IntelliGrocery@2024 |
| **Streamlit App** | http://localhost:8501 | (User login via app) |

---

## 🔧 Docker Commands

### Container Management
```bash
# List all containers
docker ps

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker logs intelligrocery_db
docker logs intelligrocery_pgadmin

# Execute commands in container
docker exec -it intelligrocery_db psql -U intelligrocery
```

### Database Commands
```bash
# Connect to database
docker exec -it intelligrocery_db psql -U intelligrocery -d intelligrocery

# List databases
\l

# List tables
\dt

# Describe table
\d transactions

# Exit psql
\q
```

---

## 🎯 pgAdmin4 Common Tasks

### 1️⃣ Query Execution
1. Open http://localhost:5050
2. Expand "Servers" → "IntelliGrocery"
3. Right-click Database → "Query Tool"
4. Write and execute SQL

**Example Queries:**
```sql
-- All users
SELECT * FROM users;

-- Monthly revenue
SELECT * FROM monthly_revenue;

-- User statistics
SELECT * FROM user_stats;

-- Top 10 products
SELECT Itemname, COUNT(*) as sales, SUM(Revenue) as total_revenue
FROM transactions
GROUP BY Itemname
ORDER BY total_revenue DESC
LIMIT 10;
```

### 2️⃣ Create Backup
1. Right-click Database → "Backup"
2. Format: Choose "Custom" (recommended)
3. Click Backup
4. File saved to Downloads

### 3️⃣ Restore Backup
1. Right-click Database → "Restore"
2. Select backup file
3. Click Restore

### 4️⃣ View Query Stats
1. Go to "Dashboard" tab
2. See connections, transactions, queries
3. Click "Queries" for slow query log

---

## 🛠️ Troubleshooting

### Container Won't Start
```bash
# View error logs
docker-compose logs

# Clean and restart
docker-compose down -v
docker-compose up -d
```

### Port Already in Use
```bash
# Find what's using port 5432
lsof -i :5432  # Mac/Linux
netstat -ano | findstr :5432  # Windows

# OR change port in docker-compose.yml
ports:
  - "5433:5432"
```

### pgAdmin4 Not Accessible
```bash
# Restart pgAdmin container
docker restart intelligrocery_pgadmin

# Check if it's running
docker ps | grep pgadmin
```

### Connection Refused
```bash
# Ensure PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL is healthy
docker exec intelligrocery_db pg_isready
```

---

## 📊 Useful SQL Queries

### Database Size
```sql
SELECT pg_size_pretty(pg_database_size('intelligrocery')) as db_size;
```

### Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Connection Count
```sql
SELECT count(*) FROM pg_stat_activity;
```

### Kill Long-Running Query
```sql
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
  AND query_start < now() - interval '10 minutes';
```

### Vacuum & Analyze (Maintenance)
```sql
VACUUM ANALYZE;
```

### Reindex Database
```sql
REINDEX DATABASE intelligrocery;
```

---

## 🔐 Security Quick Tips

### Change Default Passwords
1. Edit `.env` file
2. Update DB_PASSWORD and PGADMIN_DEFAULT_PASSWORD
3. Restart containers: `docker-compose restart`

### Enable SSL
```yaml
# In docker-compose.yml
postgres:
  environment:
    POSTGRES_INITDB_ARGS: "-c ssl=on"
```

### Restrict Access
```bash
# Only allow localhost
# In docker-compose.yml ports:
ports:
  - "127.0.0.1:5432:5432"  # PostgreSQL only from localhost
  - "127.0.0.1:5050:80"    # pgAdmin4 only from localhost
```

---

## 📈 Performance Tuning

### Increase Shared Buffers
```yaml
postgres:
  environment:
    POSTGRES_INITDB_ARGS: "-c shared_buffers=256MB -c effective_cache_size=1GB"
```

### Create Index for Queries
```sql
CREATE INDEX idx_user_purchases 
ON purchase_history(username, PurchasedAt DESC);

CREATE INDEX idx_transactions_date_country 
ON transactions(Date, Country);
```

### Monitor Slow Queries
```sql
-- Enable slow query log (> 1 second)
SET log_min_duration_statement = 1000;

-- View slow queries
SELECT 
    query,
    calls,
    mean_time,
    total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

## 🎓 Docker Compose Cheat Sheet

```bash
# Start (background)
docker-compose up -d

# Start (foreground, show logs)
docker-compose up

# Stop
docker-compose down

# Remove volumes (DATA LOSS!)
docker-compose down -v

# View logs
docker-compose logs
docker-compose logs postgres
docker-compose logs pgadmin

# Rebuild images
docker-compose up -d --build

# Scale services
docker-compose up -d --scale postgres=3

# View resource usage
docker stats

# Pull latest images
docker-compose pull

# Network inspect
docker network ls
docker network inspect intelligrocery_intelligrocery_network
```

---

## 📚 File Reference

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main Docker configuration |
| `pgadmin_servers.json` | pgAdmin4 auto-connection config |
| `init_scripts/01-schema.sql` | Database schema (auto-created) |
| `docker-startup.sh` | Startup script (Mac/Linux) |
| `docker-startup.bat` | Startup script (Windows) |
| `.env.example` | Environment template |
| `backend/db_config.py` | Database config module |

---

## 🆘 Getting Help

### View Full Logs
```bash
docker-compose logs --tail=100 postgres
docker-compose logs --tail=100 pgadmin
```

### Connect Directly
```bash
# Interactive PostgreSQL shell
docker exec -it intelligrocery_db psql -U intelligrocery -d intelligrocery

# View server logs
docker exec intelligrocery_db tail -f /var/log/postgresql.log
```

### Check Docker Version
```bash
docker --version
docker-compose --version
```

### Read Official Docs
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [pgAdmin4 Docs](https://www.pgadmin.org/docs/)
- [Docker Docs](https://docs.docker.com/)

---

## ✨ Pro Tips

💡 **Tip 1**: Use pgAdmin4 Query Tool for complex queries (better UI than terminal)

💡 **Tip 2**: Set up automated backups:
```bash
docker exec intelligrocery_db pg_dump -U intelligrocery intelligrocery > backup-$(date +%Y%m%d).sql
```

💡 **Tip 3**: Monitor in real-time:
```bash
docker stats --no-stream
```

💡 **Tip 4**: Export data to CSV from pgAdmin4:
- Query Tool → Results → Right-click → Export

💡 **Tip 5**: Create views in pgAdmin4 for common queries

---

## 🎉 You're Ready!

```bash
# 1. Start services
docker-startup.bat start  # Windows
# OR
./docker-startup.sh start # Mac/Linux

# 2. Access pgAdmin4
# Open: http://localhost:5050

# 3. Run Streamlit app
streamlit run frontend/app.py

# 4. Start shopping or managing!
```

**Happy data managing! 🐘📊**
