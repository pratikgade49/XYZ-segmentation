"""
SAP IBP OData Service Metadata Checker
Add these endpoints to your main Flask app file
"""

from flask import jsonify, request
import requests
import xml.etree.ElementTree as ET
# Example SAP IBP configuration
SAP_IBP_CONFIG = {
    'base_url': 'https://my303361-api.scmibp1.ondemand.com',  # Single base URL for all services
    'username': 'ODATA_USER',
    'password': 'JyqEsTPHyn7uzVZnHMyfLpN$SFJLwktUloHPaxAu',
    'verify_ssl': False,  # Set to False for development only
    'services': {
        'master_data': '/sap/opu/odata/IBP/MASTER_DATA_API_SRV',
        'planning_data': '/sap/opu/odata/IBP/PLANNING_DATA_API_SRV'
    }
}


def register_debug_endpoints(app, sap_config):
    """
    Register debug endpoints for SAP IBP troubleshooting
    Call this function from your main app file
    """
    
    @app.route('/api/debug/service-metadata', methods=['GET'])
    def check_service_metadata():
        service_type = request.args.get('service', 'master_data')

        try:
            if service_type == 'planning_data':
                service_url = f"{SAP_IBP_CONFIG['base_url']}{SAP_IBP_CONFIG['services']['planning_data']}/$metadata"
            else:
                service_url = f"{SAP_IBP_CONFIG['base_url']}{SAP_IBP_CONFIG['services']['master_data']}/$metadata"

            auth = (SAP_IBP_CONFIG['username'], SAP_IBP_CONFIG['password'])

            response = requests.get(
                service_url,
                auth=auth,
                verify=SAP_IBP_CONFIG['verify_ssl'],
                timeout=30
            )

            return jsonify({
                'status': 'success',
                'service_type': service_type,
                'url': service_url,
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type'),
                'metadata_preview': response.text[:5000]  # First 5000 chars
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500


    @app.route('/api/debug/test-connection', methods=['GET'])
    def test_sap_connection():
        """
        Test basic connectivity to SAP IBP
        """
        results = {}
        
        # Test base URL
        try:
            response = requests.get(
                sap_config['base_url'],
                auth=(sap_config['username'], sap_config['password']),
                verify=sap_config['verify_ssl'],
                timeout=10
            )
            results['base_url'] = {
                'status': 'success',
                'status_code': response.status_code
            }
        except Exception as e:
            results['base_url'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test Master Data Service
        try:
            master_url = f"{sap_config['base_url']}{sap_config['services']['master_data']}"
            response = requests.get(
                master_url,
                auth=(sap_config['username'], sap_config['password']),
                verify=sap_config['verify_ssl'],
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
            planning_url = f"{sap_config['base_url']}{sap_config['services']['planning_data']}"
            response = requests.get(
                planning_url,
                auth=(sap_config['username'], sap_config['password']),
                verify=sap_config['verify_ssl'],
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


    @app.route('/api/debug/list-entity-sets', methods=['GET'])
    def list_entity_sets():
        """
        Parse metadata and list all available entity sets
        """
        try:
            master_data_url = f"{sap_config['base_url']}{sap_config['services']['master_data']}/$metadata"
            
            response = requests.get(
                master_data_url,
                auth=(sap_config['username'], sap_config['password']),
                verify=sap_config['verify_ssl'],
                timeout=30
            )
            
            # Parse XML metadata
            root = ET.fromstring(response.content)
            
            # Find all EntitySet elements
            namespaces = {
                'edmx': 'http://schemas.microsoft.com/ado/2007/06/edmx',
                'edm': 'http://schemas.microsoft.com/ado/2008/09/edm'
            }
            
            entity_sets = []
            for entity_set in root.findall('.//edm:EntitySet', namespaces):
                entity_sets.append({
                    'name': entity_set.get('Name'),
                    'entity_type': entity_set.get('EntityType')
                })
            
            return jsonify({
                'status': 'success',
                'total_entity_sets': len(entity_sets),
                'entity_sets': entity_sets,
                'note': 'Use these entity set names in your API calls'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    
    @app.route('/api/debug/raw-service', methods=['GET'])
    def test_raw_service():
        """Test raw service document"""
        service_type = request.args.get('service', 'master_data')

        try:
            if service_type == 'planning_data':
                service_url = f"{sap_config['base_url']}{sap_config['services']['planning_data']}"
            else:
                service_url = f"{sap_config['base_url']}{sap_config['services']['master_data']}"

            response = requests.get(
                service_url,
                auth=(sap_config['username'], sap_config['password']),
                verify=sap_config['verify_ssl'],
                headers={'Accept': 'application/json'},
                timeout=30
            )

            return jsonify({
                'service_type': service_type,
                'url': service_url,
                'status_code': response.status_code,
                'response': response.json() if response.ok else response.text
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
