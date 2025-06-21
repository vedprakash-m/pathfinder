from functools import lru_cache
import sys
import os

from app.core.container import Container

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from domain.trip import TripDomainService


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
