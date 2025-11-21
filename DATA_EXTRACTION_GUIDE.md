# Enhanced SAP IBP Data Extraction Guide

## Overview

The Enhanced SAP IBP Data Extraction module provides specialized functions to extract:
1. **Sales quantity data** from SAP IBP Planning Data Service with proper date filtering
2. **Version-specific master data** using PlanningAreaID and VersionID parameters

This guide covers all available endpoints, parameters, and usage examples.

---

## 1. Sales Quantity Extraction with Date Filtering

### Endpoint
```
POST /api/data-extraction/sales-quantity
```

### Purpose
Extracts actual sales quantity (or any key figure) from the SAP IBP Planning Data Service with comprehensive filtering capabilities.

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key_figure` | string | Yes | Name of the planning data key figure (e.g., `SALES_QUANTITY`, `YSAPIBP1`) |
| `start_date` | string | No | Start date in format `YYYY-MM-DD` for filtering historical data |
| `end_date` | string | No | End date in format `YYYY-MM-DD` for filtering historical data |
| `product_filter` | string | No | Filter results to specific product ID |
| `location_filter` | string | No | Filter results to specific location ID |
| `top` | integer | No | Number of records to retrieve (default: 10000, max: 50000) |
| `skip` | integer | No | Number of records to skip for pagination (default: 0) |

### Request Example

```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "product_filter": "PRODUCT_001",
    "location_filter": "LOC_A",
    "top": 5000,
    "skip": 0
  }'
```

### Response Example

```json
{
  "status": "success",
  "key_figure": "SALES_QUANTITY",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  },
  "items": {
    "PRODUCT_001": {
      "data_points": [
        {
          "date": "2024-01-01",
          "value": 100,
          "product": "PRODUCT_001",
          "location": "LOC_A"
        },
        {
          "date": "2024-01-02",
          "value": 105,
          "product": "PRODUCT_001",
          "location": "LOC_A"
        }
      ],
      "total_points": 365,
      "locations": ["LOC_A", "LOC_B"],
      "date_range": {
        "min": "2024-01-01",
        "max": "2024-12-31"
      }
    }
  },
  "summary": {
    "total_records": 1000,
    "unique_products": 50,
    "unique_locations": 10,
    "date_range_covered": {
      "min": "2024-01-01",
      "max": "2024-12-31"
    },
    "pagination": {
      "top": 5000,
      "skip": 0
    }
  }
}
```

### Use Cases

1. **Historical Demand Analysis**: Extract 12 months of sales data
   ```json
   {
     "key_figure": "SALES_QUANTITY",
     "start_date": "2024-01-01",
     "end_date": "2024-12-31"
   }
   ```

2. **Specific Product Analysis**: Extract data for one product across all locations
   ```json
   {
     "key_figure": "SALES_QUANTITY",
     "product_filter": "PRODUCT_001",
     "start_date": "2023-01-01",
     "end_date": "2024-12-31"
   }
   ```

3. **Regional Analysis**: Extract data for specific location
   ```json
   {
     "key_figure": "SALES_QUANTITY",
     "location_filter": "WAREHOUSE_NORTH",
     "start_date": "2024-06-01",
     "end_date": "2024-12-31"
   }
   ```

4. **Paginated Extraction**: Get large datasets in batches
   ```json
   {
     "key_figure": "SALES_QUANTITY",
     "top": 50000,
     "skip": 0
   }
   ```
   Then fetch next batch:
   ```json
   {
     "key_figure": "SALES_QUANTITY",
     "top": 50000,
     "skip": 50000
   }
   ```

---

## 2. Version-Specific Master Data Extraction

### Endpoint
```
POST /api/data-extraction/version-specific-master-data
```

### Purpose
Extracts version-specific master data types from SAP IBP using PlanningAreaID and VersionID parameters. This is essential for understanding which master data types are assigned to specific planning areas and versions.

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `master_data_type_id` | string | No | Filter by specific master data type (e.g., `CUSTOMER`, `PRODUCT`, `LOCATION`) |
| `planning_area_id` | string | No | Filter by planning area ID (e.g., `SAPIBP1`, `SAPIBP2`) |
| `version_id` | string | No | Filter by specific version ID (e.g., `UPSIDE`, `DOWNSIDE`) |
| `use_baseline` | boolean | No | If `true`, returns only baseline version data (default: `false`) |

### Request Example

```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{
    "planning_area_id": "SAPIBP1",
    "master_data_type_id": "CUSTOMER"
  }'
