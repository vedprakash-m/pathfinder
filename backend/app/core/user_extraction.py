"""
Standard user extraction function implementing the VedUser interface.
This function MUST be used across all Vedprakash domain apps for consistency.
"""

import json
from typing import Any, Dict


def extract_standard_user(token_claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract standardized user object from Microsoft Entra ID token claims.
    Implements the exact VedUser interface specified in Apps_Auth_Requirement.md

    Args:
        token_claims: Decoded JWT token claims from Microsoft Entra ID

    Returns:
        Dict representing the standard VedUser object

    Raises:
        ValueError: If required claims are missing
    """
    # Validate required claims
    if not token_claims.get("sub") or not token_claims.get("email"):
        raise ValueError("Invalid token: missing required claims (sub, email)")

    # Extract permissions from roles claim or default
    permissions = []
    if "roles" in token_claims:
        # Map Entra ID roles to app-specific permissions
        role_to_permissions = {
            "FamilyAdmin": [
                "read:trips",
                "create:trips",
                "update:trips",
                "delete:trips",
                "read:families",
                "create:families",
                "update:families",
                "delete:families",
                "read:itineraries",
                "create:itineraries",
                "update:itineraries",
                "delete:itineraries",
            ],
            "FamilyMember": [
                "read:trips",
                "create:trips",
                "update:trips",
                "read:families",
                "update:families",
                "read:itineraries",
                "create:itineraries",
                "update:itineraries",
            ],
            "User": ["read:trips", "read:families", "read:itineraries"],
        }

        for role in token_claims["roles"]:
            permissions.extend(role_to_permissions.get(role, []))

        # Remove duplicates
        permissions = list(set(permissions))
    else:
        # Default permissions for authenticated users
        permissions = [
            "read:trips",
            "create:trips",
            "update:trips",
            "read:families",
            "create:families",
            "update:families",
            "read:itineraries",
            "create:itineraries",
            "update:itineraries",
        ]

    # Parse Vedprakash-specific profile data
    ved_preferences = {}
    if "ved_preferences" in token_claims:
        try:
            ved_preferences = (
                json.loads(token_claims["ved_preferences"])
                if isinstance(token_claims["ved_preferences"], str)
                else token_claims["ved_preferences"]
            )
        except (json.JSONDecodeError, TypeError):
            ved_preferences = {}

    apps_enrolled = token_claims.get("ved_apps_enrolled", [])
    if isinstance(apps_enrolled, str):
        apps_enrolled = [apps_enrolled]
    elif not isinstance(apps_enrolled, list):
        apps_enrolled = []

    # Ensure pathfinder is in enrolled apps
    if "pathfinder" not in apps_enrolled:
        apps_enrolled.append("pathfinder")

    return {
        "id": token_claims["sub"],
        "email": token_claims["email"],
        "name": token_claims.get("name")
        or token_claims.get("preferred_username")
        or token_claims["email"],
        "givenName": token_claims.get("given_name", ""),
        "familyName": token_claims.get("family_name", ""),
        "permissions": permissions,
        "vedProfile": {
            "profileId": token_claims.get("ved_profile_id") or token_claims["sub"],
            "subscriptionTier": token_claims.get("ved_subscription_tier", "free"),
            "appsEnrolled": apps_enrolled,
            "preferences": ved_preferences,
        },
    }
