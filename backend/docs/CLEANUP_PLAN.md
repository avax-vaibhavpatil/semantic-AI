# Backend Cleanup Plan

## Overview
This document lists all files that should be removed or reorganized as they are part of the old monolithic structure and have been replaced by the new modular architecture.

---

## 🗑️ FILES TO DELETE (Old Monolithic Structure)

### 1. Old API/Application Files
These are replaced by the new modular `app/` structure:

- **`sql_agent.py`** ❌ DELETE
  - **Reason**: Old monolithic FastAPI app (814 lines)
  - **Replaced by**: `app/api/main.py` + `app/api/v1/routes/`
  - **Status**: Completely replaced

- **`start_backend.sh`** ❌ DELETE
  - **Reason**: Old startup script for `sql_agent.py`
  - **Replaced by**: `start_api.sh` (for new modular app)
  - **Status**: Obsolete

- **`start_with_groq.sh`** ❌ DELETE
  - **Reason**: Old startup script variant
  - **Replaced by**: `start_api.sh` (uses new modular app)
  - **Status**: Obsolete

### 2. Old Database Files
These are replaced by the new infrastructure layer:

- **`db_connector.py`** ❌ DELETE
  - **Reason**: Old synchronous database connector
  - **Replaced by**: `app/infrastructure/database/connection.py` (async)
  - **Status**: Completely replaced

### 3. Old Model Files
These are replaced by the new core models:

- **`models.py`** ❌ DELETE
  - **Reason**: Old Pydantic models (508 lines)
  - **Replaced by**: `app/core/models/` (query.py, report.py, semantic.py)
  - **Status**: Completely replaced

### 4. Old Repository Files
These are replaced by the new repositories layer:

- **`report_repository.py`** ❌ DELETE
  - **Reason**: Old synchronous repository (709 lines)
  - **Replaced by**: `app/repositories/report_repository.py` (async)
  - **Status**: Completely replaced

### 5. Old Service Logic Files
These are replaced by the new services layer:

- **`prompts.py`** ❌ DELETE
  - **Reason**: Old prompt templates (200 lines)
  - **Replaced by**: `app/services/query_service.py` (has `_build_system_prompt()`)
  - **Status**: Logic moved to QueryService

- **`sql_validator.py`** ❌ DELETE
  - **Reason**: Old SQL validation (205 lines)
  - **Replaced by**: `app/services/query_service.py` (has validation logic)
  - **Status**: Logic moved to QueryService

### 6. Old Test Files
These are redundant or replaced by new tests:

- **`test_endpoints.py`** ❌ DELETE
  - **Reason**: Old endpoint tests (likely for `sql_agent.py`)
  - **Replaced by**: `test_report_routes.py`, `test_reports_with_real_data.py`
  - **Status**: Obsolete

- **`test_comprehensive_queries.py`** ❌ DELETE
  - **Reason**: Old query tests
  - **Replaced by**: `test_api.py`, `test_concurrent_queries.py`
  - **Status**: Obsolete

- **`test_api_complete.py`** ✅ KEEP
  - **Reason**: Tests new modular API (uses `/api/v1/query`, `/health`)
  - **Status**: Current test file - KEEP

- **`test_api_live.py`** ✅ KEEP
  - **Reason**: Tests new modular API (uses `/api/v1/query`, `/health`)
  - **Status**: Current test file - KEEP

### 7. Old Utility/Script Files
These are obsolete:

- **`setup_and_test.sh`** ❌ DELETE
  - **Reason**: Old setup script
  - **Replaced by**: `start_api.sh` (if needed)
  - **Status**: Obsolete

### 8. Old Generator/Inference Files
These might be obsolete (check if still used):

- **`inference_engine.py`** ⚠️ REVIEW
  - **Reason**: Might be for generating semantic.json
  - **Check**: If still used for semantic layer generation, KEEP. Otherwise DELETE.
  - **Status**: Needs review

