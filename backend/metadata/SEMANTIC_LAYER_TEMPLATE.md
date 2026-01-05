# Semantic Layer JSON Template - Complete Reference

This is the **complete, official template** for creating semantic layer JSON files. Use this structure for all new semantic files.

## 📋 Complete Structure

```json
{
  "tables": {
    "schema.table_name": {
      "description": "REQUIRED: Clear description with business keywords",
      "columns": {
        "column_name": {
          "type": "REQUIRED: dimension | measure | date",
          "description": "OPTIONAL: Column description",
          "role": "OPTIONAL: name | code | id",
          "preferred": "OPTIONAL: true | false (default: false)",
          "aliases": "OPTIONAL: Array of alternative names"
        }
      },
      "dimensions": ["REQUIRED: Array of dimension column names"],
      "measures": ["REQUIRED: Array of measure column names"],
      "time_columns": ["REQUIRED: Array of date column names"],
      "derived_measures": ["OPTIONAL: Array of calculated metrics"],
      "quality_rules": ["OPTIONAL: Array of data quality checks"]
    }
  }
}
```

---

## 📝 Field-by-Field Guide

### 1. **Table Name** (`"schema.table_name"`)
- **Format**: `"schema.table_name"` or `"table_name"`
- **Required**: Yes
- **Example**: `"public.gwanalytics"`, `"public.stock_planning_data"`
- **Note**: Must be unique across all files (if same name, second file overwrites first)

### 2. **Description** (`"description"`)
- **Type**: String
- **Required**: Yes
- **Purpose**: Helps AI choose the right table for queries
- **Best Practice**: Include business keywords users might search for
- **Example**: 
  ```json
  "description": "GW Analytics - Sales transactions, customer orders, and salesperson performance data"
  ```
- **Bad Example**: `"Analytics data"` (too vague)
- **Good Example**: `"Stock planning and inventory control metrics by item and location"`

### 3. **Columns** (`"columns"`)
- **Type**: Object (dictionary)
- **Required**: Yes
- **Purpose**: Defines all columns in the table

#### Column Properties:

##### `"type"` (REQUIRED)
- **Values**: `"dimension"` | `"measure"` | `"date"`
- **dimension**: Categorical data (IDs, names, categories, codes)
- **measure**: Numeric data that can be aggregated (amounts, quantities, counts)
- **date**: Date/timestamp columns

##### `"description"` (OPTIONAL)
- **Type**: String
- **Purpose**: Human-readable description of the column
- **Example**: `"Customer name or company name"`

##### `"role"` (OPTIONAL)
- **Values**: `"name"` | `"code"` | `"id"`
- **Purpose**: Indicates the semantic role of the column
- **name**: Human-readable name (e.g., "John Doe")
- **code**: Code or abbreviation (e.g., "CUST001")
- **id**: Unique identifier (e.g., 12345)

##### `"preferred"` (OPTIONAL)
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Marks this as the preferred column for this role
- **Example**: If multiple name columns exist, mark the main one as `true`

##### `"aliases"` (OPTIONAL)
- **Type**: Array of strings
- **Purpose**: Alternative names users might use in queries
- **Critical**: This is how AI maps natural language to columns!
- **Example**: 
  ```json
  "aliases": ["customer name", "cust name", "client name", "company name"]
  ```
- **Best Practice**: Include common variations, abbreviations, and synonyms

### 4. **Dimensions** (`"dimensions"`)
- **Type**: Array of strings
- **Required**: Yes
- **Purpose**: Lists all dimension columns (for grouping/filtering)
- **Note**: Must match column names from `"columns"` object
- **Example**: 
  ```json
  "dimensions": ["customer_id", "customer_name", "region", "status"]
  ```

### 5. **Measures** (`"measures"`)
- **Type**: Array of strings
- **Required**: Yes
- **Purpose**: Lists all measure columns (for aggregation)
- **Note**: Must match column names from `"columns"` object
- **Example**: 
  ```json
  "measures": ["sales_amount", "quantity", "discount_amount"]
  ```

### 6. **Time Columns** (`"time_columns"`)
- **Type**: Array of strings
- **Required**: Yes (can be empty array `[]`)
- **Purpose**: Lists all date/timestamp columns
- **Note**: Must match column names from `"columns"` object
- **Example**: 
  ```json
  "time_columns": ["order_date", "created_at", "updated_at"]
  ```

