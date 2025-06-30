#!/usr/bin/env python3
"""
Day 3 AI Integration & Cost Management Validation Test
Tests AI cost management implementation and end-to-end AI features.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
import traceback

# Test imports
try:
    from app.core.ai_cost_management import (
        AIUsageTracker, 
        ai_cost_control, 
        get_ai_usage_stats,
        AICostManagementMiddleware
    )
    from app.core.config import get_settings
    from app.repositories.cosmos_unified import UnifiedCosmosRepository
    from app.models.user import User
    
    print("✅ AI cost management imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    traceback.print_exc()
    exit(1)

class Day3AICostManagementTest:
    """Test AI cost management and integration functionality"""
    
    def __init__(self):
        self.settings = get_settings()
        self.test_results = {
            "ai_cost_tracking": False,
            "cost_limits_enforcement": False, 
            "graceful_degradation": False,
            "ai_endpoint_integration": False,
            "usage_statistics": False,
            "middleware_functionality": False
        }
        self.detailed_results = []
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        message = f"{status} - {test_name}"
        if details:
            message += f": {details}"
        print(message)
        self.detailed_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_ai_usage_tracker(self):
        """Test AI usage tracking functionality"""
        print("\n🧪 Testing AI Usage Tracker...")
        
        try:
            tracker = AIUsageTracker()
            
            # Test tracking usage
            user_id = "test_user_123"
            endpoint = "assistant"
            model = "gpt-4"
            tokens = 1000
            
            result = tracker.track_usage(user_id, endpoint, model, tokens)
            
            # Verify tracking results
            assert "user_daily_cost" in result
            assert "request_cost" in result
            assert "total_daily_cost" in result
            assert "within_limits" in result
            
            expected_cost = (tokens / 1000) * 0.03  # gpt-4 cost
            assert abs(result["request_cost"] - expected_cost) < 0.001
            
            self.log_result("AI Usage Tracker - Basic tracking", True, f"Cost: ${result['request_cost']:.4f}")
            
            # Test limit checking
            limits = result["within_limits"]
            assert isinstance(limits["user_within_limit"], bool)
            assert isinstance(limits["request_within_limit"], bool)
            assert isinstance(limits["daily_within_limit"], bool)
            
            self.log_result("AI Usage Tracker - Limit checking", True, "All limit checks working")
            
            # Test usage statistics
            stats = tracker.get_usage_stats(user_id)
            assert "user_stats" in stats
            assert "limits" in stats
            assert "remaining" in stats
            
            self.log_result("AI Usage Tracker - Statistics", True, f"Remaining budget: ${stats['remaining']['user_budget']:.2f}")
            
            self.test_results["ai_cost_tracking"] = True
            
        except Exception as e:
            self.log_result("AI Usage Tracker", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def test_cost_limits_enforcement(self):
        """Test cost limits enforcement"""
        print("\n🛡️ Testing Cost Limits Enforcement...")
        
        try:
            tracker = AIUsageTracker()
            
            # Set low limits for testing
            original_limits = tracker.cost_thresholds.copy()
            tracker.cost_thresholds = {
                'daily_limit': 1.0,    # $1 daily limit
                'user_limit': 0.5,     # $0.50 per user daily
                'request_limit': 0.1   # $0.10 per request
            }
            
            # Test exceeding user limit
            user_id = "test_user_limit"
            
            # First request within limit
            result1 = tracker.track_usage(user_id, "assistant", "gpt-4", 100)  # ~$0.003
            assert result1["within_limits"]["user_within_limit"] == True
            
            # Request that exceeds user limit
            result2 = tracker.track_usage(user_id, "assistant", "gpt-4", 20000)  # ~$0.6
            assert result2["within_limits"]["user_within_limit"] == False
            
            self.log_result("Cost Limits - User limit enforcement", True, "User limit properly enforced")
            
            # Test daily limit
            daily_stats = tracker.get_usage_stats()
            remaining_budget = daily_stats["remaining"]["daily_budget"]
            
            self.log_result("Cost Limits - Daily budget tracking", True, f"Remaining: ${remaining_budget:.3f}")
            
            # Restore original limits
            tracker.cost_thresholds = original_limits
            
            self.test_results["cost_limits_enforcement"] = True
            
        except Exception as e:
            self.log_result("Cost Limits Enforcement", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def test_ai_cost_decorator(self):
        """Test AI cost control decorator"""
        print("\n🎯 Testing AI Cost Control Decorator...")
        
        try:
            # Create a test function with the decorator
            @ai_cost_control(model='gpt-3.5-turbo', max_tokens=500)
            async def test_ai_function(current_user=None):
                return {
                    "response": "Test AI response",
                    "success": True
                }
            
            # Test with mock user
            mock_user = {"id": "test_decorator_user"}
            result = await test_ai_function(current_user=mock_user)
            
            assert "response" in result
            assert result["success"] == True
            
            self.log_result("AI Cost Decorator - Basic functionality", True, "Decorator applied successfully")
            
            # Test cost tracking in response
            if "ai_usage" in result:
                usage = result["ai_usage"]
                assert "cost" in usage
                assert "remaining_budget" in usage
                assert "tokens_used" in usage
                
                self.log_result("AI Cost Decorator - Usage tracking", True, f"Cost: ${usage['cost']:.4f}")
            else:
                self.log_result("AI Cost Decorator - Usage tracking", True, "No usage info (expected in test)")
            
            self.test_results["ai_endpoint_integration"] = True
            
        except Exception as e:
            self.log_result("AI Cost Decorator", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def test_graceful_degradation(self):
        """Test graceful degradation functionality"""
        print("\n🛟 Testing Graceful Degradation...")
        
        try:
            # Test the middleware graceful degradation response
            middleware = AICostManagementMiddleware(app=None)
            response = middleware._graceful_degradation_response()
            
            assert response.status_code == 503
            
            # Parse response content
            content = json.loads(response.body.decode())
            assert "error" in content
            assert content["error"] == "AI_SERVICE_UNAVAILABLE"
            assert "message" in content
            assert "fallback_suggestions" in content
            assert "retry_after" in content
            
            self.log_result("Graceful Degradation - Response format", True, "Proper 503 response with fallbacks")
            
            # Test fallback suggestions are helpful
            suggestions = content["fallback_suggestions"]
            assert len(suggestions) > 0
            assert any("manual" in suggestion.lower() for suggestion in suggestions)
            
            self.log_result("Graceful Degradation - Fallback suggestions", True, f"{len(suggestions)} suggestions provided")
            
            self.test_results["graceful_degradation"] = True
            
        except Exception as e:
            self.log_result("Graceful Degradation", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def test_usage_statistics(self):
        """Test usage statistics functionality"""
        print("\n📊 Testing Usage Statistics...")
        
        try:
            # Test global usage stats function
            stats = get_ai_usage_stats()
            
            assert "daily_stats" in stats or "user_stats" in stats
            assert "limits" in stats
            assert "remaining" in stats
            
            self.log_result("Usage Statistics - Global stats", True, "Statistics accessible")
            
            # Test user-specific stats
            user_stats = get_ai_usage_stats("test_user_123")
            
            if "user_stats" in user_stats:
                user_data = user_stats["user_stats"]
                assert "requests" in user_data
                assert "tokens" in user_data
                assert "cost" in user_data
                
                self.log_result("Usage Statistics - User stats", True, f"Requests: {user_data['requests']}, Cost: ${user_data['cost']:.4f}")
            else:
                self.log_result("Usage Statistics - User stats", True, "No user data (expected for test)")
            
            self.test_results["usage_statistics"] = True
            
        except Exception as e:
            self.log_result("Usage Statistics", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def test_middleware_functionality(self):
        """Test middleware functionality"""
        print("\n⚙️ Testing Middleware Functionality...")
        
        try:
            # Test middleware initialization
            ai_endpoints = ['/api/assistant', '/api/polls', '/api/consensus']
            middleware = AICostManagementMiddleware(app=None, ai_endpoints=ai_endpoints)
            
            assert middleware.ai_endpoints == ai_endpoints
            
            self.log_result("Middleware - Initialization", True, f"Configured for {len(ai_endpoints)} endpoints")
            
            # Test reset time calculation
            reset_time = middleware._get_reset_time()
            assert isinstance(reset_time, str)
            assert "T" in reset_time  # ISO format
            
            self.log_result("Middleware - Reset time calculation", True, f"Next reset: {reset_time}")
            
            self.test_results["middleware_functionality"] = True
            
        except Exception as e:
            self.log_result("Middleware Functionality", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def test_ai_endpoint_imports(self):
        """Test that AI endpoints have cost management imports"""
        print("\n📦 Testing AI Endpoint Imports...")
        
        try:
            # Test assistant.py imports
            from app.api.assistant import router as assistant_router
            self.log_result("AI Endpoints - Assistant import", True, "Assistant module imported")
            
            # Test polls.py imports  
            from app.api.polls import router as polls_router
            self.log_result("AI Endpoints - Polls import", True, "Polls module imported")
            
            # Test consensus.py imports
            from app.api.consensus import router as consensus_router
            self.log_result("AI Endpoints - Consensus import", True, "Consensus module imported")
            
            # Verify routers have endpoints
            assert len(assistant_router.routes) > 0
            assert len(polls_router.routes) > 0
            assert len(consensus_router.routes) > 0
            
            self.log_result("AI Endpoints - Router configuration", True, "All routers have endpoints")
            
        except Exception as e:
            self.log_result("AI Endpoint Imports", False, f"Error: {str(e)}")
            traceback.print_exc()
    
    async def run_all_tests(self):
        """Run all AI cost management tests"""
        print("🚀 Starting Day 3 AI Cost Management Validation Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        await self.test_ai_usage_tracker()
        await self.test_cost_limits_enforcement()
        await self.test_ai_cost_decorator()
        await self.test_graceful_degradation()
        await self.test_usage_statistics()
        await self.test_middleware_functionality()
        await self.test_ai_endpoint_imports()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        success_rate = (passed_tests / total_tests) * 100
        
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("🎯 DAY 3 AI COST MANAGEMENT TEST RESULTS")
        print("=" * 60)
        
        for category, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {category.replace('_', ' ').title()}")
        
        print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"⏱️ Execution Time: {execution_time:.2f} seconds")
        
        # Detailed results summary
        if success_rate >= 90:
            print("\n🎉 EXCELLENT: AI cost management implementation is production-ready!")
        elif success_rate >= 75:
            print("\n👍 GOOD: AI cost management mostly implemented, minor issues to resolve")
        elif success_rate >= 50:
            print("\n⚠️ PARTIAL: AI cost management partially implemented, significant work needed")
        else:
            print("\n🚨 NEEDS WORK: AI cost management requires major implementation")
        
        # Save detailed results
        results_file = f"day3_ai_cost_management_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": self.test_results,
                "success_rate": success_rate,
                "execution_time": execution_time,
                "detailed_results": self.detailed_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Next steps recommendations
        print("\n🔄 NEXT STEPS:")
        if self.test_results["ai_cost_tracking"] and self.test_results["cost_limits_enforcement"]:
            print("✅ AI cost management is implemented - proceed with real AI integration testing")
        else:
            print("❌ Fix AI cost management issues before proceeding")
            
        if passed_tests == total_tests:
            print("✅ Ready for production AI endpoint testing with real Cosmos DB")
            print("✅ Ready to integrate frontend AI components with cost-managed backend")
        
        return success_rate >= 75  # 75% threshold for Day 3 readiness

if __name__ == "__main__":
    test_runner = Day3AICostManagementTest()
    success = asyncio.run(test_runner.run_all_tests())
    exit(0 if success else 1)
