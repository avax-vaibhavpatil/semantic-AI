# Multi-Semantic File Architecture

## Problems with Multiple Semantic Files

### Current System Limitations
1. **Single File Path**: Only `semantic_json_path` in settings
2. **No Multi-File Loading**: `FileSemanticRepository` loads one file
3. **No Merging**: Can't combine multiple `SemanticLayer` objects
4. **No Table Selection**: All tables sent to AI (inefficient)

### Performance Issues
- **Huge Prompts**: 10 files × 5 tables = 50 tables in prompt
- **High Costs**: More tokens = expensive AI calls
- **Slow Responses**: Large prompts = slower AI
- **Memory Overhead**: Loading all files every time

### AI Confusion
- Too much context (50+ tables)
- Wrong table selection
- Ambiguous column names

---

## Solution Architecture

### 1. Multi-File Repository (Required)

```python
class MultiFileSemanticRepository(SemanticRepository):
    """
    Loads semantic layers from multiple files
    """
    def __init__(self, semantic_dir: str):
        self.semantic_dir = Path(semantic_dir)
        self._cached_layers: Dict[str, SemanticLayer] = {}
        self._index: TableIndex = None  # For fast searching
    
    async def load_all_semantic(self) -> Dict[str, SemanticLayer]:
        """Load all semantic files from directory"""
        # Load: semantic.json, stock_planning_data.json, etc.
        # Return: {"gwanalytics": SemanticLayer, "stock_planning": SemanticLayer}
    
    async def merge_semantic_layers(self) -> SemanticLayer:
        """Merge all semantic layers into one"""
        # Combine all tables from all files
```

### 2. Table Index (Critical for Efficiency)

```python
class TableIndex:
    """
    Fast search index for finding relevant tables
    """
    def __init__(self):
        self.table_keywords: Dict[str, List[str]] = {}  # table -> keywords
        self.column_keywords: Dict[str, List[str]] = {}  # column -> keywords
        self.aliases_index: Dict[str, str] = {}  # alias -> column
    
    def find_relevant_tables(self, query: str) -> List[str]:
        """
        Find tables relevant to user query
        
        Example:
        Query: "show me stock planning sales"
        Returns: ["stock_planning_data", "gwanalytics"] (if both match)
        """
        query_words = query.lower().split()
        scores = {}
        
        for table_name, keywords in self.table_keywords.items():
            score = sum(1 for word in query_words if word in keywords)
            if score > 0:
                scores[table_name] = score
        
        # Return top 3-5 most relevant tables
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
```

### 3. Smart Table Selection (Efficiency)

```python
class QueryService:
    async def execute_query(self, request: QueryRequest):
        # OLD: Load all tables
        # semantic_layer = await self.semantic_repository.load_semantic()
        
        # NEW: Load only relevant tables
        relevant_tables = self.table_index.find_relevant_tables(request.question)
        semantic_layer = await self.semantic_repository.load_tables(relevant_tables)
        
        # Send only 3-5 tables to AI instead of 50+
```

---

## Implementation Strategy

### Phase 1: Multi-File Loading
1. Update `Settings` to support `semantic_dir` or `semantic_files: List[str]`
2. Create `MultiFileSemanticRepository`
3. Add `SemanticLayer.merge()` method

### Phase 2: Table Indexing
1. Build `TableIndex` from all semantic files
2. Index: table names, column names, aliases, descriptions
3. Cache index in memory

### Phase 3: Smart Selection
1. Extract keywords from user query
2. Match against index
3. Load only relevant tables
4. Send subset to AI

### Phase 4: Caching
1. Cache loaded semantic layers
2. Cache table index
3. Invalidate on file changes (watch files)

---

## Efficiency Comparison

### Current (All Files)
```
Query: "show me sales"
- Load: 10 files (500ms)
- Send to AI: 50 tables, 1000 columns (50KB prompt)
- AI Cost: $0.10 per query
- Response Time: 5-8 seconds
```

### With Smart Selection
```
Query: "show me sales"
- Search Index: 5ms (in-memory)
- Load: 1 file, 2 tables (50ms)
- Send to AI: 2 tables, 40 columns (2KB prompt)
- AI Cost: $0.01 per query
- Response Time: 1-2 seconds
```

**Improvement: 10x faster, 10x cheaper**

---

## Configuration

### Option 1: Directory-Based
```python
# settings.py
semantic_dir: str = "backend/metadata"  # Load all *.json files
```

### Option 2: Explicit List
```python
# settings.py
semantic_files: List[str] = [
    "backend/metadata/semantic.json",
    "backend/metadata/stock_planning_data.json"
]
```

### Option 3: Hybrid (Recommended)
```python
# settings.py
semantic_dir: Optional[str] = "backend/metadata"  # Auto-discover
semantic_files: Optional[List[str]] = None  # Override with explicit list
semantic_table_limit: int = 5  # Max tables to send to AI
```

---

## Is Searching Every File Efficient?

### ❌ NO - Current Approach
- Load all files every query = **SLOW**
- Send all tables to AI = **EXPENSIVE**
- No filtering = **WASTEFUL**

### ✅ YES - With Index
- Build index once at startup = **FAST**
- Search in-memory index = **INSTANT** (5ms)
- Load only relevant files = **EFFICIENT**
- Send subset to AI = **CHEAP**

---

## Recommended Approach

1. **Build Index at Startup** (one-time cost)
2. **Search Index for Each Query** (fast, in-memory)
3. **Load Only Relevant Tables** (lazy loading)
4. **Cache Everything** (avoid repeated I/O)
5. **Watch Files for Changes** (auto-reload)

This gives you:
- ✅ Fast queries (1-2 seconds)
- ✅ Low costs ($0.01 vs $0.10)
- ✅ Scalable (works with 100+ tables)
- ✅ Maintainable (clear separation)

