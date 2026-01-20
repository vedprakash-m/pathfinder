"""
Families HTTP Functions

CRUD operations for family and member management.
"""
import logging
from datetime import UTC, datetime

import azure.functions as func

from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request
from models.schemas import (
    FamilyCreateRequest,
    FamilyResponse,
    FamilyUpdateRequest,
    InvitationRequest,
    UserResponse,
)
from services.family_service import get_family_service

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


async def require_auth(req: func.HttpRequest):
    """Helper to require authentication and return user."""
    user = await get_user_from_request(req)
    if not user:
        raise APIError(code=ErrorCode.AUTHENTICATION_ERROR, message="Authentication required")
    return user


@bp.route(route="families", methods=["GET"])
async def list_families(req: func.HttpRequest) -> func.HttpResponse:
    """
    List families the current user belongs to.
    """
    try:
        user = await require_auth(req)

        service = get_family_service()
        families = await service.get_user_families(user.id)

        family_responses = [FamilyResponse.from_document(f) for f in families]

        return success_response({"items": [f.model_dump() for f in family_responses], "total": len(families)})

    except APIError as e:
        return error_response(e, status_code=401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400)
    except Exception:
        logger.exception("Error listing families")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to list families"), status_code=500
        )


@bp.route(route="families", methods=["POST"])
async def create_family(req: func.HttpRequest) -> func.HttpResponse:
    """
    Create a new family.

    Body: FamilyCreateRequest
    """
    try:
        user = await require_auth(req)

        body = req.get_json()
        family_data = FamilyCreateRequest(**body)

        service = get_family_service()
        family = await service.create_family(name=family_data.name, creator_id=user.id)

        family_response = FamilyResponse.from_document(family)
        return success_response(family_response.model_dump(), status_code=201)

    except APIError as e:
        return error_response(e, status_code=401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400)
    except Exception:
        logger.exception("Error creating family")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to create family"), status_code=500
        )


@bp.route(route="families/{family_id}", methods=["GET"])
async def get_family(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get a specific family by ID.
    """
    try:
        user = await require_auth(req)
        family_id = req.route_params.get("family_id")

        if not family_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Family ID is required"), status_code=400
            )

        service = get_family_service()
        family = await service.get_family(family_id)

        if not family:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Family not found"), status_code=404)

        # Check if user is a member
        if user.id not in family.member_user_ids:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        family_response = FamilyResponse.from_document(family)
        return success_response(family_response.model_dump())

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting family")
        return error_response(APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get family"), status_code=500)


@bp.route(route="families/{family_id}", methods=["PUT", "PATCH"])
async def update_family(req: func.HttpRequest) -> func.HttpResponse:
    """
    Update a family.

    Only the admin can update family details.
    """
    try:
        user = await require_auth(req)
        family_id = req.route_params.get("family_id")

        if not family_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Family ID is required"), status_code=400
            )

        body = req.get_json()
        update_data = FamilyUpdateRequest(**body)

        service = get_family_service()
        family = await service.get_family(family_id)

        if not family:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Family not found"), status_code=404)

        # Check admin access
        if family.admin_user_id != user.id:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Only the admin can update the family"),
                status_code=403,
            )

        # Apply updates
        update_fields = update_data.model_dump(exclude_unset=True)
        updated_family = await service.update_family(family_id, **update_fields)

        if not updated_family:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to update family"), status_code=500
            )

        family_response = FamilyResponse.from_document(updated_family)
        return success_response(family_response.model_dump())

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error updating family")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to update family"), status_code=500
        )


@bp.route(route="families/{family_id}/members", methods=["GET"])
async def get_family_members(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get all members of a family.
    """
    try:
        user = await require_auth(req)
        family_id = req.route_params.get("family_id")

        if not family_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Family ID is required"), status_code=400
            )

        service = get_family_service()
        family = await service.get_family(family_id)

        if not family:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Family not found"), status_code=404)

        # Check membership
        if user.id not in family.member_user_ids:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Access denied"), status_code=403
            )

        members = await service.get_family_members(family_id)
        member_responses = [UserResponse.from_document(m) for m in members]

        return success_response(
            {
                "items": [m.model_dump() for m in member_responses],
                "total": len(members),
                "admin_id": family.admin_user_id,
            }
        )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error getting family members")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get family members"), status_code=500
        )


