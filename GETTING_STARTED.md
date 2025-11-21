# Getting Started with Enhanced SAP IBP Data Extraction

Welcome! This guide will get you up and running with the new data extraction capabilities in minutes.

## 5-Minute Quick Start

### Step 1: Start the Flask Application
```bash
python app.py
```

You should see output like:
```
SAP IBP Master Data API - Flask Backend Started
================================================================================
ENHANCED DATA EXTRACTION ENDPOINTS:
  - POST http://localhost:5000/api/data-extraction/sales-quantity
  - POST http://localhost:5000/api/data-extraction/version-specific-master-data
  - POST http://localhost:5000/api/data-extraction/sales-quantity-by-product
...
```

### Step 2: Test Connectivity
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"status": "healthy", "service": "SAP IBP Master Data API"}
```

### Step 3: Extract Your First Data
```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "top": 1000
  }'
```

That's it! You now have historical sales data extracted from SAP IBP.

---

## What You Just Did

The extraction call above:
- Connected to your SAP IBP instance
- Queried the Planning Data Service
- Retrieved 12 months of sales data
- Organized it by product and location
- Returned comprehensive statistics

All in one API call!

---

## Next Steps

### Option 1: Learn by Examples (Recommended)
Go to **USAGE_EXAMPLES.md** and try the practical examples.

### Option 2: Deep Dive into API
Read **DATA_EXTRACTION_GUIDE.md** for complete API specification.

### Option 3: Run Tests
```bash
python test_data_extraction.py
```

This validates all functionality and shows you what's possible.

---

## Common Use Cases

### Use Case 1: Analyze Product Demand
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

### Use Case 2: Discover SAP IBP Versions
```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Use Case 3: Get Data Ready for XYZ Segmentation
```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity-by-product \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

Then use the response directly with:
```bash
POST /api/xyz-segmentation/classify
```

---

## Documentation Map

Choose your learning style:

### For Quick Reference
→ Read **DATA_EXTRACTION_README.md** (2 min read)

### For Learning by Example
→ Read **USAGE_EXAMPLES.md** (10 min read)

### For Complete API Details
→ Read **DATA_EXTRACTION_GUIDE.md** (15 min read)

### For Technical Understanding
→ Read **IMPLEMENTATION_SUMMARY.md** (15 min read)

### For This Implementation
→ Read **IMPLEMENTATION_COMPLETE.md** (5 min read)

---

## Testing

### Run All Tests
```bash
python test_data_extraction.py
```

This will:
- Test sales quantity extraction with dates
- Test product filtering
- Test version-specific extraction
- Test array format for segmentation
- Test pagination
- Validate all responses

### Expected Output
```
================================================================================
SAP IBP Enhanced Data Extraction - Test Suite
================================================================================
✓ Extract Sales Quantity with Date Filtering: PASSED
✓ Extract Sales Quantity with Product Filter: PASSED
✓ Extract Version-Specific Master Data (All): PASSED
✓ Extract Version-Specific Master Data (Filtered): PASSED
✓ Extract Baseline Version Data: PASSED
✓ Extract Sales Quantity by Product: PASSED
✓ Test Pagination: PASSED

Total: 7/7 tests passed
```

---

## Troubleshooting

### Issue: Connection Refused
**Solution**: Make sure Flask is running
```bash
python app.py
```

### Issue: No Data Returned
**Solution**: Check SAP IBP has data for the date range
```bash
curl http://localhost:5000/api/debug/entity-stats/SALES_QUANTITY?service=planning_data
```

### Issue: Invalid Key Figure Name
**Solution**: Discover available key figures
```bash
curl http://localhost:5000/api/debug/discover-all
```

### Issue: Date Format Error
**Solution**: Use YYYY-MM-DD format (not DD-MM-YYYY)
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

---

## Complete XYZ Segmentation Workflow

Once you've extracted data, here's the complete workflow:

### Step 1: Extract Sales Data
```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity-by-product \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

Response gives you:
```json
{
  "items": {
    "PRODUCT_001": [100, 105, 98, 102, ...],
    "PRODUCT_002": [50, 80, 45, 90, ...]
  }
}
```

### Step 2: Run XYZ Segmentation
```bash
curl -X POST http://localhost:5000/api/xyz-segmentation/classify \
  -H "Content-Type: application/json" \
  -d '{
    "items": {
      "PRODUCT_001": [100, 105, 98, 102, ...],
      "PRODUCT_002": [50, 80, 45, 90, ...]
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
    "PRODUCT_001": {
      "segment": "X",
      "coefficient_of_variation": 3.2
    },
    "PRODUCT_002": {
      "segment": "Z",
      "coefficient_of_variation": 42.5
    }
  }
}
```