```

### Response Example

```json
{
  "status": "success",
  "version_specific_types": [
    {
      "master_data_type_id": "CUSTOMER",
      "planning_area_id": "SAPIBP1",
      "version_id": "__BASELINE",
      "planning_area_descr": "Unified Planning Area",
      "version_name": "Baseline Version",
      "is_baseline": true
    },
    {
      "master_data_type_id": "CUSTOMER",
      "planning_area_id": "SAPIBP1",
      "version_id": "UPSIDE",
      "planning_area_descr": "Unified Planning Area",
      "version_name": "Upside Version",
      "is_baseline": false
    }
  ],
  "summary": {
    "total_types": 10,
    "unique_planning_areas": 2,
    "unique_versions": 5,
    "planning_areas": ["SAPIBP1", "SAPIBP2"],
    "versions": ["__BASELINE", "UPSIDE", "DOWNSIDE"],
    "master_data_types": ["CUSTOMER", "PRODUCT", "LOCATION"],
    "filters_applied": {
      "master_data_type_id": "CUSTOMER",
      "planning_area_id": "SAPIBP1",
      "version_id": null,
      "use_baseline": false
    }
  }
}
```

### Use Cases

1. **Discover All Versions**: See all available planning areas and versions
   ```json
   {}
   ```

2. **Get Baseline Versions Only**: Extract only baseline version master data
   ```json
   {
     "use_baseline": true
   }
   ```

3. **Specific Planning Area**: Find all versions in a planning area
   ```json
   {
     "planning_area_id": "SAPIBP1"
   }
   ```

4. **Specific Master Data Type**: Find all areas and versions for a master data type
   ```json
   {
     "master_data_type_id": "PRODUCT"
   }
   ```

5. **Combined Filters**: Find specific master data type in specific area and version
   ```json
   {
     "master_data_type_id": "PRODUCT",
     "planning_area_id": "SAPIBP1",
     "version_id": "UPSIDE"
   }
   ```

---

## 3. Sales Quantity by Product (Array Format)

### Endpoint
```
POST /api/data-extraction/sales-quantity-by-product
```

### Purpose
Extracts sales quantity organized as arrays per product, formatted specifically for XYZ segmentation analysis. Returns data in a format ready for coefficient of variation calculations.

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key_figure` | string | Yes | Planning data key figure name |
| `product_ids` | array | No | List of specific product IDs to extract (empty = all products) |
| `start_date` | string | No | Start date in `YYYY-MM-DD` format |
| `end_date` | string | No | End date in `YYYY-MM-DD` format |

### Request Example

```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity-by-product \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "product_ids": ["PRODUCT_001", "PRODUCT_002", "PRODUCT_003"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

### Response Example

```json
{
  "status": "success",
  "key_figure": "SALES_QUANTITY",
  "items": {
    "PRODUCT_001": [100, 105, 98, 102, 99, 103, 101, 104, 98, 106, 100, 102],
    "PRODUCT_002": [50, 80, 45, 90, 40, 95, 35, 100, 55, 85, 50, 92],
    "PRODUCT_003": [200, 202, 198, 201, 199, 203, 200, 202, 198, 204, 201, 200]
  },
  "summary": {
    "total_products": 3,
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  },
  "timestamp": "2024-11-21T10:30:45.123456"
}
```

### Use Case: Direct Integration with XYZ Segmentation

```python
import requests