### 7. **Derived Measures** (`"derived_measures"`) - OPTIONAL
- **Type**: Array of objects
- **Required**: No
- **Purpose**: Calculated metrics using SQL expressions

#### Derived Measure Object:
```json
{
  "name": "metric_name",
  "expression": "SUM(column) / NULLIF(COUNT(*), 0)",
  "type": "sum | avg | ratio | percentage",
  "description": "What this metric represents"
}
```

**Properties:**
- `"name"`: Unique name for the derived measure
- `"expression"`: SQL expression (can reference columns from the table)
- `"type"`: Aggregation type
- `"description"`: Human-readable description

**Examples:**
```json
"derived_measures": [
  {
    "name": "total_revenue",
    "expression": "SUM(sales_amount)",
    "type": "sum",
    "description": "Total revenue across all records"
  },
  {
    "name": "avg_order_value",
    "expression": "AVG(order_amount)",
    "type": "avg",
    "description": "Average order value"
  },
  {
    "name": "discount_rate",
    "expression": "SUM(discount_amount) / NULLIF(SUM(total_amount), 0)",
    "type": "ratio",
    "description": "Discount as percentage of total"
  }
]
```

### 8. **Quality Rules** (`"quality_rules"`) - OPTIONAL
- **Type**: Array of objects
- **Required**: No
- **Purpose**: Data quality checks and validation flags

#### Quality Rule Object:
```json
{
  "name": "rule_name",
  "expression": "CASE WHEN condition THEN 1 ELSE 0 END",
  "description": "What this rule checks"
}
```

**Properties:**
- `"name"`: Unique name for the quality rule
- `"expression"`: SQL CASE expression that returns 1 (flag) or 0 (no flag)
- `"description"`: What condition this rule checks

**Examples:**
```json
"quality_rules": [
  {
    "name": "high_value_flag",
    "expression": "CASE WHEN amount > 100000 THEN 1 ELSE 0 END",
    "description": "Flag for transactions over 100k"
  },
  {
    "name": "missing_data_flag",
    "expression": "CASE WHEN customer_id IS NULL OR amount IS NULL THEN 1 ELSE 0 END",
    "description": "Flag for records with missing critical data"
  }
]
```

---

## ✅ Complete Example

```json
{
  "tables": {
    "public.stock_planning_data": {
      "description": "Stock planning and inventory control metrics by item and location. Contains planned stock quantities, reorder levels, safety stock, and inventory coverage metrics.",
      
      "columns": {
        "spd_date": {
          "type": "date",
          "description": "Date on which stock planning snapshot is taken",
          "aliases": ["date", "planning date", "snapshot date"]
        },
        "spd_company_code": {
          "type": "dimension",
          "description": "Identifier of the company owning the stock",
          "role": "code",
          "aliases": ["company", "company code", "comp code"]
        },
        "spd_item_code": {
          "type": "dimension",
          "description": "Unique identifier of the item",
          "role": "code",
          "aliases": ["item", "item code", "product code", "sku"]
        },
        "spd_stock_level": {
          "type": "measure",
          "description": "Total available stock quantity at snapshot date",
          "aliases": ["stock", "stock level", "inventory", "quantity on hand"]
        },
        "spd_reorder_level": {
          "type": "measure",
          "description": "Reorder threshold quantity",
          "aliases": ["reorder level", "reorder point", "min stock"]
        },
        "spd_planned_value": {
          "type": "measure",
          "description": "Planned inventory value",
          "aliases": ["planned value", "stock value", "inventory value"]
        }
      },
      
      "dimensions": [
        "spd_company_code",
        "spd_item_code"
      ],
      
      "measures": [
        "spd_stock_level",
        "spd_reorder_level",
        "spd_planned_value"
      ],
      
      "time_columns": [
        "spd_date"
      ],
      
      "derived_measures": [
        {
          "name": "total_stock_value",
          "expression": "SUM(spd_planned_value)",
          "type": "sum",
          "description": "Total planned inventory value across all items"
        },
        {
          "name": "stock_coverage_ratio",
          "expression": "SUM(spd_stock_level) / NULLIF(SUM(spd_reorder_level), 0)",
          "type": "ratio",
          "description": "Ratio of current stock to reorder level"
        }
      ],
      
      "quality_rules": [
        {
          "name": "low_stock_flag",
          "expression": "CASE WHEN spd_stock_level < spd_reorder_level THEN 1 ELSE 0 END",
          "description": "Flag for items below reorder level"
        },
        {
          "name": "negative_stock_flag",
          "expression": "CASE WHEN spd_stock_level < 0 THEN 1 ELSE 0 END",
          "description": "Flag for negative stock quantities (data quality issue)"
        }
      ]
    }
  }
}
```

