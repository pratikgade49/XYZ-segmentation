"""
Complete SAP IBP Master Data OData Service - Flask Backend
WITH COMPLETE DEBUG ENDPOINTS AND MISSING FUNCTIONALITY IMPLEMENTED
"""

from flask import Flask, request, jsonify, Response
from functools import wraps
import requests
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
import xml.etree.ElementTree as ET
from xyz_flask_integration import xyz_bp
from sap_data_extraction import SAPDataExtractor

app = Flask(__name__)
app.register_blueprint(xyz_bp)

# Configuration
SAP_IBP_CONFIG = {
    'base_url': 'https://my303361-api.scmibp1.ondemand.com',
    'username': 'ODATA_USER',
    'password': 'JyqEsTPHyn7uzVZnHMyfLpN$SFJLwktUloHPaxAu',
    'verify_ssl': False,
    'services': {
        'master_data': '/sap/opu/odata/IBP/MASTER_DATA_API_SRV',
        'planning_data': '/sap/opu/odata/IBP/PLANNING_DATA_API_SRV'
    }
}


class SAPODataClient:
    """Client for interacting with SAP IBP OData services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config['base_url']
        self.auth = (config['username'], config['password'])
        self.verify_ssl = config['verify_ssl']
        self.services = config.get('services', {
            'master_data': '/sap/opu/odata/IBP/MASTER_DATA_API_SRV',
            'planning_data': '/sap/opu/odata/IBP/PLANNING_DATA_API_SRV'
        })
    
    def _get_service_url(self, service_type: str = 'master_data') -> str:
        """Get full URL for a specific service"""
        service_path = self.services.get(service_type, self.services['master_data'])
        return f"{self.base_url}{service_path}"
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, headers: Dict = None, 
                     service_type: str = 'master_data') -> requests.Response:
        """Make HTTP request to SAP OData service"""
        service_url = self._get_service_url(service_type)
        url = f"{service_url}/{endpoint}"
        
        default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if headers:
            default_headers.update(headers)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                params=params,
                json=data,
                headers=default_headers,
                verify=self.verify_ssl,
                timeout=300
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"SAP OData request failed: {str(e)}")
    
    def extract_master_data(self, master_data_type: str, params: Dict) -> Dict:
        """Extract master data from SAP IBP"""
        response = self._make_request('GET', master_data_type, params=params, 
                                     service_type='master_data')
        return response.json()
    
    def extract_planning_data(self, key_figure: str, params: Dict) -> Dict:
        """Extract planning data (time series) from SAP IBP"""
        response = self._make_request('GET', key_figure, params=params, 
                                     service_type='planning_data')
        return response.json()
    
    def import_master_data(self, master_data_type: str, data: Dict) -> Dict:
        """Import master data to SAP IBP"""
        endpoint = f"{master_data_type}Trans"
        response = self._make_request('POST', endpoint, data=data, 
                                     service_type='master_data')
        return response.json()
    
    def import_planning_data(self, key_figure: str, data: Dict) -> Dict:
        """Import planning data (time series) to SAP IBP"""
        response = self._make_request('POST', key_figure, data=data, 
                                     service_type='planning_data')
        return response.json()
    
    def commit_transaction(self, transaction_id: str) -> Dict:
        """Commit master data import transaction"""
        endpoint = "Commit"
        params = {'TransactionID': transaction_id}
        response = self._make_request('POST', endpoint, params=params)
        return response.json()
    
    def get_import_status(self, transaction_id: str) -> Dict:
        """Check import transaction status"""
        endpoint = "GetExportResult"
        params = {'TransactionID': transaction_id}
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def get_error_messages(self, master_data_type: str, params: Dict = None) -> Dict:
        """Get error messages for failed imports"""
        endpoint = f"{master_data_type}Message"
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def list_version_specific_types(self, params: Dict = None) -> Dict:
        """List version-specific master data types"""
        response = self._make_request('GET', 'VersionSpecificMasterDataTypes', params=params)
        return response.json()
    
    def initiate_parallel_process(self, data: Dict) -> Dict:
        """Initiate parallel master data import process"""
        endpoint = "InitiateParallelProcess"
        response = self._make_request('POST', endpoint, data=data)
        return response.json()


# Initialize SAP client
sap_client = SAPODataClient(SAP_IBP_CONFIG)


def error_handler(f):
    """Decorator for error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    return decorated_function


