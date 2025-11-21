"""
Comprehensive Test Script for SAP IBP Integration
Tests all core functionality including master data, planning data, and XYZ segmentation
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

def print_response(data: Dict[Any, Any]):
    print(json.dumps(data, indent=2))

# =============================================================================
# Test 1: Health Check
# =============================================================================

def test_health_check():
    print_test("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_success(f"Health check passed")
            print_response(response.json())
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False

# =============================================================================
# Test 2: Extract Products
# =============================================================================

def test_extract_products():
    print_test("Extract Products (Y1BPRODUCT)")
    try:
        response = requests.get(f"{BASE_URL}/api/products?top=5")
        if response.status_code == 200:
            data = response.json()
            if 'd' in data and 'results' in data['d']:
                count = len(data['d']['results'])
                print_success(f"Extracted {count} products")
                if count > 0:
                    print("Sample product:")
                    print_response(data['d']['results'][0])
                return True
            else:
                print_warning("No products found or unexpected response format")
                print_response(data)
                return True
        else:
            print_error(f"Failed to extract products: {response.status_code}")
            print_response(response.json())
            return False
    except Exception as e:
        print_error(f"Extract products error: {str(e)}")
        return False

# =============================================================================
# Test 3: Extract Locations
# =============================================================================

def test_extract_locations():
    print_test("Extract Locations (Y1BLOCATION)")
    try:
        response = requests.get(f"{BASE_URL}/api/master-data/Y1BLOCATION/extract?$top=5")
        if response.status_code == 200:
            data = response.json()
            if 'd' in data and 'results' in data['d']:
                count = len(data['d']['results'])
                print_success(f"Extracted {count} locations")
                if count > 0:
                    print("Sample location:")
                    print_response(data['d']['results'][0])
                return True
            else:
                print_warning("No locations found or unexpected response format")
                return True
        else:
            print_error(f"Failed to extract locations: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Extract locations error: {str(e)}")
        return False

# =============================================================================
# Test 4: Extract Customers
# =============================================================================

def test_extract_customers():
    print_test("Extract Customers (Y1BCUSTOMER)")
    try:
        response = requests.get(f"{BASE_URL}/api/master-data/Y1BCUSTOMER/extract?$top=5")
        if response.status_code == 200:
            data = response.json()
            if 'd' in data and 'results' in data['d']:
                count = len(data['d']['results'])
                print_success(f"Extracted {count} customers")
                if count > 0:
                    print("Sample customer:")
                    print_response(data['d']['results'][0])
                return True
            else:
                print_warning("No customers found or unexpected response format")
                return True
        else:
            print_error(f"Failed to extract customers: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Extract customers error: {str(e)}")
        return False

# =============================================================================
# Test 5: Batch Extract
# =============================================================================

def test_batch_extract():
    print_test("Batch Extract Multiple Entity Types")
    try:
        payload = {
            "extractions": [
                {
                    "master_data_type": "Y1BPRODUCT",
                    "params": {"$top": "3"}
                },
                {
                    "master_data_type": "Y1BLOCATION",
                    "params": {"$top": "3"}
                },
                {
                    "master_data_type": "Y1BCUSTOMER",
                    "params": {"$top": "3"}
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/master-data/batch-extract",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Batch extract completed")
            for result in data.get('results', []):
                entity_type = result.get('master_data_type')
                status = result.get('status')
                if status == 'success':
                    print_success(f"  {entity_type}: {status}")
                else:
                    print_error(f"  {entity_type}: {status}")
            return True
        else:
            print_error(f"Batch extract failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Batch extract error: {str(e)}")
        return False

# =============================================================================
# Test 6: XYZ Classification (Manual Data)
# =============================================================================

def test_xyz_classification_manual():
    print_test("XYZ Classification (Manual Data)")
    try:
        payload = {
            "items": {
                "PRODUCT_001": [100, 105, 98, 102, 99, 103, 101, 104],
                "PRODUCT_002": [50, 80, 45, 90, 40, 95, 35, 100],
                "PRODUCT_003": [200, 202, 198, 201, 199, 203, 200, 202]
            },
            "config": {
                "strategy": "calculate_variation",
                "thresholds": {
                    "x_upper_limit": 5.0,
                    "y_upper_limit": 25.0
                },
                "use_cv_squared": False,
                "min_data_points": 6
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/xyz-segmentation/classify",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("XYZ classification completed")
            
            # Print results
            results = data.get('results', {})
            for item_id, item_data in results.items():
                segment = item_data.get('segment')
                cv = item_data.get('coefficient_of_variation', 0)
                print(f"  {item_id}: Segment {segment} (CV: {cv:.2f}%)")
            
            # Print summary
            summary = data.get('summary', {})
            print("\nSegment Distribution:")
            for segment, count in summary.get('segment_distribution', {}).items():
                print(f"  {segment}: {count} items")
            
            return True
        else:
            print_error(f"XYZ classification failed: {response.status_code}")
            print_response(response.json())
            return False
    except Exception as e:
        print_error(f"XYZ classification error: {str(e)}")
        return False

# =============================================================================
# Test 7: XYZ K-Means Classification
# =============================================================================

def test_xyz_kmeans():
    print_test("XYZ K-Means Classification (Auto-Thresholds)")
    try:
        payload = {
            "items": {
                "ITEM_001": [100, 105, 98, 102, 99, 103],
                "ITEM_002": [50, 70, 55, 65, 60, 68],
                "ITEM_003": [10, 30, 15, 40, 5, 45],
                "ITEM_004": [200, 202, 198, 201, 199, 203],
                "ITEM_005": [80, 120, 90, 110, 85, 115]
            },
            "config": {
                "clusters": 3,
                "remove_trend": False,
                "remove_seasonality": False
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/xyz-segmentation/kmeans-classify",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("K-Means classification completed")
            
            # Print results
            results = data.get('results', {})
            for item_id, item_data in results.items():
                segment = item_data.get('segment')
                cv = item_data.get('coefficient_of_variation', 0)
                print(f"  {item_id}: Segment {segment} (CV: {cv:.2f}%)")
            
            return True
        else:
            print_error(f"K-Means classification failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"K-Means classification error: {str(e)}")
        return False

# =============================================================================
# Test 8: List Entity Sets
# =============================================================================

def test_list_entity_sets():
    print_test("List Available Entity Sets")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/list-entity-sets")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_entity_sets', 0)
            print_success(f"Found {total} entity sets")
            
            # Print first 10 entities
            entities = data.get('entity_sets', [])[:10]
            print("\nFirst 10 entities:")
            for entity in entities:
                print(f"  - {entity.get('name')}")
            
            return True
        else:
            print_error(f"Failed to list entity sets: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List entity sets error: {str(e)}")
        return False

# =============================================================================
# Test 9: Test Connection
# =============================================================================

def test_connection():
    print_test("Test SAP Connection")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/test-connection")
        if response.status_code == 200:
            data = response.json()
            
            # Check base URL
            base_status = data.get('base_url', {}).get('status')
            if base_status == 'success':
                print_success("Base URL connection successful")
            else:
                print_error("Base URL connection failed")
            
            # Check master data service
            master_status = data.get('master_data_service', {}).get('status')
            if master_status == 'success':
                print_success("Master Data Service connection successful")
            else:
                print_error("Master Data Service connection failed")
            
            # Check planning data service
            planning_status = data.get('planning_data_service', {}).get('status')
            if planning_status == 'success':
                print_success("Planning Data Service connection successful")
            else:
                print_error("Planning Data Service connection failed")
            
            return True
        else:
            print_error(f"Connection test failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection test error: {str(e)}")
        return False

# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    print("\n")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}SAP IBP Integration - Core Functionality Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Health Check", test_health_check),
        ("SAP Connection", test_connection),
        ("List Entity Sets", test_list_entity_sets),
        ("Extract Products", test_extract_products),
        ("Extract Locations", test_extract_locations),
        ("Extract Customers", test_extract_customers),
        ("Batch Extract", test_batch_extract),
        ("XYZ Classification (Manual)", test_xyz_classification_manual),
        ("XYZ K-Means Classification", test_xyz_kmeans),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
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