---

## 🎯 Best Practices

### 1. **Table Description**
- ✅ Include business keywords users might search for
- ✅ Be specific about what the table contains
- ✅ Mention key dimensions and measures
- ❌ Don't use vague descriptions like "data" or "information"

### 2. **Column Aliases**
- ✅ Add 3-5 aliases per important column
- ✅ Include common abbreviations
- ✅ Include synonyms and variations
- ✅ Include business terms users might use
- ❌ Don't leave aliases empty for important columns

### 3. **Column Types**
- ✅ Use `"dimension"` for IDs, names, categories, codes
- ✅ Use `"measure"` for numeric values that can be summed/averaged
- ✅ Use `"date"` for date/timestamp columns
- ❌ Don't use `"measure"` for IDs or codes

### 4. **Arrays Must Match**
- ✅ All column names in `dimensions`, `measures`, `time_columns` must exist in `columns`
- ✅ Column names must match exactly (case-sensitive)
- ❌ Don't list columns that don't exist in `columns` object

### 5. **Derived Measures**
- ✅ Use `NULLIF()` to avoid division by zero
- ✅ Reference columns using their exact names
- ✅ Use standard SQL functions (SUM, AVG, COUNT, etc.)
- ❌ Don't use database-specific functions

### 6. **Quality Rules**
- ✅ Return 1 for flag (condition met) or 0 (condition not met)
- ✅ Use CASE WHEN expressions
- ✅ Keep expressions simple and readable
- ❌ Don't use complex subqueries

---

## ⚠️ Common Mistakes

### ❌ Missing Required Fields
```json
{
  "tables": {
    "my_table": {
      "columns": {...}
      // Missing: dimensions, measures, time_columns
    }
  }
}
```

### ❌ Column Not in Arrays
```json
{
  "columns": {
    "customer_id": {"type": "dimension"}
  },
  "dimensions": []  // ❌ customer_id not listed!
}
```

### ❌ Wrong Column Type
```json
{
  "columns": {
    "customer_id": {"type": "measure"}  // ❌ Should be "dimension"
  }
}
```

### ❌ Vague Description
```json
{
  "description": "Data"  // ❌ Too vague, AI can't choose table
}
```

### ❌ Missing Aliases
```json
{
  "columns": {
    "gws_cust_name": {"type": "dimension"}  // ❌ No aliases!
  }
}
```

---

## 📋 Checklist for New Files

When creating a new semantic file, ensure:

- [ ] Table name is unique (not in other files)
- [ ] Description is clear and includes business keywords
- [ ] All columns are defined in `columns` object
- [ ] All columns have correct `type` (dimension/measure/date)
- [ ] Important columns have `aliases` array
- [ ] All dimension columns listed in `dimensions` array
- [ ] All measure columns listed in `measures` array
- [ ] All date columns listed in `time_columns` array
- [ ] Arrays match column names exactly (case-sensitive)
- [ ] Derived measures use valid SQL expressions
- [ ] Quality rules return 1 or 0
- [ ] JSON is valid (no syntax errors)

---

## 🔍 Validation

After creating your file, validate it:

1. **JSON Syntax**: Use a JSON validator
2. **Structure**: Check against this template
3. **Test**: Restart backend and check logs for errors
4. **Query**: Try a simple query to verify it works

---

## 📚 Quick Reference

| Field | Required | Type | Purpose |
|-------|----------|------|---------|
| `description` | ✅ Yes | String | Table description with keywords |
| `columns` | ✅ Yes | Object | All column definitions |
| `columns[].type` | ✅ Yes | String | dimension/measure/date |
| `columns[].description` | ❌ No | String | Column description |
| `columns[].role` | ❌ No | String | name/code/id |
| `columns[].preferred` | ❌ No | Boolean | Preferred column flag |
| `columns[].aliases` | ❌ No | Array | Alternative names |
| `dimensions` | ✅ Yes | Array | List of dimension columns |
| `measures` | ✅ Yes | Array | List of measure columns |
| `time_columns` | ✅ Yes | Array | List of date columns |
| `derived_measures` | ❌ No | Array | Calculated metrics |
| `quality_rules` | ❌ No | Array | Data quality checks |

---

**Use this template for all new semantic layer files!** 🎯

