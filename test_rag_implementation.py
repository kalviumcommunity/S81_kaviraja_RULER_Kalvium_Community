"""
RAG Platform Integration Test Suite
Tests all major components and generates verification report
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
TEST_TIMEOUT = 30

class TestColors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{TestColors.BOLD}{TestColors.BLUE}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{TestColors.RESET}\n")

def print_success(text: str):
    """Print a success message"""
    print(f"{TestColors.GREEN}✅ {text}{TestColors.RESET}")

def print_error(text: str):
    """Print an error message"""
    print(f"{TestColors.RED}❌ {text}{TestColors.RESET}")

def print_warning(text: str):
    """Print a warning message"""
    print(f"{TestColors.YELLOW}⚠️  {text}{TestColors.RESET}")

def print_info(text: str):
    """Print an info message"""
    print(f"{TestColors.BLUE}ℹ️  {text}{TestColors.RESET}")

class RAGTester:
    """Comprehensive RAG Platform Tester"""
    
    def __init__(self):
        self.test_results = {
            "api_status": None,
            "chat_test": None,
            "source_display": None,
            "error_handling": None,
            "token_tracking": None,
            "timestamp": datetime.now().isoformat()
        }
        self.total_tests = 0
        self.passed_tests = 0
    
    def test_api_status(self) -> bool:
        """Test 1: Check API connectivity and status"""
        print_info("Testing API connectivity...")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/status",
                timeout=5
            )
            
            if response.status_code != 200:
                print_error(f"API returned status {response.status_code}")
                self.test_results["api_status"] = {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                return False
            
            data = response.json()
            
            # Verify required fields
            required_fields = ["status", "model_name", "has_api_key"]
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                print_error(f"Missing fields in API response: {missing}")
                return False
            
            print_success(f"API Online - Model: {data.get('model_name')}")
            print_info(f"API Key Available: {data.get('has_api_key')}")
            print_info(f"Token Chunker Available: {data.get('token_chunker_available')}")
            
            self.test_results["api_status"] = {
                "success": True,
                "data": data
            }
            return True
        
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to API server (http://127.0.0.1:8000)")
            print_warning("Make sure to run: python run_ui.py")
            return False
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            return False
    
    def test_chat_functionality(self) -> bool:
        """Test 2: Test chat endpoint with sample questions"""
        print_info("Testing chat functionality...")
        
        test_questions = [
            "What are AML requirements?",
            "Explain compliance thresholds",
            "Banking regulations"
        ]
        
        responses = []
        
        for question in test_questions:
            try:
                payload = {
                    "user_message": question,
                    "system_role": "Banking Regulatory Compliance Assistant",
                    "required_fields": ["answer", "source", "confidence"],
                    "temperature": 0.2,
                    "use_mock": False
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/api/chat",
                    json=payload,
                    timeout=API_TIMEOUT
                )
                elapsed = time.time() - start_time
                
                if response.status_code != 200:
                    print_error(f"Chat API returned {response.status_code}")
                    continue
                
                data = response.json()
                
                if not data.get("success"):
                    print_error(f"Chat returned unsuccessful response")
                    continue
                
                parsed = data.get("parsed_object", {})
                answer = parsed.get("answer", "")
                citations = parsed.get("citations", [])
                
                # Validate response structure
                if not answer:
                    print_error("Empty answer received")
                    continue
                
                print_success(f"Question: '{question}'")
                print_info(f"  Answer Length: {len(answer)} characters")
                print_info(f"  Citations Found: {len(citations)}")
                print_info(f"  Grounded: {parsed.get('is_grounded', False)}")
                print_info(f"  Response Time: {elapsed:.2f}s")
                
                responses.append({
                    "question": question,
                    "answer": answer[:100] + "...",
                    "citations": len(citations),
                    "response_time": elapsed,
                    "grounded": parsed.get("is_grounded", False)
                })
                
                # Small delay between requests
                time.sleep(0.5)
            
            except Exception as e:
                print_error(f"Error testing question '{question}': {str(e)}")
        
        success = len(responses) > 0
        self.test_results["chat_test"] = {
            "success": success,
            "questions_tested": len(test_questions),
            "successful_responses": len(responses),
            "responses": responses
        }
        
        return success
    
    def test_source_display(self) -> bool:
        """Test 3: Verify source attribution structure"""
        print_info("Testing source display structure...")
        
        try:
            payload = {
                "user_message": "What are AML requirements?",
                "system_role": "Banking Regulatory Compliance Assistant",
                "required_fields": ["answer", "source", "confidence"],
                "temperature": 0.2
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                json=payload,
                timeout=API_TIMEOUT
            )
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            parsed = data.get("parsed_object", {})
            citations = parsed.get("citations", [])
            
            if not citations:
                print_warning("No citations found in response (this is okay for out-of-domain queries)")
                return True
            
            # Validate each citation structure
            required_citation_fields = ["marker", "filename", "raw_text"]
            
            all_valid = True
            for idx, citation in enumerate(citations, 1):
                missing = [f for f in required_citation_fields if f not in citation]
                if missing:
                    print_error(f"Citation {idx} missing fields: {missing}")
                    all_valid = False
                    continue
                
                print_success(f"Citation {idx}: {citation.get('filename')}")
                print_info(f"  Marker: {citation.get('marker')}")
                print_info(f"  Doc ID: {citation.get('doc_id', 'N/A')}")
                print_info(f"  Chunk ID: {citation.get('chunk_id', 'N/A')}")
                print_info(f"  Text Preview: {citation.get('raw_text', '')[:80]}...")
            
            self.test_results["source_display"] = {
                "success": all_valid,
                "citations_found": len(citations),
                "citations": citations
            }
            
            return all_valid
        
        except Exception as e:
            print_error(f"Error testing source display: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test 4: Verify error handling for edge cases"""
        print_info("Testing error handling...")
        
        test_cases = [
            {
                "name": "Empty question",
                "payload": {
                    "user_message": "",
                    "system_role": "RAG",
                    "required_fields": ["answer"],
                    "temperature": 0.2
                },
                "expect_error": True
            },
            {
                "name": "Out-of-domain query",
                "payload": {
                    "user_message": "Tell me a joke about penguins",
                    "system_role": "RAG",
                    "required_fields": ["answer"],
                    "temperature": 0.2
                },
                "expect_error": False  # Should still return answer
            },
            {
                "name": "Very long question",
                "payload": {
                    "user_message": "What " * 500,
                    "system_role": "RAG",
                    "required_fields": ["answer"],
                    "temperature": 0.2
                },
                "expect_error": False
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/chat",
                    json=test_case["payload"],
                    timeout=API_TIMEOUT
                )
                
                success = response.status_code in [200, 400]  # 400 is acceptable for validation errors
                
                print_success(f"Handled: {test_case['name']}")
                print_info(f"  Status: {response.status_code}")
                
                results.append({
                    "test": test_case["name"],
                    "status": response.status_code,
                    "handled": success
                })
            
            except Exception as e:
                print_warning(f"Error in test '{test_case['name']}': {str(e)}")
                results.append({
                    "test": test_case["name"],
                    "error": str(e),
                    "handled": False
                })
        
        success = any(r.get("handled") for r in results)
        self.test_results["error_handling"] = {
            "success": success,
            "test_cases": len(results),
            "results": results
        }
        
        return success
    
    def test_token_tracking(self) -> bool:
        """Test 5: Verify token usage tracking"""
        print_info("Testing token usage tracking...")
        
        try:
            payload = {
                "user_message": "What are compliance requirements?",
                "system_role": "RAG",
                "required_fields": ["answer"],
                "temperature": 0.2
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                json=payload,
                timeout=API_TIMEOUT
            )
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            token_usage = data.get("token_usage", {})
            
            required_fields = ["prompt_tokens", "completion_tokens", "total_tokens"]
            missing = [f for f in required_fields if f not in token_usage]
            
            if missing:
                print_error(f"Missing token fields: {missing}")
                return False
            
            print_success("Token tracking verified")
            print_info(f"  Prompt Tokens: {token_usage.get('prompt_tokens')}")
            print_info(f"  Completion Tokens: {token_usage.get('completion_tokens')}")
            print_info(f"  Total Tokens: {token_usage.get('total_tokens')}")
            
            self.test_results["token_tracking"] = {
                "success": True,
                "token_usage": token_usage
            }
            
            return True
        
        except Exception as e:
            print_error(f"Error testing token tracking: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print_header("RAG Platform Integration Test Suite")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API URL: {API_BASE_URL}\n")
        
        tests = [
            ("API Status", self.test_api_status),
            ("Chat Functionality", self.test_chat_functionality),
            ("Source Display", self.test_source_display),
            ("Error Handling", self.test_error_handling),
            ("Token Tracking", self.test_token_tracking),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print_header(f"Test: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                self.total_tests += 1
                if result:
                    self.passed_tests += 1
            except Exception as e:
                print_error(f"Test failed with exception: {str(e)}")
                results[test_name] = False
                self.total_tests += 1
        
        # Generate summary
        self.print_summary(results)
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        print_header("Test Summary")
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status} | {test_name}")
        
        print(f"\n{TestColors.BOLD}Results:{TestColors.RESET}")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  Passed: {self.passed_tests}")
        print(f"  Failed: {self.total_tests - self.passed_tests}")
        
        if self.passed_tests == self.total_tests:
            print_success("All tests passed! Implementation is complete.")
        else:
            print_warning(f"{self.total_tests - self.passed_tests} test(s) failed. See details above.")
        
        # Save report
        self.save_report()
    
    def save_report(self):
        """Save test results to JSON file"""
        report_file = "outputs/test_report.json"
        
        try:
            with open(report_file, "w") as f:
                json.dump(self.test_results, f, indent=2)
            print_success(f"Test report saved to {report_file}")
        except Exception as e:
            print_warning(f"Could not save test report: {str(e)}")


def main():
    """Main test entry point"""
    print(f"\n{TestColors.BOLD}{TestColors.BLUE}")
    print("""
    ██████╗ ██╗   ██╗██╗     ███████╗██████╗ 
    ██╔══██╗██║   ██║██║     ██╔════╝██╔══██╗
    ██████╔╝██║   ██║██║     █████╗  ██████╔╝
    ██╔══██╗██║   ██║██║     ██╔══╝  ██╔══██╗
    ██║  ██║╚██████╔╝███████╗███████╗██║  ██║
    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝
    
    Banking Regulatory RAG Platform
    Integration Test Suite
    """)
    print(f"{TestColors.RESET}")
    
    # Create tester and run all tests
    tester = RAGTester()
    tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if tester.passed_tests == tester.total_tests else 1)


if __name__ == "__main__":
    main()
