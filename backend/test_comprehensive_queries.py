#!/usr/bin/env python3
"""
Comprehensive Query Test Suite
Tests all possible query scenarios including:
- Basic queries
- Complex queries
- Date-based queries
- Queries with typos/grammar mistakes (non-native English)
- Edge cases
"""

import requests
import json
import time
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_query(question: str, category: str, expected_keywords: List[str] = None) -> Tuple[bool, Dict]:
    """Test a single query and return result"""
    print(f"\n{BLUE}[{category}]{RESET} Testing: {question}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"question": question, "max_rows": 100},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            sql = data.get("sql", "")
            rows = data.get("rows", [])
            warning = data.get("warning", "")
            
            # Check if SQL contains expected keywords
            sql_lower = sql.lower()
            if expected_keywords:
                missing = [kw for kw in expected_keywords if kw.lower() not in sql_lower]
                if missing:
                    print(f"{YELLOW}⚠️  Missing expected keywords: {missing}{RESET}")
            
            # Print results
            print(f"{GREEN}✅ SUCCESS{RESET}")
            print(f"   SQL: {sql[:150]}..." if len(sql) > 150 else f"   SQL: {sql}")
            print(f"   Rows returned: {len(rows)}")
            if warning:
                print(f"   {YELLOW}Warning: {warning}{RESET}")
            
            return True, {
                "status": "success",
                "sql": sql,
                "row_count": len(rows),
                "warning": warning
            }
        else:
            error = response.json().get("detail", "Unknown error")
            print(f"{RED}❌ FAILED (Status {response.status_code}){RESET}")
            print(f"   Error: {error}")
            return False, {
                "status": "failed",
                "error": error,
                "status_code": response.status_code
            }
    except Exception as e:
        print(f"{RED}❌ EXCEPTION{RESET}")
        print(f"   Error: {str(e)}")
        return False, {
            "status": "exception",
            "error": str(e)
        }

def run_test_suite():
    """Run comprehensive test suite"""
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0,
        "details": []
    }
    
    # ============================================================================
    # CATEGORY 1: BASIC QUERIES (Simple SELECT statements)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 1: BASIC QUERIES{RESET}")
    print(f"{'='*80}")
    
    basic_queries = [
        ("show me total sales", ["sum", "gws_ytd_sales"]),
        ("total ytd sales", ["sum", "gws_ytd_sales"]),
        ("give me all customer names", ["gws_cust_name"]),
        ("list all handler names", ["gws_hand_name"]),
        ("show me profit loss", ["gws_profit_loss"]),
        ("total outstanding amount", ["sum", "gws_os_amount"]),
        ("count of customers", ["count"]),
    ]
    
    for question, keywords in basic_queries:
        results["total"] += 1
        success, detail = test_query(question, "BASIC", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "BASIC", "question": question, **detail})
        time.sleep(1)  # Rate limiting
    
    # ============================================================================
    # CATEGORY 2: FILTER QUERIES (WHERE clauses)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 2: FILTER QUERIES (WHERE clauses){RESET}")
    print(f"{'='*80}")
    
    filter_queries = [
        ("show sales for handler 50149", ["gws_handled_by", "50149"]),
        ("ytd sales where handled by is 50149", ["gws_handled_by", "where"]),
        ("customer name and sales for customer code 12345", ["gws_cust_code", "where"]),
        ("show me sales above 10000", ["gws_ytd_sales", ">", "10000"]),
        ("outstanding amount greater than 50000", ["gws_os_amount", ">"]),
        ("profit loss less than zero", ["gws_profit_loss", "<", "0"]),
    ]
    
    for question, keywords in filter_queries:
        results["total"] += 1
        success, detail = test_query(question, "FILTER", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "FILTER", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 3: GROUPING QUERIES (GROUP BY)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 3: GROUPING QUERIES (GROUP BY){RESET}")
    print(f"{'='*80}")
    
    grouping_queries = [
        ("sales by handler name", ["group by", "gws_hand_name"]),
        ("total sales grouped by customer name", ["group by", "gws_cust_name"]),
        ("ytd sales by handler", ["group by", "gws_hand_name"]),
        ("outstanding by customer code", ["group by", "gws_cust_code"]),
        ("profit loss by handler name", ["group by", "gws_hand_name"]),
        ("sales and budget by customer", ["group by", "gws_cust_name"]),
    ]
    
    for question, keywords in grouping_queries:
        results["total"] += 1
        success, detail = test_query(question, "GROUPING", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "GROUPING", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 4: TOP-N QUERIES (ORDER BY + LIMIT)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 4: TOP-N QUERIES (ORDER BY + LIMIT){RESET}")
    print(f"{'='*80}")
    
    topn_queries = [
        ("top 5 handler by ytd sales", ["order by", "limit", "5"]),
        ("top 10 customers by sales", ["order by", "limit", "10"]),
        ("show me top 5 handle by ytd sales", ["order by", "limit", "5"]),
        ("bottom 5 customers by outstanding", ["order by", "limit", "5"]),
        ("highest 3 sales", ["order by", "limit", "3"]),
        ("lowest profit loss top 5", ["order by", "limit", "5"]),
    ]
    
    for question, keywords in topn_queries:
        results["total"] += 1
        success, detail = test_query(question, "TOP-N", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "TOP-N", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 5: DATE-BASED QUERIES
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 5: DATE-BASED QUERIES{RESET}")
    print(f"{'='*80}")
    
    date_queries = [
        ("sales on 12 dec 2025", ["gws_date", "2025-12-12"]),
        ("ytd sales as on 12-dec-2025", ["gws_date", "2025-12-12"]),
        ("sales from 1 jan 2025 to 31 dec 2025", ["gws_date", "between", "2025-01-01", "2025-12-31"]),
        ("sales from date 2025-01-01 to 2025-12-31", ["gws_date", "between"]),
        ("sales for last 30 days", ["gws_date", ">="]),
        ("sales for current month", ["gws_date"]),
        ("sales for december 2025", ["gws_date", "2025-12"]),
    ]
    
    for question, keywords in date_queries:
        results["total"] += 1
        success, detail = test_query(question, "DATE", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "DATE", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 6: COMPLEX QUERIES (Multiple clauses)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 6: COMPLEX QUERIES (Multiple clauses){RESET}")
    print(f"{'='*80}")
    
    complex_queries = [
        ("sales by handler name where sales above 10000", ["group by", "where", "having"]),
        ("top 5 customers by sales where outstanding is zero", ["order by", "limit", "where"]),
        ("handler wise total sales for date 12-dec-2025", ["group by", "where", "gws_date"]),
        ("customer name and sales where handled by 50149 and date is 12-dec-2025", ["where", "and"]),
        ("sales by handler having total sales greater than 50000", ["group by", "having"]),
    ]
    
    for question, keywords in complex_queries:
        results["total"] += 1
        success, detail = test_query(question, "COMPLEX", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "COMPLEX", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 7: QUERIES WITH TYPOS & GRAMMAR MISTAKES (Non-native English)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 7: QUERIES WITH TYPOS & GRAMMAR MISTAKES{RESET}")
    print(f"{'='*80}")
    
    typo_queries = [
        ("show me totl sales", ["sum", "gws_ytd_sales"]),  # typo: totl -> total
        ("giv me customer name", ["gws_cust_name"]),  # typo: giv -> give
        ("sales by handlar name", ["group by", "gws_hand_name"]),  # typo: handlar -> handler
        ("top 5 handel by sales", ["order by", "limit"]),  # typo: handel -> handle
        ("ytd salse by customer", ["group by", "gws_ytd_sales"]),  # typo: salse -> sales
        ("show me custmer code", ["gws_cust_code"]),  # typo: custmer -> customer
        ("total outstandng amount", ["sum", "gws_os_amount"]),  # typo: outstandng -> outstanding
        ("sales for handelr 50149", ["gws_handled_by", "50149"]),  # typo: handelr -> handler
        ("profit los by handler", ["gws_profit_loss", "group by"]),  # typo: los -> loss
        ("show top 5 by ytd sal", ["order by", "limit"]),  # typo: sal -> sales
    ]
    
    for question, keywords in typo_queries:
        results["total"] += 1
        success, detail = test_query(question, "TYPO", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "TYPO", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 8: GRAMMAR MISTAKES (Non-native English patterns)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 8: GRAMMAR MISTAKES (Non-native English){RESET}")
    print(f"{'='*80}")
    
    grammar_queries = [
        ("show me sales", ["gws_ytd_sales"]),  # Missing article (should be "the sales")
        ("give total sales", ["sum", "gws_ytd_sales"]),  # Missing "me"
        ("sales by handler name please", ["group by", "gws_hand_name"]),  # Extra "please"
        ("i want see customer name", ["gws_cust_name"]),  # Missing "to"
        ("show sales where handler is 50149", ["gws_handled_by", "where"]),  # "is" instead of "="
        ("total sales group by customer", ["group by", "gws_cust_name"]),  # Missing "by" before group
        ("top 5 sales order by sales", ["order by", "limit"]),  # Redundant but understandable
        ("customer name and their sales", ["gws_cust_name", "gws_ytd_sales"]),  # Natural but informal
        ("show me handler name sales", ["gws_hand_name", "gws_ytd_sales"]),  # Missing "and"
        ("sales for date 12 dec", ["gws_date"]),  # Missing year
    ]
    
    for question, keywords in grammar_queries:
        results["total"] += 1
        success, detail = test_query(question, "GRAMMAR", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "GRAMMAR", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 9: AMBIGUOUS QUERIES (Multiple interpretations)
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 9: AMBIGUOUS QUERIES{RESET}")
    print(f"{'='*80}")
    
    ambiguous_queries = [
        ("show me name", ["gws_cust_name", "gws_hand_name"]),  # Which name?
        ("total amount", ["gws_ytd_sales", "gws_os_amount"]),  # Which amount?
        ("sales by code", ["gws_cust_code", "gws_handled_by"]),  # Which code?
        ("show me top sales", ["order by", "limit"]),  # Top what?
        ("handler total", ["group by", "gws_hand_name"]),  # Total what?
    ]
    
    for question, keywords in ambiguous_queries:
        results["total"] += 1
        success, detail = test_query(question, "AMBIGUOUS", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "AMBIGUOUS", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # CATEGORY 10: EDGE CASES
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}CATEGORY 10: EDGE CASES{RESET}")
    print(f"{'='*80}")
    
    edge_queries = [
        ("show me everything", ["select"]),  # Too vague
        ("all data", ["select"]),  # Too vague
        ("sales", ["gws_ytd_sales"]),  # Single word
        ("total", ["sum"]),  # Single word
        ("", []),  # Empty query (should fail gracefully)
    ]
    
    for question, keywords in edge_queries:
        if not question:  # Skip empty for now
            continue
        results["total"] += 1
        success, detail = test_query(question, "EDGE", keywords)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({"category": "EDGE", "question": question, **detail})
        time.sleep(1)
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print(f"\n{'='*80}")
    print(f"{GREEN}TEST SUMMARY{RESET}")
    print(f"{'='*80}")
    print(f"Total Tests: {results['total']}")
    print(f"{GREEN}Passed: {results['passed']}{RESET}")
    print(f"{RED}Failed: {results['failed']}{RESET}")
    print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
    
    # Save detailed results
    with open("/tmp/query_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{BLUE}Detailed results saved to: /tmp/query_test_results.json{RESET}")
    
    return results

if __name__ == "__main__":
    print(f"{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}COMPREHENSIVE QUERY TEST SUITE{RESET}")
    print(f"{GREEN}{'='*80}{RESET}")
    print(f"Testing backend at: {BASE_URL}")
    print(f"Make sure backend is running before starting tests!")
    
    input("\nPress Enter to start tests...")
    
    results = run_test_suite()
    
    # Print failed tests
    if results["failed"] > 0:
        print(f"\n{RED}FAILED TESTS:{RESET}")
        for detail in results["details"]:
            if detail.get("status") != "success":
                print(f"  - [{detail.get('category')}] {detail.get('question')}")
                print(f"    Error: {detail.get('error', 'Unknown')}")

