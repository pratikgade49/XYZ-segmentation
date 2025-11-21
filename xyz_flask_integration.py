"""
Flask API Integration for XYZ Segmentation
Add these routes to your existing Flask backend
"""

from flask import Blueprint, request, jsonify
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List


from xyz_segmentation import (
    XYZSegmentationEngine, SegmentationConfig, CalculationStrategy,
    AggregationMethod, SegmentationThresholds, XYZSegmentationReport
)

# Create blueprint for XYZ segmentation endpoints
xyz_bp = Blueprint('xyz_segmentation', __name__, url_prefix='/api/xyz-segmentation')


@xyz_bp.route('/classify', methods=['POST'])
def classify_items():
    """
    Classify items using XYZ segmentation
    
    Request Body:
    {
        "items": {
            "PRODUCT_001": [100, 105, 98, 102, 99, 103],
            "PRODUCT_002": [10, 0, 45, 5, 0, 30]
        },
        "config": {
            "strategy": "calculate_variation",
            "thresholds": {
                "x_upper_limit": 5.0,
                "y_upper_limit": 50.0
            },
            "use_cv_squared": false,
            "remove_trend": false,
            "remove_seasonality": false,
            "min_data_points": 6
        }
    }
    
    Response:
    {
        "results": {
            "PRODUCT_001": {
                "segment": "X",
                "variation_value": 2.45,
                "mean_demand": 101.17,
                ...
            }
        },
        "summary": {
            "total_items": 2,
            "segment_distribution": {"X": 1, "Y": 0, "Z": 1}
        }
    }
    """
    try:
        data = request.get_json()
        items_data = data.get('items', {})
        config_data = data.get('config', {})
        
        # Validate input
        if not items_data:
            return jsonify({'error': 'No items data provided'}), 400
        
        # Convert lists to numpy arrays
        items_arrays = {
            item_id: np.array(demand_list, dtype=float)
            for item_id, demand_list in items_data.items()
        }
        
        # Build configuration
        config = build_segmentation_config(config_data)
        
        # Run segmentation
        engine = XYZSegmentationEngine(config)
        
        if config.strategy == CalculationStrategy.CALCULATE_VARIATION:
            results = engine.segment_items(items_arrays)
        else:
            # For aggregate strategy, items_data should contain error metrics
            results = engine.segment_from_error_metrics(items_data)
        
        # Generate summary
        report = XYZSegmentationReport()
        summary = report.generate_summary(results)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@xyz_bp.route('/classify-from-sap', methods=['POST'])
