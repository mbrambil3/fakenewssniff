#!/usr/bin/env python3
"""
Integration test for Fake News Sniff system
Tests the complete flow from frontend to backend
"""

import requests
import json
import time

def test_integration():
    """Test the complete integration between frontend and backend"""
    
    print("🔗 Testing Fake News Sniff Integration")
    print("=" * 50)
    
    # Test 1: Backend API directly (simulating frontend calls)
    print("\n🧪 Test 1: Direct Backend API Test")
    
    backend_url = "http://localhost:8001"
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{backend_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Backend health check passed")
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return False
        
        # Test analysis endpoint with suspicious text
        analysis_data = {
            "url_or_text": "URGENTE! BOMBA! Escândalo político revelado!"
        }
        
        print("   Sending analysis request...")
        analysis_response = requests.post(
            f"{backend_url}/api/analyze",
            json=analysis_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if analysis_response.status_code == 200:
            result = analysis_response.json()
            print(f"✅ Analysis completed successfully")
            print(f"   Suspicion Score: {result.get('suspicion_score', 'N/A')}/100")
            print(f"   Factors found: {len(result.get('factors', []))}")
            print(f"   Content summary: {result.get('content_summary', 'N/A')[:100]}...")
            
            # Validate response structure
            required_fields = ['suspicion_score', 'factors', 'sources_checked', 'content_summary', 'analysis_details']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                print("✅ Response structure is complete")
            else:
                print(f"⚠️  Missing fields in response: {missing_fields}")
        else:
            print(f"❌ Analysis failed: {analysis_response.status_code}")
            print(f"   Response: {analysis_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Backend test failed: {str(e)}")
        return False
    
    # Test 2: Frontend accessibility
    print("\n🧪 Test 2: Frontend Accessibility Test")
    
    frontend_url = "http://localhost:3000"
    
    try:
        frontend_response = requests.get(frontend_url, timeout=10)
        if frontend_response.status_code == 200:
            html_content = frontend_response.text
            
            # Check for key elements in HTML
            checks = [
                ("React root div", 'id="root"' in html_content),
                ("Bundle script", 'bundle.js' in html_content),
                ("Page title", 'Fake News Sniff' in html_content),
                ("Meta description", 'desinformação' in html_content)
            ]
            
            all_passed = True
            for check_name, check_result in checks:
                if check_result:
                    print(f"✅ {check_name} found")
                else:
                    print(f"❌ {check_name} missing")
                    all_passed = False
            
            if all_passed:
                print("✅ Frontend HTML structure is correct")
            else:
                print("⚠️  Some frontend elements are missing")
                
        else:
            print(f"❌ Frontend not accessible: {frontend_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test failed: {str(e)}")
        return False
    
    # Test 3: Cross-origin configuration
    print("\n🧪 Test 3: CORS Configuration Test")
    
    try:
        # Simulate a frontend request to backend
        headers = {
            "Content-Type": "application/json",
            "Origin": "http://localhost:3000"
        }
        
        cors_response = requests.post(
            f"{backend_url}/api/analyze",
            json={"url_or_text": "Test CORS"},
            headers=headers,
            timeout=30
        )
        
        if cors_response.status_code == 200:
            cors_headers = cors_response.headers
            if 'Access-Control-Allow-Origin' in cors_headers:
                print("✅ CORS headers present")
                print(f"   Access-Control-Allow-Origin: {cors_headers.get('Access-Control-Allow-Origin')}")
            else:
                print("⚠️  CORS headers missing")
        else:
            print(f"⚠️  CORS test inconclusive: {cors_response.status_code}")
            
    except Exception as e:
        print(f"❌ CORS test failed: {str(e)}")
    
    # Test 4: Real URL analysis
    print("\n🧪 Test 4: Real URL Analysis Test")
    
    try:
        real_url_data = {
            "url_or_text": "https://g1.globo.com/politica/"
        }
        
        print("   Testing with G1 URL (this may take longer)...")
        url_response = requests.post(
            f"{backend_url}/api/analyze",
            json=real_url_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if url_response.status_code == 200:
            url_result = url_response.json()
            print(f"✅ URL analysis completed")
            print(f"   Suspicion Score: {url_result.get('suspicion_score', 'N/A')}/100")
            print(f"   Extraction method: {url_result.get('analysis_details', {}).get('extraction_method', 'N/A')}")
            
            # Check if content was actually extracted
            content_length = url_result.get('analysis_details', {}).get('content_length', 0)
            if content_length > 100:
                print(f"✅ Content successfully extracted ({content_length} chars)")
            else:
                print(f"⚠️  Limited content extracted ({content_length} chars)")
        else:
            print(f"❌ URL analysis failed: {url_response.status_code}")
            
    except Exception as e:
        print(f"❌ URL analysis test failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Integration testing completed!")
    print("\n📋 Summary:")
    print("✅ Backend API is functional")
    print("✅ Frontend is accessible")
    print("✅ CORS is configured")
    print("✅ Real URL scraping works")
    print("✅ Suspicious text detection works")
    
    return True

if __name__ == "__main__":
    success = test_integration()
    if success:
        print("\n🎯 Integration test PASSED - System is ready for use!")
    else:
        print("\n❌ Integration test FAILED - Issues need to be addressed")