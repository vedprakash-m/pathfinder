"""
Load Testing for Performance Validation
Simple load tests to validate system performance under stress.
"""

import pytest
import asyncio
import time
import concurrent.futures
from typing import List, Dict, Any
import statistics

# Mock the test client for load testing
try:
    from fastapi.testclient import TestClient
    from app.main import app

    TEST_APP_AVAILABLE = True
except ImportError:
    TEST_APP_AVAILABLE = False
    app = None


class LoadTestMetrics:
    """Simple metrics collector for load tests"""

    def __init__(self):
        self.response_times: List[float] = []
        self.status_codes: List[int] = []
        self.errors: List[str] = []

    def add_response(self, response_time: float, status_code: int, error: str = None):
        self.response_times.append(response_time)
        self.status_codes.append(status_code)
        if error:
            self.errors.append(error)

    def get_summary(self) -> Dict[str, Any]:
        if not self.response_times:
            return {"error": "No data collected"}

        return {
            "total_requests": len(self.response_times),
            "successful_requests": sum(
                1 for code in self.status_codes if 200 <= code < 300
            ),
            "error_rate": len(self.errors) / len(self.response_times),
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": (
                statistics.quantiles(self.response_times, n=20)[18]
                if len(self.response_times) > 1
                else 0
            ),
            "errors": self.errors[:10],  # First 10 errors
        }


def simulate_user_request(endpoint: str = "/health") -> Dict[str, Any]:
    """Simulate a single user request"""
    if not TEST_APP_AVAILABLE:
        return {"response_time": 0, "status_code": 500, "error": "App not available"}

    client = TestClient(app)
    start_time = time.time()

    try:
        response = client.get(endpoint)
        end_time = time.time()

        return {
            "response_time": end_time - start_time,
            "status_code": response.status_code,
            "error": None,
        }
    except Exception as e:
        end_time = time.time()
        return {
            "response_time": end_time - start_time,
            "status_code": 500,
            "error": str(e),
        }


class TestLoadPerformance:
    """Load testing for performance validation"""

    @pytest.mark.skip(reason="Load test - run separately")
    def test_concurrent_health_checks(self):
        """Test concurrent health check requests"""
        if not TEST_APP_AVAILABLE:
            pytest.skip("App not available for testing")

        metrics = LoadTestMetrics()
        concurrent_users = 10
        requests_per_user = 5

        def user_session():
            results = []
            for _ in range(requests_per_user):
                result = simulate_user_request("/health")
                results.append(result)
                time.sleep(0.1)  # Small delay between requests
            return results

        # Run concurrent user sessions
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=concurrent_users
        ) as executor:
            futures = [executor.submit(user_session)
                                       for _ in range(concurrent_users)]

            for future in concurrent.futures.as_completed(futures):
                try:
                    results = future.result()
                    for result in results:
                        metrics.add_response(
                            result["response_time"],
                            result["status_code"],
                            result["error"],
                        )
                except Exception as e:
                    metrics.add_response(0, 500, str(e))

        summary = metrics.get_summary()

        # Performance assertions
        assert (
            summary["total_requests"] >= concurrent_users * \
                requests_per_user * 0.8
        )  # Allow some failures
        assert summary["error_rate"] < 0.1  # Less than 10% error rate
        assert (
            summary["avg_response_time"] < 2.0
        )  # Average response time under 2 seconds

        print(f"Load test summary: {summary}")

    @pytest.mark.skip(reason="Load test - run separately")
    def test_sustained_load(self):
        """Test sustained load over time"""
        if not TEST_APP_AVAILABLE:
            pytest.skip("App not available for testing")

        metrics = LoadTestMetrics()
        duration_seconds = 30
        target_rps = 2  # Requests per second

        start_time = time.time()
        request_count = 0

        while time.time() - start_time < duration_seconds:
            result = simulate_user_request("/health")
            metrics.add_response(
                result["response_time"], result["status_code"], result["error"]
            )

            request_count += 1

            # Maintain target RPS
            elapsed = time.time() - start_time
            expected_requests = elapsed * target_rps
            if request_count > expected_requests:
                time.sleep((request_count - expected_requests) / target_rps)

        summary = metrics.get_summary()

        # Performance assertions
        assert summary["error_rate"] < 0.05  # Less than 5% error rate
        assert (
            summary["avg_response_time"] < 1.0
        )  # Average response time under 1 second
        # 95th percentile under 2 seconds
        assert summary["p95_response_time"] < 2.0

        print(f"Sustained load test summary: {summary}")

    def test_memory_usage_simulation(self):
        """Basic memory usage validation"""
        if not TEST_APP_AVAILABLE:
            pytest.skip("App not available for testing")

        # Simple test to ensure basic operations don't consume excessive memory
        client = TestClient(app)

        # Make multiple requests to see if memory usage grows excessively
        for i in range(50):
            response = client.get("/health")
            assert response.status_code == 200

            # Basic check - should complete without memory errors
            if i % 10 == 0:
                print(f"Completed {i + 1} requests")

    def test_response_time_consistency(self):
        """Test response time consistency"""
        if not TEST_APP_AVAILABLE:
            pytest.skip("App not available for testing")

        client = TestClient(app)
        response_times = []

        # Collect response times
        for _ in range(20):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            assert response.status_code == 200
            response_times.append(end_time - start_time)

        # Check consistency
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        # Maximum response time shouldn't be more than 3x average
        assert (
            max_time < avg_time * 3
        ), f"Inconsistent response times: avg={avg_time:.3f}, max={max_time:.3f}"

        # No response should take more than 5 seconds
        assert max_time < 5.0, f"Response time too slow: {max_time:.3f}s"


class TestResourceLimits:
    """Test resource limit handling"""

    def test_large_request_handling(self):
        """Test handling of large requests"""
        if not TEST_APP_AVAILABLE:
            pytest.skip("App not available for testing")

        client = TestClient(app)

        # Test with large JSON payload
        large_data = {
            "title": "A" * 1000,  # Large title
            "description": "B" * 5000,  # Large description
            "destination": "Test City",
            "start_date": "2024-06-01",
            "end_date": "2024-06-10",
            "budget_total": 5000.0,
        }

        start_time = time.time()
        response = client.post("/api/trips", json=large_data)
        end_time = time.time()

        # Should handle large requests (either accept or reject gracefully)
        assert response.status_code in [201, 400, 413, 422]
        assert end_time - start_time < 10.0  # Should not hang

    def test_rapid_requests(self):
        """Test rapid successive requests"""
        if not TEST_APP_AVAILABLE:
            pytest.skip("App not available for testing")

        client = TestClient(app)

        # Rapid fire requests
        for i in range(30):
            response = client.get("/health")
            # Should handle rapid requests without crashing
            assert response.status_code in [
                200, 429, 503]  # Allow rate limiting


# Skip all tests if app is not available
if not TEST_APP_AVAILABLE:
    pytest.skip("Backend app not available", allow_module_level=True)
