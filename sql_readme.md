
# GWAnalytics – SQL Templates for Reporting & Analytics

This document contains **ready-to-use SQL templates** based on the agreed analytics use cases derived from the `gwanalytics` data mart.

> Assumption:  
> - Table name: `gwanalytics`  
> - One row = Customer × Salesperson × Date snapshot  

---

## 1. Direct / General Analytics

---

### 1.1 Salesperson Performance Snapshot

```sql
SELECT
    gws_handled_by,
    gws_hand_name,
    SUM(gws_ytd_sales)        AS ytd_sales,
    SUM(gws_lytd_sales)       AS lytd_sales,
    SUM(gws_ytd_budget)       AS ytd_budget,
    SUM(gws_profit_loss)      AS profit_loss,
    SUM(gws_last90_sales)     AS last_90_days_sales
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_handled_by, gws_hand_name
ORDER BY ytd_sales DESC;
```

---

### 1.2 Customer Health Report

```sql
SELECT
    gws_cust_code,
    gws_cust_name,
    SUM(gws_ytd_sales)      AS ytd_sales,
    SUM(gws_os_amount)      AS total_outstanding,
    SUM(gws_os_abv_90)      AS os_above_90,
    SUM(gws_os_abv_180)     AS os_above_180,
    SUM(gws_unadjusted_amt) AS unadjusted_amount
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_cust_code, gws_cust_name
ORDER BY os_above_90 DESC;
```

---

### 1.3 Collections & Risk Aging Dashboard

```sql
SELECT
    gws_cust_name,
    gws_hand_name,f
    SUM(gws_due_os)        AS due_outstanding,
    SUM(gws_non_due_os)    AS non_due_outstanding,
    SUM(gws_os_abv_90)     AS os_above_90,
    SUM(gws_os_abv_180)    AS os_above_180,
    SUM(gws_pending_cform_amt) AS pending_cform_amount
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_cust_name, gws_hand_name
ORDER BY os_above_180 DESC;
```

---

### 1.4 Pipeline & Work-in-Progress Report

```sql
SELECT
    gws_hand_name,
    gws_industry_code,
    SUM(gws_pending_enq_amt)   AS pending_enquiry_amt,
    SUM(gws_pending_quot_amt)  AS pending_quotation_amt,
    SUM(gws_pending_ao_amt)    AS pending_ao_amt,
    SUM(gws_pending_grb_amt)   AS pending_grb_amt,
    SUM(gws_pending_rdb_amt)   AS pending_rdb_amt
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_hand_name, gws_industry_code
ORDER BY pending_quotation_amt DESC;
```

---

### 1.5 Daily Executive Summary

```sql
SELECT
    gws_date,
    SUM(gws_ytd_sales)        AS total_ytd_sales,
    SUM(gws_cymtd_sale)       AS total_mtd_sales,
    SUM(gws_os_amount)        AS total_outstanding,
    SUM(gws_profit_loss)      AS total_profit_loss,
    SUM(gws_pending_enq_amt +
        gws_pending_quot_amt +
        gws_pending_ao_amt)   AS total_pipeline_value
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_date;
```

---

## 2. Unique / Insight-Driven Analytics

---

### 2.1 Sales vs Outstanding Imbalance Analysis

```sql
SELECT
    gws_cust_name,
    SUM(gws_ytd_sales) AS ytd_sales,
    SUM(gws_os_amount) AS outstanding,
    ROUND(
        SUM(gws_os_amount) / NULLIF(SUM(gws_ytd_sales), 0),
        2
    ) AS os_to_sales_ratio
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_cust_name
HAVING SUM(gws_os_amount) > 0
ORDER BY os_to_sales_ratio DESC;
```

---

### 2.2 Salesperson Risk Concentration Pattern

```sql
SELECT
    gws_hand_name,
    COUNT(DISTINCT gws_cust_code) AS total_customers,
    COUNT(DISTINCT CASE
        WHEN gws_os_abv_90 > 0 THEN gws_cust_code
    END) AS risky_customers_90
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_hand_name
ORDER BY risky_customers_90 DESC;
```

---

### 2.3 Pipeline Conversion Stress Indicator

```sql
SELECT
    gws_hand_name,
    SUM(gws_pending_quot_nos) AS pending_quotations,
    SUM(gws_pending_ao_nos)   AS pending_ao,
    SUM(gws_last90_sales)     AS last_90_days_sales
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_hand_name
ORDER BY pending_quotations DESC;
```

---

### 2.4 Industry Performance vs Risk Matrix

```sql
SELECT
    gws_industry_code,
    SUM(gws_ytd_sales)    AS total_sales,
    SUM(gws_profit_loss)  AS total_profit,
    SUM(gws_os_abv_90)    AS os_above_90
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_industry_code
ORDER BY total_sales DESC;
```

---

### 2.5 Sales Momentum Change Detection

```sql
SELECT
    gws_hand_name,
    SUM(gws_last90_sales) AS last_90_sales,
    SUM(gws_cymtd_sale)   AS current_mtd_sales,
    SUM(gws_lymtd_sale)   AS last_year_mtd_sales
FROM gwanalytics
WHERE gws_date = CURRENT_DATE
GROUP BY gws_hand_name
ORDER BY last_90_sales DESC;
```

---

## Notes
- All queries assume **daily snapshot usage**
- Replace `CURRENT_DATE` with a specific date for historical analysis
- These queries are BI-ready and NL-query friendly

---









Show me salesperson performance with YTD sales, last year sales, budget, profit loss, and last 90 days sales grouped by handler


show me top 5 handle by name ytd sales

give me second top(top 5) outstanding amount handle by name 