extraction_response = requests.post(
    'http://localhost:5000/api/data-extraction/sales-quantity-by-product',
    json={
        "key_figure": "SALES_QUANTITY",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)

items_data = extraction_response.json()['items']

segmentation_response = requests.post(
    'http://localhost:5000/api/xyz-segmentation/classify',
    json={
        "items": items_data,
        "config": {
            "strategy": "calculate_variation",
            "thresholds": {
                "x_upper_limit": 5.0,
                "y_upper_limit": 25.0
            }
        }
    }
)
```

---

## Date Range Filtering Reference

All date-based filtering follows SAP OData standards with `datetime` format:

- **Start of day**: `2024-01-01T00:00:00`
- **End of day**: `2024-12-31T23:59:59`

The API automatically handles these conversions when you provide dates in `YYYY-MM-DD` format.

### Supported Scenarios

| Scenario | start_date | end_date | Result |
|----------|-----------|----------|--------|
| Last 12 months | `2024-01-01` | `2024-12-31` | Exactly 12 months of data |
| Current year | Current year Jan 1 | Current year Dec 31 | Year-to-date |
| Last quarter | Quarter start date | Quarter end date | Specific quarter |
| Last 30 days | Current date - 30 | Current date | Recent activity |
| All time | Empty | Empty | Complete history |

---

## Pagination for Large Datasets

When extracting large volumes of data, use pagination:

```json
{
  "key_figure": "SALES_QUANTITY",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "top": 50000,
  "skip": 0
}
```

Then fetch next batch:
```json
{
  "key_figure": "SALES_QUANTITY",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "top": 50000,
  "skip": 50000
}
```

**Note**: The API limit for `$top` parameter is 50,000 records. For datasets larger than this, use multiple requests with `skip` parameter.

---

## Error Handling

### Common Error Responses

**Missing required parameter:**
```json
{
  "status": "error",
  "error": "key_figure parameter is required",
  "key_figure": null
}
```

**Invalid date format:**
```json
{
  "status": "error",
  "error": "Invalid date format: 01-01-2024. Expected YYYY-MM-DD",
  "key_figure": "SALES_QUANTITY"
}
```

**SAP IBP connection error:**
```json
{
  "status": "error",
  "error": "SAP OData request failed: [connection error details]",
  "key_figure": "SALES_QUANTITY"
}
```

### Error Resolution

1. **No data returned**: Check that the date range contains actual data in SAP IBP
2. **Invalid key figure**: Verify the planning data key figure name matches SAP IBP configuration
3. **Connection timeout**: Check SAP IBP service availability and network connectivity
4. **Invalid planning area**: Confirm the PlanningAreaID exists in your SAP IBP instance

---

## Integration with XYZ Segmentation

### Complete Workflow

1. **Extract Sales Data**
   ```bash
   POST /api/data-extraction/sales-quantity-by-product
   ```

2. **Perform XYZ Segmentation**
   ```bash
   POST /api/xyz-segmentation/classify
   ```

3. **Write Results Back to SAP IBP**
   ```bash
   POST /api/master-data/[TYPE]/import
   ```

### Example Python Integration

```python
import requests

def xyz_segmentation_workflow():
    base_url = "http://localhost:5000"

    extraction = requests.post(
        f"{base_url}/api/data-extraction/sales-quantity-by-product",
        json={
            "key_figure": "SALES_QUANTITY",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
    )

    items_data = extraction.json()['items']

    segmentation = requests.post(
        f"{base_url}/api/xyz-segmentation/classify",
        json={
            "items": items_data,
            "config": {
                "strategy": "calculate_variation",
                "thresholds": {
                    "x_upper_limit": 10.0,
                    "y_upper_limit": 25.0
                },
                "remove_trend": True,
                "remove_seasonality": True,
                "seasonality_period": 12
            }
        }
    )

    results = segmentation.json()['results']
    return results
```

---

## Performance Considerations

1. **Data Volume**: Maximum 50,000 records per request. For larger datasets, use pagination.
2. **Date Range**: Narrower date ranges are processed faster.
3. **Filters**: Using product_filter or location_filter reduces data transfer.
4. **Pagination**: Sequential pagination is more efficient than large single requests.

---

## Version-Specific Master Data in XYZ Segmentation

### Workflow for Version-Specific Analysis

1. **Discover Available Versions**
   ```bash
   POST /api/data-extraction/version-specific-master-data
   ```

2. **Extract Master Data for Specific Version**
   ```bash
   POST /api/master-data/[TYPE]/extract?$filter=PlanningAreaID eq 'SAPIBP1' and VersionID eq 'UPSIDE'
   ```

3. **Extract Sales Data for Same Version Context**
   ```bash
   POST /api/data-extraction/sales-quantity-by-product
   ```

4. **Perform Segmentation**
   ```bash
   POST /api/xyz-segmentation/classify
   ```

---

## Support for Baseline Versions

To work exclusively with baseline versions:

```json
{
  "use_baseline": true
}
```

This is useful for:
- **Current state analysis**: Baseline represents current approved master data
- **Comparison baseline**: Use baseline as reference point for variance analysis
- **Stable segmentation**: Baseline versions are typically more stable than draft versions

---

## Testing

Run the comprehensive test suite:

```bash
python test_data_extraction.py
```

This will test:
- Sales quantity extraction with date filtering
- Product-specific extraction
- Version-specific master data extraction
- Baseline version extraction
- Array format extraction
- Pagination functionality

---

## Support

For issues or questions regarding data extraction:
1. Check SAP IBP OData service connectivity using debug endpoints
2. Verify key figure and master data type names in SAP IBP
3. Confirm date formats are in `YYYY-MM-DD` format
4. Review error messages for specific SAP IBP API errors
