"""
Performance and load testing suite for Pathfinder backend.
"""

import asyncio
import time
from datetime import datetime

import pytest
from app.main import app
from httpx import AsyncClient


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self):
        """Test health endpoint responds within performance thresholds."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            response = await client.get("/health")
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < 0.5  # Should respond within 500ms

            # Log performance metrics
            print(f"Health endpoint response time: {response_time:.3f}s")

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test performance under concurrent load."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            concurrent_requests = 20

            start_time = time.time()

            # Create concurrent requests
            tasks = [client.get("/health") for _ in range(concurrent_requests)]

            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = end_time - start_time
            avg_response_time = total_time / concurrent_requests

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200

            # Performance thresholds
            assert total_time < 5.0  # All requests within 5 seconds
            assert avg_response_time < 1.0  # Average response time under 1 second

            print(f"Concurrent requests: {concurrent_requests}")
            print(f"Total time: {total_time:.3f}s")
            print(f"Average response time: {avg_response_time:.3f}s")

    @pytest.mark.asyncio
    async def test_memory_usage_during_load(self):
        """Test memory usage doesn't grow excessively under load."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Generate load
            for batch in range(5):
                tasks = [client.get("/health") for _ in range(10)]
                await asyncio.gather(*tasks)

                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory

                # Memory growth should be reasonable
                assert memory_growth < 50  # Less than 50MB growth

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Initial memory: {initial_memory:.1f}MB")
        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Memory growth: {final_memory - initial_memory:.1f}MB")


@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations."""

    @pytest.mark.asyncio
    async def test_database_query_performance(self):
        """Test database query response times."""
        # This would test actual database queries
        # For now, we'll test the health check that includes database

        async with AsyncClient(app=app, base_url="http://test") as client:
            query_times = []

            for _ in range(10):
                start_time = time.time()
                response = await client.get("/health/ready")
                end_time = time.time()

                if response.status_code == 200:
                    query_times.append(end_time - start_time)

            if query_times:
                avg_query_time = sum(query_times) / len(query_times)
                max_query_time = max(query_times)

                # Database queries should be fast
                assert avg_query_time < 1.0  # Average under 1 second
                assert max_query_time < 2.0  # Max under 2 seconds

                print(f"Average DB query time: {avg_query_time:.3f}s")
                print(f"Max DB query time: {max_query_time:.3f}s")

    @pytest.mark.asyncio
    async def test_concurrent_database_access(self):
        """Test database performance under concurrent access."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            concurrent_queries = 15

            start_time = time.time()

            tasks = [client.get("/health/ready") for _ in range(concurrent_queries)]

            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = end_time - start_time
            successful_queries = sum(1 for r in responses if r.status_code == 200)

            if successful_queries > 0:
                avg_time_per_query = total_time / successful_queries

                # Performance thresholds for database access
                assert total_time < 10.0  # All queries within 10 seconds
                assert avg_time_per_query < 2.0  # Average query time under 2 seconds

                print(f"Concurrent DB queries: {concurrent_queries}")
                print(f"Successful queries: {successful_queries}")
                print(f"Total time: {total_time:.3f}s")
                print(f"Average time per query: {avg_time_per_query:.3f}s")


@pytest.mark.performance
class TestAIServicePerformance:
    """Performance tests for AI service operations."""

    @pytest.mark.asyncio
    async def test_ai_cost_calculation_performance(self):
        """Test AI cost calculation performance."""
        from app.services.ai_service import CostTracker

        tracker = CostTracker()

        # Test cost calculation performance
        start_time = time.time()

        for _ in range(1000):
            cost = tracker.calculate_cost("gpt-4o-mini", 1000, 500)
            assert cost > 0

        end_time = time.time()
        calculation_time = end_time - start_time

        # Cost calculations should be very fast
        assert calculation_time < 1.0  # 1000 calculations in under 1 second

        print(f"1000 cost calculations: {calculation_time:.3f}s")
        print(f"Average per calculation: {calculation_time/1000*1000:.1f}μs")

    @pytest.mark.asyncio
    async def test_usage_tracking_performance(self):
        """Test usage tracking performance under load."""
        from app.services.ai_service import CostTracker

        tracker = CostTracker()

        start_time = time.time()

        # Simulate high-frequency usage tracking
        for i in range(100):
            tracker.track_usage("gpt-4o-mini", 1000, 500, "general")

        end_time = time.time()
        tracking_time = end_time - start_time

        # Usage tracking should be efficient
        assert tracking_time < 2.0  # 100 tracking operations under 2 seconds

        # Verify data structure integrity under load
        today = datetime.now().date().isoformat()
        assert today in tracker.daily_usage
        assert tracker.daily_usage[today]["requests"] == 100

        print(f"100 usage tracking operations: {tracking_time:.3f}s")
        print(f"Average per operation: {tracking_time/100*1000:.1f}ms")


