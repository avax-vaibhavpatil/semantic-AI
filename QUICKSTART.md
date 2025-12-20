# Quick Start Guide

Get your Auto Semantic Project up and running in 5 minutes! ⚡

## Prerequisites Check

Before starting, ensure you have:
- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] OpenAI API key
- [ ] Database connection string

## 🚀 Fast Setup (3 Steps)

### Step 1: Install Dependencies

```bash
# Using Make (recommended)
make install

# OR manually
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
```

### Step 2: Configure Environment

Create `backend/.env` file:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

**Quick Database URL Examples:**
- PostgreSQL: `postgresql://user:pass@localhost:5432/dbname`
- MySQL: `mysql+pymysql://user:pass@localhost:3306/dbname`
- SQLite: `sqlite:///./test.db`

### Step 3: Create Semantic Layer

**Option A: Generate from DBT Manifest** (if you have DBT)

```bash
make generate-semantic MANIFEST=/path/to/your/dbt/target/manifest.json
```

**Option B: Create Manually** (quick test)

Create `backend/metadata/semantic.json`:

```json
{
  "tables": {
    "your_table_name": {
      "description": "Description of your table",
      "columns": {
        "id": {"type": "dimension"},
        "name": {"type": "dimension"},
        "amount": {"type": "measure"},
        "created_at": {"type": "date"}
      },
      "dimensions": ["id", "name"],
      "measures": ["amount"],
      "time_columns": ["created_at"],
      "derived_measures": [],
      "quality_rules": []
    }
  }
}
```

## ▶️ Run the Project

**Terminal 1 - Backend:**
```bash
make backend
# OR
cd backend && ./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
make frontend
# OR
cd frontend && ./start_frontend.sh
```

## 🎯 Test It Out

1. Open browser: http://localhost:3000
2. Ask a question: "Show me all records from your_table_name"
3. See the magic! ✨

## ✅ Verify Setup

Check backend health:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"ok": true, "semantic_loaded": true}
```

## 📝 Example Questions

Once running, try asking:
- "Show me the top 10 records"
- "What is the total amount?"
- "Group by name and show count"
- "Show records from last month"

## 🔧 Troubleshooting

### Backend won't start?
1. Check `.env` file exists in `backend/` directory
2. Verify `OPENAI_API_KEY` is set
3. Test database connection: `python -c "from backend.db_connector import get_engine; print(get_engine())"`

### Frontend can't connect?
1. Ensure backend is running on port 8000
2. Check browser console for errors
3. Verify CORS settings in `sql_agent.py`

### "Semantic JSON not found"?
1. Create `backend/metadata/` directory
2. Add `semantic.json` file (see Step 3 above)
3. Restart backend server

## 🎓 Next Steps

- [ ] Read full [README.md](README.md) for detailed documentation
- [ ] Customize semantic layer for your database schema
- [ ] Modify prompts in `backend/prompts.py` for better SQL generation
- [ ] Add more tables and relationships to semantic layer

## 📚 Key Files to Know

| File | Purpose |
|------|---------|
| `backend/.env` | Configuration (API keys, DB) |
| `backend/metadata/semantic.json` | Semantic layer definition |
| `backend/prompts.py` | OpenAI prompt templates |
| `frontend/pages/index.js` | UI component |

## 🆘 Need Help?

- Check [README.md](README.md) troubleshooting section
- Verify all prerequisites are met
- Check terminal logs for specific errors

---

**You're all set! Happy querying! 🎉**



