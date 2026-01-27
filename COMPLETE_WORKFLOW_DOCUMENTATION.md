# Complete Workflow Documentation - Semantic AI Analytics Platform

## 📋 Table of Contents
1. [Overview](#overview)
2. [User Perspective - How the System Works](#user-perspective)
3. [Complete Workflow - Step by Step](#complete-workflow)
4. [Technical Architecture](#technical-architecture)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Component Details](#component-details)
7. [Report Management Workflow](#report-management-workflow)
8. [Visualization Workflow](#visualization-workflow)

---

## 🎯 Overview

The **Semantic AI Analytics Platform** is an intelligent Business Intelligence (BI) system that allows users to ask questions in natural language and receive instant analytics reports. The system uses AI to translate natural language questions into SQL queries, executes them against your database, and displays results in an interactive interface.

### Key Features
- **Natural Language Interface**: Ask questions in plain English
- **AI-Powered SQL Generation**: Automatically converts questions to SQL
- **Real-Time Data Access**: Direct connection to your database
- **Report Management**: Save, organize, and reuse reports
- **Data Visualization**: Create charts and graphs from results
- **Export Capabilities**: Download data as Excel files

---

## 👤 User Perspective - How the System Works

### What Users See

Users interact with a modern web interface (`http://localhost:3000`) that includes:

1. **Query Input Box**: A text field where users type their questions
2. **Results Table**: Displays query results in a paginated table
3. **SQL Preview**: Shows the generated SQL query (for transparency)
4. **Action Buttons**: 
   - Save Report
   - Visualize (Create charts)
   - Export to Excel
5. **Saved Reports Sidebar**: Access previously saved reports

### User Experience Flow

```
User Types Question → Clicks "Ask" → Sees Loading → Gets Results → Can Save/Visualize/Export
```

---

## 🔄 Complete Workflow - Step by Step

### Phase 1: User Input

#### Step 1.1: User Types a Question
- **Location**: Frontend (`frontend/pages/index.js`)
- **User Action**: Types a natural language question in the text field
- **Example Questions**:
  - "Show me top 10 customers by sales"
  - "What is the total sales by branch?"
  - "Give me handler-wise sales summary with customer count"

#### Step 1.2: User Submits Query
- **Action**: Clicks "Ask" button or presses Enter
- **Frontend Code**: `ask()` function in `index.js` (line 84)
- **What Happens**:
  - Loading state is set to `true`
  - Error messages are cleared
  - Previous results are cleared
  - HTTP POST request is prepared

---

### Phase 2: Frontend Request

#### Step 2.1: HTTP Request Sent
- **Endpoint**: `POST http://localhost:8000/ask`
- **Request Body**:
  ```json
  {
    "question": "Show me top 10 customers by sales",
    "max_rows": 500
  }
  ```
- **Technology**: Axios HTTP client
- **Location**: `frontend/pages/index.js` line 93-96

#### Step 2.2: CORS Handling
- **Backend**: FastAPI CORS middleware allows requests from `localhost:3000`
- **Location**: `backend/sql_agent.py` lines 92-98
- **Purpose**: Enables frontend to communicate with backend API

---

### Phase 3: Backend Processing

#### Step 3.1: Request Received
- **Backend File**: `backend/sql_agent.py`
- **Endpoint Handler**: `@app.post("/ask")` (line 149)
- **What Happens**:
  - Request is validated
  - AI API key is checked
  - User question is extracted

#### Step 3.2: Semantic Layer Loading
- **Location**: `backend/sql_agent.py` lines 46-52
- **File Used**: `backend/metadata/semantic.json`
- **Content**: Database schema, columns, measures, dimensions, derived measures
- **Purpose**: Provides context to AI about available data structures

**Semantic JSON Structure**:
```json
{
  "tables": {
    "table_name": {
      "description": "Table description",
      "columns": {
        "column_name": {"type": "dimension|measure|date"}
      },
      "dimensions": ["dimension_columns"],
      "measures": ["measure_columns"],
      "derived_measures": [
        {
          "name": "derived_measure_name",
          "expression": "SQL expression",
          "type": "sum|avg|ratio"
        }
      ],
      "time_columns": ["date_columns"]
    }
  }
}
```

#### Step 3.3: Column Hints Generation
- **Function**: `build_column_hints()` (line 126)
- **Purpose**: Builds context-aware hints for AI about which columns to use
- **Example**: If user mentions "customer name", hints direct AI to use `gws_cust_name` instead of `gws_hand_name`

#### Step 3.4: Prompt Construction
- **System Prompt**: `PROMPT_SYSTEM` from `backend/prompts.py`
  - Contains rules for SQL generation
  - Defines safety constraints
  - Specifies data handling rules
  
- **User Prompt**: Built using `PROMPT_USER_TEMPLATE` (line 156-160)
  ```python
  prompt_user = PROMPT_USER_TEMPLATE.format(
      semantic_json=sem_json_str,      # Full semantic JSON
      user_question=req.question,       # User's question
      column_hints=column_hints         # Column preference hints
  )
  ```

**Prompt Contents**:
1. Complete semantic JSON (table structure)
2. Column selection preferences
3. User's natural language question
4. Instructions to generate SQL

---

### Phase 4: AI SQL Generation

#### Step 4.1: AI Model Call
- **Function**: `call_openai_generate_sql()` (line 105)
- **AI Provider**: Groq (default) or OpenAI/Anthropic
- **Model**: `llama-3.1-8b-instant` (Groq) or user-configured model
- **Process**:
  ```
  System Prompt + User Prompt → AI Model → SQL Query
  ```

#### Step 4.2: SQL Generation Process
The AI model receives:
- **Input**: 
  - System prompt with rules and constraints
  - Semantic JSON describing database structure
  - User's natural language question
  - Column preference hints

- **AI Processing**:
  1. Analyzes user question intent
  2. Maps question to database schema (using semantic JSON)
  3. Selects appropriate tables and columns
  4. Constructs SQL query following rules
  5. Applies aggregations, filters, sorting as needed

- **Output**: Pure SQL SELECT statement (no explanations)

**Example Transformation**:
```
User Question: "Show me top 10 customers by sales"

AI Generates:
SELECT gws_cust_name, SUM(gws_ytd_sales) AS total_sales
FROM public.gwanalytics
WHERE gws_ytd_sales IS NOT NULL
GROUP BY gws_cust_name
ORDER BY total_sales DESC NULLS LAST
LIMIT 10
```

#### Step 4.3: SQL Safety Validation
- **Function**: `basic_sql_safety()` from `sql_validator.py`
- **Checks**:
  - ✅ Must start with SELECT
  - ❌ No INSERT, UPDATE, DELETE, DROP, ALTER
  - ❌ No semicolons
  - ❌ No stored procedures or file operations

- **Location**: `backend/sql_agent.py` line 168
- **If Fails**: HTTP 400 error returned to user

#### Step 4.4: Semantic Validation
- **Function**: `validate_against_semantic()` from `sql_validator.py`
- **Checks**:
  - ✅ Only uses tables defined in semantic.json
  - ✅ Only uses columns that exist in schema
  - ✅ No hallucinated column names
  - ✅ Follows semantic layer constraints

- **Location**: `backend/sql_agent.py` line 171
- **If Fails**: HTTP 400 error with helpful message showing available columns

---

### Phase 5: Database Execution

#### Step 5.1: SQL Execution Preparation
- **Function**: `run_select()` from `db_connector.py`
- **Parameters**:
  - SQL query (generated by AI)
  - `max_rows`: Maximum rows to return (default: 500)

#### Step 5.2: Database Connection
- **Location**: `backend/db_connector.py` lines 6-10
- **Connection String**: From `DATABASE_URL` environment variable
- **Format**: `postgresql://user:password@host:port/database`
- **Engine**: SQLAlchemy with connection pooling

#### Step 5.3: Query Execution
- **Process**:
  1. SQL query is executed against database
  2. Automatic LIMIT added if not present (safety measure)
  3. Results are fetched as dictionaries
  4. Rows are converted to list of dictionaries

**Code Flow**:
```python
# backend/db_connector.py lines 17-21
with eng.connect() as conn:
    res = conn.execute(text(safe_sql))
    rows = [dict(row._mapping) for row in res]
return rows
```

#### Step 5.4: Result Validation
- **Function**: `check_query_results()` from `sql_validator.py`
- **Checks**:
  - Results are not empty (unless expected)
  - Data quality warnings (if applicable)
- **If Issues**: Warning message included in response

#### Step 5.5: Error Handling (Auto-Fix)
- **Location**: `backend/sql_agent.py` lines 186-214
- **If SQL Execution Fails**:
  1. Error is captured
  2. Error prompt is constructed with:
     - Original SQL
     - Error message
  3. AI is asked to fix the SQL
  4. Fixed SQL is validated again
  5. Fixed SQL is executed
  6. If still fails, error is returned to user

---

### Phase 6: Response to Frontend

#### Step 6.1: Response Construction
- **Response Format**:
  ```json
  {
    "sql": "SELECT ...",
    "rows": [
      {"column1": "value1", "column2": "value2"},
      {"column1": "value3", "column2": "value4"}
    ],
    "warning": "Optional warning message"
  }
  ```

#### Step 6.2: HTTP Response Sent
- **Status Code**: 200 (success)
- **Content-Type**: `application/json`
- **Body**: Contains SQL, rows, and optional warning

---

### Phase 7: Frontend Display

#### Step 7.1: Response Reception
- **Location**: `frontend/pages/index.js` line 93-104
- **Process**:
  ```javascript
  const res = await axios.post("http://localhost:8000/ask", {...});
  setSql(res.data.sql);        // Store SQL query
  setRows(res.data.rows);      // Store results
  setWarning(res.data.warning); // Store warnings if any
  ```

#### Step 7.2: State Updates
- **React State Updated**:
  - `sql`: Generated SQL query (for display)
  - `rows`: Query results (array of objects)
  - `warning`: Any warnings from backend
  - `loading`: Set to `false`
  - `page`: Reset to 0 (first page)

#### Step 7.3: Column Auto-Detection for Visualization
- **Location**: `frontend/pages/index.js` lines 106-119
- **Process**:
  - Analyzes first row of results
  - Identifies categorical columns (strings, codes, names)
  - Identifies numerical columns (numbers)
  - Pre-selects columns for chart creation

#### Step 7.4: UI Rendering

**SQL Display Section** (lines 485-525):
- Shows generated SQL query in a code block
- Displays row count badge
- Syntax highlighting ready (monospace font)

**Results Table** (lines 528-634):
- **Table Structure**:
  - Header row with column names
  - Data rows with pagination
  - Sticky header (scrolls with content)
- **Pagination Controls**:
  - Rows per page: 5, 10, 25, 50, 100
  - Page navigation buttons
  - Row count display

**Action Buttons** (lines 534-569):
1. **Save Report**: Opens save dialog
2. **Visualize**: Opens chart creation dialog
3. **Export to Excel**: Downloads data as XLSX file

**Error/Warning Display** (lines 472-482):
- Error alerts (red) for failures
- Warning alerts (yellow) for data quality issues

---

## 🏗️ Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│                  (React/Next.js Frontend)                     │
│                   http://localhost:3000                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Query Input  │  │ Results Table│  │ Action Buttons│      │
│  │              │  │              │  │              │      │
│  │ - Text Field │  │ - Paginated  │  │ - Save       │      │
│  │ - Ask Button │  │ - Sortable   │  │ - Visualize  │      │
│  │              │  │ - Filterable │  │ - Export     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                              │ HTTP POST /ask
                              │ JSON Request
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API SERVER                                │
│              (FastAPI Backend)                               │
│              http://localhost:8000                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         /ask Endpoint Handler                        │    │
│  │                                                       │    │
│  │  1. Load Semantic JSON                               │    │
│  │  2. Build AI Prompt                                  │    │
│  │  3. Call AI Model (Groq/OpenAI)                     │    │
│  │  4. Validate Generated SQL                           │    │
│  │  5. Execute SQL                                      │    │
│  │  6. Return Results                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Semantic JSON│  │  AI Service  │  │  Database    │
    │   Metadata   │  │  (Groq API)  │  │  (PostgreSQL) │
    │              │  │              │  │              │
    │ - Tables     │  │ - LLM Model  │  │ - Tables     │
    │ - Columns    │  │ - SQL Gen    │  │ - Data       │
    │ - Measures   │  │              │  │ - Schema     │
    │ - Dimensions │  │              │  │              │
    └──────────────┘  └──────────────┘  └──────────────┘
```

### Data Flow Diagram

```
USER INPUT
    │
    │ "Show me top 10 customers by sales"
    ▼
FRONTEND (index.js)
    │
    │ HTTP POST /ask
    │ {question: "...", max_rows: 500}
    ▼
BACKEND API (sql_agent.py)
    │
    ├─► Load semantic.json
    │   └─► Tables, columns, measures
    │
    ├─► Build prompt
    │   ├─► System prompt (rules)
    │   ├─► Semantic JSON (schema)
    │   ├─► Column hints (preferences)
    │   └─► User question
    │
    ├─► Call AI Model (Groq/OpenAI)
    │   └─► Generate SQL query
    │
    ├─► Validate SQL
    │   ├─► Safety checks (SELECT only)
    │   └─► Semantic validation (schema compliance)
    │
    ├─► Execute SQL (db_connector.py)
    │   └─► Database query execution
    │
    └─► Return Response
        │
        │ JSON {sql, rows, warning}
        ▼
FRONTEND (index.js)
    │
    ├─► Display SQL query
    ├─► Display results table
    ├─► Enable actions (Save/Visualize/Export)
    │
    └─► USER SEES RESULTS
```

---

## 📦 Component Details

### 1. Frontend Components

#### Main Page (`frontend/pages/index.js`)
- **Purpose**: Main user interface
- **Key Functions**:
  - `ask()`: Sends query to backend
  - `downloadExcel()`: Exports data to XLSX
  - `saveReport()`: Saves report to database
  - `prepareChartData()`: Prepares data for visualization
  - `handleExecuteSavedReport()`: Executes saved report

#### Saved Reports Sidebar (`frontend/components/SavedReportsSidebar.js`)
- **Purpose**: Manage saved reports
- **Features**:
  - List all saved reports
  - Search reports
  - Filter by favorites
  - Execute saved reports
  - Delete reports
  - Toggle favorites

#### Theme (`frontend/theme.js`)
- **Purpose**: Material-UI theme configuration
- **Features**: Custom colors, typography, components

### 2. Backend Components

#### SQL Agent (`backend/sql_agent.py`)
- **Purpose**: Main API server
- **Endpoints**:
  - `POST /ask`: Main query endpoint
  - `POST /reports/save`: Save report
  - `GET /reports`: List reports
  - `GET /reports/{id}`: Get report details
  - `POST /reports/{id}/execute`: Execute saved report
  - `GET /reports/search`: Search reports
  - `PATCH /reports/{id}`: Update report
  - `DELETE /reports/{id}`: Delete report
  - `GET /health`: Health check

#### Database Connector (`backend/db_connector.py`)
- **Purpose**: Database connection and query execution
- **Functions**:
  - `get_engine()`: Create database connection
  - `run_select()`: Execute SELECT queries safely

#### SQL Validator (`backend/sql_validator.py`)
- **Purpose**: SQL safety and semantic validation
- **Functions**:
  - `basic_sql_safety()`: Check for forbidden operations
  - `validate_against_semantic()`: Ensure schema compliance
  - `check_query_results()`: Validate result quality

#### Prompts (`backend/prompts.py`)
- **Purpose**: AI prompt templates
- **Content**:
  - `PROMPT_SYSTEM`: Rules and guidelines for AI
  - `PROMPT_USER_TEMPLATE`: User question template
  - `ERROR_PROMPT`: Error fixing template

#### Report Repository (`backend/report_repository.py`)
- **Purpose**: Database operations for reports
- **Functions**:
  - `create_report()`: Save new report
  - `get_user_reports()`: List user's reports
  - `get_report_by_id()`: Get specific report
  - `update_report()`: Update report metadata
  - `delete_report()`: Delete report
  - `search_reports()`: Search reports
  - `execute_report()`: Execute saved report SQL

#### Models (`backend/models.py`)
- **Purpose**: Pydantic models for API requests/responses
- **Models**:
  - `AskRequest`: Query request
  - `SaveReportRequest`: Save report request
  - `ReportResponse`: Report data
  - `ReportListResponse`: List of reports

#### Inference Engine (`backend/inference_engine.py`)
- **Purpose**: Generate semantic layer from metadata
- **Process**: Analyzes database schema and infers dimensions, measures, time columns

#### Semantic Generator (`backend/semantic_generator.py`)
- **Purpose**: Convert inferred metadata to semantic.json format
- **Process**: Formats metadata for AI consumption

---

## 📊 Report Management Workflow

### Saving a Report

1. **User Action**: After getting results, clicks "Save Report" button
2. **Frontend**: Opens save dialog (`openSaveDialog()`)
3. **User Input**: 
   - Report name (required)
   - Description (optional)
   - Tags (optional, comma-separated)
4. **Frontend Request**: `POST /reports/save`
   ```json
   {
     "report_name": "Monthly Sales Summary",
     "user_question": "Show me top 10 customers by sales",
     "generated_sql": "SELECT ...",
     "report_description": "Monthly report",
     "tags": ["sales", "monthly"]
   }
   ```
5. **Backend Processing**:
   - Receives request (`save_report()` endpoint)
   - Gets user ID (currently "demo_user")
   - Saves to database via `ReportRepository`
   - Returns report ID
6. **Frontend**: Shows success message

### Executing a Saved Report

1. **User Action**: Opens sidebar, clicks on saved report
2. **Frontend**: Calls `executeReport()` function
3. **Backend Request**: `POST /reports/{id}/execute`
4. **Backend Processing**:
   - Fetches report from database
   - Extracts SQL query
   - Executes SQL against database
   - Updates execution statistics
   - Logs execution history
   - Returns results
5. **Frontend**: Displays results same as new query

### Listing Reports

1. **User Action**: Opens saved reports sidebar
2. **Frontend**: Calls `loadReports()` on sidebar open
3. **Backend Request**: `GET /reports?limit=20&offset=0`
4. **Backend Processing**:
   - Fetches user's reports from database
   - Applies filters (favorites, tags if specified)
   - Returns paginated list
5. **Frontend**: Displays list in sidebar

### Searching Reports

1. **User Action**: Types in search box
2. **Frontend**: Debounced search (500ms delay)
3. **Backend Request**: `GET /reports/search?q=search+term`
4. **Backend Processing**:
   - Full-text search on report names
   - Returns matching reports
5. **Frontend**: Updates list with search results

---

## 📈 Visualization Workflow

### Creating a Chart

1. **User Action**: After getting results, clicks "Visualize" button
2. **Frontend**: Opens visualization dialog (`openVisualization()`)
3. **Configuration Options**:
   - **Category Column**: Select column for chart slices/categories
   - **Value Column**: Select column for values
   - **Aggregation Method**: SUM, AVG, COUNT, MAX, MIN
   - **Top N**: Show top 5, 10, 15, 20, or all
4. **Data Preparation** (`prepareChartData()`):
   - Groups data by category column
   - Applies aggregation to value column
   - Sorts by value (descending)
   - Takes top N items
   - Calculates percentages
5. **Chart Rendering**:
   - Uses Recharts library
   - Pie chart visualization
   - Color-coded slices
   - Tooltips with values and percentages
   - Legend display
6. **Export**: Can download chart as PNG image

### Chart Data Processing Example

**Input Data**:
```
[
  {branch: "Mumbai", sales: 10000},
  {branch: "Pune", sales: 8000},
  {branch: "Bangalore", sales: 5000}
]
```

**Processing** (with SUM aggregation):
```
[
  {name: "Mumbai", value: 10000, percentage: 43.5},
  {name: "Pune", value: 8000, percentage: 34.8},
  {name: "Bangalore", value: 5000, percentage: 21.7}
]
```

---

## 🔍 Detailed Technical Flow

### Complete Request-Response Cycle

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: USER INPUT                                            │
└──────────────────────────────────────────────────────────────┘
User types: "Show me handler-wise sales summary"
Location: frontend/pages/index.js (TextField component)

┌──────────────────────────────────────────────────────────────┐
│ STEP 2: FRONTEND PREPARATION                                 │
└──────────────────────────────────────────────────────────────┘
Function: ask() in index.js (line 84)
Actions:
  - setLoading(true)
  - setError("")
  - setSql("")
  - setRows([])
  
Request Body:
  {
    question: "Show me handler-wise sales summary",
    max_rows: 500
  }
  
HTTP Request: POST http://localhost:8000/ask
Method: axios.post()

┌──────────────────────────────────────────────────────────────┐
│ STEP 3: BACKEND RECEPTION                                    │
└──────────────────────────────────────────────────────────────┘
File: backend/sql_agent.py
Endpoint: @app.post("/ask") (line 149)
Handler: async def ask(req: AskRequest)

Actions:
  1. Check AI API key available
  2. Load semantic.json (already loaded at startup)
  3. Build column hints
  4. Construct prompt

┌──────────────────────────────────────────────────────────────┐
│ STEP 4: PROMPT CONSTRUCTION                                  │
└──────────────────────────────────────────────────────────────┘
File: backend/sql_agent.py (lines 154-160)

Semantic JSON: Full database schema (tables, columns, measures)
Column Hints: Context-aware column preferences
User Question: Original question from user

Prompt Template Format:
  Semantic JSON: {semantic_json}
  Column hints: {column_hints}
  User question: {user_question}

System Prompt: Rules from prompts.py (PROMPT_SYSTEM)

┌──────────────────────────────────────────────────────────────┐
│ STEP 5: AI SQL GENERATION                                    │
└──────────────────────────────────────────────────────────────┘
File: backend/sql_agent.py
Function: call_openai_generate_sql() (line 105)

AI Provider: Groq API
Model: llama-3.1-8b-instant
API Call:
  - Endpoint: https://api.groq.com/openai/v1
  - Method: POST /chat/completions
  - Messages: [system, user]
  - Temperature: 0.0 (deterministic)
  - Max tokens: 1500

Input to AI:
  System: Rules, constraints, examples
  User: Semantic JSON + Question + Hints

AI Processing:
  1. Analyze question intent
  2. Map to database schema
  3. Select tables/columns
  4. Generate SQL query
  5. Apply filters/aggregations
  6. Return pure SQL

Output: SQL SELECT statement

Example Generated SQL:
  SELECT gws_handled_by,
         gws_hand_name,
         COUNT(DISTINCT gws_cust_code) AS customer_count,
         SUM(gws_ytd_sales) AS total_sales
  FROM public.gwanalytics
  WHERE gws_ytd_sales IS NOT NULL
  GROUP BY gws_handled_by, gws_hand_name
  ORDER BY total_sales DESC NULLS LAST

┌──────────────────────────────────────────────────────────────┐
│ STEP 6: SQL VALIDATION                                       │
└──────────────────────────────────────────────────────────────┘
File: backend/sql_validator.py

Step 6.1: Basic Safety (line 15)
  Function: basic_sql_safety()
  Checks:
    ✅ Starts with SELECT
    ❌ No INSERT/UPDATE/DELETE/DROP
    ❌ No semicolons
    ❌ No stored procedures
    
  If fails: HTTP 400 error

Step 6.2: Semantic Validation (line 37)
  Function: validate_against_semantic()
  Checks:
    ✅ Tables exist in semantic.json
    ✅ Columns exist in schema
    ✅ No hallucinated names
    ✅ Follows constraints
    
  If fails: HTTP 400 with helpful error message

┌──────────────────────────────────────────────────────────────┐
│ STEP 7: DATABASE EXECUTION                                    │
└──────────────────────────────────────────────────────────────┘
File: backend/db_connector.py
Function: run_select() (line 12)

Step 7.1: Connection Setup
  - Get DATABASE_URL from environment
  - Create SQLAlchemy engine
  - Enable connection pooling (pool_pre_ping=True)

Step 7.2: Query Execution
  - Add LIMIT if not present (safety)
  - Execute SQL using text() wrapper
  - Fetch all results
  - Convert rows to dictionaries

Step 7.3: Result Format
  [
    {"gws_handled_by": "50149", "gws_hand_name": "John", 
     "customer_count": 25, "total_sales": 150000},
    {"gws_handled_by": "50150", "gws_hand_name": "Jane",
     "customer_count": 30, "total_sales": 180000}
  ]

Step 7.4: Result Validation
  Function: check_query_results()
  - Check if results are meaningful
  - Validate data quality
  - Return warnings if needed

┌──────────────────────────────────────────────────────────────┐
│ STEP 8: ERROR HANDLING (if execution fails)                  │
└──────────────────────────────────────────────────────────────┘
File: backend/sql_agent.py (lines 186-214)

If SQL execution fails:
  1. Capture error message
  2. Build error prompt:
     - Original SQL
     - Error message
  3. Call AI again to fix SQL
  4. Validate fixed SQL
  5. Execute fixed SQL
  6. If still fails: Return error to user

┌──────────────────────────────────────────────────────────────┐
│ STEP 9: RESPONSE CONSTRUCTION                                │
└──────────────────────────────────────────────────────────────┘
File: backend/sql_agent.py (lines 175-185)

Response Format:
  {
    "sql": "SELECT ...",
    "rows": [...],
    "warning": "Optional warning"
  }

HTTP Response:
  Status: 200 OK
  Content-Type: application/json
  Body: JSON response

┌──────────────────────────────────────────────────────────────┐
│ STEP 10: FRONTEND RECEPTION                                  │
└──────────────────────────────────────────────────────────────┘
File: frontend/pages/index.js (lines 93-104)

Step 10.1: Response Handling
  const res = await axios.post(...)
  setSql(res.data.sql)
  setRows(res.data.rows)
  setWarning(res.data.warning)
  setLoading(false)

Step 10.2: Column Auto-Detection (lines 106-119)
  - Analyze first row
  - Detect categorical columns (strings)
  - Detect numerical columns (numbers)
  - Pre-select for visualization

Step 10.3: State Updates
  - sql: Generated SQL query
  - rows: Result data
  - page: Reset to 0
  - warning: Optional warning message
  - loading: Set to false

┌──────────────────────────────────────────────────────────────┐
│ STEP 11: UI RENDERING                                        │
└──────────────────────────────────────────────────────────────┘
File: frontend/pages/index.js

Component 1: SQL Display (lines 485-525)
  - Shows generated SQL in code block
  - Monospace font
  - Row count badge
  - Copy-ready format

Component 2: Results Table (lines 528-634)
  - Header row (sticky)
  - Data rows (paginated)
  - Column names as headers
  - Cell values formatted
  - Null handling (shows "null" in gray)
  
Component 3: Pagination (lines 623-632)
  - Rows per page selector
  - Page navigation
  - Row count display
  - Page number display

Component 4: Action Buttons (lines 534-569)
  - Save Report: Opens save dialog
  - Visualize: Opens chart dialog
  - Export Excel: Downloads file

Component 5: Warnings/Errors (lines 472-482)
  - Error alerts (red)
  - Warning alerts (yellow)
  - Dismissible

┌──────────────────────────────────────────────────────────────┐
│ STEP 12: USER INTERACTION                                    │
└──────────────────────────────────────────────────────────────┘
User can now:
  1. View SQL query
  2. Browse results table
  3. Navigate pages
  4. Save report for later
  5. Create visualization
  6. Export to Excel
  7. Ask new question
```

---

## 🎨 Visualization Workflow Details

### Chart Creation Process

```
USER CLICKS "VISUALIZE"
    │
    ▼
OPEN VISUALIZATION DIALOG
    │
    ├─► Category Column Selector
    │   └─► Dropdown with categorical columns
    │       (strings, codes, names, IDs)
    │
    ├─► Value Column Selector
    │   └─► Dropdown with numerical columns
    │       (numbers, not IDs/codes)
    │
    ├─► Aggregation Method
    │   └─► SUM, AVG, COUNT, MAX, MIN
    │
    └─► Top N Selector
        └─► 5, 10, 15, 20, or All

USER CONFIGURES CHART
    │
    ▼
PREPARE CHART DATA (prepareChartData function)
    │
    ├─► Group rows by category column
    │   └─► Create grouped object
    │
    ├─► Apply aggregation to value column
    │   ├─► SUM: Add all values
    │   ├─► AVG: Average all values
    │   ├─► COUNT: Count occurrences
    │   ├─► MAX: Maximum value
    │   └─► MIN: Minimum value
    │
    ├─► Sort by aggregated value (descending)
    │
    ├─► Take top N items
    │   └─► Group remaining as "Others"
    │
    └─► Calculate percentages
        └─► (value / total) * 100

RENDER CHART (Recharts PieChart)
    │
    ├─► Pie slices (one per category)
    ├─► Colors (rotating palette)
    ├─► Labels (category: percentage)
    ├─► Tooltips (name, value, percentage)
    └─► Legend (category names)

USER CAN:
    ├─► Download as PNG (html2canvas)
    ├─► Adjust settings
    └─► Close dialog
```

### Export to Excel Workflow

```
USER CLICKS "EXPORT TO EXCEL"
    │
    ▼
downloadExcel() FUNCTION (line 137)
    │
    ├─► Check if rows exist
    │
    ├─► Convert rows to worksheet
    │   └─► XLSX.utils.json_to_sheet(rows)
    │
    ├─► Create workbook
    │   └─► XLSX.utils.book_new()
    │
    ├─► Add worksheet to workbook
    │   └─► XLSX.utils.book_append_sheet()
    │
    ├─► Generate filename with timestamp
    │   └─► query_results_2025-12-15.xlsx
    │
    └─► Download file
        └─► XLSX.writeFile()
```

---

## 🔐 Security & Safety Features

### SQL Safety Measures

1. **Read-Only Enforcement**
   - Only SELECT statements allowed
   - Blocks INSERT, UPDATE, DELETE, DROP, ALTER

2. **Semantic Validation**
   - Only tables/columns in semantic.json can be queried
   - Prevents SQL injection via column whitelisting

3. **Query Limits**
   - Maximum rows: 500 (default)
   - Automatic LIMIT added if missing

4. **Input Sanitization**
   - SQL queries are validated before execution
   - No semicolons allowed (prevents multiple statements)

5. **Error Handling**
   - Errors are logged but not exposed to users
   - Generic error messages for security

### Data Privacy

- User-specific report storage (user_id isolation)
- Soft delete for reports (data preservation)
- No direct database access from frontend

---

## 📝 Environment Configuration

### Required Environment Variables

```bash
# Database Connection
DATABASE_URL=postgresql://user:password@host:port/database

# AI Service
GROQ_API_KEY=your_groq_api_key
# OR
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Semantic Layer
SEMANTIC_JSON=backend/metadata/semantic.json
```

### Configuration Files

1. **`.env`**: Environment variables (not in git)
2. **`semantic.json`**: Database schema metadata
3. **`requirements.txt`**: Python dependencies
4. **`package.json`**: Node.js dependencies

---

## 🚀 Deployment Architecture

### Development Setup

```
┌─────────────────────────────────────────────┐
│          Development Machine                 │
│                                              │
│  ┌──────────────┐      ┌──────────────┐    │
│  │   Frontend   │      │   Backend     │    │
│  │              │      │              │    │
│  │ Next.js Dev  │◄────►│ FastAPI/Uvicorn│  │
│  │ Port 3000    │      │ Port 8000     │    │
│  └──────────────┘      └──────┬───────┘    │
│                                │            │
│                                ▼            │
│                        ┌──────────────┐    │
│                        │   Database   │     │
│                        │  (PostgreSQL) │    │
│                        │   Port 5432  │     │
│                        └──────────────┘    │
│                                │            │
│                                ▼            │
│                        ┌──────────────┐    │
│                        │  AI Service  │     │
│                        │  (Groq API)  │     │
│                        │   External   │     │
│                        └──────────────┘    │
└─────────────────────────────────────────────┘
```

### Production Considerations

1. **Frontend**: Build static files, serve via Nginx/CDN
2. **Backend**: Deploy with Gunicorn/Uvicorn behind reverse proxy
3. **Database**: Production PostgreSQL with connection pooling
4. **Security**: HTTPS, authentication, rate limiting
5. **Monitoring**: Logging, error tracking, performance metrics

---

## 📚 Additional Resources

### Key Files Reference

- **Frontend Main**: `frontend/pages/index.js`
- **Backend API**: `backend/sql_agent.py`
- **Database**: `backend/db_connector.py`
- **Validation**: `backend/sql_validator.py`
- **Prompts**: `backend/prompts.py`
- **Semantic Layer**: `backend/metadata/semantic.json`
- **Report Management**: `backend/report_repository.py`

### Documentation Files

- `README.md`: Main project documentation
- `QUICKSTART.md`: Quick setup guide
- `SEMANTIC_LAYER_GUIDE.md`: Semantic layer details
- `REPORTS_API_GUIDE.md`: Report API documentation
- `TESTING_GUIDE.md`: Testing procedures

---

## 🎓 Summary

This Semantic AI Analytics Platform provides a complete end-to-end solution for natural language analytics:

1. **User Experience**: Simple question → Instant results
2. **AI Processing**: Natural language → SQL generation
3. **Data Access**: Direct database connection with safety
4. **Report Management**: Save, organize, and reuse queries
5. **Visualization**: Create charts and export data
6. **Security**: Multiple layers of protection

The system is designed to be:
- **User-Friendly**: Natural language interface
- **Safe**: Multiple validation layers
- **Flexible**: Customizable semantic layer
- **Powerful**: Handles complex queries
- **Maintainable**: Clean code structure

---

**Last Updated**: December 2025
**Version**: 1.0
**Maintained By**: Development Team


