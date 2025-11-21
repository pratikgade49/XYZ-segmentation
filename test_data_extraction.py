"""
Test Script for Enhanced SAP IBP Data Extraction Endpoints
Tests extraction of sales quantity with date filtering and version-specific master data
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Testing: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_response(data: Dict[Any, Any], limit_lines: int = 20):
    lines = json.dumps(data, indent=2).split('\n')
    for line in lines[:limit_lines]:
        print(line)
    if len(lines) > limit_lines:
        print(f"... ({len(lines) - limit_lines} more lines)")

def test_extract_sales_quantity_with_dates():
    """Test extraction of sales quantity with date filtering"""
    print_test("Extract Sales Quantity with Date Filtering")
    try:
        payload = {
            "key_figure": "SALES_QUANTITY",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "top": 1000,
            "skip": 0
        }

        response = requests.post(
            f"{BASE_URL}/api/data-extraction/sales-quantity",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Sales quantity extraction successful")
                summary = data.get('summary', {})
                print(f"  Total records: {summary.get('total_records')}")
                print(f"  Unique products: {summary.get('unique_products')}")
                print(f"  Unique locations: {summary.get('unique_locations')}")
                print(f"  Date range: {summary.get('date_range_covered')}")
                print("\nSample response structure:")
                print_response(data)
                return True
            else:
                print_error(f"API returned error: {data.get('error')}")
                return False
        else:
            print_error(f"Request failed with status code: {response.status_code}")
            print_response(response.json())
            return False

    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False

def test_extract_sales_quantity_with_product_filter():
    """Test extraction of sales quantity with product filter"""
    print_test("Extract Sales Quantity with Product Filter")
    try:
        payload = {
            "key_figure": "SALES_QUANTITY",
            "product_filter": "PRODUCT_001",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "top": 500
        }

        response = requests.post(
            f"{BASE_URL}/api/data-extraction/sales-quantity",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Product-filtered sales quantity extraction successful")
                items = data.get('items', {})
                print(f"  Extracted products: {len(items)}")
                for product_id, item_data in list(items.items())[:2]:
                    print(f"  - {product_id}: {item_data.get('total_points')} data points")
                return True
            else:
                print_error(f"API returned error: {data.get('error')}")
                return False
        else:
            print_error(f"Request failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False

def test_extract_version_specific_master_data():
    """Test extraction of version-specific master data"""
    print_test("Extract Version-Specific Master Data (All)")
    try:
        payload = {}

        response = requests.post(
            f"{BASE_URL}/api/data-extraction/version-specific-master-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Version-specific master data extraction successful")
                version_types = data.get('version_specific_types', [])
                summary = data.get('summary', {})
                print(f"  Total types: {summary.get('total_types')}")
                print(f"  Unique planning areas: {summary.get('unique_planning_areas')}")
                print(f"  Unique versions: {summary.get('unique_versions')}")
                print(f"  Master data types: {summary.get('master_data_types', [])}")
                print(f"  Planning areas: {summary.get('planning_areas', [])}")
                print(f"  Versions: {summary.get('versions', [])}")

                if version_types:
                    print("\n  Sample version-specific types:")
                    for vtype in version_types[:3]:
                        print(f"    - {vtype.get('master_data_type_id')} "
                              f"({vtype.get('planning_area_id')}, {vtype.get('version_id')})")
                return True
            else:
                print_error(f"API returned error: {data.get('error')}")
                return False
        else:
            print_error(f"Request failed with status code: {response.status_code}")
            print_response(response.json())
            return False

    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False

def test_extract_version_specific_by_planning_area():
    """Test extraction of version-specific master data filtered by planning area"""
    print_test("Extract Version-Specific Master Data (by Planning Area)")
    try:
        payload = {
            "planning_area_id": "SAPIBP1"
        }

        response = requests.post(
            f"{BASE_URL}/api/data-extraction/version-specific-master-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Filtered version-specific master data extraction successful")
                summary = data.get('summary', {})
                print(f"  Total types for area 'SAPIBP1': {summary.get('total_types')}")
                print(f"  Versions available: {summary.get('versions', [])}")
                return True
            else:
                print_warning(f"No data found or error: {data.get('error')}")
                return True

        else:
            print_error(f"Request failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False

def test_extract_version_specific_baseline():
    """Test extraction of baseline version data"""
    print_test("Extract Version-Specific Master Data (Baseline Only)")
    try:
        payload = {
            "use_baseline": True
        }

        response = requests.post(
            f"{BASE_URL}/api/data-extraction/version-specific-master-data",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                version_types = data.get('version_specific_types', [])
                baseline_count = sum(1 for vt in version_types if vt.get('is_baseline'))
                print_success(f"Baseline version extraction successful ({baseline_count} baseline types)")
                return True
            else:
                print_warning(f"No baseline data found: {data.get('error')}")
                return True

        else:
            print_error(f"Request failed with status code: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False

def test_extract_sales_quantity_by_product():
    """Test extraction of sales quantity organized as arrays by product"""
    print_test("Extract Sales Quantity By Product (Array Format)")
    try:
        payload = {
            "key_figure": "SALES_QUANTITY",
            "product_ids": ["PRODUCT_001", "PRODUCT_002"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }

        response = requests.post(
            f"{BASE_URL}/api/data-extraction/sales-quantity-by-product",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print_success("Sales quantity by product extraction successful")
                items = data.get('items', {})
                summary = data.get('summary', {})
                print(f"  Total products extracted: {summary.get('total_products')}")
                for product_id, values in list(items.items())[:2]:
                    print(f"  - {product_id}: {len(values)} time periods")
                return True
            else:
                print_error(f"API returned error: {data.get('error')}")
                return False
        else:
            print_error(f"Request failed with status code: {response.status_code}")
            print_response(response.json())
            return False

    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False

def test_pagination():
    """Test pagination with $top and $skip parameters"""
    print_test("Test Pagination ($top and $skip)")
    try:
        payload1 = {
            "key_figure": "SALES_QUANTITY",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "top": 100,
            "skip": 0
        }

        response1 = requests.post(
            f"{BASE_URL}/api/data-extraction/sales-quantity",
            json=payload1,
            headers={"Content-Type": "application/json"}
        )

        if response1.status_code == 200:
            data1 = response1.json()
            total_records = data1.get('summary', {}).get('total_records', 0)
            print(f"  First page (top=100, skip=0): {data1.get('summary', {}).get('total_records')} records")

            if total_records > 100:
                payload2 = {
                    "key_figure": "SALES_QUANTITY",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "top": 100,
                    "skip": 100
                }

                response2 = requests.post(
                    f"{BASE_URL}/api/data-extraction/sales-quantity",
                    json=payload2,
                    headers={"Content-Type": "application/json"}
                )

                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"  Second page (top=100, skip=100): {len(data2.get('items', {}))} items")
                    print_success("Pagination test successful")
                    return True
            else:
                print_warning("Total records less than 100, skipping second page test")
                print_success("Pagination test passed")
                return True
        else:
            print_error(f"Request failed with status code: {response1.status_code}")
            return False

    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False

def run_all_tests():
    print("\n")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}SAP IBP Enhanced Data Extraction - Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Extract Sales Quantity with Date Filtering", test_extract_sales_quantity_with_dates),
        ("Extract Sales Quantity with Product Filter", test_extract_sales_quantity_with_product_filter),
        ("Extract Version-Specific Master Data (All)", test_extract_version_specific_master_data),
        ("Extract Version-Specific Master Data (Filtered)", test_extract_version_specific_by_planning_area),
        ("Extract Baseline Version Data", test_extract_version_specific_baseline),
        ("Extract Sales Quantity by Product", test_extract_sales_quantity_by_product),
        ("Test Pagination", test_pagination),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test {test_name} crashed: {str(e)}")
            results.append((test_name, False))

    print("\n")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.END}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
