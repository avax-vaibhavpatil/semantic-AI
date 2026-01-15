# Auto-Semantic BI Platform — Local Setup Guide

This guide explains how to run the **entire analytics pipeline locally**, including:

```
DBT Manifest Reader → Inference Engine → Semantic JSON Generator →
SQL Agent (FastAPI) → React/Next.js BI UI
```

You can fully test AI-driven analytics on your laptop with real SQL execution.

---

# 📁 1. Project Structure

```
auto-semantic/
│
├── backend/
│   ├── manifest_reader.py
│   ├── inference_engine.py
│   ├── semantic_generator.py
│   ├── sql_agent.py
│   ├── sql_validator.py
│   ├── db_connector.py
│   ├── prompts.py
│   ├── requirements.txt
│   └── metadata/
│       ├── metadata.json        (generated)
│       ├── inferred.json        (generated)
│       └── semantic.json        (generated)
│
└── frontend/
    ├── package.json
    └── pages/
        └── index.js
```

---

# 🧰 2. Prerequisites

Install these tools:

### Required
- Python 3.10+
- Node.js 18+
- npm or yarn
- Docker (for Postgres)
- Git

---

# 🗄️ 3. Start Local Postgres

Run Postgres in Docker:

```bash
docker run --name semantic_pg   -e POSTGRES_USER=postgres   -e POSTGRES_PASSWORD=postgres   -e POSTGRES_DB=analytics   -p 5432:5432   -d postgres:15
```

Verify:

```bash
psql -h localhost -U postgres -d analytics
```

---

# 📊 4. Create Sample Wide Table

```sql
CREATE SCHEMA IF NOT EXISTS analytics_dm;

CREATE TABLE analytics_dm.branch_sales_wide (
  invoice_id TEXT PRIMARY KEY,
  invoice_date DATE,
  branch_id TEXT,
  branch_name TEXT,
  salesperson_id TEXT,
  salesperson_name TEXT,
  invoice_amount NUMERIC,
  amount_paid NUMERIC,
  payment_status TEXT,
  product_category TEXT,
  qty_sold INTEGER,
  discount_amount NUMERIC,
  tax_amount NUMERIC
);

INSERT INTO analytics_dm.branch_sales_wide VALUES
('INV-001','2025-11-16','B001','Mumbai Central','S001','Ravi',10000,10000,'Paid','Electronics',2,500,180),
('INV-002','2025-11-17','B002','Pune','S002','Meera',8000,4000,'Partially Paid','Apparel',3,200,144),
('INV-003','2025-11-18','B001','Mumbai Central','S003','Anil',15000,7000,'Partially Paid','Electronics',1,1000,270),
('INV-004','2025-10-05','B003','Bangalore','S004','Kavita',5000,500,'Partially Paid','FMCG',5,0,90),
('INV-005','2025-09-01','B002','Pune','S002','Meera',12000,12000,'Paid','Home',4,600,216);
```

---

# 🏗️ 5. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

# 📥 6. Generate metadata.json (Manifest Reader)

If using dbt:

```bash
python manifest_reader.py   --manifest target/manifest.json   --out metadata/metadata.json   --filter-tag wide
```

### OR (Quick Mode)  
Use provided `metadata.json` from project.

---

# 🤖 7. Run Inference Engine

```bash
python inference_engine.py   --metadata metadata/metadata.json   --out metadata/inferred.json
```

---

# 🧠 8. Generate semantic.json

```bash
python semantic_generator.py   --inferred metadata/inferred.json   --out metadata/semantic.json
```

This file defines your Semantic Layer for AI.

---

# 🔑 9. Environment Variables

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/analytics"
export SEMANTIC_JSON="backend/metadata/semantic.json"
```

---

# 🧵 10. Run SQL Agent

```bash
uvicorn sql_agent:app --reload --host 0.0.0.0 --port 8000
```

Test:

```bash
curl http://localhost:8000/health
```

---

# 💬 11. Test Natural Language Queries

Example:

```bash
curl -X POST http://localhost:8000/ask   -H "Content-Type: application/json"   -d '{"question":"Which branch has the highest sales contribution?"}'
```

---

# 🎨 12. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open:

```
http://localhost:3000
```

---

# 🧪 13. End-to-End Test Scenarios

### Try:
- “Show branch-wise % contribution of sales last 90 days”
- “Find invoices paid < 50% in Pune”
- “Top 3 branches by invoice_amount”

---

# 🧹 14. Troubleshooting

### semantic not loaded  
Check:
```
export SEMANTIC_JSON="backend/metadata/semantic.json"
```

### DB connection issues  
Ensure Postgres container is running:
```
docker ps
```

### OpenAI model errors  
Check your API key:
```
echo $OPENAI_API_KEY
```

---

# 🎯 15. Full Local Pipeline Summary

```
1. Start Postgres
2. Create sample wide table
3. Generate metadata.json
4. Generate inferred.json
5. Generate semantic.json
6. Start FastAPI SQL Agent
7. Start Next.js frontend
8. Ask natural language questions
```

You now have a fully functional **AI-powered BI Analytics Platform** running locally.

---


"Show me total YTD sales by customer"
"Which customers have outstanding above 180 days?"
"What is the profit/loss by company code?"
"Give me top 10 customers by YTD sales"
"Show customers with sales below budget"

subgroup the data handle by wise and group head wise        use coelesec

Show me handler code, handler name, customer count, total YTD sales, total outstanding, and total profit/loss grouped by handler code and handler name, replacing nulls with Unknown and No Name, ordered by total YTD sales descending with nulls last

Give me handler-wise summary with customer count and sales totals grouped by handler


give me top 10 costumer and handle by name which their ytd sales and i don't want 0 and null value in the ytd sales and also i want in decending order 



  show me DONEPUDI NIREESHA	salesman total yeayly sales 



Why it sometimes fails
Ambiguous queries: "sales by location" (location doesn't exist in sales table)
Similar concepts: both tables have "company_code"
Generic terms: "amount", "code", "date" exist in multiple tables
No hard validation: relies on AI following instructions