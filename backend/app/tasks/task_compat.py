"""
Task compatibility module for Redis-free task execution.
Provides decorators that work with or without Celery.
"""

import asyncio
import functools
from typing import Callable, Optional

from app.core.celery_app import celery_app
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def conditional_task(
    bind: bool = True, name: Optional[str] = None, max_retries: int = 3
):
    """
    Decorator that creates tasks compatible with both Celery and Redis-free modes.

    In Celery mode: Uses celery_app.task decorator
    In Redis-free mode: Returns a simple wrapper function
    """

    def decorator(func: Callable) -> Callable:
        if celery_app is not None:
            # Celery is available - use normal Celery task
            return celery_app.task(bind=bind, name=name, max_retries=max_retries)(func)
        else:
            # Redis-free mode - return a simple wrapper
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    logger.debug(
                        f"Executing task {name or func.__name__} in Redis-free mode"
                    )

                    # Handle bound tasks (first arg is 'self')
                    if bind and args:
                        # Create a mock self object with basic retry functionality
                        mock_self = MockTaskContext(name or func.__name__, max_retries)
                        return func(mock_self, *args[1:], **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    logger.error(
                        f"Task {name or func.__name__} failed in Redis-free mode: {e}"
                    )
                    raise

            # Add task-like attributes for compatibility
            wrapper.delay = lambda *args, **kwargs: wrapper(*args, **kwargs)
            wrapper.apply_async = lambda *args, **kwargs: wrapper(*args, **kwargs)
            wrapper.__name__ = func.__name__

            return wrapper

    return decorator


class MockTaskContext:
    """
    Mock context object for tasks in Redis-free mode.
    Provides basic retry functionality without Celery.
    """

    def __init__(self, task_name: str, max_retries: int = 3):
        self.task_name = task_name
        self.max_retries = max_retries
        self.request = MockRequest()

    def retry(
        self, exc: Exception, countdown: int = 60, max_retries: Optional[int] = None
    ):
        """
        Mock retry functionality for Redis-free mode.
        In production, this would be handled by a proper task queue.
        """
        max_retries = max_retries or self.max_retries
        current_retries = getattr(self.request, "retries", 0)

        if current_retries < max_retries:
            logger.warning(
                f"Task {self.task_name} retry {current_retries + 1}/{max_retries} "
                f"after {countdown}s delay. Error: {exc}"
            )
            # In a real implementation, this would schedule a retry
            # For now, just increment retry count and re-raise
            self.request.retries = current_retries + 1
            raise exc
        else:
            logger.error(
                f"Task {self.task_name} exhausted retries ({max_retries}). Giving up."
            )
            raise exc


class MockRequest:
    """Mock request object for task context."""

    def __init__(self):
        self.retries = 0


def run_async_task(coro):
    """
    Helper to run async functions in task context.
    Handles both Celery and Redis-free modes.
    """
    if celery_app is not None:
        # Use Celery's run_async helper
        from app.core.celery_app import run_async

        return run_async(coro)
    else:
        # Direct asyncio execution for Redis-free mode
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, this won't work
                # Create a new event loop in a thread
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop in current thread, create new one
            return asyncio.run(coro)


# Convenience function for task registration in Redis-free mode
def register_redis_free_task(name: str, func: Callable):
    """
    Register a task function for Redis-free execution.
    In production, this would integrate with SQLite task queue.
    """
    logger.info(f"Registered Redis-free task: {name}")
    # This is where we'd integrate with the SQLite task queue
    # For now, just log the registration


# Export the main decorator
task = conditional_task
