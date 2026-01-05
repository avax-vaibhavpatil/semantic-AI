# App Directory Structure Explanation

uvicorn app.api.main:app --host 0.0.0.0 --port 8000

This document explains the purpose of each folder in the new modular structure.

## 📁 Folder Structure

```
app/
├── config/          # Configuration Management
├── api/             # API Routes (HTTP layer)
├── core/            # Core Domain Models
├── services/        # Business Logic
├── repositories/    # Data Access Layer
├── infrastructure/  # External Integrations
├── middleware/      # Cross-cutting Concerns
└── utils/           # Helper Functions
```

---

## 📂 Detailed Explanation

### 1. `config/` - Configuration Management
**Purpose**: Centralized settings and configuration

**Why separate?**
- All environment variables in one place
- Easy to change settings for dev/staging/prod
- Type-safe configuration with validation

**Contains**:
- `settings.py` - Main configuration (API keys, database URLs, etc.)
- `database.py` - Database connection settings
- `logging_config.py` - Logging setup

---

### 2. `api/` - API Routes (Presentation Layer)
**Purpose**: HTTP request/response handling

**Why separate?**
- Thin controllers - only handle HTTP, no business logic
- Easy to version APIs (`v1/`, `v2/`)
- Easy to test with HTTP clients

**Contains**:
- `v1/queries.py` - Query endpoints
- `v1/reports.py` - Report endpoints
- `v1/health.py` - Health check endpoints
- `dependencies.py` - Dependency injection for FastAPI

---

### 3. `core/` - Core Domain Models
**Purpose**: Business domain models and rules

**Why separate?**
- Pure business logic, no dependencies on frameworks
- Reusable across different layers
- Type-safe models

**Contains**:
- `models/query.py` - Query domain model
- `models/report.py` - Report domain model
- `exceptions.py` - Custom exceptions
- `constants.py` - Business constants

---

### 4. `services/` - Business Logic (Application Layer)
**Purpose**: Orchestrates business operations

**Why separate?**
- Contains the actual business logic
- Coordinates between repositories and external services
- Reusable - can be called from API, CLI, or background jobs

**Contains**:
- `query_service.py` - Query processing logic
- `report_service.py` - Report management logic
- `ai_service.py` - AI provider abstraction

---

### 5. `repositories/` - Data Access Layer
**Purpose**: Database operations

**Why separate?**
- Abstracts database details
- Easy to swap databases (PostgreSQL → MySQL)
- Easy to mock for testing

**Contains**:
- `base.py` - Base repository interface
- `report_repository.py` - Report database operations
- `semantic_repository.py` - Semantic layer file operations

---g q67


### 6. `infrastructure/` - External Integrations
**Purpose**: Third-party services and external systems

**Why separate?**
- Isolates external dependencies
- Easy to swap implementations (OpenAI → Groq)
- Easy to test with mocks

**Contains**:
- `ai/` - AI providers (OpenAI, Groq, Claude)
- `database/` - Database connection setup
- `cache/` - Caching layer (Redis, etc.)

---

### 7. `middleware/` - Cross-cutting Concerns
**Purpose**: Request/response processing

**Why separate?**
- Centralized logging, error handling, CORS
- Applied to all requests automatically
- Easy to add new middleware

**Contains**:
- `cors.py` - CORS configuration
- `logging.py` - Request logging
- `error_handler.py` - Global error handling

---

### 8. `utils/` - Helper Functions
**Purpose**: Reusable utility functions

**Why separate?**
- Pure functions, no side effects
- Reusable across modules
- Easy to test

**Contains**:
- `validators.py` - SQL validation utilities
- `prompts.py` - Prompt templates
- `helpers.py` - General helper functions

---

## 🔄 How They Work Together

```
User Request
    ↓
api/v1/queries.py (HTTP layer)
    ↓
services/query_service.py (Business logic)
    ↓
repositories/ (Data access)
    ↓
infrastructure/database/ (Database connection)
    ↓
Database
```

**Flow Example**:
1. User sends HTTP request → `api/v1/queries.py`
2. API calls → `services/query_service.py`
3. Service uses → `repositories/` to get data
4. Repository uses → `infrastructure/database/` to connect
5. Results flow back up the chain

---

## 🎯 Benefits of This Structure

1. **Clear Separation**: Each folder has one responsibility
2. **Easy to Find**: Know exactly where to look for code
3. **Easy to Test**: Can test each layer independently
4. **Easy to Extend**: Add new features without breaking existing code
5. **Team Friendly**: Multiple developers can work on different modules

---

## 📚 Next Steps

We'll start building from the bottom up:
1. **config/** - Foundation (settings, database)
2. **core/** - Domain models
3. **infrastructure/** - External services
4. **repositories/** - Data access
5. **services/** - Business logic
6. **api/** - HTTP endpoints
7. **middleware/** - Cross-cutting concerns

