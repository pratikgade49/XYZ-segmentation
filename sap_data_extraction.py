"""
Enhanced SAP IBP Data Extraction Module
Provides extraction of sales quantity from planning data service with proper date filtering
and support for version-specific master data using PlanningAreaID and VersionID
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from flask import current_app


class SAPDataExtractor:
    """Enhanced data extraction from SAP IBP OData services"""

    def __init__(self):
        pass

    @staticmethod
    def extract_sales_quantity_with_dates(
        key_figure: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        product_filter: Optional[str] = None,
        location_filter: Optional[str] = None,
        top: int = 10000,
        skip: int = 0
    ) -> Dict:
        """
        Extract actual sales quantity from planning data service with proper date filtering

        Args:
            key_figure: Name of the planning data key figure (e.g., 'SALES_QUANTITY', 'YSAPIBP1')
            start_date: Start date in format 'YYYY-MM-DD' (optional)
            end_date: End date in format 'YYYY-MM-DD' (optional)
            product_filter: Filter by product ID (optional)
            location_filter: Filter by location ID (optional)
            top: Number of records to retrieve (max 50000)
            skip: Number of records to skip for pagination

        Returns:
            Dictionary containing extracted sales quantity data organized by product

        Example response:
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
                        {"date": "2024-01-01", "value": 100, "product": "PRODUCT_001", "location": "LOC_A"},
                        {"date": "2024-01-02", "value": 105, "product": "PRODUCT_001", "location": "LOC_A"}
                    ],
                    "total_points": 365,
                    "locations": ["LOC_A", "LOC_B"],
                    "date_range": {"min": "2024-01-01", "max": "2024-12-31"}
                }
            },
            "summary": {
                "total_records": 1000,
                "unique_products": 50,
                "unique_locations": 10,
                "date_range_covered": 365
            }
        }
        """
        try:
            sap_client = current_app.config.get('SAP_CLIENT')
            if not sap_client:
                raise Exception("SAP client not available in application config")

            filter_conditions = []

            if start_date:
                SAPDataExtractor._validate_date_format(start_date)
                filter_conditions.append(f"DATE ge datetime'{start_date}T00:00:00'")

            if end_date:
                SAPDataExtractor._validate_date_format(end_date)
                filter_conditions.append(f"DATE le datetime'{end_date}T23:59:59'")

            if product_filter:
                filter_conditions.append(f"PRDID eq '{product_filter}'")

            if location_filter:
                filter_conditions.append(f"LOCID eq '{location_filter}'")

            filter_str = ' and '.join(filter_conditions) if filter_conditions else None

            params = {
                '$select': 'PRDID,LOCID,DATE,VALUE',
                '$orderby': 'PRDID,LOCID,DATE',
                '$top': str(top),
                '$skip': str(skip),
                '$format': 'json'
            }

            if filter_str:
                params['$filter'] = filter_str

            result = sap_client.extract_planning_data(key_figure, params)

            items_data = {}
            all_records = []

            if 'd' in result and 'results' in result['d']:
                all_records = result['d']['results']
            elif 'value' in result:
                all_records = result['value']

            min_date = None
            max_date = None
            unique_locations = set()

            for record in all_records:
                product_id = record.get('PRDID')
                location_id = record.get('LOCID')
                date_value = record.get('DATE')
                demand_value = record.get('VALUE', 0)

                if product_id:
                    if product_id not in items_data:
                        items_data[product_id] = {
                            'data_points': [],
                            'locations': set(),
                            'dates': []
                        }

                    items_data[product_id]['data_points'].append({
                        'date': str(date_value) if date_value else None,
                        'value': float(demand_value) if demand_value is not None else 0.0,
                        'product': product_id,
                        'location': location_id or 'UNKNOWN'
                    })

                    if location_id:
                        items_data[product_id]['locations'].add(location_id)
                        unique_locations.add(location_id)

                    if date_value:
                        items_data[product_id]['dates'].append(str(date_value))
                        if min_date is None or str(date_value) < min_date:
                            min_date = str(date_value)
                        if max_date is None or str(date_value) > max_date:
                            max_date = str(date_value)

            formatted_items = {}
            for product_id, data in items_data.items():
                formatted_items[product_id] = {
                    'data_points': data['data_points'],
                    'total_points': len(data['data_points']),
                    'locations': sorted(list(data['locations'])),
                    'date_range': {
                        'min': min(data['dates']) if data['dates'] else None,
                        'max': max(data['dates']) if data['dates'] else None
                    }
                }

            return {
                'status': 'success',
                'key_figure': key_figure,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'items': formatted_items,
                'summary': {
                    'total_records': len(all_records),
                    'unique_products': len(items_data),
                    'unique_locations': len(unique_locations),
                    'date_range_covered': {
                        'min': min_date,
                        'max': max_date
                    },
                    'pagination': {
                        'top': top,
                        'skip': skip
                    }
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'key_figure': key_figure
            }

    @staticmethod
    def extract_version_specific_master_data(
        master_data_type_id: Optional[str] = None,
        planning_area_id: Optional[str] = None,
        version_id: Optional[str] = None,
        use_baseline: bool = False
    ) -> Dict:
        """
        Extract version-specific master data using PlanningAreaID and VersionID

        Args:
            master_data_type_id: Filter by specific master data type (optional)
            planning_area_id: Filter by planning area ID (optional)
            version_id: Filter by version ID (optional)
            use_baseline: If True, use '__BASELINE' for version_id

        Returns:
            Dictionary containing version-specific master data types with their
            planning areas, versions, and descriptions

        Example response:
        {
            "status": "success",
            "version_specific_types": [
                {
                    "master_data_type_id": "CUSTOMER",
                    "planning_area_id": "SAPIBP1",
                    "version_id": "BASELINE",
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
                "master_data_types": ["CUSTOMER", "PRODUCT", "LOCATION"]
            }
        }
        """
        try:
            sap_client = current_app.config.get('SAP_CLIENT')
            if not sap_client:
                raise Exception("SAP client not available in application config")

            filter_conditions = []

            if master_data_type_id:
                filter_conditions.append(f"MasterDataTypeID eq '{master_data_type_id}'")

            if planning_area_id:
                filter_conditions.append(f"PlanningAreaID eq '{planning_area_id}'")

            if use_baseline:
                filter_conditions.append("VersionID eq '__BASELINE'")
            elif version_id:
                filter_conditions.append(f"VersionID eq '{version_id}'")

            filter_str = ' and '.join(filter_conditions) if filter_conditions else None

            params = {
                '$format': 'json',
                '$top': '10000'
            }

            if filter_str:
                params['$filter'] = filter_str

            result = sap_client.list_version_specific_types(params)

            version_types = []
            all_records = []

            if 'd' in result and 'results' in result['d']:
                all_records = result['d']['results']
            elif 'value' in result:
                all_records = result['value']

            unique_planning_areas = set()
            unique_versions = set()
            unique_master_data_types = set()

            for record in all_records:
                mdt_id = record.get('MasterDataTypeID')
                pa_id = record.get('PlanningAreaID')
                ver_id = record.get('VersionID', '')
                pa_descr = record.get('PlanningAreaDescr', '')
                ver_name = record.get('VersionName', '')

                is_baseline = (ver_id == '__BASELINE' or ver_id == '' or
                              ver_id is None or ver_id.upper() == 'BASELINE')

                version_types.append({
                    'master_data_type_id': mdt_id,
                    'planning_area_id': pa_id,
                    'version_id': ver_id if ver_id else '__BASELINE',
                    'planning_area_descr': pa_descr,
                    'version_name': ver_name,
                    'is_baseline': is_baseline,
                    'raw_data': record
                })

                if mdt_id:
                    unique_master_data_types.add(mdt_id)
                if pa_id:
                    unique_planning_areas.add(pa_id)
                if ver_id:
                    unique_versions.add(ver_id)

            return {
                'status': 'success',
                'version_specific_types': version_types,
                'summary': {
                    'total_types': len(version_types),
                    'unique_planning_areas': len(unique_planning_areas),
                    'unique_versions': len(unique_versions),
                    'planning_areas': sorted(list(unique_planning_areas)),
                    'versions': sorted(list(unique_versions)),
                    'master_data_types': sorted(list(unique_master_data_types)),
                    'filters_applied': {
                        'master_data_type_id': master_data_type_id,
                        'planning_area_id': planning_area_id,
                        'version_id': version_id,
                        'use_baseline': use_baseline
                    }
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'filters_applied': {
                    'master_data_type_id': master_data_type_id,
                    'planning_area_id': planning_area_id,
                    'version_id': version_id,
                    'use_baseline': use_baseline
                }
            }

    @staticmethod
    def extract_sales_quantity_by_product(
        key_figure: str,
        product_ids: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, np.ndarray]:
        """
        Extract sales quantity for specific products and return as numpy arrays
        Useful for XYZ segmentation which expects arrays per product

        Args:
            key_figure: Planning data key figure name
            product_ids: List of product IDs to extract
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)

        Returns:
            Dictionary mapping product IDs to numpy arrays of demand values

        Example:
        {
            "PRODUCT_001": np.array([100, 105, 98, 102, 99, 103, 101, 104]),
            "PRODUCT_002": np.array([50, 80, 45, 90, 40, 95, 35, 100])
        }
        """
        try:
            sap_client = current_app.config.get('SAP_CLIENT')
            if not sap_client:
                raise Exception("SAP client not available")

            filter_conditions = []

            if start_date:
                SAPDataExtractor._validate_date_format(start_date)
                filter_conditions.append(f"DATE ge datetime'{start_date}T00:00:00'")

            if end_date:
                SAPDataExtractor._validate_date_format(end_date)
                filter_conditions.append(f"DATE le datetime'{end_date}T23:59:59'")

            filter_str = ' and '.join(filter_conditions) if filter_conditions else None

            params = {
                '$select': 'PRDID,DATE,VALUE',
                '$orderby': 'PRDID,DATE',
                '$format': 'json',
                '$top': '50000'
            }

            if filter_str:
                params['$filter'] = filter_str

            result = sap_client.extract_planning_data(key_figure, params)

            items_demand = {}
            all_records = []

            if 'd' in result and 'results' in result['d']:
                all_records = result['d']['results']
            elif 'value' in result:
                all_records = result['value']

            for record in all_records:
                product_id = record.get('PRDID')
                demand_value = record.get('VALUE', 0)

                if product_id and (not product_ids or product_id in product_ids):
                    if product_id not in items_demand:
                        items_demand[product_id] = []

                    items_demand[product_id].append(
                        float(demand_value) if demand_value is not None else 0.0
                    )

            return {
                product_id: np.array(values, dtype=float)
                for product_id, values in items_demand.items()
                if len(values) > 0
            }

        except Exception as e:
            raise Exception(f"Failed to extract sales quantity by product: {str(e)}")

    @staticmethod
    def _validate_date_format(date_str: str) -> bool:
        """
        Validate date string is in YYYY-MM-DD format

        Args:
            date_str: Date string to validate

        Returns:
            True if valid, raises exception otherwise
        """
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

    @staticmethod
    def get_available_key_figures(service_metadata: Dict) -> List[str]:
        """
        Extract available key figures from OData service metadata

        Args:
            service_metadata: Metadata XML content from planning data service

        Returns:
            List of available key figure entity names
        """
        try:
            import xml.etree.ElementTree as ET

            if isinstance(service_metadata, str):
                root = ET.fromstring(service_metadata)
            else:
                root = service_metadata

            namespaces = {
                'edm': 'http://schemas.microsoft.com/ado/2008/09/edm',
                'edmx': 'http://schemas.microsoft.com/ado/2007/06/edmx'
            }

            key_figures = []
            for entity_set in root.findall('.//edm:EntitySet', namespaces):
                name = entity_set.get('Name')
                if name:
                    key_figures.append(name)

            if not key_figures:
                for entity_set in root.findall('.//{*}EntitySet'):
                    name = entity_set.get('Name')
                    if name:
                        key_figures.append(name)

            return sorted(key_figures)

        except Exception as e:
            raise Exception(f"Failed to parse key figures from metadata: {str(e)}")
