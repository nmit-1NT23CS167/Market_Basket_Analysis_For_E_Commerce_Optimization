# Database Setup Summary

## Quick Overview

**IntelliGrocery** now supports two database backends:

### 🟢 Development: SQLite (Default)
```bash
# Just run - no setup needed
streamlit run frontend/app.py
```
- ✅ Instant setup
- ✅ No dependencies
- ✅ Perfect for testing

### 🐘 Production: PostgreSQL + pgAdmin4
```bash
# Set environment
export DB_TYPE=postgres

# Start services
docker-compose up -d

# Run app
streamlit run frontend/app.py
```
- ✅ Scalable multi-user
- ✅ Visual DB management (pgAdmin4)
- ✅ Advanced monitoring
- ✅ Professional backups

---

## Files Added

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Docker setup for PostgreSQL + pgAdmin4 |
| `pgadmin_servers.json` | Auto-connection config for pgAdmin4 |
| `init_scripts/01-schema.sql` | Database schema (auto-created) |
| `backend/db_config.py` | Database configuration module |
| `.env.example` | Environment template (copy to `.env`) |
| `POSTGRESQL_PGADMIN_GUIDE.md` | Complete setup & usage guide |

---

## Current Status

✅ **SQLite** (Active) - Works immediately  
✅ **PostgreSQL** (Ready) - Requires Docker + `.env` configuration  
✅ **pgAdmin4** (Ready) - Web interface on `http://localhost:5050`

---

## Next Steps

### To Keep Using SQLite
👉 No action needed! It already works.

### To Switch to PostgreSQL

1. **Install Docker** (if not already installed)
   ```bash
   # Windows/Mac: Download Docker Desktop
   # Linux: sudo apt-get install docker.io docker-compose
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env to set DB_TYPE=postgres
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Access pgAdmin4**
   ```
   http://localhost:5050
   Email: admin@intelligrocery.local
   Password: AdminPass@2024
   ```

5. **Run App**
   ```bash
   pip install -r requirements.txt
   streamlit run frontend/app.py
   ```

---

## Database Architecture

```
Streamlit App (frontend/app.py)
    ↓
Database Config (backend/db_config.py)
    ├→ SQLite: data/grocery.db
    └→ PostgreSQL: postgres:5432
         ↓
      pgAdmin4: localhost:5050 (UI)
```

---

## Security Notes

⚠️ **Development Only** - Change these before production:
- Default PostgreSQL password: `IntelliGrocery@2024`
- Default pgAdmin password: `AdminPass@2024`
- See `POSTGRESQL_PGADMIN_GUIDE.md` for security checklist

---

## Troubleshooting

**Q: Docker not found?**  
A: Install Docker Desktop (Windows/Mac) or docker.io (Linux)

**Q: Port 5432 already in use?**  
A: Edit `docker-compose.yml` port mapping to `5433:5432`

**Q: Can't connect to pgAdmin4?**  
A: Ensure Docker containers are running: `docker ps`

**Q: Need to migrate from SQLite to PostgreSQL?**  
A: See "Migrate from SQLite to PostgreSQL" in `POSTGRESQL_PGADMIN_GUIDE.md`

---

## Documentation

- **Setup & Usage**: See `POSTGRESQL_PGADMIN_GUIDE.md`
- **Quick Start**: See `QUICKSTART.md`
- **Complete Features**: See `ADMIN_USER_GUIDE.md`

---

**Ready to get started? Choose your path above! 🚀**
