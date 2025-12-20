# Semantic Layer Guide

This guide explains how to create and customize your semantic layer JSON file.

## What is a Semantic Layer?

The semantic layer is a JSON file that defines:
- **Tables** - Which database tables are accessible
- **Columns** - Which columns exist and their types
- **Dimensions** - Attributes for grouping/filtering (e.g., branch_name, category)
- **Measures** - Numeric values for aggregation (e.g., amount, quantity)
- **Derived Measures** - Calculated metrics (e.g., ratios, percentages)
- **Time Columns** - Date/timestamp columns for time-based queries
- **Quality Rules** - Data quality flags and validations

## Basic Structure

```json
{
  "tables": {
    "table_name": {
      "description": "Human-readable description",
      "columns": { ... },
      "dimensions": [ ... ],
      "measures": [ ... ],
      "time_columns": [ ... ],
      "derived_measures": [ ... ],
      "quality_rules": [ ... ]
    }
  }
}
```

## Column Types

### Dimensions
Categorical or identifier columns used for grouping and filtering.

```json
"columns": {
  "customer_id": {"type": "dimension"},
  "customer_name": {"type": "dimension"},
  "region": {"type": "dimension"},
  "status": {"type": "dimension"}
}
```

**Examples:**
- IDs: `customer_id`, `product_id`, `order_id`
- Names: `customer_name`, `product_name`
- Categories: `region`, `status`, `type`, `category`
- Codes: `country_code`, `currency_code`

### Measures
Numeric columns that can be aggregated (sum, avg, count, etc.).

```json
"columns": {
  "amount": {"type": "measure"},
  "quantity": {"type": "measure"},
  "price": {"type": "measure"},
  "discount": {"type": "measure"}
}
```

**Examples:**
- Money: `amount`, `price`, `revenue`, `cost`
- Quantities: `quantity`, `count`, `units`
- Metrics: `score`, `rating`, `weight`

### Date/Time Columns
Timestamp or date columns for time-based analysis.

```json
"columns": {
  "created_at": {"type": "date"},
  "order_date": {"type": "date"},
  "updated_at": {"type": "date"}
}
```

**Examples:**
- `created_at`, `updated_at`
- `order_date`, `invoice_date`
- `timestamp`, `event_time`

## Derived Measures

Calculated metrics using SQL expressions.

### Sum Aggregation
```json
{
  "name": "total_revenue",
  "expression": "SUM(amount)",
  "type": "sum",
  "description": "Total revenue across all records"
}
```

### Average Aggregation
```json
{
  "name": "avg_order_value",
  "expression": "AVG(amount)",
  "type": "avg",
  "description": "Average order value"
}
```

### Ratios and Percentages
```json
{
  "name": "discount_rate",
  "expression": "SUM(discount_amount) / NULLIF(SUM(total_amount), 0)",
  "type": "ratio",
  "description": "Discount as percentage of total amount"
}
```

### Complex Calculations
```json
{
  "name": "net_revenue",
  "expression": "SUM(gross_amount - discount_amount - tax_amount)",
  "type": "sum",
  "description": "Net revenue after discounts and taxes"
}
```

### Window Functions
```json
{
  "name": "branch_contribution",
  "expression": "SUM(amount) / NULLIF(SUM(amount) OVER (), 0)",
  "type": "percentage",
  "description": "Branch percentage of total sales"
}
```

## Quality Rules

Data quality checks and validation flags.

### Range Checks
```json
{
  "name": "invalid_amount_flag",
  "expression": "CASE WHEN amount <= 0 THEN 1 ELSE 0 END",
  "description": "Flag for invalid amounts (zero or negative)"
}
```

### Threshold Checks
```json
{
  "name": "high_discount_flag",
  "expression": "CASE WHEN discount > 0.3 * amount THEN 1 ELSE 0 END",
  "description": "Flag for discounts exceeding 30%"
}
```

### Completeness Checks
```json
{
  "name": "missing_data_flag",
  "expression": "CASE WHEN customer_id IS NULL OR amount IS NULL THEN 1 ELSE 0 END",
  "description": "Flag for records with missing critical data"
}
```

## Complete Example