# ============================================================================
# DEBUG ENDPOINTS
# ============================================================================

@app.route('/api/debug/test-connection', methods=['GET'])
@error_handler
def test_sap_connection():
    """Test basic connectivity to SAP IBP"""
    results = {}
    
    try:
        response = requests.get(
            SAP_IBP_CONFIG['base_url'],
            auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
            verify=SAP_IBP_CONFIG['verify_ssl'],
            timeout=10
        )
        results['base_url'] = {
            'status': 'success',
            'status_code': response.status_code,
            'url': SAP_IBP_CONFIG['base_url']
        }
    except Exception as e:
        results['base_url'] = {
            'status': 'error',
            'error': str(e),
            'url': SAP_IBP_CONFIG['base_url']
        }
    
    # Test Master Data Service
    try:
        master_url = f"{SAP_IBP_CONFIG['base_url']}{SAP_IBP_CONFIG['services']['master_data']}"
        response = requests.get(
            master_url,
            auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
            verify=SAP_IBP_CONFIG['verify_ssl'],
            timeout=10
        )
        results['master_data_service'] = {
            'status': 'success',
            'url': master_url,
            'status_code': response.status_code
        }
    except Exception as e:
        results['master_data_service'] = {
            'status': 'error',
            'url': master_url,
            'error': str(e)
        }
    
    # Test Planning Data Service
    try:
        planning_url = f"{SAP_IBP_CONFIG['base_url']}{SAP_IBP_CONFIG['services']['planning_data']}"
        response = requests.get(
            planning_url,
            auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
            verify=SAP_IBP_CONFIG['verify_ssl'],
            timeout=10
        )
        results['planning_data_service'] = {
            'status': 'success',
            'url': planning_url,
            'status_code': response.status_code
        }
    except Exception as e:
        results['planning_data_service'] = {
            'status': 'error',
            'url': planning_url,
            'error': str(e)
        }
    
    return jsonify(results)


@app.route('/api/debug/service-metadata', methods=['GET'])
@error_handler
def check_service_metadata():
    """Check SAP IBP OData service metadata"""
    service_type = request.args.get('service', 'master_data')
    service_path = SAP_IBP_CONFIG['services'].get(service_type, SAP_IBP_CONFIG['services']['master_data'])
    metadata_url = f"{SAP_IBP_CONFIG['base_url']}{service_path}/$metadata"
    
    response = requests.get(
        metadata_url,
        auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
        verify=SAP_IBP_CONFIG['verify_ssl'],
        timeout=30
    )
    
    return jsonify({
        'status': 'success',
        'service_type': service_type,
        'url': metadata_url,
        'status_code': response.status_code,
        'content_type': response.headers.get('Content-Type'),
        'metadata_preview': response.text[:5000],
        'full_length': len(response.text)
    })


@app.route('/api/debug/list-entity-sets', methods=['GET'])
@error_handler
def list_entity_sets():
    """Parse metadata and list all available entity sets"""
    service_type = request.args.get('service', 'master_data')
    service_path = SAP_IBP_CONFIG['services'].get(service_type, SAP_IBP_CONFIG['services']['master_data'])
    metadata_url = f"{SAP_IBP_CONFIG['base_url']}{service_path}/$metadata"
    
    response = requests.get(
        metadata_url,
        auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
        verify=SAP_IBP_CONFIG['verify_ssl'],
        timeout=30
    )
    
    root = ET.fromstring(response.content)
    
    namespace_variants = [
        {
            'edmx': 'http://schemas.microsoft.com/ado/2007/06/edmx',
            'edm': 'http://schemas.microsoft.com/ado/2008/09/edm'
        },
        {
            'edmx': 'http://docs.oasis-open.org/odata/ns/edmx',
            'edm': 'http://docs.oasis-open.org/odata/ns/edm'
        }
    ]
    
    entity_sets = []
    for namespaces in namespace_variants:
        entity_sets = []
        for entity_set in root.findall('.//edm:EntitySet', namespaces):
            entity_sets.append({
                'name': entity_set.get('Name'),
                'entity_type': entity_set.get('EntityType')
            })
        
        if entity_sets:
            break
    
    if not entity_sets:
        for entity_set in root.findall('.//{*}EntitySet'):
            entity_sets.append({
                'name': entity_set.get('Name'),
                'entity_type': entity_set.get('EntityType')
            })
    
    return jsonify({
        'status': 'success',
        'service_type': service_type,
        'total_entity_sets': len(entity_sets),
        'entity_sets': entity_sets,
        'note': 'Use these entity set names in your API calls'
    })


