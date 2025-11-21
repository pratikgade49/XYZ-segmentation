# Enhanced SAP IBP Data Extraction - Usage Examples

## Quick Start Examples

### Example 1: Extract 12 Months of Sales Data

**Request:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

**What this does:**
- Extracts all sales quantity data for the entire year 2024
- Organizes data by product
- Returns date ranges and location information
- Ideal for annual demand analysis

---

### Example 2: Extract Data for Specific Product

**Request:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "product_filter": "PRODUCT_001",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

**What this does:**
- Focuses on a single product
- Shows demand across all locations for this product
- Useful for product-level demand analysis
- Faster response due to filtered scope

---

### Example 3: Discover All Planning Areas and Versions

**Request:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response Summary:**
```json
{
  "summary": {
    "planning_areas": ["SAPIBP1", "SAPIBP2", "SAPIBP3"],
    "versions": ["__BASELINE", "UPSIDE", "DOWNSIDE", "CONSERVATIVE"],
    "master_data_types": ["CUSTOMER", "PRODUCT", "LOCATION", "SUPPLIER"]
  }
}
```

**What this does:**
- Lists all available planning areas in your SAP IBP instance
- Shows all versions you can work with
- Identifies which master data types are version-specific
- First step in understanding your SAP IBP configuration

---

### Example 4: Extract Baseline Version Master Data

**Request:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{
    "use_baseline": true
  }'
```

**What this does:**
- Returns only baseline version master data
- Baseline is the approved, locked version
- Useful for stable reporting and analysis
- Excludes draft or scenario versions

---

### Example 5: Extract Data for XYZ Segmentation

**Request:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity-by-product \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

**Response Format (suitable for XYZ segmentation):**
```json
{
  "items": {
    "PRODUCT_001": [100, 105, 98, 102, 99, 103, 101, 104, ...],
    "PRODUCT_002": [50, 80, 45, 90, 40, 95, 35, 100, ...],
    "PRODUCT_003": [200, 202, 198, 201, 199, 203, 200, 202, ...]
  }
}
```

**What this does:**
- Returns data in array format (perfect for numpy/pandas)
- Ready for coefficient of variation calculations
- Direct input to XYZ segmentation algorithm
- Useful for demand analysis and forecasting

---

## Workflow Examples

### Complete XYZ Segmentation Workflow

**Step 1: Extract Sales Data**
```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity-by-product \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

Response gives you data arrays like:
```json
{
  "items": {
    "SKU_001": [100, 105, 98, 102, ...],
    "SKU_002": [50, 80, 45, 90, ...]
  }
}
```

**Step 2: Run XYZ Segmentation**
```bash
curl -X POST http://localhost:5000/api/xyz-segmentation/classify \
  -H "Content-Type: application/json" \
  -d '{
    "items": {
      "SKU_001": [100, 105, 98, 102, ...],
      "SKU_002": [50, 80, 45, 90, ...]
    },
    "config": {
      "strategy": "calculate_variation",
      "thresholds": {
        "x_upper_limit": 10.0,
        "y_upper_limit": 25.0
      }
    }
  }'
```

Response shows segments:
```json
{
  "results": {
    "SKU_001": {
      "segment": "X",
      "coefficient_of_variation": 3.2,
      "mean_demand": 102.5,
      "std_demand": 3.3
    },
    "SKU_002": {
      "segment": "Z",
      "coefficient_of_variation": 42.5,
      "mean_demand": 65.0,
      "std_demand": 27.6
    }
  },
  "summary": {
    "segment_distribution": {
      "X": 45,
      "Y": 30,
      "Z": 25
    }
  }
}
```

**Step 3: Prepare Update for SAP IBP**
```bash
curl -X POST http://localhost:5000/api/master-data/Y1BPRODUCT/import \
  -H "Content-Type: application/json" \
  -d '{
    "RequestedAttributes": "PRDID,XYZ_SEGMENT",
    "items": [
      {"PRDID": "SKU_001", "XYZ_SEGMENT": "X"},
      {"PRDID": "SKU_002", "XYZ_SEGMENT": "Z"}
    ]
  }'
```

