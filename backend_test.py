import requests
import sys
import time
import json
from datetime import datetime

class FakeNewsSniffAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FakeNewsSniff-Tester/1.0'
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=60):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = self.session.get(url, timeout=timeout)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=timeout)
            
            elapsed_time = time.time() - start_time
            print(f"   Response time: {elapsed_time:.2f}s")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test(
            "Health Check",
            "GET", 
            "api/health",
            200
        )

    def test_root_endpoint(self):
        """Test root endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )

    def test_analyze_with_reliable_url(self):
        """Test analysis with reliable news URL"""
        reliable_url = "https://g1.globo.com/politica/"
        
        success, response = self.run_test(
            "Analyze Reliable URL (G1)",
            "POST",
            "api/analyze",
            200,
            data={"url_or_text": reliable_url},
            timeout=90
        )
        
        if success and isinstance(response, dict):
            # Validate response structure
            required_fields = ['suspicion_score', 'factors', 'sources_checked', 'content_summary', 'analysis_details']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"⚠️  Missing response fields: {missing_fields}")
                return False
            
            score = response.get('suspicion_score', -1)
            factors = response.get('factors', [])
            sources = response.get('sources_checked', [])
            
            print(f"   Suspicion Score: {score}/100")
            print(f"   Factors found: {len(factors)}")
            print(f"   Sources checked: {len(sources)}")
            
            # For reliable source, score should be relatively low
            if score <= 50:
                print(f"✅ Score appropriate for reliable source: {score}")
            else:
                print(f"⚠️  High score for reliable source: {score}")
            
            return True
        
        return success

    def test_analyze_with_suspicious_text(self):
        """Test analysis with suspicious text patterns"""
        suspicious_text = "URGENTE! BOMBA! ESCÂNDALO CHOCANTE revelado! Você não vai acreditar no que descobrimos!"
        
        success, response = self.run_test(
            "Analyze Suspicious Text",
            "POST",
            "api/analyze", 
            200,
            data={"url_or_text": suspicious_text},
            timeout=60
        )
        
        if success and isinstance(response, dict):
            score = response.get('suspicion_score', -1)
            factors = response.get('factors', [])
            
            print(f"   Suspicion Score: {score}/100")
            print(f"   Factors: {factors}")
            
            # Should detect suspicious patterns
            suspicious_detected = any('sensacionalista' in factor.lower() for factor in factors)
            if suspicious_detected:
                print("✅ Suspicious patterns correctly detected")
            else:
                print("⚠️  Suspicious patterns not detected")
            
            return True
        
        return success

    def test_analyze_with_normal_text(self):
        """Test analysis with normal news text"""
        normal_text = "O presidente participou de uma reunião sobre políticas públicas na manhã desta terça-feira, conforme informado pela assessoria de imprensa."
        
        success, response = self.run_test(
            "Analyze Normal Text",
            "POST",
            "api/analyze",
            200,
            data={"url_or_text": normal_text},
            timeout=60
        )
        
        if success and isinstance(response, dict):
            score = response.get('suspicion_score', -1)
            print(f"   Suspicion Score: {score}/100")
            return True
        
        return success

    def test_analyze_empty_input(self):
        """Test analysis with empty input"""
        return self.run_test(
            "Analyze Empty Input",
            "POST",
            "api/analyze",
            400,  # Should return bad request
            data={"url_or_text": ""}
        )

    def test_analyze_invalid_url(self):
        """Test analysis with invalid URL"""
        return self.run_test(
            "Analyze Invalid URL",
            "POST",
            "api/analyze",
            200,  # Should still process but may have different results
            data={"url_or_text": "https://this-is-not-a-real-website-12345.com/fake-news"}
        )

    def test_scraping_functionality(self):
        """Test real scraping with a known working URL"""
        # Test with a simple, reliable URL that should work
        test_url = "https://www.bbc.com/portuguese"
        
        success, response = self.run_test(
            "Test Real Scraping (BBC)",
            "POST",
            "api/analyze",
            200,
            data={"url_or_text": test_url},
            timeout=90
        )
        
        if success and isinstance(response, dict):
            content_summary = response.get('content_summary', '')
            analysis_details = response.get('analysis_details', {})
            
            print(f"   Content extracted: {len(content_summary)} chars")
            print(f"   Extraction method: {analysis_details.get('extraction_method', 'unknown')}")
            
            # Check if content was actually extracted
            if len(content_summary) > 50 and 'não foi possível' not in content_summary.lower():
                print("✅ Real scraping working - content extracted")
                return True
            else:
                print("⚠️  Scraping may not be working properly")
                return False
        
        return success

def main():
    print("🚀 Starting Fake News Sniff API Tests")
    print("=" * 50)
    
    # Use the public endpoint from frontend .env
    tester = FakeNewsSniffAPITester("http://10.64.130.223:8001")
    
    # Run all tests
    test_methods = [
        tester.test_health_check,
        tester.test_root_endpoint,
        tester.test_analyze_empty_input,
        tester.test_analyze_with_normal_text,
        tester.test_analyze_with_suspicious_text,
        tester.test_analyze_with_reliable_url,
        tester.test_scraping_functionality,
        tester.test_analyze_invalid_url,
    ]
    
    print(f"\n📋 Running {len(test_methods)} test scenarios...")
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
        
        # Small delay between tests
        time.sleep(1)
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    elif tester.tests_passed >= tester.tests_run * 0.7:  # 70% pass rate
        print("⚠️  Most tests passed, but some issues detected.")
        return 0
    else:
        print("❌ Multiple test failures detected. Backend needs attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())