@bp.route(route="families/{family_id}/invite", methods=["POST"])
async def invite_member(req: func.HttpRequest) -> func.HttpResponse:
    """
    Invite a new member to the family.

    Body: InvitationRequest
    """
    try:
        user = await require_auth(req)
        family_id = req.route_params.get("family_id")

        if not family_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Family ID is required"), status_code=400
            )

        body = req.get_json()
        invite_data = InvitationRequest(**body)

        service = get_family_service()
        family = await service.get_family(family_id)

        if not family:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Family not found"), status_code=404)

        # Check if user can invite (must be member)
        if user.id not in family.member_user_ids:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Only members can invite others"), status_code=403
            )

        invitation = await service.invite_member(family_id=family_id, email=invite_data.email, inviter_id=user.id)

        if not invitation:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to create invitation"), status_code=500
            )

        # Send notification (if user exists)
        # This would typically be done via email service for new users

        return success_response(
            {
                "invitation_id": invitation.id,
                "email": invitation.email,
                "status": invitation.status,
                "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
            },
            status_code=201,
        )

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error inviting member")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to send invitation"), status_code=500
        )


@bp.route(route="invitations/{invitation_id}/accept", methods=["POST"])
async def accept_invitation(req: func.HttpRequest) -> func.HttpResponse:
    """
    Accept a family invitation.
    """
    try:
        user = await require_auth(req)
        invitation_id = req.route_params.get("invitation_id")

        if not invitation_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Invitation ID is required"), status_code=400
            )

        service = get_family_service()
        family = await service.accept_invitation(invitation_id=invitation_id, user_id=user.id)

        if not family:
            return error_response(
                APIError(code=ErrorCode.NOT_FOUND, message="Invitation not found or expired"), status_code=404
            )

        family_response = FamilyResponse.from_document(family)
        return success_response({"message": "Invitation accepted", "family": family_response.model_dump()})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error accepting invitation")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to accept invitation"), status_code=500
        )


@bp.route(route="invitations/{invitation_id}/decline", methods=["POST"])
async def decline_invitation(req: func.HttpRequest) -> func.HttpResponse:
    """
    Decline a family invitation.
    """
    try:
        user = await require_auth(req)
        invitation_id = req.route_params.get("invitation_id")

        if not invitation_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Invitation ID is required"), status_code=400
            )

        service = get_family_service()
        success = await service.decline_invitation(invitation_id=invitation_id, user_id=user.id)

        if not success:
            return error_response(
                APIError(code=ErrorCode.NOT_FOUND, message="Invitation not found or already processed"), status_code=404
            )

        return success_response({"message": "Invitation declined"})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error declining invitation")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to decline invitation"), status_code=500
        )


@bp.route(route="families/{family_id}/members/{member_id}", methods=["DELETE"])
async def remove_member(req: func.HttpRequest) -> func.HttpResponse:
    """
    Remove a member from the family.

    Admin can remove any member. Members can remove themselves.
    """
    try:
        user = await require_auth(req)
        family_id = req.route_params.get("family_id")
        member_id = req.route_params.get("member_id")

        if not family_id or not member_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Family ID and Member ID are required"),
                status_code=400,
            )

        service = get_family_service()
        family = await service.get_family(family_id)

        if not family:
            return error_response(APIError(code=ErrorCode.NOT_FOUND, message="Family not found"), status_code=404)

        # Check permissions: admin can remove anyone, members can remove themselves
        is_admin = family.admin_user_id == user.id
        is_self = member_id == user.id

        if not is_admin and not is_self:
            return error_response(
                APIError(code=ErrorCode.AUTHORIZATION_ERROR, message="Cannot remove other members"), status_code=403
            )

        # Cannot remove admin
        if member_id == family.admin_user_id:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Cannot remove the family admin"), status_code=400
            )

        success = await service.remove_member(family_id, member_id)

        if not success:
            return error_response(
                APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to remove member"), status_code=500
            )

        return success_response({"message": "Member removed successfully"})

    except APIError as e:
        status = 401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400
        return error_response(e, status_code=status)
    except Exception:
        logger.exception("Error removing member")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to remove member"), status_code=500
        )


@bp.route(route="invitations", methods=["GET"])
async def get_pending_invitations(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get pending invitations for the current user.
    """
    try:
        user = await require_auth(req)

        service = get_family_service()
        invitations = await service.get_user_invitations(user.id)

        return success_response(
            {
                "items": [
                    {
                        "id": inv.id,
                        "family_id": inv.family_id,
                        "email": inv.email,
                        "status": inv.status,
                        "created_at": inv.created_at.isoformat(),
                        "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
                    }
                    for inv in invitations
                ],
                "total": len(invitations),
            }
        )

    except APIError as e:
        return error_response(e, status_code=401 if e.code == ErrorCode.AUTHENTICATION_ERROR else 400)
    except Exception:
        logger.exception("Error getting invitations")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get invitations"), status_code=500
        )
