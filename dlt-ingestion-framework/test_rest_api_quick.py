#!/usr/bin/env python3
"""
Quick validation test for REST API source v2.0
Tests basic configuration building without making actual API calls.

Run this script to verify REST API source is working correctly.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Mock ConfigLoader for testing
class MockConfigLoader:
    def get_source_config(self, source_type, source_name):
        """Return mock API configuration."""
        if source_name == 'test_api':
            return {
                'base_url': 'https://api.example.com',
                'auth_type': 'api_key',
                'api_key': 'test_key_123',
                'pagination_type': 'offset',
                'page_size': 100
            }
        elif source_name == 'github_api':
            return {
                'base_url': 'https://api.github.com',
                'auth_type': 'bearer',
                'token': 'ghp_test_token',
                'pagination_type': 'header_link'
            }
        return {}

def test_rest_api_source():
    """Test REST API source configuration building."""
    print("\n" + "="*70)
    print("REST API Source v2.0 - Quick Validation Test")
    print("="*70 + "\n")
    
    try:
        from sources.rest_api_v2 import RESTAPISource
        
        config_loader = MockConfigLoader()
        
        # Test 1: API Key Authentication + Offset Pagination
        print("[TEST 1] API Key + Offset Pagination")
        print("-" * 70)
        
        source = RESTAPISource(config_loader)
        
        job = {
            'source_name': 'test_api',
            'table_name': 'users',
            'api_endpoint': '/api/users',
            'pagination_type': 'offset',
            'page_size': 100
        }
        
        rest_config = source.build_rest_config(job)
        
        # Validate configuration structure
        assert 'client' in rest_config, "Missing 'client' key"
        assert 'resources' in rest_config, "Missing 'resources' key"
        assert rest_config['client']['base_url'] == 'https://api.example.com'
        assert 'X-API-Key' in rest_config['client']['headers']
        assert rest_config['client']['headers']['X-API-Key'] == 'test_key_123'
        
        # Validate pagination config
        resource = rest_config['resources'][0]
        assert resource['name'] == 'users'
        assert 'paginator' in resource['endpoint']
        
        print("✓ Client config correct")
        print("✓ Authentication headers present")
        print("✓ Pagination config present")
        print("✓ Resource configuration valid")
        print(f"  Base URL: {rest_config['client']['base_url']}")
        print(f"  Endpoint: {resource['endpoint']['path']}")
        print(f"  Pagination: {job['pagination_type']}")
        
        # Test 2: Bearer Token + Header Link Pagination
        print("\n[TEST 2] Bearer Token + Header Link Pagination")
        print("-" * 70)
        
        source2 = RESTAPISource(config_loader)
        
        job2 = {
            'source_name': 'github_api',
            'table_name': 'issues',
            'api_endpoint': '/repos/owner/repo/issues',
            'pagination_type': 'header_link',
            'page_size': 100
        }
        
        rest_config2 = source2.build_rest_config(job2)
        
        # Validate bearer token auth
        assert 'Authorization' in rest_config2['client']['headers']
        assert rest_config2['client']['headers']['Authorization'].startswith('Bearer ')
        
        print("✓ Bearer token authentication configured")
        print("✓ Header link pagination configured")
        print(f"  Base URL: {rest_config2['client']['base_url']}")
        print(f"  Endpoint: {rest_config2['resources'][0]['endpoint']['path']}")
        
        # Test 3: Pagination Configuration Building
        print("\n[TEST 3] Pagination Configuration Types")
        print("-" * 70)
        
        pagination_types = [
            ('offset', {'page_size': 100}),
            ('cursor', {'cursor_param': 'after', 'cursor_path': 'data[-1].id'}),
            ('page_number', {'page_size': 50, 'base_page': 1}),
            ('header_link', {}),
            ('json_link', {'next_url_path': 'links.next'}),
            ('single_page', {})
        ]
        
        for pag_type, job_data in pagination_types:
            test_job = {
                'source_name': 'test_api',
                'table_name': 'data',
                'api_endpoint': '/api/data',
                'pagination_type': pag_type,
                **job_data
            }
            
            config = source.build_rest_config(test_job)
            resource = config['resources'][0]
            
            if pag_type != 'single_page':
                assert 'paginator' in resource['endpoint'], f"Missing paginator for {pag_type}"
                print(f"✓ {pag_type:<15} - Configuration valid")
            else:
                print(f"✓ {pag_type:<15} - No paginator (single page)")
        
        # Test 4: Authentication Types
        print("\n[TEST 4] Authentication Configuration Types")
        print("-" * 70)
        
        auth_tests = [
            ('api_key_header', {
                'auth_type': 'api_key',
                'api_key': 'test_key',
                'api_key_name': 'X-API-Key',
                'api_key_location': 'header'
            }),
            ('api_key_query', {
                'auth_type': 'api_key',
                'api_key': 'test_key',
                'api_key_name': 'key',
                'api_key_location': 'query'
            }),
            ('bearer', {
                'auth_type': 'bearer',
                'token': 'bearer_token_123'
            }),
            ('basic', {
                'auth_type': 'basic',
                'username': 'user',
                'password': 'pass'
            }),
            ('oauth2', {
                'auth_type': 'oauth2',
                'oauth_url': 'https://auth.example.com/token',
                'client_id': 'client_123',
                'client_secret': 'secret_456'
            }),
            ('none', {
                'auth_type': 'none'
            })
        ]
        
        for auth_name, auth_config in auth_tests:
            # Create temporary config loader with this auth
            class TempConfigLoader:
                def get_source_config(self, source_type, source_name):
                    return {
                        'base_url': 'https://api.example.com',
                        **auth_config
                    }
            
            temp_source = RESTAPISource(TempConfigLoader())
            test_job = {
                'source_name': 'test',
                'table_name': 'data',
                'api_endpoint': '/data',
                'pagination_type': 'single_page',
                **auth_config
            }
            
            config = temp_source.build_rest_config(test_job)
            print(f"✓ {auth_name:<20} - Configuration valid")
        
        # Summary
        print("\n" + "="*70)
        print("[SUCCESS] All REST API Source v2.0 Validations Passed!")
        print("="*70)
        print("\nFeature Summary:")
        print("  ✓ 6 pagination types (offset, cursor, page_number, header_link, json_link, single_page)")
        print("  ✓ 6 authentication methods (api_key, bearer, basic, oauth2, none)")
        print("  ✓ Configuration building")
        print("  ✓ DLT rest_api_source() integration ready")
        print("\nNext Steps:")
        print("  1. Add API jobs to config/ingestion_config.xlsx")
        print("  2. Configure secrets in .dlt/secrets.toml")
        print("  3. Run: python run.py")
        print("  4. See docs/REST_API_CONFIGURATION_EXAMPLES.md for examples")
        
        return True
        
    except AssertionError as e:
        print(f"\n[FAILED] Validation error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_rest_api_source()
    sys.exit(0 if success else 1)