@app.route('/api/debug/raw-service', methods=['GET'])
@error_handler
def test_raw_service():
    """Get raw service document (lists all available collections)"""
    service_type = request.args.get('service', 'master_data')
    service_path = SAP_IBP_CONFIG['services'].get(service_type, SAP_IBP_CONFIG['services']['master_data'])
    service_url = f"{SAP_IBP_CONFIG['base_url']}{service_path}"
    
    response = requests.get(
        service_url,
        auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
        verify=SAP_IBP_CONFIG['verify_ssl'],
        headers={'Accept': 'application/json'},
        timeout=30
    )
    
    return jsonify({
        'status': 'success',
        'service_type': service_type,
        'url': service_url,
        'status_code': response.status_code,
        'response': response.json() if response.ok else response.text
    })


@app.route('/api/debug/test-entity/<entity_name>', methods=['GET'])
@error_handler
def test_entity_access(entity_name):
    """Test access to a specific entity"""
    service_type = request.args.get('service', 'master_data')
    top = request.args.get('top', '1')
    
    params = {'$top': top}
    
    try:
        if service_type == 'planning_data':
            result = sap_client.extract_planning_data(entity_name, params)
        else:
            result = sap_client.extract_master_data(entity_name, params)
        
        return jsonify({
            'status': 'success',
            'entity_name': entity_name,
            'service_type': service_type,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'entity_name': entity_name,
            'service_type': service_type,
            'error': str(e)
        }), 404


@app.route('/api/debug/find-product-entity', methods=['GET'])
@error_handler
def find_product_entity():
    """Automatically find the correct product entity name by testing common variations"""
    possible_names = [
        'PRODUCT',
        'Product',
        'Products',
        'ProductMasterData',
        'MasterDataProduct',
        'PRDMASTER',
        'PRD',
        'ZPRODUCT',
        'ProductSet',
        'ProductCollection',
        'Y1BPRODUCT',
        'Y1BPRODUCTSet'
    ]
    
    results = []
    working_entity = None
    
    for entity_name in possible_names:
        try:
            params = {'$top': '1'}
            result = sap_client.extract_master_data(entity_name, params)
            
            # Check if we got valid data back
            if result and ('d' in result or 'value' in result):
                results.append({
                    'entity_name': entity_name,
                    'status': 'working',
                    'preview': result
                })
                if not working_entity:
                    working_entity = entity_name
            else:
                results.append({
                    'entity_name': entity_name,
                    'status': 'no_data'
                })
        except Exception as e:
            results.append({
                'entity_name': entity_name,
                'status': 'error',
                'error': str(e)
            })
    
    return jsonify({
        'status': 'success',
        'working_entity': working_entity,
        'tested_entities': results,
        'recommendation': f"Use '{working_entity}' as your product entity" if working_entity else "No working product entity found"
    })


# ============================================================================
# MAIN API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SAP IBP Master Data API',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/master-data/<master_data_type>/extract', methods=['GET'])
@error_handler
def extract_master_data(master_data_type):
    """Extract master data from SAP IBP"""
    params = {}
    
    if request.args.get('select'):
        params['$select'] = request.args.get('select')
    if request.args.get('filter'):
        params['$filter'] = request.args.get('filter')
    if request.args.get('orderby'):
        params['$orderby'] = request.args.get('orderby')
    if request.args.get('top'):
        params['$top'] = request.args.get('top')
    if request.args.get('skip'):
        params['$skip'] = request.args.get('skip')
    if request.args.get('format'):
        params['$format'] = request.args.get('format')
    if request.args.get('inlinecount'):
        params['$inlinecount'] = request.args.get('inlinecount')
    if request.args.get('expand'):
        params['$expand'] = request.args.get('expand')
    
    result = sap_client.extract_master_data(master_data_type, params)
    return jsonify(result)


