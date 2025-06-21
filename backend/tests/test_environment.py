"""
Test to check environment settings during test runs.
"""


def test_environment_check():
    """Check what environment settings we have during tests."""
    from app.core.config import get_settings

    settings = get_settings()

    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Is testing: {settings.is_testing}")
    print(f"CSRF enabled: {settings.ENVIRONMENT not in ['testing', 'test']}")

    # Just check that we can identify the environment
    assert settings.ENVIRONMENT is not None
