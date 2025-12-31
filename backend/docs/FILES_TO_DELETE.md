# Files to Delete - Quick Reference

## 🗑️ DEFINITE DELETIONS (12 files)

### Old Monolithic Application
1. `sql_agent.py` - Old monolithic FastAPI app (814 lines)
2. `start_backend.sh` - Old startup script
3. `start_with_groq.sh` - Old startup script variant
4. `setup_and_test.sh` - Old setup script

### Old Database Layer
5. `db_connector.py` - Old synchronous DB connector
6. `app/config/database.py` - Obsolete synchronous DB connector (replaced by async)

### Old Models
6. `models.py` - Old Pydantic models (508 lines)

### Old Repository
7. `report_repository.py` - Old synchronous repository (709 lines)

### Old Service Logic
8. `prompts.py` - Old prompt templates (200 lines)
9. `sql_validator.py` - Old SQL validation (205 lines)

### Old Tests
10. `test_endpoints.py` - Old endpoint tests
11. `test_comprehensive_queries.py` - Old query tests

---

## ⚠️ REVIEW RESULTS (See FILES_REVIEW_RESULTS.md for details)

### ✅ KEEP (3 files - Utility tools for semantic.json generation)
1. `inference_engine.py` - ✅ KEEP (CLI tool for semantic layer generation)
2. `semantic_generator.py` - ✅ KEEP (CLI tool for semantic layer generation)
3. `manifest_reader.py` - ✅ KEEP (CLI tool for semantic layer generation)

### ❌ DELETE (1 file - Obsolete)
4. `app/config/database.py` - ❌ DELETE (obsolete synchronous DB, replaced by async)

### 📁 MOVE (1 file - Demo/example)
5. `app/config/demo_logging.py` - 📁 MOVE to `docs/examples/`

---

## 📁 EMPTY DIRECTORIES TO DELETE (3)

1. `app/infrastructure/cache/` - Empty
2. `app/middleware/` - Empty
3. `app/utils/` - Empty

---

## 📁 FILES TO MOVE (1 file)

1. `app/config/demo_logging.py` → `docs/examples/demo_logging.py`

## 📊 SUMMARY

- **Total files to delete**: 12 files (11 definite + 1 from review)
- **Total files to keep**: 3 files (utility tools)
- **Total files to move**: 1 file (demo)
- **Total lines removed**: ~2,500+ lines
- **Empty directories**: 3
- **Result**: Cleaner modular codebase!

---

**See `CLEANUP_PLAN.md` for detailed explanations.**