- **`semantic_generator.py`** ⚠️ REVIEW
  - **Reason**: Might be for generating semantic.json
  - **Check**: If still used for semantic layer generation, KEEP. Otherwise DELETE.
  - **Status**: Needs review

- **`manifest_reader.py`** ⚠️ REVIEW
  - **Reason**: Might be for reading metadata
  - **Check**: If still used, KEEP. Otherwise DELETE.
  - **Status**: Needs review

---

## 📁 EMPTY DIRECTORIES TO REMOVE

These directories are empty and not used:

- **`app/infrastructure/cache/`** ❌ DELETE
  - **Reason**: Empty directory
  - **Status**: Not used

- **`app/middleware/`** ❌ DELETE
  - **Reason**: Empty directory
  - **Status**: Not used (middleware is in `app/api/main.py`)

- **`app/utils/`** ❌ DELETE
  - **Reason**: Empty directory
  - **Status**: Not used

---

## 🧪 CONFIG TEST FILES (Development Tests)

These are development/test files in the config module. They might be useful for testing but are not part of the production code:

- **`app/config/test_database.py`** ⚠️ REVIEW
  - **Reason**: Test file for database config
  - **Action**: Move to `tests/` folder or DELETE if not needed

- **`app/config/test_file_logging.py`** ⚠️ REVIEW
  - **Reason**: Test file for file logging
  - **Action**: Move to `tests/` folder or DELETE if not needed

- **`app/config/test_logging.py`** ⚠️ REVIEW
  - **Reason**: Test file for logging
  - **Action**: Move to `tests/` folder or DELETE if not needed

- **`app/config/test_settings.py`** ⚠️ REVIEW
  - **Reason**: Test file for settings
  - **Action**: Move to `tests/` folder or DELETE if not needed

- **`app/config/demo_logging.py`** ⚠️ REVIEW
  - **Reason**: Demo file for logging
  - **Action**: DELETE if not needed, or move to `docs/examples/`

- **`app/config/database.py`** ⚠️ REVIEW
  - **Reason**: Check if this is used or replaced by `app/infrastructure/database/`
  - **Action**: If not used, DELETE

---

## 📚 DOCUMENTATION FILES TO ORGANIZE

### Learning/Educational Files (KEEP - Move to `docs/`)
These are valuable learning resources:

- **`SYSTEM_DESIGN_MULTI_USER_LOAD_BALANCING.md`** ✅ KEEP → Move to `docs/`
- **`CODE_WALKTHROUGH_CONCURRENT_REQUESTS.md`** ✅ KEEP → Move to `docs/`
- **`CONCURRENT_QUERY_TEST_RESULTS.md`** ✅ KEEP → Move to `docs/`
- **`QUERY_TEST_RESULTS.md`** ✅ KEEP → Move to `docs/`
- **`TEST_RESULTS.md`** ✅ KEEP → Move to `docs/`

### Implementation Documentation (KEEP - Move to `docs/`)
These document the implementation:

- **`NEXT_STEPS_CURRENT_STATUS.md`** ✅ KEEP → Move to `docs/`
- **`TESTING_GUIDE.md`** ✅ KEEP → Move to `docs/`
- **`REPORTS_API_GUIDE.md`** ✅ KEEP → Move to `docs/`
- **`app/api/PRODUCTION_IMPROVEMENTS.md`** ✅ KEEP → Move to `docs/`
- **`app/api/v1/routes/QUERY_ROUTE_EXPLANATION.md`** ✅ KEEP → Move to `docs/`
- **`app/services/QUERY_SERVICE_EXPLANATION.md`** ✅ KEEP → Move to `docs/`
- **`app/services/REPORT_SERVICE_EXPLANATION.md`** ✅ KEEP → Move to `docs/`
- **`app/services/TEST_ERRORS_DIAGNOSIS.md`** ✅ KEEP → Move to `docs/`
- **`app/repositories/FIXES_APPLIED.md`** ✅ KEEP → Move to `docs/`

