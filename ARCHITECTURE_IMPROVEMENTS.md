# Architecture Improvements: Query Preprocessing Layer

## Problem Statement

**Issue**: Constantly adding rules to the system prompt is not scalable:
- System prompts become very long (high token cost)
- Hard to maintain and debug
- Rules can conflict with each other
- Doesn't scale well for new patterns

**Example**: The compound location parsing issue required adding complex rules to the system prompt, but this approach doesn't scale.

## Solution: Hybrid Architecture

We've implemented a **hybrid approach** that combines:
1. **Preprocessing Layer** (Programmatic) - Extracts structured entities
2. **System Prompt** (AI Guidance) - High-level rules and examples
3. **Validation Layer** (Post-generation) - Catches errors and retries

## Architecture Components

### 1. Query Preprocessor (`query_preprocessor.py`)

**Purpose**: Extract structured entities from natural language before SQL generation.

**Extracts**:
- Company names (handles compound names like "Shree NM Mumbai branch")
- Branch names (validates against known cities)
- Make/Brand names (maps to database codes, e.g., "Polycab" → "POL")

**Benefits**:
- Reduces system prompt complexity
- Validates entities against database
- Handles compound names intelligently
- Maps brand names to codes automatically

**Example**:
```python
# Input: "list of Polycab items in Shree NM Mumbai branch"
# Output:
{
    "company_name": "Shree NM",
    "branch_name": "Mumbai",
    "make": "POL",
    "enhanced_question": "list of Polycab items in Shree NM Mumbai branch [Extracted entities: Company: Shree NM, Branch: Mumbai, Make/Brand code: POL]"
}
```

### 2. Enhanced System Prompt

**Purpose**: Provide high-level guidance, not detailed parsing rules.

**Changes**:
- Removed complex compound location parsing rules
- Added concise guidance about using extracted entities
- Focuses on SQL generation patterns, not entity extraction

**Benefits**:
- Shorter prompts (lower token cost)
- Easier to maintain
- Less prone to conflicts

### 3. Validation Layer

**Purpose**: Catch errors post-generation and provide feedback.

**Validations**:
- Table selection
- Column existence
- Type mismatches (code vs name columns)
- Extracted entity usage (warnings only)

**Benefits**:
- Catches errors before execution
- Provides targeted feedback to AI
- Enables automatic retry with corrections

## How It Works

### Flow Diagram

```
User Query
    ↓
Query Preprocessor (Extract entities)
    ↓
Enhanced Query + Entity Hints
    ↓
AI SQL Generation (with concise system prompt)
    ↓
Validation Layer (check extracted entities, columns, types)
    ↓
If validation fails → Retry with corrections
    ↓
Execute SQL
```

### Example: "list of Polycab items in Shree NM Mumbai branch"

1. **Preprocessing**:
   - Extracts: company="Shree NM", branch="Mumbai", make="POL"
   - Enhances query with hints

2. **AI Generation**:
   - Receives: Original query + entity hints
   - Generates: `SELECT item_name FROM stock_gw WHERE company_name LIKE '%Shree NM%' AND branch_name = 'Mumbai' AND stgw_make = 'POL'`

3. **Validation**:
   - Checks: Company filter present ✓, Branch filter present ✓, Make filter present ✓
   - All validations pass

## Benefits of This Approach

### 1. Scalability
- **Before**: Each new pattern → add system prompt rule → longer prompts
- **After**: Each new pattern → add preprocessing logic → no prompt changes

### 2. Maintainability
- **Before**: Rules scattered in system prompt, hard to find/update
- **After**: Logic centralized in preprocessor, easy to test/debug

### 3. Token Efficiency
- **Before**: Long system prompts (high cost)
- **After**: Shorter prompts + programmatic extraction (lower cost)

### 4. Accuracy
- **Before**: AI must parse everything from scratch
- **After**: Preprocessor handles complex patterns, AI focuses on SQL generation

### 5. Validation
- **Before**: Errors discovered at execution time
- **After**: Errors caught early with targeted feedback

## When to Use Each Approach

### Use Preprocessing For:
- ✅ Entity extraction (company, branch, make)
- ✅ Value mappings (brand names → codes)
- ✅ Pattern recognition (compound names)
- ✅ Validation against database values

### Use System Prompt For:
- ✅ SQL generation patterns
- ✅ Table selection rules
- ✅ Column usage guidelines
- ✅ General best practices

### Use Validation For:
- ✅ Post-generation checks
- ✅ Error detection
- ✅ Automatic retry with corrections

## Future Improvements

### 1. Dynamic Branch Name Loading
Currently, branch names are hardcoded. We can load them from the database:
```python
# Load branch names from database on startup
branch_names = await load_branch_names_from_db()
preprocessor = QueryPreprocessor(branch_names=branch_names)
```

### 2. Make/Brand Mappings from Database
Load brand mappings from a configuration table:
```python
# Load from database or config file
make_mappings = await load_make_mappings()
preprocessor = QueryPreprocessor(make_mappings=make_mappings)
```

### 3. More Entity Types
Extend preprocessor to extract:
- Date ranges ("last 90 days", "this month")
- Numeric ranges ("above 1000", "between X and Y")
- Category values ("Z category", "A category")

### 4. Machine Learning
Train a model to extract entities instead of rule-based patterns:
- More accurate
- Handles edge cases better
- Learns from user queries

## Best Practices

### 1. Keep System Prompts Concise
- Focus on SQL generation, not entity extraction
- Use examples, not exhaustive rules
- Let preprocessing handle complex patterns

### 2. Test Preprocessing Separately
- Unit test entity extraction
- Test edge cases (compound names, full company names)
- Validate against database values

### 3. Monitor Validation Warnings
- Log when extracted entities aren't used
- Investigate why AI omitted filters
- Adjust preprocessing or prompts as needed

### 4. Iterate Based on Real Queries
- Collect failing queries
- Identify patterns
- Add preprocessing logic for common patterns

## Conclusion

**Key Takeaway**: Don't solve every problem by adding system prompt rules. Use a hybrid approach:
- **Preprocessing** for entity extraction and pattern recognition
- **System prompts** for SQL generation guidance
- **Validation** for error detection and correction

This architecture is more maintainable, scalable, and cost-effective than constantly expanding system prompts.