def classify_from_sap():
    """
    Extract demand data from SAP IBP and perform XYZ classification

    Request Body:
    {
        "master_data_type": "Y1BPRODUCT",
        "key_attribute": "PRDID",
        "demand_key_figure": "YSAPIBP1",
        "demand_field": "QUANTITY",
        "time_period": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        },
        "config": {
            "strategy": "calculate_variation",
            "thresholds": {
                "x_upper_limit": 5.0,
                "y_upper_limit": 50.0
            }
        },
        "update_master_data": true,
        "segment_attribute": "XYZ_SEGMENT"
    }
    """
    try:
        data = request.get_json()

        master_data_type = data.get('master_data_type')
        key_attribute = data.get('key_attribute')
        demand_key_figure = data.get('demand_key_figure')
        demand_field = data.get('demand_field', 'QUANTITY')
        time_period = data.get('time_period', {})
        config_data = data.get('config', {})
        update_master_data = data.get('update_master_data', False)
        segment_attribute = data.get('segment_attribute', 'XYZ_SEGMENT')

        # Step 1: Extract demand data from SAP IBP
        items_demand = extract_demand_from_sap(
            master_data_type,
            key_attribute,
            demand_key_figure,
            demand_field,
            time_period
        )
        
        if not items_demand:
            return jsonify({
                'status': 'error',
                'error': 'No demand data extracted from SAP IBP'
            }), 404
        
        # Step 2: Perform XYZ classification
        config = build_segmentation_config(config_data)
        engine = XYZSegmentationEngine(config)
        results = engine.segment_items(items_demand)
        
        # Step 3: Update master data in SAP IBP (if requested)
        if update_master_data:
            update_results = update_segments_in_sap(
                master_data_type,
                key_attribute,
                segment_attribute,
                results
            )
            
            return jsonify({
                'status': 'success',
                'classification_results': results,
                'sap_update_results': update_results,
                'items_processed': len(results),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Generate summary
        report = XYZSegmentationReport()
        summary = report.generate_summary(results)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@xyz_bp.route('/kmeans-classify', methods=['POST'])
def kmeans_classify():
    """
    Classify items using K-means clustering (auto-determine thresholds)
    
    Request Body:
    {
        "items": {
            "ITEM_001": [100, 105, 98, 102],
            "ITEM_002": [50, 70, 55, 65]
        },
        "config": {
            "clusters": 3,
            "remove_trend": true,
            "remove_seasonality": false
        }
    }
    """
    try:
        data = request.get_json()
        items_data = data.get('items', {})
        config_data = data.get('config', {})
        
        # Convert to numpy arrays
        items_arrays = {
            item_id: np.array(demand_list, dtype=float)
            for item_id, demand_list in items_data.items()
        }
        
        # Build K-means configuration
        config = SegmentationConfig(
            strategy=CalculationStrategy.CALCULATE_VARIATION,
            use_kmeans=True,
            kmeans_clusters=config_data.get('clusters', 3),
            remove_trend=config_data.get('remove_trend', False),
            remove_seasonality=config_data.get('remove_seasonality', False),
            seasonality_period=config_data.get('seasonality_period', 12)
        )
        
        # Run segmentation
        engine = XYZSegmentationEngine(config)
        results = engine.segment_items(items_arrays)
        
        # Generate summary
        report = XYZSegmentationReport()
        summary = report.generate_summary(results)
        
        return jsonify({
            'status': 'success',
            'method': 'kmeans',
            'results': results,
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@xyz_bp.route('/batch-classify', methods=['POST'])
def batch_classify():
    """
    Batch classification for large datasets with pagination support
    
    Request Body:
    {
        "batch_size": 1000,
        "items": {...},
        "config": {...}
    }
    """
    try:
        data = request.get_json()
        items_data = data.get('items', {})
        config_data = data.get('config', {})
        batch_size = data.get('batch_size', 1000)
        
        # Convert to numpy arrays
        items_arrays = {
            item_id: np.array(demand_list, dtype=float)
            for item_id, demand_list in items_data.items()
        }
        
        # Build configuration
        config = build_segmentation_config(config_data)
        engine = XYZSegmentationEngine(config)
        
        # Process in batches
        all_results = {}
        item_ids = list(items_arrays.keys())
        
        for i in range(0, len(item_ids), batch_size):
            batch_items = {
                item_id: items_arrays[item_id]
                for item_id in item_ids[i:i+batch_size]
            }
            
            batch_results = engine.segment_items(batch_items)
            all_results.update(batch_results)
        
        # Generate summary
        report = XYZSegmentationReport()
        summary = report.generate_summary(all_results)
        
        return jsonify({
            'status': 'success',
            'results': all_results,
            'summary': summary,
            'batches_processed': (len(item_ids) + batch_size - 1) // batch_size,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@xyz_bp.route('/analyze', methods=['POST'])
def analyze_segments():
    """
    Analyze existing XYZ segments and provide insights
    
    Request Body:
    {
        "master_data_type": "PRODUCT",
        "segment_attribute": "XYZ_SEGMENT",
        "demand_key_figure": "SALES_QTY"
    }
    """
    try:
        data = request.get_json()
        
        master_data_type = data.get('master_data_type')
        segment_attribute = data.get('segment_attribute', 'XYZ_SEGMENT')
        
        # Extract current segments from SAP
        segments_data = extract_segments_from_sap(
            master_data_type,
            segment_attribute
        )
        
        # Analyze distribution
        analysis = {
            'total_items': len(segments_data),
            'segment_distribution': {},
            'recommendations': []
        }
        
        # Count segments
        for segment in ['X', 'Y', 'Z']:
            count = sum(1 for s in segments_data.values() if s == segment)
            percentage = (count / len(segments_data) * 100) if segments_data else 0
            analysis['segment_distribution'][segment] = {
                'count': count,
                'percentage': percentage
            }
        
        # Generate recommendations
        z_percentage = analysis['segment_distribution']['Z']['percentage']
        if z_percentage > 40:
            analysis['recommendations'].append({
                'type': 'high_volatility',
                'message': f'{z_percentage:.1f}% of items are in Z segment (high volatility). '
                          'Consider reviewing forecasting methods for these items.'
            })
        
        x_percentage = analysis['segment_distribution']['X']['percentage']
        if x_percentage > 60:
            analysis['recommendations'].append({
                'type': 'automation_opportunity',
                'message': f'{x_percentage:.1f}% of items are in X segment (low volatility). '
                          'These items are good candidates for automated forecasting.'
            })
        
        return jsonify({
            'status': 'success',
            'analysis': analysis,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Helper functions

def build_segmentation_config(config_data: Dict) -> SegmentationConfig:
    """Build SegmentationConfig from request data"""
    strategy_str = config_data.get('strategy', 'calculate_variation')
    strategy = CalculationStrategy.CALCULATE_VARIATION if strategy_str == 'calculate_variation' \
               else CalculationStrategy.AGGREGATE_OVER_PERIODS
    
    thresholds_data = config_data.get('thresholds', {})
    thresholds = SegmentationThresholds(
        x_upper_limit=thresholds_data.get('x_upper_limit', 0.3),
        y_upper_limit=thresholds_data.get('y_upper_limit', 0.6)
    ) if thresholds_data else None
    
    agg_method_str = config_data.get('aggregation_method', 'average')
    agg_method = AggregationMethod[agg_method_str.upper()]
    
    return SegmentationConfig(
        strategy=strategy,
        thresholds=thresholds,
        use_cv_squared=config_data.get('use_cv_squared', False),
        remove_trend=config_data.get('remove_trend', False),
        remove_seasonality=config_data.get('remove_seasonality', False),
        seasonality_period=config_data.get('seasonality_period', 12),
        aggregation_method=agg_method,
        min_data_points=config_data.get('min_data_points', 6),
        use_kmeans=config_data.get('use_kmeans', False),
        kmeans_clusters=config_data.get('kmeans_clusters', 3)
    )


def extract_demand_from_sap(master_data_type: str, key_attribute: str,
                            demand_key_figure: str, demand_field: str, time_period: Dict) -> Dict[str, np.ndarray]:
    """
    Extract historical demand data from SAP IBP planning data
    This function extracts from planning data entities and joins with master data
    """
    from flask import current_app

    try:
        # Build filter for time period and required dimensions
        filter_conditions = [
            "VERSIONID eq '000'",  # Base version
            "SCENARIOID eq 'BASE'"  # Base scenario
        ]
        if time_period.get('start_date'):
            filter_conditions.append(f"DATE ge '{time_period['start_date']}'")
        if time_period.get('end_date'):
            filter_conditions.append(f"DATE le '{time_period['end_date']}'")

        filter_str = ' and '.join(filter_conditions)

        # Extract data from planning data service
        params = {
            '$select': f'{key_attribute},{demand_field},DATE',
            '$orderby': f'{key_attribute},DATE',
            '$filter': filter_str
        }

        # Use the SAP client for planning data
        sap_client = current_app.config.get('SAP_CLIENT')
        result = sap_client.extract_planning_data(demand_key_figure, params)

        # Parse results and organize by item
        items_demand = {}
        if 'd' in result and 'results' in result['d']:
            for record in result['d']['results']:
                item_id = record.get(key_attribute)
                demand_value = record.get(demand_field, 0)

                if item_id not in items_demand:
                    items_demand[item_id] = []
                items_demand[item_id].append(float(demand_value) if demand_value else 0.0)

        # Convert to numpy arrays
        return {
            item_id: np.array(values, dtype=float)
            for item_id, values in items_demand.items()
            if len(values) > 0  # Only include items with data
        }

    except Exception as e:
        raise Exception(f"Failed to extract demand from SAP: {str(e)}")


def update_segments_in_sap(master_data_type: str, key_attribute: str,
                           segment_attribute: str, results: Dict) -> Dict:
    """
    Update XYZ segment classifications in SAP IBP master data
    """
    from flask import current_app
    
    try:
        sap_client = current_app.config.get('SAP_CLIENT')
        
        # Prepare update payload
        nav_property = f"Nav{master_data_type}"
        items_to_update = [
            {
                key_attribute: item_id,
                segment_attribute: item_data['segment']
            }
            for item_id, item_data in results.items()
        ]
        
        # Build import request
        import_data = {
            'RequestedAttributes': f'{key_attribute},{segment_attribute}',
            'DoCommit': True,
            'TransactionName': 'XYZ Segmentation Update',
            nav_property: items_to_update
        }
        
        # Import to SAP
        result = sap_client.import_master_data(master_data_type, import_data)
        
        return {
            'status': 'success',
            'items_updated': len(items_to_update),
            'transaction_id': import_data.get('TransactionID'),
            'result': result
        }
        
    except Exception as e:
        raise Exception(f"Failed to update segments in SAP: {str(e)}")


def extract_segments_from_sap(master_data_type: str, segment_attribute: str) -> Dict[str, str]:
    """
    Extract current XYZ segment classifications from SAP IBP
    """
    from flask import current_app
    
    try:
        sap_client = current_app.config.get('SAP_CLIENT')
        
        params = {
            '$select': f'PRDID,{segment_attribute}',
            '$format': 'json'
        }
        
        result = sap_client.extract_master_data(master_data_type, params)
        
        segments_data = {}
        if 'd' in result and 'results' in result['d']:
            for record in result['d']['results']:
                item_id = record.get('PRDID')
                segment = record.get(segment_attribute)
                if item_id and segment:
                    segments_data[item_id] = segment
        
        return segments_data
        
    except Exception as e:
        raise Exception(f"Failed to extract segments from SAP: {str(e)}")


# Register blueprint in your main Flask app
# app.register_blueprint(xyz_bp)
# app.config['SAP_CLIENT'] = sap_client  # Make SAP client available to blueprint