---

### Analyze Specific Planning Area

**Discover what's in SAPIBP1:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{
    "planning_area_id": "SAPIBP1"
  }'
```

**Result:**
```json
{
  "version_specific_types": [
    {
      "master_data_type_id": "PRODUCT",
      "planning_area_id": "SAPIBP1",
      "version_id": "__BASELINE",
      "version_name": "Baseline Version"
    },
    {
      "master_data_type_id": "PRODUCT",
      "planning_area_id": "SAPIBP1",
      "version_id": "UPSIDE",
      "version_name": "Upside Scenario"
    }
  ],
  "summary": {
    "versions": ["__BASELINE", "UPSIDE", "DOWNSIDE"],
    "master_data_types": ["PRODUCT", "LOCATION", "CUSTOMER"]
  }
}
```

**What this tells you:**
- SAPIBP1 has 3 scenarios: baseline, upside, downside
- These scenarios apply to product, location, and customer master data
- You can run separate analyses for each scenario

---

## Python Integration Examples

### Example: Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Extract sales data
extraction_response = requests.post(
    f"{BASE_URL}/api/data-extraction/sales-quantity-by-product",
    json={
        "key_figure": "SALES_QUANTITY",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)

items = extraction_response.json()['items']
print(f"Extracted {len(items)} products")

# Run segmentation
segmentation_response = requests.post(
    f"{BASE_URL}/api/xyz-segmentation/classify",
    json={
        "items": items,
        "config": {
            "strategy": "calculate_variation",
            "thresholds": {
                "x_upper_limit": 10.0,
                "y_upper_limit": 25.0
            }
        }
    }
)

results = segmentation_response.json()['results']

# Show results
for product_id, result in results.items():
    print(f"{product_id}: Segment {result['segment']}, CV: {result['coefficient_of_variation']:.1f}%")
```

### Example: Pandas Integration

```python
import requests
import pandas as pd

response = requests.post(
    "http://localhost:5000/api/data-extraction/sales-quantity",
    json={
        "key_figure": "SALES_QUANTITY",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)

data = response.json()
items = data['items']

# Create DataFrame
rows = []
for product, item_data in items.items():
    for point in item_data['data_points']:
        rows.append({
            'product': product,
            'date': point['date'],
            'quantity': point['value'],
            'location': point['location']
        })

df = pd.DataFrame(rows)
df['date'] = pd.to_datetime(df['date'])

# Analyze
product_summary = df.groupby('product')['quantity'].agg(['mean', 'std', 'count'])
print(product_summary)
```

---

## Advanced Scenarios

### Scenario 1: Multi-Location Analysis

```bash
# Extract for specific location across all products
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "location_filter": "WAREHOUSE_NORTH",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

Useful for:
- Warehouse performance analysis
- Regional demand patterns
- Location-specific inventory planning

---

### Scenario 2: Quarterly Trend Analysis

**Q1 2024:**
```json
{
  "key_figure": "SALES_QUANTITY",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31"
}
```

**Q2 2024:**
```json
{
  "key_figure": "SALES_QUANTITY",
  "start_date": "2024-04-01",
  "end_date": "2024-06-30"
}
```

Compare quarterly variations to identify seasonal patterns or trends.

---

### Scenario 3: New Product Evaluation

Extract recent data for newly launched products:
```json
{
  "key_figure": "SALES_QUANTITY",
  "product_filter": "NEW_SKU_2024",
  "start_date": "2024-09-01",
  "end_date": "2024-12-31"
}
```

---

### Scenario 4: Version-Based Scenario Comparison

**Get baseline version data:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{
    "planning_area_id": "SAPIBP1",
    "version_id": "__BASELINE"
  }'
```

