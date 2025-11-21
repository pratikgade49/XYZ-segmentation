"""
Complete XYZ Segmentation Implementation for SAP IBP
Fully functional with all features: trend removal, seasonality removal, K-means clustering, and more
"""

from flask import Blueprint, request, jsonify, current_app
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from scipy import signal
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class CalculationStrategy(Enum):
    CALCULATE_VARIATION = "calculate_variation"
    AGGREGATE_OVER_PERIODS = "aggregate_over_periods"


class AggregationMethod(Enum):
    AVERAGE = "average"
    MEDIAN = "median"
    SUM = "sum"
    MIN = "min"
    MAX = "max"


@dataclass
class SegmentationThresholds:
    x_upper_limit: float
    y_upper_limit: float


@dataclass
class SegmentationConfig:
    strategy: CalculationStrategy
    thresholds: Optional[SegmentationThresholds] = None
    use_cv_squared: bool = False
    remove_trend: bool = False
    remove_seasonality: bool = False
    seasonality_period: int = 12
    aggregation_method: AggregationMethod = AggregationMethod.AVERAGE
    min_data_points: int = 6
    use_kmeans: bool = False
    kmeans_clusters: int = 3
    outlier_removal: bool = False
    outlier_std_threshold: float = 3.0


# ============================================================================
# XYZ SEGMENTATION ENGINE
# ============================================================================

