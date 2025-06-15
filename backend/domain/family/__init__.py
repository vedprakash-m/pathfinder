from __future__ import annotations

"""Family bounded-context – domain layer stubs.

This package starts the extraction of family-related business rules out of the
legacy services.  For now we expose an empty `FamilyDomainService` so upper
layers can be wired without immediate implementation.
"""

from dataclasses import dataclass


@dataclass
class FamilyDomainService:  # pragma: no cover – stub
    """Placeholder for family domain logic to be implemented in upcoming sprints."""
    pass 