**Get upside scenario data:**
```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{
    "planning_area_id": "SAPIBP1",
    "version_id": "UPSIDE"
  }'
```

Compare master data differences between scenarios.

---

## Error Scenarios & Solutions

### Scenario 1: No Data in Date Range

**Error:**
```json
{
  "status": "success",
  "summary": {
    "total_records": 0,
    "unique_products": 0
  }
}
```

**Solution:**
- Verify the date range has actual data in SAP IBP
- Try a broader date range
- Check if the product exists
- Confirm the key figure name is correct

---

### Scenario 2: Invalid Key Figure Name

**Error:**
```json
{
  "status": "error",
  "error": "SAP OData request failed: 404 Not Found"
}
```

**Solution:**
- Use correct key figure name as defined in SAP IBP
- Common names: SALES_QUANTITY, YSAPIBP1, FORECAST_DEMAND, etc.
- Use debug endpoint to discover available key figures

---

### Scenario 3: Large Dataset Extraction

**Problem:** Need to extract 500,000+ records

**Solution - Use Pagination:**
```python
import requests

BASE_URL = "http://localhost:5000"
all_items = {}
skip = 0
top = 50000

while True:
    response = requests.post(
        f"{BASE_URL}/api/data-extraction/sales-quantity",
        json={
            "key_figure": "SALES_QUANTITY",
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
            "top": top,
            "skip": skip
        }
    )

    data = response.json()
    items = data.get('items', {})

    if not items:
        break

    all_items.update(items)
    skip += top
    print(f"Extracted {len(all_items)} total items")
```

---

## Performance Tips

### Tip 1: Use Filters for Speed
```json
// ✓ FAST - Filtered
{
  "key_figure": "SALES_QUANTITY",
  "product_filter": "PRODUCT_001",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}

// ✗ SLOW - No filters
{
  "key_figure": "SALES_QUANTITY"
}
```

### Tip 2: Narrow Date Ranges
```json
// ✓ FAST - 1 quarter
{
  "start_date": "2024-10-01",
  "end_date": "2024-12-31"
}

// ✗ SLOW - 3 years
{
  "start_date": "2022-01-01",
  "end_date": "2024-12-31"
}
```

### Tip 3: Use Pagination for Large Volumes
```json
// ✓ Better performance
{
  "top": 50000,
  "skip": 0
}
// Then: skip: 50000, then 100000, etc.

// ✗ May timeout
{
  "top": 500000
}
```

---

## Integration Checklist

Before running XYZ segmentation workflow:

- [ ] Verify SAP IBP connectivity: `GET /api/debug/test-connection`
- [ ] Confirm key figure exists: `GET /api/debug/test-entity/SALES_QUANTITY`
- [ ] Check master data type: `GET /api/debug/test-entity/Y1BPRODUCT`
- [ ] Validate configuration: `POST /api/debug/validate-config`
- [ ] Extract sample data to verify format
- [ ] Test segmentation with sample data
- [ ] Review results before updating SAP IBP
- [ ] Prepare batch update for master data

---

## Support & Troubleshooting

### Check Connectivity
```bash
curl http://localhost:5000/health
```

### Test SAP IBP Connection
```bash
curl http://localhost:5000/api/debug/test-connection
```

### Discover Entities
```bash
curl http://localhost:5000/api/debug/discover-all
```

### Get Sample Data
```bash
curl "http://localhost:5000/api/debug/sample-data/SALES_QUANTITY?service=planning_data&top=5"
```

### View Entity Statistics
```bash
curl "http://localhost:5000/api/debug/entity-stats/SALES_QUANTITY?service=planning_data"
```

---

## Next Steps

After successful data extraction:
1. Run XYZ segmentation on extracted data
2. Review segment distribution and metrics
3. Prepare SAP IBP update with segment assignments
4. Execute master data import transaction
5. Commit changes in SAP IBP
6. Monitor and validate results