```json
{
  "tables": {
    "sales_transactions": {
      "description": "Daily sales transactions with customer and product details",
      "columns": {
        "transaction_id": {"type": "dimension"},
        "transaction_date": {"type": "date"},
        "customer_id": {"type": "dimension"},
        "customer_name": {"type": "dimension"},
        "product_id": {"type": "dimension"},
        "product_category": {"type": "dimension"},
        "region": {"type": "dimension"},
        "quantity": {"type": "measure"},
        "unit_price": {"type": "measure"},
        "total_amount": {"type": "measure"},
        "discount_amount": {"type": "measure"}
      },
      "dimensions": [
        "transaction_id",
        "customer_id",
        "customer_name",
        "product_id",
        "product_category",
        "region"
      ],
      "measures": [
        "quantity",
        "unit_price",
        "total_amount",
        "discount_amount"
      ],
      "time_columns": [
        "transaction_date"
      ],
      "derived_measures": [
        {
          "name": "total_revenue",
          "expression": "SUM(total_amount)",
          "type": "sum",
          "description": "Total sales revenue"
        },
        {
          "name": "avg_transaction_value",
          "expression": "AVG(total_amount)",
          "type": "avg",
          "description": "Average transaction amount"
        },
        {
          "name": "total_quantity_sold",
          "expression": "SUM(quantity)",
          "type": "sum",
          "description": "Total quantity of products sold"
        },
        {
          "name": "discount_rate",
          "expression": "SUM(discount_amount) / NULLIF(SUM(total_amount), 0)",
          "type": "ratio",
          "description": "Discount as percentage of total sales"
        },
        {
          "name": "net_revenue",
          "expression": "SUM(total_amount - discount_amount)",
          "type": "sum",
          "description": "Revenue after discounts"
        }
      ],
      "quality_rules": [
        {
          "name": "negative_amount_flag",
          "expression": "CASE WHEN total_amount < 0 THEN 1 ELSE 0 END",
          "description": "Flag for negative transaction amounts"
        },
        {
          "name": "excessive_discount_flag",
          "expression": "CASE WHEN discount_amount > total_amount THEN 1 ELSE 0 END",
          "description": "Flag where discount exceeds total amount"
        }
      ]
    }
  }
}
```

## Best Practices

### 1. Clear Naming
Use descriptive, consistent names:
- ✅ `total_revenue`, `avg_order_value`, `customer_count`
- ❌ `tr`, `aov`, `cc`

### 2. Add Descriptions
Always include descriptions for clarity:
```json
{
  "name": "paid_ratio",
  "expression": "...",
  "description": "Percentage of invoice amount that has been paid"
}
```

### 3. Handle Division by Zero
Always use `NULLIF` when dividing:
```json
"SUM(amount_paid) / NULLIF(SUM(invoice_amount), 0)"
```

### 4. Use Standard SQL
Stick to vendor-neutral SQL for portability:
- ✅ `SUM()`, `AVG()`, `COUNT()`
- ❌ Database-specific functions

### 5. Group Related Measures
Organize related metrics together:
```json
"derived_measures": [
  // Revenue metrics
  {"name": "total_revenue", ...},
  {"name": "net_revenue", ...},
  
  // Discount metrics
  {"name": "total_discount", ...},
  {"name": "discount_rate", ...}
]
```

## Validation

The SQL Agent validates all generated queries against the semantic layer:

1. **Table Whitelist** - Only tables in semantic.json can be queried
2. **Column Whitelist** - Only defined columns can be referenced
3. **Read-Only** - Only SELECT statements allowed
4. **Safety Checks** - No DROP, DELETE, UPDATE, etc.

## Auto-Generation

Generate semantic layer from DBT manifest:

```bash
# Step 1: Extract metadata
python manifest_reader.py --manifest target/manifest.json --out metadata/metadata.json

# Step 2: Infer semantic layer
python inference_engine.py --metadata metadata/metadata.json --out metadata/inferred.json

# Step 3: Generate final semantic.json
python semantic_generator.py --inferred metadata/inferred.json --out metadata/semantic.json
```

Or use the Makefile:
```bash
make generate-semantic MANIFEST=/path/to/manifest.json
```

## Testing Your Semantic Layer

1. **Validate JSON**
   ```bash
   python -c "import json; json.load(open('backend/metadata/semantic.json'))"
   ```

2. **Check in Agent**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"ok": true, "semantic_loaded": true}`

3. **Test Queries**
   Ask simple questions through the UI:
   - "Show me all dimensions"
   - "What measures are available?"
   - "Give me a count of records"

## Common Patterns

### E-commerce
```json
{
  "dimensions": ["customer_id", "product_id", "category"],
  "measures": ["quantity", "price", "total"],
  "derived_measures": [
    {"name": "revenue", "expression": "SUM(quantity * price)"},
    {"name": "avg_basket", "expression": "AVG(total)"}
  ]
}
```

### Finance
```json
{
  "dimensions": ["account_id", "transaction_type"],
  "measures": ["debit", "credit", "balance"],
  "derived_measures": [
    {"name": "net_change", "expression": "SUM(credit - debit)"}
  ]
}
```

### Operations
```json
{
  "dimensions": ["facility_id", "shift", "operator"],
  "measures": ["units_produced", "defects", "downtime_minutes"],
  "derived_measures": [
    {"name": "defect_rate", "expression": "SUM(defects) / NULLIF(SUM(units_produced), 0)"}
  ]
}
```

## Troubleshooting

### "SQL validation failed"
- Check that all referenced columns are in the semantic layer
- Verify table names match exactly
- Ensure all columns are listed in the `columns` object

### "Semantic JSON not found"
- Verify file exists at `backend/metadata/semantic.json`
- Check `SEMANTIC_JSON` path in `.env` file
- Restart backend server after changes

### "Generated SQL references unknown columns"
- Add missing columns to semantic layer
- Update `dimensions` or `measures` arrays
- Regenerate semantic layer if using DBT

---

For more examples, see `backend/metadata/semantic.json.example`



