# Enhanced SAP IBP Data Extraction Module

This module adds professional-grade data extraction capabilities for SAP Integrated Business Planning (IBP), focusing on sales quantity extraction with date filtering and version-specific master data retrieval.

## Features

### 1. Sales Quantity Extraction with Date Filtering
- Extract historical demand data from SAP IBP Planning Data Service
- Filter by date range (start_date, end_date)
- Optional product-level filtering
- Optional location-level filtering
- Pagination support for large datasets
- Returns organized data by product with timestamps

### 2. Version-Specific Master Data Extraction
- Query VersionSpecificMasterDataTypes entity set
- Filter by PlanningAreaID and VersionID
- Support for baseline version queries
- Discover all available planning areas and versions
- Track baseline vs. scenario versions

### 3. Direct Array Format for Segmentation
- Extract sales data in numpy-compatible array format
- Ready for coefficient of variation calculations
- Direct input to XYZ segmentation algorithm

## Quick Start

### Installation
1. Ensure Flask backend is running:
   ```bash
   python app.py
   ```

2. Dependencies are already in requirements.txt:
   - Flask, numpy, pandas, scikit-learn, scipy

### Extract Sales Data

```bash
curl -X POST http://localhost:5000/api/data-extraction/sales-quantity \
  -H "Content-Type: application/json" \
  -d '{
    "key_figure": "SALES_QUANTITY",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'
```

### Discover Versions

```bash
curl -X POST http://localhost:5000/api/data-extraction/version-specific-master-data \
  -H "Content-Type: application/json" \
  -d '{}'
```

## API Endpoints

### 1. POST /api/data-extraction/sales-quantity
Extract sales quantity with date filtering
- **Parameters**: key_figure, start_date, end_date, product_filter, location_filter, top, skip
- **Response**: Organized data by product with statistics

### 2. POST /api/data-extraction/version-specific-master-data
Extract version-specific master data types
- **Parameters**: master_data_type_id, planning_area_id, version_id, use_baseline
- **Response**: List of version-specific master data with metadata

### 3. POST /api/data-extraction/sales-quantity-by-product
Extract sales as arrays for segmentation
- **Parameters**: key_figure, product_ids, start_date, end_date
- **Response**: Product arrays ready for XYZ segmentation

## Files Included

### Core Implementation
- **sap_data_extraction.py** - SAPDataExtractor class with all extraction methods
- **app.py** - Flask application with new API endpoints (modified)

### Documentation
- **DATA_EXTRACTION_GUIDE.md** - Complete API documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation details
- **USAGE_EXAMPLES.md** - Practical examples and workflows
- **DATA_EXTRACTION_README.md** - This file

### Testing
- **test_data_extraction.py** - Comprehensive test suite with 7 test scenarios

## Documentation

### For Quick Reference
→ **USAGE_EXAMPLES.md** - Real-world examples and workflows

### For Complete Details
→ **DATA_EXTRACTION_GUIDE.md** - Full API specification and reference

### For Technical Understanding
→ **IMPLEMENTATION_SUMMARY.md** - Architecture and design details

## Testing

Run the test suite:
```bash
python test_data_extraction.py
```

Tests cover:
- Sales quantity extraction with dates
- Product filtering
- Location filtering
- Version-specific extraction
- Baseline version queries
- Array format for segmentation
- Pagination

## Integration with XYZ Segmentation

### Complete Workflow

1. **Extract Data**
   ```
   POST /api/data-extraction/sales-quantity-by-product
   ```

2. **Perform Segmentation**
   ```
   POST /api/xyz-segmentation/classify
   ```

3. **Update SAP IBP**
   ```
   POST /api/master-data/[TYPE]/import
   ```

See USAGE_EXAMPLES.md for complete Python code.

## OData Compliance

The implementation follows SAP OData standards:
- Uses $filter for date range queries
- Supports $top and $skip for pagination
- Returns JSON format ($format=json)
- Handles datetime format: `datetime'YYYY-MM-DDTHH:MM:SS'`
- Properly orders results with $orderby

## Date Filtering

All dates use YYYY-MM-DD format:
- Input: `2024-01-01`
- Internally converted to: `datetime'2024-01-01T00:00:00'` (start of day)
- End of day: `datetime'YYYY-MM-DDTHH:MM:SS'` where HH:MM:SS = 23:59:59

