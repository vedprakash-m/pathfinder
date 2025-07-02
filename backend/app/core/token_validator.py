"""
Production-ready JWT token validation with proper JWKS verification and monitoring.
Implements all security requirements from Apps_Auth_Requirement.md
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
import jwt
from app.core.auth_errors import AuthServiceUnavailableError, TokenInvalidError
from app.core.config import get_settings
from app.core.user_extraction import extract_standard_user

logger = logging.getLogger(__name__)
settings = get_settings()


class ProductionTokenValidator:
    """Production-ready token validator with JWKS caching and monitoring."""

    def __init__(self):
        self._jwks_cache: Dict[str, Any] = {}
        self._jwks_cache_expiry: Optional[datetime] = None
        self._validation_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    async def get_jwks(self) -> Dict[str, Any]:
        """
        Get JWKS with proper caching and error handling.
        Implements mandatory JWKS caching per requirements.
        """
        try:
            # Check cache first (required by security standards)
            if (
                self._jwks_cache_expiry
                and datetime.utcnow() < self._jwks_cache_expiry
                and self._jwks_cache
            ):
                self._validation_metrics["cache_hits"] += 1
                return self._jwks_cache

            self._validation_metrics["cache_misses"] += 1

            # Use standard Vedprakash domain tenant
            jwks_url = "https://login.microsoftonline.com/vedid.onmicrosoft.com/discovery/v2.0/keys"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()

                jwks_data = response.json()

                # Cache for 1 hour per requirements
                self._jwks_cache = jwks_data
                self._jwks_cache_expiry = datetime.utcnow() + timedelta(hours=1)

                logger.info(f"JWKS refreshed with {len(jwks_data.get('keys', []))} keys")
                return jwks_data

        except Exception as e:
            logger.error(f"Failed to retrieve JWKS: {e}")
            raise AuthServiceUnavailableError({"reason": f"JWKS retrieval failed: {str(e)}"})

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token with proper signature verification.
        Implements all mandatory security checks per requirements.
        """
        start_time = time.time()
        self._validation_metrics["total_validations"] += 1

        try:
            # Get JWKS for signature verification
            jwks = await self.get_jwks()

            # Get the key ID from token header
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise TokenInvalidError({"reason": "Token missing key ID"})

            # Find the matching public key
            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key.get("use", "sig"),
                        "n": key["n"],
                        "e": key["e"],
                    }
                    break

            if not rsa_key:
                raise TokenInvalidError({"reason": f"No matching key found for kid: {kid}"})

            # ✅ REQUIRED: Proper signature verification with all security checks
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.ENTRA_EXTERNAL_CLIENT_ID,  # Validate audience
                issuer="https://login.microsoftonline.com/vedid.onmicrosoft.com/v2.0",  # Validate issuer
                options={
                    "verify_signature": True,  # ✅ Required: Verify signature
                    "verify_exp": True,  # ✅ Required: Verify expiration
                    "verify_aud": True,  # ✅ Required: Verify audience
                    "verify_iss": True,  # ✅ Required: Verify issuer
                },
            )

            # Extract standardized user object
            user_data = extract_standard_user(payload)

            # Log successful validation for monitoring
            duration = time.time() - start_time
            self._validation_metrics["successful_validations"] += 1

            logger.info(
                "Token validation successful",
                extra={
                    "user_id": user_data["id"],
                    "duration_ms": round(duration * 1000, 2),
                    "permissions_count": len(user_data["permissions"]),
                },
            )

            return user_data

        except jwt.ExpiredSignatureError:
            self._validation_metrics["failed_validations"] += 1
            logger.warning("Token validation failed: Token expired")
            raise TokenInvalidError({"reason": "Token has expired"})

        except jwt.InvalidAudienceError:
            self._validation_metrics["failed_validations"] += 1
            logger.warning("Token validation failed: Invalid audience")
            raise TokenInvalidError({"reason": "Token audience mismatch"})

        except jwt.InvalidIssuerError:
            self._validation_metrics["failed_validations"] += 1
            logger.warning("Token validation failed: Invalid issuer")
            raise TokenInvalidError({"reason": "Token issuer mismatch"})

        except jwt.InvalidTokenError as e:
            self._validation_metrics["failed_validations"] += 1
            logger.warning(f"Token validation failed: {str(e)}")
            raise TokenInvalidError({"reason": str(e)})

        except Exception as e:
            self._validation_metrics["failed_validations"] += 1
            logger.error(f"Unexpected token validation error: {e}", exc_info=True)
            raise TokenInvalidError({"reason": "Token validation failed"})

    def get_metrics(self) -> Dict[str, Any]:
        """Get authentication metrics for monitoring."""
        success_rate = (
            self._validation_metrics["successful_validations"]
            / max(self._validation_metrics["total_validations"], 1)
            * 100
        )

        cache_hit_rate = (
            self._validation_metrics["cache_hits"]
            / max(
                self._validation_metrics["cache_hits"] + self._validation_metrics["cache_misses"], 1
            )
            * 100
        )

        return {
            **self._validation_metrics,
            "success_rate_percent": round(success_rate, 2),
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "jwks_cache_status": (
                "valid"
                if self._jwks_cache_expiry and datetime.utcnow() < self._jwks_cache_expiry
                else "expired"
            ),
        }


# Global instance
token_validator = ProductionTokenValidator()