@app.route('/api/master-data/<master_data_type>/import', methods=['POST'])
@error_handler
def import_master_data(master_data_type):
    """Import master data to SAP IBP"""
    data = request.get_json()
    
    if not data.get('TransactionID'):
        data['TransactionID'] = uuid.uuid4().hex[:32]
    
    result = sap_client.import_master_data(master_data_type, data)
    
    return jsonify({
        'transaction_id': data['TransactionID'],
        'master_data_type': master_data_type,
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/master-data/<master_data_type>/delete', methods=['POST'])
@error_handler
def delete_master_data(master_data_type):
    """Delete master data records from SAP IBP"""
    data = request.get_json()
    data['DeleteEntries'] = True
    
    if not data.get('TransactionID'):
        data['TransactionID'] = uuid.uuid4().hex[:32]
    
    result = sap_client.import_master_data(master_data_type, data)
    
    return jsonify({
        'transaction_id': data['TransactionID'],
        'master_data_type': master_data_type,
        'operation': 'delete',
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/transaction/<transaction_id>/commit', methods=['POST'])
@error_handler
def commit_transaction(transaction_id):
    """Commit a master data import transaction"""
    result = sap_client.commit_transaction(transaction_id)
    return jsonify({
        'transaction_id': transaction_id,
        'status': 'committed',
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/transaction/<transaction_id>/status', methods=['GET'])
@error_handler
def get_transaction_status(transaction_id):
    """Get the status of an import transaction"""
    result = sap_client.get_import_status(transaction_id)
    return jsonify({
        'transaction_id': transaction_id,
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/master-data/<master_data_type>/errors', methods=['GET'])
@error_handler
def get_error_messages(master_data_type):
    """Get error messages for a master data type"""
    params = {}
    
    if request.args.get('top'):
        params['$top'] = request.args.get('top')
    if request.args.get('skip'):
        params['$skip'] = request.args.get('skip')
    if request.args.get('expand'):
        params['$expand'] = request.args.get('expand')
    if request.args.get('select'):
        params['$select'] = request.args.get('select')
    
    result = sap_client.get_error_messages(master_data_type, params)
    return jsonify(result)


@app.route('/api/version-specific-types', methods=['GET'])
@error_handler
def list_version_specific_types():
    """List version-specific master data types"""
    params = {}
    
    if request.args.get('filter'):
        params['$filter'] = request.args.get('filter')
    if request.args.get('format'):
        params['$format'] = request.args.get('format')
    
    result = sap_client.list_version_specific_types(params)
    return jsonify(result)


@app.route('/api/master-data/<master_data_type>/import-parallel', methods=['POST'])
@error_handler
def import_parallel(master_data_type):
    """Initiate parallel master data import"""
    data = request.get_json()
    data['MasterDataTypeID'] = master_data_type
    
    if not data.get('TransactionID'):
        data['TransactionID'] = uuid.uuid4().hex[:32]
    
    result = sap_client.initiate_parallel_process(data)
    
    return jsonify({
        'transaction_id': data['TransactionID'],
        'master_data_type': master_data_type,
        'mode': 'parallel',
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/master-data/batch-extract', methods=['POST'])
@error_handler
def batch_extract():
    """Extract multiple master data types in a single request"""
    data = request.get_json()
    extractions = data.get('extractions', [])
    
    results = []
    for extraction in extractions:
        master_data_type = extraction.get('master_data_type')
        params = extraction.get('params', {})
        
        try:
            result = sap_client.extract_master_data(master_data_type, params)
            results.append({
                'master_data_type': master_data_type,
                'status': 'success',
                'data': result
            })
        except Exception as e:
            results.append({
                'master_data_type': master_data_type,
                'status': 'error',
                'error': str(e)
            })
    
    return jsonify({
        'results': results,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/products', methods=['GET'])
@error_handler
def get_products():
    """Get present products from SAP IBP master data"""
    params = {}
    
    if request.args.get('select'):
        params['$select'] = request.args.get('select')
    else:
        params['$select'] = 'PRDID,PRDDESCR'
    
    if request.args.get('filter'):
        params['$filter'] = request.args.get('filter')
    if request.args.get('orderby'):
        params['$orderby'] = request.args.get('orderby')
    if request.args.get('top'):
        params['$top'] = request.args.get('top')
    if request.args.get('skip'):
        params['$skip'] = request.args.get('skip')
    
    result = sap_client.extract_master_data('Y1BPRODUCT', params)
    return jsonify(result)


# ============================================================================
# PLANNING DATA ENDPOINTS (Time Series Data)
# ============================================================================

@app.route('/api/planning-data/<key_figure>/extract', methods=['GET'])
@error_handler
def extract_planning_data(key_figure):
    """Extract planning data (time series) from SAP IBP"""
    params = {}
    
    if request.args.get('select'):
        params['$select'] = request.args.get('select')
    if request.args.get('filter'):
        params['$filter'] = request.args.get('filter')
    if request.args.get('orderby'):
        params['$orderby'] = request.args.get('orderby')
    if request.args.get('top'):
        params['$top'] = request.args.get('top')
    if request.args.get('skip'):
        params['$skip'] = request.args.get('skip')
    if request.args.get('format'):
        params['$format'] = request.args.get('format')
    
    result = sap_client.extract_planning_data(key_figure, params)
    return jsonify(result)


@app.route('/api/planning-data/<key_figure>/import', methods=['POST'])
@error_handler
def import_planning_data(key_figure):
    """Import planning data (time series) to SAP IBP"""
    data = request.get_json()
    
    if not data.get('TransactionID'):
        data['TransactionID'] = uuid.uuid4().hex[:32]
    
    result = sap_client.import_planning_data(key_figure, data)
    
    return jsonify({
        'transaction_id': data['TransactionID'],
        'key_figure': key_figure,
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    })

"""
SAP IBP Discovery Helper Endpoints
Add these to your main Flask app (main.py) to help discover entities and key figures
"""

@app.route('/api/debug/discover-all', methods=['GET'])
@error_handler
def discover_all():
    """
    Complete discovery endpoint - finds entities, attributes, and key figures
    Useful when you're completely new to your SAP IBP instance
    """
    discovery_results = {}
    
    # 1. Test connection
    try:
        response = requests.get(
            SAP_IBP_CONFIG['base_url'],
            auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
            verify=SAP_IBP_CONFIG['verify_ssl'],
            timeout=10
        )
        discovery_results['connection'] = 'working'
    except Exception as e:
        discovery_results['connection'] = f'failed: {str(e)}'
        return jsonify(discovery_results), 500
    
    # 2. Discover master data entities
    try:
        service_path = SAP_IBP_CONFIG['services']['master_data']
        metadata_url = f"{SAP_IBP_CONFIG['base_url']}{service_path}/$metadata"
        
        response = requests.get(
            metadata_url,
            auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
            verify=SAP_IBP_CONFIG['verify_ssl'],
            timeout=30
        )
        
        root = ET.fromstring(response.content)
        
        namespaces = {
            'edmx': 'http://schemas.microsoft.com/ado/2007/06/edmx',
            'edm': 'http://schemas.microsoft.com/ado/2008/09/edm'
        }
        
        master_data_entities = []
        for entity_set in root.findall('.//edm:EntitySet', namespaces):
            entity_name = entity_set.get('Name')
            master_data_entities.append(entity_name)
        
        discovery_results['master_data_entities'] = sorted(master_data_entities)
        discovery_results['master_data_count'] = len(master_data_entities)
    
    except Exception as e:
        discovery_results['master_data_error'] = str(e)
    
    # 3. Discover planning data (key figures)
    try:
        service_path = SAP_IBP_CONFIG['services']['planning_data']
        metadata_url = f"{SAP_IBP_CONFIG['base_url']}{service_path}/$metadata"
        
        response = requests.get(
            metadata_url,
            auth=(SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password']),
            verify=SAP_IBP_CONFIG['verify_ssl'],
            timeout=30
        )
        
        root = ET.fromstring(response.content)
        
        namespaces = {
            'edmx': 'http://schemas.microsoft.com/ado/2007/06/edmx',
            'edm': 'http://schemas.microsoft.com/ado/2008/09/edm'
        }
        
        key_figures = []
        for entity_set in root.findall('.//edm:EntitySet', namespaces):
            entity_name = entity_set.get('Name')
            key_figures.append(entity_name)
        
        discovery_results['key_figures'] = sorted(key_figures)
        discovery_results['key_figures_count'] = len(key_figures)
    
    except Exception as e:
        discovery_results['key_figures_error'] = str(e)
    
    # 4. Find product entity and sample it
    try:
        for entity_name in ['Y1BPRODUCT', 'PRODUCT', 'Products', 'Y1BPRODUCTSet']:
            try:
                params = {'$top': '1'}
                result = sap_client.extract_master_data(entity_name, params)
                
                if result and 'd' in result and 'results' in result['d'] and result['d']['results']:
                    sample_record = result['d']['results'][0]
                    discovery_results['product_entity'] = entity_name
                    discovery_results['product_attributes'] = list(sample_record.keys())
                    discovery_results['product_sample'] = sample_record
                    break
            except:
                pass
    except Exception as e:
        discovery_results['product_discovery_error'] = str(e)
    
    return jsonify({
        'status': 'success',
        'discovery': discovery_results,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/debug/sample-data/<entity_name>', methods=['GET'])
@error_handler
def get_sample_data(entity_name):
    """
    Get sample data from any entity to inspect attributes
    Use this to see what fields are available in your data
    
    Usage:
    GET /api/debug/sample-data/Y1BPRODUCT?top=3&service=master_data
    GET /api/debug/sample-data/SALES_QUANTITY?top=3&service=planning_data
    """
    service_type = request.args.get('service', 'master_data')
    top = request.args.get('top', '1')
    
    try:
        params = {'$top': top, '$format': 'json'}
        
        if service_type == 'planning_data':
            result = sap_client.extract_planning_data(entity_name, params)
        else:
            result = sap_client.extract_master_data(entity_name, params)
        
        # Extract records
        records = []
        if 'd' in result and 'results' in result['d']:
            records = result['d']['results']
        elif 'value' in result:
            records = result['value']
        
        # Analyze attributes
        all_attributes = set()
        for record in records:
            all_attributes.update(record.keys())
        
        return jsonify({
            'status': 'success',
            'entity_name': entity_name,
            'service_type': service_type,
            'record_count': len(records),
            'attributes': sorted(list(all_attributes)),
            'sample_records': records[:int(top)],
            'attribute_types': {
                attr: type(records[0].get(attr, '')).__name__ 
                for attr in all_attributes 
                if records
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'entity_name': entity_name,
            'error': str(e),
            'suggestion': 'Entity might not exist. Use /api/debug/discover-all to see available entities'
        }), 404


@app.route('/api/debug/entity-stats/<entity_name>', methods=['GET'])
@error_handler
def get_entity_stats(entity_name):
    """
    Get statistics about an entity (record count, date range, etc.)
    
    Usage:
    GET /api/debug/entity-stats/SALES_QUANTITY?service=planning_data
    """
    service_type = request.args.get('service', 'master_data')
    
    try:
        # Get metadata about the entity
        params = {'$top': '0', '$inlinecount': 'allpages'}
        
        if service_type == 'planning_data':
            result = sap_client.extract_planning_data(entity_name, params)
        else:
            result = sap_client.extract_master_data(entity_name, params)
        
        total_count = 0
        if '__count' in result.get('d', {}):
            total_count = result['d']['__count']
        elif 'odata.count' in str(result):
            # Parse count from response
            import re
            match = re.search(r'"odata\.count":"(\d+)"', str(result))
            if match:
                total_count = int(match.group(1))
        
        # Sample some records to get date range (if it's a time series entity)
        sample_params = {'$top': '100'}
        if service_type == 'planning_data':
            sample_result = sap_client.extract_planning_data(entity_name, sample_params)
        else:
            sample_result = sap_client.extract_master_data(entity_name, sample_params)
        
        date_range = {'min': None, 'max': None}
        sample_records = []
        
        if 'd' in sample_result and 'results' in sample_result['d']:
            sample_records = sample_result['d']['results']
        
        # Look for date fields
        for record in sample_records:
            for key, value in record.items():
                if 'DATE' in key.upper() or 'DATE' in str(type(value)):
                    if date_range['min'] is None or str(value) < date_range['min']:
                        date_range['min'] = str(value)
                    if date_range['max'] is None or str(value) > date_range['max']:
                        date_range['max'] = str(value)
        
        return jsonify({
            'status': 'success',
            'entity_name': entity_name,
            'service_type': service_type,
            'total_records': total_count,
            'date_range': date_range,
            'sample_size': len(sample_records),
            'sample_records': sample_records[:5]
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'entity_name': entity_name,
            'error': str(e)
        }), 404



@app.route('/api/debug/validate-config', methods=['POST'])
@error_handler
def validate_config():
    """
    Validate your XYZ segmentation configuration before running full analysis
    
    Usage:
    POST /api/debug/validate-config
    
    Payload:
    {
        "master_data_type": "Y1BPRODUCT",
        "key_attribute": "PRDID",
        "demand_key_figure": "SALES_QUANTITY",
        "time_period": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
    }
    """
    data = request.get_json()
    
    validation = {
        'is_valid': True,
        'checks': {},
        'errors': [],
        'warnings': []
    }
    
    # Check 1: Master data type exists
    try:
        master_data_type = data.get('master_data_type')
        params = {'$top': '1'}
        result = sap_client.extract_master_data(master_data_type, params)
        
        if 'd' in result and 'results' in result['d'] and result['d']['results']:
            sample = result['d']['results'][0]
            validation['checks']['master_data_entity'] = {
                'status': 'valid',
                'message': f"Entity '{master_data_type}' found",
                'attributes': list(sample.keys())
            }
        else:
            validation['checks']['master_data_entity'] = {'status': 'error'}
            validation['errors'].append(f"Master data entity '{master_data_type}' has no data")
            validation['is_valid'] = False
    except Exception as e:
        validation['checks']['master_data_entity'] = {'status': 'error'}
        validation['errors'].append(f"Master data entity error: {str(e)}")
        validation['is_valid'] = False
    
    # Check 2: Key attribute exists
    key_attribute = data.get('key_attribute')
    if 'master_data_entity' in validation['checks']:
        attrs = validation['checks']['master_data_entity'].get('attributes', [])
        if key_attribute in attrs:
            validation['checks']['key_attribute'] = {
                'status': 'valid',
                'message': f"Attribute '{key_attribute}' found in entity"
            }
        else:
            validation['checks']['key_attribute'] = {'status': 'error'}
            validation['errors'].append(f"Attribute '{key_attribute}' not found. Available: {attrs}")
            validation['is_valid'] = False
    
    # Check 3: Demand key figure exists
    try:
        demand_key_figure = data.get('demand_key_figure')
        params = {'$top': '1'}
        result = sap_client.extract_planning_data(demand_key_figure, params)
        
        if 'd' in result and 'results' in result['d'] and result['d']['results']:
            sample = result['d']['results'][0]
            validation['checks']['demand_key_figure'] = {
                'status': 'valid',
                'message': f"Key figure '{demand_key_figure}' found",
                'attributes': list(sample.keys())
            }
        else:
            validation['checks']['demand_key_figure'] = {'status': 'warning'}
            validation['warnings'].append(f"Key figure '{demand_key_figure}' has no data")
    except Exception as e:
        validation['checks']['demand_key_figure'] = {'status': 'error'}
        validation['errors'].append(f"Demand key figure error: {str(e)}")
        validation['is_valid'] = False
    
    # Check 4: Date range validity
    time_period = data.get('time_period', {})
    if time_period.get('start_date') and time_period.get('end_date'):
        validation['checks']['time_period'] = {
            'status': 'valid',
            'message': f"Time period: {time_period['start_date']} to {time_period['end_date']}"
        }
    else:
        validation['checks']['time_period'] = {'status': 'warning'}
        validation['warnings'].append("No time period specified, will use all available data")
    
    # Summary
    validation['summary'] = {
        'valid_checks': sum(1 for c in validation['checks'].values() if c.get('status') == 'valid'),
        'total_checks': len(validation['checks']),
        'errors_count': len(validation['errors']),
        'warnings_count': len(validation['warnings'])
    }
    
    return jsonify({
        'status': 'success',
        'validation': validation,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/debug/search-entity', methods=['GET'])
@error_handler
def search_entity():
    """
    Search for entities by keyword
    
    Usage:
    GET /api/debug/search-entity?keyword=PRODUCT&service=master_data
    GET /api/debug/search-entity?keyword=SALES&service=planning_data
    """
    keyword = request.args.get('keyword', '').upper()
    service_type = request.args.get('service', 'master_data')
    
    if not keyword:
        return jsonify({'error': 'keyword parameter required'}), 400
    
    try:
        if service_type == 'planning_data':
            all_entities = discovery_results.get('key_figures', [])
        else:
            all_entities = discovery_results.get('master_data_entities', [])
        
        matching = [e for e in all_entities if keyword in e.upper()]
        
        return jsonify({
            'status': 'success',
            'keyword': keyword,
            'service_type': service_type,
            'matches': matching,
            'match_count': len(matching)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Add this near the top with other globals for caching discovery results
discovery_results = {}

# Make SAP client accessible to other modules
app.config['SAP_CLIENT'] = sap_client


# ============================================================================
# ENHANCED DATA EXTRACTION ENDPOINTS
# ============================================================================

@app.route('/api/data-extraction/sales-quantity', methods=['POST'])
@error_handler
def extract_sales_quantity():
    """
    Extract actual sales quantity from planning data service with proper date filtering

    Request body:
    {
        "key_figure": "SALES_QUANTITY",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "product_filter": "PRODUCT_001",
        "location_filter": "LOC_A",
        "top": 10000,
        "skip": 0
    }
    """
    data = request.get_json()

    key_figure = data.get('key_figure')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    product_filter = data.get('product_filter')
    location_filter = data.get('location_filter')
    top = data.get('top', 10000)
    skip = data.get('skip', 0)

    if not key_figure:
        return jsonify({'error': 'key_figure parameter is required'}), 400

    result = SAPDataExtractor.extract_sales_quantity_with_dates(
        key_figure=key_figure,
        start_date=start_date,
        end_date=end_date,
        product_filter=product_filter,
        location_filter=location_filter,
        top=top,
        skip=skip
    )

    return jsonify(result)


@app.route('/api/data-extraction/version-specific-master-data', methods=['POST'])
@error_handler
def extract_version_specific_master_data():
    """
    Extract version-specific master data using PlanningAreaID and VersionID

    Request body:
    {
        "master_data_type_id": "CUSTOMER",
        "planning_area_id": "SAPIBP1",
        "version_id": "UPSIDE",
        "use_baseline": false
    }
    """
    data = request.get_json()

    master_data_type_id = data.get('master_data_type_id')
    planning_area_id = data.get('planning_area_id')
    version_id = data.get('version_id')
    use_baseline = data.get('use_baseline', False)

    result = SAPDataExtractor.extract_version_specific_master_data(
        master_data_type_id=master_data_type_id,
        planning_area_id=planning_area_id,
        version_id=version_id,
        use_baseline=use_baseline
    )

    return jsonify(result)


@app.route('/api/data-extraction/sales-quantity-by-product', methods=['POST'])
@error_handler
def extract_sales_quantity_by_product():
    """
    Extract sales quantity for specific products (returns as arrays for segmentation)

    Request body:
    {
        "key_figure": "SALES_QUANTITY",
        "product_ids": ["PRODUCT_001", "PRODUCT_002"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    """
    data = request.get_json()

    key_figure = data.get('key_figure')
    product_ids = data.get('product_ids', [])
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not key_figure:
        return jsonify({'error': 'key_figure parameter is required'}), 400

    try:
        items_arrays = SAPDataExtractor.extract_sales_quantity_by_product(
            key_figure=key_figure,
            product_ids=product_ids,
            start_date=start_date,
            end_date=end_date
        )

        return jsonify({
            'status': 'success',
            'key_figure': key_figure,
            'items': {
                product_id: array.tolist()
                for product_id, array in items_arrays.items()
            },
            'summary': {
                'total_products': len(items_arrays),
                'date_range': {
                    'start': start_date,
                    'end': end_date
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*80)
    print("SAP IBP Master Data API - Flask Backend Started")
    print("="*80)
    print("\nDEBUG ENDPOINTS:")
    print("  - GET  http://localhost:5000/api/debug/test-connection")
    print("  - GET  http://localhost:5000/api/debug/list-entity-sets")
    print("  - GET  http://localhost:5000/api/debug/find-product-entity")
    print("  - GET  http://localhost:5000/api/debug/service-metadata")
    print("  - GET  http://localhost:5000/api/debug/raw-service")
    print("  - GET  http://localhost:5000/api/debug/test-entity/<ENTITY_NAME>")
    print("\nREGULAR ENDPOINTS:")
    print("  - GET  http://localhost:5000/health")
    print("  - GET  http://localhost:5000/api/products")
    print("  - GET  http://localhost:5000/api/master-data/<TYPE>/extract")
    print("\nENHANCED DATA EXTRACTION ENDPOINTS:")
    print("  - POST http://localhost:5000/api/data-extraction/sales-quantity")
    print("  - POST http://localhost:5000/api/data-extraction/version-specific-master-data")
    print("  - POST http://localhost:5000/api/data-extraction/sales-quantity-by-product")
    print("\nXYZ SEGMENTATION ENDPOINTS:")
    print("  - POST http://localhost:5000/api/xyz-segmentation/classify")
    print("  - POST http://localhost:5000/api/xyz-segmentation/classify-from-sap")
    print("  - POST http://localhost:5000/api/xyz-segmentation/kmeans-classify")
    print("  - POST http://localhost:5000/api/xyz-segmentation/aggregate-classify")
    print("="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)