class XYZSegmentationEngine:
    """Complete XYZ segmentation engine with all features"""

    def __init__(self, config: SegmentationConfig):
        self.config = config

    def segment_items(self, items: Dict[str, np.ndarray]) -> Dict[str, Dict]:
        """
        Segment items based on demand variation with full preprocessing
        """
        results = {}
        
        for item_id, demand_data in items.items():
            try:
                # Validate data
                if not self._validate_data(demand_data):
                    continue
                
                # Preprocess data
                processed_data = demand_data.copy()
                
                # Remove outliers if configured
                if self.config.outlier_removal:
                    processed_data = self._remove_outliers(processed_data)
                
                # Remove trend if configured
                if self.config.remove_trend:
                    processed_data = self._detrend_data(processed_data)
                
                # Remove seasonality if configured
                if self.config.remove_seasonality:
                    processed_data = self._remove_seasonality(processed_data)
                
                # Calculate variation metrics
                mean_demand = np.mean(demand_data)  # Use original for mean
                std_demand = np.std(processed_data)  # Use processed for std
                
                if mean_demand == 0:
                    cv = 0.0 if std_demand == 0 else float('inf')
                else:
                    cv = (std_demand / mean_demand) * 100
                
                variation_value = cv ** 2 if self.config.use_cv_squared else cv
                
                # Classify segment
                segment = self._classify_segment(variation_value)
                
                results[item_id] = {
                    'segment': segment,
                    'variation_value': float(variation_value),
                    'mean_demand': float(mean_demand),
                    'std_demand': float(std_demand),
                    'coefficient_of_variation': float(cv),
                    'data_points': len(demand_data),
                    'trend_removed': self.config.remove_trend,
                    'seasonality_removed': self.config.remove_seasonality,
                    'outliers_removed': self.config.outlier_removal
                }
            
            except Exception as e:
                results[item_id] = {
                    'segment': 'Z',
                    'error': str(e),
                    'data_points': len(demand_data) if demand_data is not None else 0
                }
        
        # Apply K-means if configured
        if self.config.use_kmeans and len(results) >= self.config.kmeans_clusters:
            results = self._apply_kmeans_classification(results)
        
        return results

    def segment_from_error_metrics(self, error_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Segment items based on pre-calculated error metrics using aggregate strategy
        
        error_data format:
        {
            "PRODUCT_001": {
                "2024-Q1": 5.2,
                "2024-Q2": 6.1,
                "2024-Q3": 5.8,
                "2024-Q4": 6.3
            }
        }
        """
        results = {}
        
        for item_id, period_errors in error_data.items():
            try:
                if not period_errors or not isinstance(period_errors, dict):
                    continue
                
                error_values = [float(v) for v in period_errors.values() if v is not None]
                
                if not error_values:
                    continue
                
                # Aggregate over periods using configured method
                if self.config.aggregation_method == AggregationMethod.AVERAGE:
                    aggregated_error = np.mean(error_values)
                elif self.config.aggregation_method == AggregationMethod.MEDIAN:
                    aggregated_error = np.median(error_values)
                elif self.config.aggregation_method == AggregationMethod.SUM:
                    aggregated_error = np.sum(error_values)
                elif self.config.aggregation_method == AggregationMethod.MIN:
                    aggregated_error = np.min(error_values)
                elif self.config.aggregation_method == AggregationMethod.MAX:
                    aggregated_error = np.max(error_values)
                else:
                    aggregated_error = np.mean(error_values)
                
                segment = self._classify_segment(aggregated_error)
                
                results[item_id] = {
                    'segment': segment,
                    'aggregated_error': float(aggregated_error),
                    'aggregation_method': self.config.aggregation_method.value,
                    'period_count': len(period_errors),
                    'min_error': float(np.min(error_values)),
                    'max_error': float(np.max(error_values)),
                    'mean_error': float(np.mean(error_values)),
                    'std_error': float(np.std(error_values))
                }
            
            except Exception as e:
                results[item_id] = {
                    'segment': 'Z',
                    'error': str(e)
                }
        
        return results

    # ========================================================================
    # PREPROCESSING METHODS
    # ========================================================================

    def _validate_data(self, demand_data: np.ndarray) -> bool:
        """Validate demand data"""
        if demand_data is None or len(demand_data) < self.config.min_data_points:
            return False
        
        # Check for all NaN or all zero
        if np.all(np.isnan(demand_data)) or len(demand_data[demand_data != 0]) == 0:
            return False
        
        return True

    def _remove_outliers(self, data: np.ndarray) -> np.ndarray:
        """Remove outliers using z-score method"""
        data = data.copy()
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return data
        
        z_scores = np.abs((data - mean) / std)
        outlier_mask = z_scores > self.config.outlier_std_threshold
        
        if np.any(outlier_mask):
            # Replace outliers with local average
            for i in np.where(outlier_mask)[0]:
                neighbors = []
                for j in range(max(0, i-2), min(len(data), i+3)):
                    if j != i and not outlier_mask[j]:
                        neighbors.append(data[j])
                
                if neighbors:
                    data[i] = np.mean(neighbors)
        
        return data

    def _detrend_data(self, data: np.ndarray) -> np.ndarray:
        """Remove trend using multiple methods"""
        if len(data) < 3:
            return data
        
        # Use scipy's detrend with linear method
        detrended = signal.detrend(data, type='linear')
        
        return detrended

    def _remove_seasonality(self, data: np.ndarray) -> np.ndarray:
        """Remove seasonality using seasonal decomposition"""
        if len(data) < 2 * self.config.seasonality_period:
            # Not enough data for proper decomposition
            return data
        
        try:
            # Use seasonal decomposition
            from statsmodels.tsa.seasonal import seasonal_decompose
            
            # Create a simple series
            ts_data = pd.Series(data)
            
            # Perform decomposition
            decomposition = seasonal_decompose(
                ts_data,
                model='additive',
                period=self.config.seasonality_period,
                extrapolate='fill_ea'
            )
            
            # Return deseasonalized data (trend + residual)
            deseasonalized = decomposition.trend + decomposition.resid
            
            # Handle NaN values
            deseasonalized = deseasonalized.fillna(method='bfill').fillna(method='ffill')
            
            return deseasonalized.values
        
        except Exception:
            # Fallback to moving average method if decompose fails
            return self._remove_seasonality_moving_average(data)

    def _remove_seasonality_moving_average(self, data: np.ndarray) -> np.ndarray:
        """Fallback seasonality removal using centered moving average"""
        if len(data) < self.config.seasonality_period:
            return data
        
        # Create centered moving average
        window = self.config.seasonality_period
        deseasonalized = data.copy()
        
        for i in range(len(data)):
            start = max(0, i - window // 2)
            end = min(len(data), i + window // 2 + 1)
            deseasonalized[i] = data[i] - (np.mean(data[start:end]) - np.mean(data))
        
        return deseasonalized

    def _classify_segment(self, variation_value: float) -> str:
        """Classify item into X, Y, or Z segment based on variation"""
        if self.config.thresholds:
            if variation_value <= self.config.thresholds.x_upper_limit:
                return 'X'
            elif variation_value <= self.config.thresholds.y_upper_limit:
                return 'Y'
            else:
                return 'Z'
        else:
            # Default thresholds
            if variation_value <= 10:
                return 'X'
            elif variation_value <= 25:
                return 'Y'
            else:
                return 'Z'

    def _apply_kmeans_classification(self, results: Dict[str, Dict]) -> Dict[str, Dict]:
        """Apply K-means clustering to determine optimal segments"""
        try:
            # Extract variation values
            item_ids = list(results.keys())
            variation_values = np.array([
                results[item_id]['variation_value'] 
                for item_id in item_ids 
                if 'error' not in results[item_id]
            ]).reshape(-1, 1)
            
            if len(variation_values) < self.config.kmeans_clusters:
                return results
            
            # Perform K-means clustering
            kmeans = KMeans(
                n_clusters=self.config.kmeans_clusters,
                random_state=42,
                n_init=10
            )
            clusters = kmeans.fit_predict(variation_values)
            
            # Map clusters to X, Y, Z based on centroid values
            centroids = np.sort(kmeans.cluster_centers_.flatten())
            cluster_to_segment = {}
            
            if self.config.kmeans_clusters == 3:
                cluster_to_segment = {
                    np.argsort(kmeans.cluster_centers_.flatten())[0]: 'X',
                    np.argsort(kmeans.cluster_centers_.flatten())[1]: 'Y',
                    np.argsort(kmeans.cluster_centers_.flatten())[2]: 'Z'
                }
            elif self.config.kmeans_clusters == 2:
                cluster_to_segment = {
                    np.argsort(kmeans.cluster_centers_.flatten())[0]: 'X',
                    np.argsort(kmeans.cluster_centers_.flatten())[1]: 'Z'
                }
            else:
                # For other cluster counts, use quantile-based mapping
                for i, centroid in enumerate(np.sort(kmeans.cluster_centers_.flatten())):
                    if i < len(np.sort(kmeans.cluster_centers_.flatten())) / 3:
                        cluster_to_segment[np.where(kmeans.cluster_centers_.flatten() == centroid)[0][0]] = 'X'
                    elif i < 2 * len(np.sort(kmeans.cluster_centers_.flatten())) / 3:
                        cluster_to_segment[np.where(kmeans.cluster_centers_.flatten() == centroid)[0][0]] = 'Y'
                    else:
                        cluster_to_segment[np.where(kmeans.cluster_centers_.flatten() == centroid)[0][0]] = 'Z'
            
            # Update results with K-means segments
            valid_idx = 0
            for item_id in item_ids:
                if 'error' not in results[item_id]:
                    cluster = clusters[valid_idx]
                    segment = cluster_to_segment.get(cluster, 'Z')
                    results[item_id]['segment'] = segment
                    results[item_id]['kmeans_cluster'] = int(cluster)
                    results[item_id]['kmeans_centroid'] = float(kmeans.cluster_centers_[cluster][0])
                    valid_idx += 1
            
            return results
        
        except Exception as e:
            # If K-means fails, return original results
            return results


# ============================================================================
# REPORT GENERATION
# ============================================================================

class XYZSegmentationReport:
    """Generate detailed reports from segmentation results"""

    def generate_summary(self, results: Dict[str, Dict]) -> Dict:
        """Generate summary statistics"""
        if not results:
            return {
                'total_items': 0,
                'segment_distribution': {'X': 0, 'Y': 0, 'Z': 0},
                'error_count': 0
            }

        total_items = len(results)
        segment_counts = {'X': 0, 'Y': 0, 'Z': 0}
        error_count = 0
        
        for item_data in results.values():
            if 'error' in item_data:
                error_count += 1
            else:
                segment = item_data.get('segment', 'Z')
                if segment in segment_counts:
                    segment_counts[segment] += 1

        return {
            'total_items': total_items,
            'segment_distribution': segment_counts,
            'error_count': error_count,
            'success_rate': ((total_items - error_count) / total_items * 100) if total_items > 0 else 0
        }

    def generate_detailed_analysis(self, results: Dict[str, Dict]) -> Dict:
        """Generate detailed analysis with metrics per segment"""
        analysis = {
            'X': {'items': [], 'metrics': {}},
            'Y': {'items': [], 'metrics': {}},
            'Z': {'items': [], 'metrics': {}},
            'errors': []
        }
        
        for item_id, item_data in results.items():
            if 'error' in item_data:
                analysis['errors'].append({
                    'item_id': item_id,
                    'error': item_data['error']
                })
            else:
                segment = item_data.get('segment', 'Z')
                if segment in analysis:
                    analysis[segment]['items'].append(item_id)
        
        # Calculate metrics per segment
        for segment in ['X', 'Y', 'Z']:
            segment_items = analysis[segment]['items']
            if segment_items:
                variation_values = [
                    results[item_id]['variation_value']
                    for item_id in segment_items
                    if 'variation_value' in results[item_id]
                ]
                
                if variation_values:
                    analysis[segment]['metrics'] = {
                        'count': len(segment_items),
                        'mean_variation': float(np.mean(variation_values)),
                        'min_variation': float(np.min(variation_values)),
                        'max_variation': float(np.max(variation_values)),
                        'std_variation': float(np.std(variation_values))
                    }
        
        return analysis


# ============================================================================
# FLASK BLUEPRINT - API ENDPOINTS
# ============================================================================

xyz_bp = Blueprint('xyz_segmentation', __name__, url_prefix='/api/xyz-segmentation')


@xyz_bp.route('/classify', methods=['POST'])
def classify_items():
    """Classify items using XYZ segmentation"""
    try:
        data = request.get_json()
        items_data = data.get('items', {})
        config_data = data.get('config', {})
        
        if not items_data:
            return jsonify({'error': 'No items data provided'}), 400
        
        # Convert to numpy arrays
        items_arrays = {
            item_id: np.array(demand_list, dtype=float)
            for item_id, demand_list in items_data.items()
        }
        
        # Build configuration
        config = build_segmentation_config(config_data)
        
        # Run segmentation
        engine = XYZSegmentationEngine(config)
        results = engine.segment_items(items_arrays)
        
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
    """Extract demand data from SAP IBP and perform XYZ classification"""
    try:
        data = request.get_json()
        
        master_data_type = data.get('master_data_type')
        key_attribute = data.get('key_attribute', 'PRDID')
        demand_key_figure = data.get('demand_key_figure', 'SALES_QTY')
        time_period = data.get('time_period', {})
        config_data = data.get('config', {})
        update_master_data = data.get('update_master_data', False)
        segment_attribute = data.get('segment_attribute', 'XYZ_SEGMENT')
        
        # Extract demand data from SAP IBP
        items_demand = extract_demand_from_sap(
            master_data_type,
            key_attribute,
            demand_key_figure,
            time_period
        )
        
        if not items_demand:
            return jsonify({
                'status': 'error',
                'error': 'No demand data extracted from SAP IBP'
            }), 404
        
        # Perform XYZ classification
        config = build_segmentation_config(config_data)
        engine = XYZSegmentationEngine(config)
        results = engine.segment_items(items_demand)
        
        # Update master data if requested
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
        
        # Generate report
        report = XYZSegmentationReport()
        summary = report.generate_summary(results)
        analysis = report.generate_detailed_analysis(results)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'summary': summary,
            'analysis': analysis,
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
    """Classify items using K-means clustering"""
    try:
        data = request.get_json()
        items_data = data.get('items', {})
        config_data = data.get('config', {})
        
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
            seasonality_period=config_data.get('seasonality_period', 12),
            outlier_removal=config_data.get('outlier_removal', False)
        )
        
        engine = XYZSegmentationEngine(config)
        results = engine.segment_items(items_arrays)
        
        report = XYZSegmentationReport()
        summary = report.generate_summary(results)
        analysis = report.generate_detailed_analysis(results)
        
        return jsonify({
            'status': 'success',
            'method': 'kmeans',
            'results': results,
            'summary': summary,
            'analysis': analysis,
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
    """Batch classification for large datasets"""
    try:
        data = request.get_json()
        items_data = data.get('items', {})
        config_data = data.get('config', {})
        batch_size = data.get('batch_size', 1000)
        
        items_arrays = {
            item_id: np.array(demand_list, dtype=float)
            for item_id, demand_list in items_data.items()
        }
        
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


@xyz_bp.route('/aggregate-classify', methods=['POST'])
def aggregate_classify():
    """Classify items using aggregated error metrics strategy"""
    try:
        data = request.get_json()
        error_data = data.get('error_data', {})
        config_data = data.get('config', {})
        
        if not error_data:
            return jsonify({'error': 'No error data provided'}), 400
        
        config = build_segmentation_config(config_data)
        config.strategy = CalculationStrategy.AGGREGATE_OVER_PERIODS
        
        engine = XYZSegmentationEngine(config)
        results = engine.segment_from_error_metrics(error_data)
        
        report = XYZSegmentationReport()
        summary = report.generate_summary(results)
        analysis = report.generate_detailed_analysis(results)
        
        return jsonify({
            'status': 'success',
            'method': 'aggregate_over_periods',
            'aggregation_method': config.aggregation_method.value,
            'results': results,
            'summary': summary,
            'analysis': analysis,
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
    """Analyze existing XYZ segments"""
    try:
        data = request.get_json()
        master_data_type = data.get('master_data_type')
        segment_attribute = data.get('segment_attribute', 'XYZ_SEGMENT')
        
        segments_data = extract_segments_from_sap(
            master_data_type,
            segment_attribute
        )
        
        analysis = {
            'total_items': len(segments_data),
            'segment_distribution': {},
            'recommendations': []
        }
        
        for segment in ['X', 'Y', 'Z']:
            count = sum(1 for s in segments_data.values() if s == segment)
            percentage = (count / len(segments_data) * 100) if segments_data else 0
            analysis['segment_distribution'][segment] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        # Generate recommendations
        z_percentage = analysis['segment_distribution']['Z']['percentage']
        if z_percentage > 40:
            analysis['recommendations'].append({
                'type': 'high_volatility',
                'severity': 'warning',
                'message': f'{z_percentage:.1f}% of items are in Z segment. Consider advanced forecasting methods.'
            })
        
        x_percentage = analysis['segment_distribution']['X']['percentage']
        if x_percentage > 60:
            analysis['recommendations'].append({
                'type': 'automation_opportunity',
                'severity': 'info',
                'message': f'{x_percentage:.1f}% of items are in X segment. Good candidates for automated forecasting.'
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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_segmentation_config(config_data: Dict) -> SegmentationConfig:
    """Build SegmentationConfig from request data"""
    strategy_str = config_data.get('strategy', 'calculate_variation')
    strategy = CalculationStrategy.CALCULATE_VARIATION if strategy_str == 'calculate_variation' \
               else CalculationStrategy.AGGREGATE_OVER_PERIODS
    
    thresholds_data = config_data.get('thresholds', {})
    thresholds = SegmentationThresholds(
        x_upper_limit=float(thresholds_data.get('x_upper_limit', 10)),
        y_upper_limit=float(thresholds_data.get('y_upper_limit', 25))
    ) if thresholds_data else None
    
    agg_method_str = config_data.get('aggregation_method', 'average').upper()
    try:
        agg_method = AggregationMethod[agg_method_str]
    except KeyError:
        agg_method = AggregationMethod.AVERAGE
    
    return SegmentationConfig(
        strategy=strategy,
        thresholds=thresholds,
        use_cv_squared=config_data.get('use_cv_squared', False),
        remove_trend=config_data.get('remove_trend', False),
        remove_seasonality=config_data.get('remove_seasonality', False),
        seasonality_period=int(config_data.get('seasonality_period', 12)),
        aggregation_method=agg_method,
        min_data_points=int(config_data.get('min_data_points', 6)),
        use_kmeans=config_data.get('use_kmeans', False),
        kmeans_clusters=int(config_data.get('kmeans_clusters', 3)),
        outlier_removal=config_data.get('outlier_removal', False),
        outlier_std_threshold=float(config_data.get('outlier_std_threshold', 3.0))
    )


def extract_demand_from_sap(master_data_type: str, key_attribute: str,
                            demand_key_figure: str, time_period: Dict) -> Dict[str, np.ndarray]:
    """Extract demand time series from SAP IBP Planning Data Service"""
    try:
        sap_client = current_app.config.get('SAP_CLIENT')
        if not sap_client:
            raise Exception("SAP client not available")
        
        # Build filter conditions
        filter_conditions = []
        if time_period.get('start_date'):
            filter_conditions.append(f"DATE ge datetime'{time_period['start_date']}T00:00:00'")
        if time_period.get('end_date'):
            filter_conditions.append(f"DATE le datetime'{time_period['end_date']}T23:59:59'")
        
        filter_str = ' and '.join(filter_conditions) if filter_conditions else None
        
        # Build OData parameters for planning data extraction
        params = {
            '$select': f'{key_attribute},{demand_key_figure},DATE',
            '$orderby': f'{key_attribute},DATE',
            '$top': '10000'
        }
        if filter_str:
            params['$filter'] = filter_str
        
        # Extract from planning data service
        result = sap_client.extract_planning_data(demand_key_figure, params)
        
        # Parse and organize by item
        items_demand = {}
        if 'd' in result and 'results' in result['d']:
            for record in result['d']['results']:
                item_id = record.get(key_attribute)
                demand_value = record.get(demand_key_figure, 0)
                
                if item_id:
                    if item_id not in items_demand:
                        items_demand[item_id] = []
                    items_demand[item_id].append(float(demand_value) if demand_value is not None else 0)
        
        # Convert to numpy arrays
        return {
            item_id: np.array(values, dtype=float)
            for item_id, values in items_demand.items()
            if len(values) >= 6  # Minimum data points
        }
    
    except Exception as e:
        raise Exception(f"Failed to extract demand from SAP: {str(e)}")


def update_segments_in_sap(master_data_type: str, key_attribute: str,
                           segment_attribute: str, results: Dict) -> Dict:
    """Update XYZ segment classifications in SAP IBP"""
    try:
        sap_client = current_app.config.get('SAP_CLIENT')
        if not sap_client:
            raise Exception("SAP client not available")
        
        # Prepare update payload
        nav_property = f"Nav{master_data_type}"
        items_to_update = [
            {
                key_attribute: item_id,
                segment_attribute: item_data['segment']
            }
            for item_id, item_data in results.items()
            if 'error' not in item_data
        ]
        
        if not items_to_update:
            return {
                'status': 'error',
                'message': 'No valid items to update'
            }
        
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
            'result': result
        }
    
    except Exception as e:
        raise Exception(f"Failed to update segments in SAP: {str(e)}")


def extract_segments_from_sap(master_data_type: str, segment_attribute: str) -> Dict[str, str]:
    """Extract current XYZ segment classifications from SAP IBP"""
    try:
        sap_client = current_app.config.get('SAP_CLIENT')
        if not sap_client:
            raise Exception("SAP client not available")
        
        params = {
            '$select': f'PRDID,{segment_attribute}',
            '$format': 'json',
            '$top': '10000'
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