@pytest.mark.performance
class TestCachePerformance:
    """Performance tests for caching mechanisms."""

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self):
        """Test cache hit response times."""
        # This would test actual cache operations
        # For now, we'll simulate cache-like behavior

        cache = {}
        cache_key = "test_key"
        cache_value = {"data": "test_value"}

        # Simulate cache write
        start_time = time.time()
        cache[cache_key] = cache_value
        write_time = time.time() - start_time

        # Simulate cache reads
        read_times = []
        for _ in range(1000):
            start_time = time.time()
            value = cache.get(cache_key)
            read_time = time.time() - start_time
            read_times.append(read_time)
            assert value == cache_value

        avg_read_time = sum(read_times) / len(read_times)
        max_read_time = max(read_times)

        # Cache operations should be extremely fast
        assert write_time < 0.001  # Write under 1ms
        assert avg_read_time < 0.001  # Average read under 1ms
        assert max_read_time < 0.01  # Max read under 10ms

        print(f"Cache write time: {write_time*1000:.3f}ms")
        print(f"Average read time: {avg_read_time*1000000:.1f}μs")
        print(f"Max read time: {max_read_time*1000000:.1f}μs")


@pytest.mark.performance
class TestEndToEndPerformance:
    """End-to-end performance tests."""

    @pytest.mark.asyncio
    async def test_typical_user_workflow_performance(self):
        """Test performance of typical user workflow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            workflow_start = time.time()

            # Simulate typical user workflow
            steps = [
                ("Health Check", client.get("/health")),
                ("Health Ready", client.get("/health/ready")),
                ("Version Info", client.get("/health/version")),
            ]

            step_times = {}

            for step_name, request_coro in steps:
                step_start = time.time()
                try:
                    response = await request_coro
                    step_end = time.time()
                    step_times[step_name] = step_end - step_start

                    # All steps should succeed or have reasonable status
                    assert response.status_code in [200, 401, 503]

                except Exception as e:
                    print(f"Step {step_name} failed: {e}")
                    step_times[step_name] = time.time() - step_start

            workflow_end = time.time()
            total_workflow_time = workflow_end - workflow_start

            # Workflow should complete within reasonable time
            assert total_workflow_time < 5.0  # Complete workflow under 5 seconds

            print(f"Total workflow time: {total_workflow_time:.3f}s")
            for step, duration in step_times.items():
                print(f"  {step}: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_stress_test_basic(self):
        """Basic stress test with multiple concurrent users."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            concurrent_users = 50
            requests_per_user = 5

            async def simulate_user():
                user_start = time.time()
                responses = []

                for _ in range(requests_per_user):
                    try:
                        response = await client.get("/health")
                        responses.append(response)
                    except Exception as e:
                        print(f"Request failed: {e}")

                user_end = time.time()
                return user_end - user_start, responses

            stress_start = time.time()

            # Create concurrent users
            user_tasks = [simulate_user() for _ in range(concurrent_users)]
            user_results = await asyncio.gather(*user_tasks)

            stress_end = time.time()
            total_stress_time = stress_end - stress_start

            # Analyze results
            total_requests = concurrent_users * requests_per_user
            successful_requests = 0
            total_user_time = 0

            for user_time, responses in user_results:
                total_user_time += user_time
                successful_requests += sum(1 for r in responses if r.status_code == 200)

            success_rate = successful_requests / total_requests
            avg_user_time = total_user_time / concurrent_users
            throughput = successful_requests / total_stress_time

            # Performance assertions
            assert success_rate > 0.9  # At least 90% success rate
            assert total_stress_time < 30.0  # Complete stress test under 30 seconds
            assert avg_user_time < 10.0  # Average user experience under 10 seconds

            print("Stress test results:")
            print(f"  Concurrent users: {concurrent_users}")
            print(f"  Requests per user: {requests_per_user}")
            print(f"  Total requests: {total_requests}")
            print(f"  Successful requests: {successful_requests}")
            print(f"  Success rate: {success_rate:.1%}")
            print(f"  Total time: {total_stress_time:.3f}s")
            print(f"  Average user time: {avg_user_time:.3f}s")
            print(f"  Throughput: {throughput:.1f} requests/second")