### Step 3: Update SAP IBP (Optional)
```bash
curl -X POST http://localhost:5000/api/master-data/Y1BPRODUCT/import \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"PRDID": "PRODUCT_001", "XYZ_SEGMENT": "X"},
      {"PRDID": "PRODUCT_002", "XYZ_SEGMENT": "Z"}
    ]
  }'
```

That's it! You've completed a full XYZ segmentation cycle.

---

## Key Concepts

### Date Filtering
- Dates must be in **YYYY-MM-DD** format
- `start_date` = beginning of day (00:00:00)
- `end_date` = end of day (23:59:59)
- Can be empty to get all available data

### Planning Areas & Versions
- **Planning Area**: Container for planning data (e.g., SAPIBP1)
- **Version**: Scenario variant (e.g., BASELINE, UPSIDE, DOWNSIDE)
- **Baseline**: The approved, locked version
- **Scenarios**: What-if versions for simulation

### Key Figures
- **Definition**: Named collection of planning data
- **Examples**: SALES_QUANTITY, FORECAST_DEMAND, ACTUAL_COST
- **Configuration**: Defined in SAP IBP master data
- **Usage**: Specify in key_figure parameter

---

## Python Integration

### Using Requests Library
```python
import requests

response = requests.post(
    'http://localhost:5000/api/data-extraction/sales-quantity-by-product',
    json={
        "key_figure": "SALES_QUANTITY",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)

items = response.json()['items']

for product_id, values in items.items():
    print(f"{product_id}: {len(values)} data points")
```

### Using Pandas
```python
import requests
import pandas as pd

response = requests.post(
    'http://localhost:5000/api/data-extraction/sales-quantity',
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
print(df.describe())
```

---

## Performance Tips

### Tip 1: Use Filters
```json
// Fast - with filter
{"product_filter": "PRODUCT_001", "key_figure": "SALES_QUANTITY"}

// Slow - without filter
{"key_figure": "SALES_QUANTITY"}
```

### Tip 2: Narrow Date Ranges
```json
// Fast - 1 quarter
{"start_date": "2024-10-01", "end_date": "2024-12-31"}

// Slow - 3 years
{"start_date": "2022-01-01", "end_date": "2024-12-31"}
```

### Tip 3: Use Pagination for Large Volumes
```json
// Good - with pagination
{"top": 50000, "skip": 0}

// Might timeout
{"top": 500000}
```

---

## What's New in This Release

✓ Sales quantity extraction with date filtering
✓ Version-specific master data discovery
✓ Direct array format for segmentation
✓ Pagination support
✓ Comprehensive documentation
✓ Full test coverage
✓ Error handling
✓ OData compliance

---

## Support

### Debug Endpoints
Test your SAP IBP configuration:
```bash
curl http://localhost:5000/api/debug/test-connection
curl http://localhost:5000/api/debug/validate-config
curl http://localhost:5000/api/debug/discover-all
```

### Documentation
- **README**: DATA_EXTRACTION_README.md
- **API Reference**: DATA_EXTRACTION_GUIDE.md
- **Examples**: USAGE_EXAMPLES.md
- **Technical**: IMPLEMENTATION_SUMMARY.md

### Testing
```bash
python test_data_extraction.py
```

---

## Ready to Dive In?

1. **Quick Overview**: Read this file (you're doing it!)
2. **Try Examples**: Go to USAGE_EXAMPLES.md
3. **API Details**: Reference DATA_EXTRACTION_GUIDE.md
4. **Run Tests**: Execute test_data_extraction.py
5. **Build Integration**: Start with your use case

---

## Next Steps

### Immediate (Now)
- [ ] Start Flask app
- [ ] Run test suite
- [ ] Try a simple extraction

### Short Term (Next Hour)
- [ ] Read USAGE_EXAMPLES.md
- [ ] Extract data for your products
- [ ] Review the results

### Medium Term (Next Day)
- [ ] Integrate with XYZ segmentation
- [ ] Run complete workflow
- [ ] Update SAP IBP with results

### Long Term (This Week)
- [ ] Set up automated extraction
- [ ] Monitor results
- [ ] Optimize parameters

---

## You're Ready!

You now have everything you need to:
- Extract sales data from SAP IBP with date filtering
- Discover planning areas and versions
- Get data ready for XYZ segmentation
- Integrate with the existing system
- Test and validate everything

Start with the quick examples in USAGE_EXAMPLES.md or dive into the complete API specification in DATA_EXTRACTION_GUIDE.md.

Happy extracting! 🚀
