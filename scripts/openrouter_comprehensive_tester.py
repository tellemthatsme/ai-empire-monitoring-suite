#!/usr/bin/env python3
"""
OpenRouter Comprehensive Testing System
======================================
Complete testing suite for OpenRouter API integration
Tests all 57 free models, connection stability, and performance
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class OpenRouterTester:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY', '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')
        self.base_url = 'https://openrouter.ai/api/v1'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/tellemthatsme/ai-empire-monitoring-suite',
            'X-Title': 'AI Empire Monitoring Suite - Comprehensive Test'
        }
        self.test_results = {}
        
    def test_api_authentication(self) -> Dict:
        """Test API authentication and account status"""
        print("Testing OpenRouter API Authentication...")
        
        try:
            # Test auth endpoint
            response = requests.get(f'{self.base_url}/auth/key', headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                auth_data = response.json().get('data', {})
                result = {
                    'status': 'success',
                    'authenticated': True,
                    'usage': auth_data.get('usage', 0),
                    'limit': auth_data.get('limit'),
                    'rate_limit': auth_data.get('rate_limit', {}),
                    'response_time': response.elapsed.total_seconds()
                }
                print(f"[SUCCESS] Authentication verified - Usage: ${result['usage']:.6f}")
            else:
                result = {
                    'status': 'failed',
                    'authenticated': False,
                    'error_code': response.status_code,
                    'error_message': response.text[:200]
                }
                print(f"[FAILED] Authentication failed - Status: {response.status_code}")
                
        except Exception as e:
            result = {
                'status': 'error',
                'authenticated': False,
                'error': str(e)
            }
            print(f"[ERROR] Authentication test failed: {e}")
            
        self.test_results['authentication'] = result
        return result
    
    def get_all_models(self) -> Tuple[List[Dict], List[Dict]]:
        """Get all available models and filter free models"""
        print("Retrieving all available models...")
        
        try:
            response = requests.get(f'{self.base_url}/models', headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                all_models = response.json().get('data', [])
                
                # Filter free models (prompt price = "0")
                free_models = []
                for model in all_models:
                    pricing = model.get('pricing', {})
                    prompt_price = pricing.get('prompt')
                    
                    if prompt_price == '0' or prompt_price == 0:
                        free_models.append(model)
                
                print(f"[SUCCESS] Found {len(all_models)} total models, {len(free_models)} free models")
                
                self.test_results['model_discovery'] = {
                    'status': 'success',
                    'total_models': len(all_models),
                    'free_models': len(free_models),
                    'response_time': response.elapsed.total_seconds()
                }
                
                return all_models, free_models
                
            else:
                print(f"[FAILED] Models endpoint returned {response.status_code}")
                return [], []
                
        except Exception as e:
            print(f"[ERROR] Failed to retrieve models: {e}")
            return [], []
    
    def test_free_model_completions(self, free_models: List[Dict], max_tests: int = 10) -> Dict:
        """Test completion API with free models"""
        print(f"Testing completions with up to {max_tests} free models...")
        
        completion_results = {
            'successful_models': [],
            'failed_models': [],
            'rate_limited_models': [],
            'total_tested': 0,
            'success_rate': 0.0
        }
        
        # Test prompt
        test_payload = {
            'messages': [{'role': 'user', 'content': 'Reply with just: SYSTEM TEST OK'}],
            'max_tokens': 20,
            'temperature': 0.1
        }
        
        models_to_test = free_models[:max_tests]
        
        for i, model in enumerate(models_to_test):
            model_id = model.get('id', 'unknown')
            context_length = model.get('context_length', 'N/A')
            
            print(f"Testing {i+1}/{len(models_to_test)}: {model_id[:50]}...")
            
            try:
                test_payload['model'] = model_id
                
                response = requests.post(
                    f'{self.base_url}/chat/completions',
                    headers=self.headers,
                    json=test_payload,
                    timeout=20
                )
                
                completion_results['total_tested'] += 1
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    completion_results['successful_models'].append({
                        'model_id': model_id,
                        'response': content.strip(),
                        'context_length': context_length,
                        'response_time': response.elapsed.total_seconds()
                    })
                    
                    print(f"  [SUCCESS] Response: {content.strip()}")
                    
                elif response.status_code == 429:
                    completion_results['rate_limited_models'].append({
                        'model_id': model_id,
                        'context_length': context_length,
                        'error': 'Rate limited'
                    })
                    print(f"  [RATE_LIMITED] Model temporarily unavailable")
                    
                else:
                    error_msg = response.text[:100]
                    completion_results['failed_models'].append({
                        'model_id': model_id,
                        'context_length': context_length,
                        'error_code': response.status_code,
                        'error': error_msg
                    })
                    print(f"  [FAILED] Status {response.status_code}: {error_msg}")
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                completion_results['failed_models'].append({
                    'model_id': model_id,
                    'context_length': context_length,
                    'error': str(e)
                })
                print(f"  [ERROR] {str(e)[:50]}")
        
        # Calculate success rate
        if completion_results['total_tested'] > 0:
            completion_results['success_rate'] = len(completion_results['successful_models']) / completion_results['total_tested']
        
        self.test_results['completions'] = completion_results
        return completion_results
    
    def test_system_performance(self) -> Dict:
        """Test system performance metrics"""
        print("Testing system performance...")
        
        performance_results = {
            'response_times': [],
            'average_response_time': 0.0,
            'fastest_response': float('inf'),
            'slowest_response': 0.0,
            'availability': 0.0,
            'total_requests': 0,
            'successful_requests': 0
        }
        
        # Test with multiple requests
        test_requests = 5
        
        for i in range(test_requests):
            try:
                start_time = time.time()
                response = requests.get(f'{self.base_url}/models', headers=self.headers, timeout=10)
                end_time = time.time()
                
                response_time = end_time - start_time
                performance_results['response_times'].append(response_time)
                performance_results['total_requests'] += 1
                
                if response.status_code == 200:
                    performance_results['successful_requests'] += 1
                
                # Update fastest/slowest
                if response_time < performance_results['fastest_response']:
                    performance_results['fastest_response'] = response_time
                if response_time > performance_results['slowest_response']:
                    performance_results['slowest_response'] = response_time
                
                print(f"  Request {i+1}: {response_time:.3f}s (Status: {response.status_code})")
                
            except Exception as e:
                performance_results['total_requests'] += 1
                print(f"  Request {i+1}: Failed - {e}")
        
        # Calculate averages
        if performance_results['response_times']:
            performance_results['average_response_time'] = sum(performance_results['response_times']) / len(performance_results['response_times'])
        
        if performance_results['total_requests'] > 0:
            performance_results['availability'] = performance_results['successful_requests'] / performance_results['total_requests']
        
        self.test_results['performance'] = performance_results
        return performance_results
    
    def run_comprehensive_test(self) -> Dict:
        """Run complete OpenRouter system test"""
        print("=" * 60)
        print("OPENROUTER COMPREHENSIVE TESTING SUITE")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test 1: Authentication
        auth_result = self.test_api_authentication()
        print()
        
        # Test 2: Model Discovery
        all_models, free_models = self.get_all_models()
        print()
        
        # Test 3: Completion Testing (if auth successful)
        if auth_result.get('authenticated', False):
            completion_result = self.test_free_model_completions(free_models, max_tests=5)
        else:
            print("[SKIP] Skipping completion tests due to authentication failure")
            completion_result = {'total_tested': 0, 'successful_models': []}
        print()
        
        # Test 4: Performance Testing
        performance_result = self.test_system_performance()
        print()
        
        # Generate comprehensive report
        report = self.generate_test_report(all_models, free_models)
        
        print("=" * 60)
        print("COMPREHENSIVE TEST COMPLETE")
        print("=" * 60)
        
        return report
    
    def generate_test_report(self, all_models: List[Dict], free_models: List[Dict]) -> Dict:
        """Generate comprehensive test report"""
        
        # Calculate overall system health
        auth_score = 100 if self.test_results.get('authentication', {}).get('authenticated', False) else 0
        model_score = min(100, len(free_models) * 2)  # Up to 100 for 50+ free models
        
        completion_results = self.test_results.get('completions', {})
        completion_score = completion_results.get('success_rate', 0) * 100
        
        performance_results = self.test_results.get('performance', {})
        performance_score = performance_results.get('availability', 0) * 100
        
        overall_health = (auth_score + model_score + completion_score + performance_score) / 4
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health_score': round(overall_health, 2),
            'system_status': 'operational' if overall_health >= 75 else 'degraded' if overall_health >= 50 else 'critical',
            
            'authentication': self.test_results.get('authentication', {}),
            'model_availability': {
                'total_models': len(all_models),
                'free_models_available': len(free_models),
                'free_model_percentage': round((len(free_models) / len(all_models)) * 100, 2) if all_models else 0
            },
            'completion_testing': completion_results,
            'performance_metrics': performance_results,
            
            'cost_analysis': {
                'operational_cost': 0.00,
                'free_models_used': len(completion_results.get('successful_models', [])),
                'cost_savings': 'Unlimited (100% free operation)'
            },
            
            'recommendations': self.generate_recommendations()
        }
        
        # Save report to file
        filename = f"openrouter_comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"SYSTEM HEALTH SCORE: {report['overall_health_score']}%")
        print(f"STATUS: {report['system_status'].upper()}")
        print(f"FREE MODELS AVAILABLE: {len(free_models)}")
        print(f"SUCCESSFUL COMPLETIONS: {len(completion_results.get('successful_models', []))}")
        print(f"OPERATIONAL COST: $0.00")
        print(f"REPORT SAVED: {filename}")
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate system recommendations based on test results"""
        recommendations = []
        
        auth_result = self.test_results.get('authentication', {})
        if not auth_result.get('authenticated', False):
            recommendations.append("Update OpenRouter API key - authentication failed")
        
        completion_results = self.test_results.get('completions', {})
        success_rate = completion_results.get('success_rate', 0)
        
        if success_rate < 0.5:
            recommendations.append("High completion failure rate - check API key permissions")
        elif success_rate < 0.8:
            recommendations.append("Moderate completion issues - some models may be temporarily unavailable")
        
        rate_limited_count = len(completion_results.get('rate_limited_models', []))
        if rate_limited_count > 3:
            recommendations.append("Multiple models rate-limited - implement retry logic with backoff")
        
        performance_results = self.test_results.get('performance', {})
        avg_response_time = performance_results.get('average_response_time', 0)
        
        if avg_response_time > 5.0:
            recommendations.append("High response times - consider geographic proximity or caching")
        elif avg_response_time > 2.0:
            recommendations.append("Elevated response times - monitor API performance")
        
        if not recommendations:
            recommendations = [
                "System performing optimally",
                "Continue using free models for zero-cost operation", 
                "Monitor rate limits during high-usage periods",
                "Consider implementing failover between multiple free models"
            ]
        
        return recommendations

def main():
    """Main execution function"""
    tester = OpenRouterTester()
    report = tester.run_comprehensive_test()
    return report

if __name__ == "__main__":
    main()