## Performance

| Operation | Expected Duration |
|-----------|---|
| Extract 1,000 records | < 1 second |
| Extract 50,000 records | 2-5 seconds |
| Version discovery | < 1 second |
| Filtered extract | 1-2 seconds |

For larger datasets, use pagination with top=50000.

## Error Handling

All endpoints return consistent error format:
```json
{
  "status": "error",
  "error": "Description of the error"
}
```

See DATA_EXTRACTION_GUIDE.md for error troubleshooting.

## SAP IBP Requirements

Your SAP IBP instance must have:
1. Planning Data Service enabled (`/IBP/PLANNING_DATA_API_SRV`)
2. Master Data Service enabled (`/IBP/MASTER_DATA_API_SRV`)
3. OData authentication credentials configured
4. Planning areas and versions configured
5. Key figures defined (e.g., SALES_QUANTITY)
6. Master data types defined (PRODUCT, LOCATION, CUSTOMER, etc.)

## Backward Compatibility

✓ All existing endpoints remain unchanged
✓ All existing functionality preserved
✓ No breaking changes to existing APIs
✓ New functionality is additive only

## Key Algorithms & Calculations

### Date Filtering
- Converts YYYY-MM-DD to OData datetime format
- Applies start-of-day and end-of-day logic
- Combines multiple filter conditions with AND operator

### Version-Specific Extraction
- Queries VersionSpecificMasterDataTypes entity set
- Identifies baseline vs. scenario versions
- Returns comprehensive metadata

### Array Formatting
- Organizes demand values as numpy-compatible arrays
- Maintains temporal ordering
- Filters for minimum data points threshold

## Configuration

The module uses existing SAP IBP configuration from app.py:
- Base URL: Configured in SAP_IBP_CONFIG
- Authentication: Uses configured username/password
- Service paths: Uses MASTER_DATA_API_SRV and PLANNING_DATA_API_SRV

No additional configuration needed.

## Troubleshooting

### No Data Returned
- Verify date range has actual data in SAP IBP
- Check product/location IDs exist
- Confirm key figure name is correct

### Connection Error
- Verify SAP IBP service is running
- Check network connectivity
- Confirm credentials are valid
- Use `/api/debug/test-connection` to verify

### Invalid Parameter Error
- Check date format is YYYY-MM-DD
- Verify required parameters are provided
- Use correct key figure name from SAP IBP

### Timeout on Large Extract
- Use pagination with smaller batch sizes
- Add product or location filters
- Reduce date range
- Use lower `top` parameter value

## Support Resources

### Debug Endpoints Available
- `GET /api/debug/test-connection` - Test SAP connectivity
- `GET /api/debug/validate-config` - Validate configuration
- `GET /api/debug/sample-data/<ENTITY>` - Get sample data
- `GET /api/debug/entity-stats/<ENTITY>` - Get statistics
- `GET /api/debug/discover-all` - Discover all entities

### Documentation
- DATA_EXTRACTION_GUIDE.md - Complete reference
- USAGE_EXAMPLES.md - Practical examples
- IMPLEMENTATION_SUMMARY.md - Technical details

### Testing
Run `python test_data_extraction.py` for comprehensive validation

## Future Enhancements

The implementation provides foundation for:
- Forecast error metric extraction
- Pre-calculated variation metrics
- Multi-period aggregation
- Custom aggregation strategies
- Trend analysis
- Direct forecast recommendations

## Version Information

- **Implementation Version**: 1.0
- **SAP IBP Version**: 2311+
- **OData Version**: OData v2/v4 compatible
- **Python Version**: 3.8+
- **Framework**: Flask 3.0.0+

## License & Support

This implementation is part of the SAP IBP Master Data API integration project. Refer to project documentation for additional support.

## Summary

This module provides production-ready data extraction from SAP IBP with:
- ✓ Date-filtered sales quantity retrieval
- ✓ Version-specific master data discovery
- ✓ Direct integration with XYZ segmentation
- ✓ Comprehensive error handling
- ✓ Full API documentation
- ✓ Complete test coverage
- ✓ Backward compatibility

Start with USAGE_EXAMPLES.md for practical examples or DATA_EXTRACTION_GUIDE.md for complete API reference.
