from functools import lru_cache

from app.core.container import Container
from backend.domain.trip import TripDomainService


@lru_cache(maxsize=1)
def _get_container() -> Container:  # pragma: no cover
    container = Container()
    container.init_resources()
    return container


async def get_trip_service() -> TripDomainService:  # pragma: no cover
    """Return repository-backed TripDomainService for use in tasks."""
    # Running inside event loop in Celery task context; ensure non-blocking
    container = _get_container()
    return container.trip_domain_service()  # type: ignore[return-value]