### README Files (KEEP - Review)
- **`app/README.md`** ✅ KEEP → Review and update if needed

---

## ✅ FILES TO KEEP (Current Modular Structure)

### Core Application Files
- `app/api/main.py` ✅
- `app/api/dependencies.py` ✅
- `app/api/exception_handlers.py` ✅
- `app/api/v1/routes/query.py` ✅
- `app/api/v1/routes/reports.py` ✅

### Core Domain Models
- `app/core/models/query.py` ✅
- `app/core/models/report.py` ✅
- `app/core/models/semantic.py` ✅
- `app/core/exceptions.py` ✅
- `app/core/constants.py` ✅

### Infrastructure
- `app/infrastructure/database/connection.py` ✅
- `app/infrastructure/database/query_executor.py` ✅
- `app/infrastructure/ai/base.py` ✅
- `app/infrastructure/ai/router.py` ✅
- `app/infrastructure/ai/providers/*.py` ✅

### Repositories
- `app/repositories/base.py` ✅
- `app/repositories/report_repository.py` ✅
- `app/repositories/semantic_repository.py` ✅

### Services
- `app/services/query_service.py` ✅
- `app/services/report_service.py` ✅
- `app/services/semantic_service.py` ✅

### Config
- `app/config/settings.py` ✅
- `app/config/logging_config.py` ✅

### Tests (Current)
- `test_api.py` ✅
- `test_api_complete.py` ✅
- `test_api_live.py` ✅
- `test_report_routes.py` ✅
- `test_reports_with_real_data.py` ✅
- `test_concurrent_queries.py` ✅
- `app/core/test_models.py` ✅
- `app/repositories/test_repositories.py` ✅
- `app/services/test_*.py` ✅
- `app/infrastructure/database/test_async_db.py` ✅

### Scripts (Current)
- `start_api.sh` ✅

### Data/Migrations
- `metadata/semantic.json` ✅
- `migrations/001_create_reports_schema.sql` ✅
- `requirements.txt` ✅

---

## 📋 CLEANUP SUMMARY

### Files to Delete (Definite):
1. `sql_agent.py` (814 lines - old monolithic app)
2. `db_connector.py` (old DB connector)
3. `models.py` (508 lines - old models)
4. `report_repository.py` (709 lines - old repo)
5. `prompts.py` (200 lines - old prompts)
6. `sql_validator.py` (205 lines - old validator)
7. `start_backend.sh` (old startup script)
8. `start_with_groq.sh` (old startup script)
9. `setup_and_test.sh` (old setup script)
10. `test_endpoints.py` (old tests)
11. `test_comprehensive_queries.py` (old tests)

### Files to Review:
1. `inference_engine.py` - Check if still used
4. `semantic_generator.py` - Check if still used
5. `manifest_reader.py` - Check if still used
6. `app/config/test_*.py` - Move to tests/ or delete
7. `app/config/demo_logging.py` - Delete or move to docs/examples/
8. `app/config/database.py` - Check if used

### Directories to Delete:
1. `app/infrastructure/cache/` (empty)
2. `app/middleware/` (empty)
3. `app/utils/` (empty)

### Documentation to Organize:
- Move all `.md` files to `docs/` folder with proper naming

---

## 🎯 RECOMMENDED ACTIONS

1. **Create `docs/` folder** for all documentation
2. **Move learning files** to `docs/learning/`
3. **Move implementation docs** to `docs/implementation/`
4. **Delete old monolithic files** (listed above)
5. **Delete empty directories**
6. **Review and decide** on files marked for review
7. **Organize test files** (move config tests to `tests/` if keeping)

---

## 📊 ESTIMATED CLEANUP

- **Files to delete**: ~11-15 files
- **Lines of code removed**: ~2,500+ lines (old monolithic code)
- **Empty directories**: 3
- **Documentation files to organize**: ~13 files

**Result**: Cleaner, more maintainable codebase following modular architecture! 🎉

