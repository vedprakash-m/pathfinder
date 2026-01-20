"""
Collaboration Service

Business logic for polls, voting, and consensus building.
"""
import logging
from datetime import UTC, datetime
from typing import Any, Optional

from models.documents import PollDocument, UserDocument
from models.schemas import PollCreate, PollVote
from repositories.cosmos_repository import cosmos_repo

logger = logging.getLogger(__name__)


class CollaborationService:
    """Service for polls, voting, and consensus operations."""

    async def create_poll(self, data: PollCreate, user: UserDocument) -> PollDocument:
        """
        Create a new poll for a trip.

        Args:
            data: Poll creation data
            user: Authenticated user creating the poll

        Returns:
            Created poll document
        """
        # Convert options to dict format
        options = [
            {"id": opt.id, "text": opt.text, "description": opt.description, "metadata": opt.metadata, "vote_count": 0}
            for opt in data.options
        ]

        poll = PollDocument(
            pk=f"poll_{data.trip_id}",
            trip_id=data.trip_id,
            creator_id=user.id,
            title=data.title,
            description=data.description,
            poll_type=data.poll_type,
            options=options,
            expires_at=data.expires_at,
            status="active",
        )

        created = await cosmos_repo.create(poll)
        logger.info(f"Created poll '{created.title}' for trip {data.trip_id}")

        return created

    async def get_poll(self, poll_id: str) -> Optional[PollDocument]:
        """
        Get a poll by ID.

        Args:
            poll_id: Poll ID

        Returns:
            Poll document if found
        """
        query = "SELECT * FROM c WHERE c.entity_type = 'poll' AND c.id = @pollId"
        polls = await cosmos_repo.query(
            query=query, parameters=[{"name": "@pollId", "value": poll_id}], model_class=PollDocument, max_items=1
        )

        return polls[0] if polls else None

    async def get_trip_polls(self, trip_id: str, status: Optional[str] = None, limit: int = 50) -> list[PollDocument]:
        """
        Get all polls for a trip.

        Args:
            trip_id: Trip ID
            status: Optional status filter
            limit: Maximum polls to return

        Returns:
            List of poll documents
        """
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'poll'
            AND c.trip_id = @tripId
        """
        params = [{"name": "@tripId", "value": trip_id}]

        if status:
            query += " AND c.status = @status"
            params.append({"name": "@status", "value": status})

        query += " ORDER BY c.created_at DESC"

        return await cosmos_repo.query(query=query, parameters=params, model_class=PollDocument, max_items=limit)

    async def vote_on_poll(self, poll_id: str, vote: PollVote, user: UserDocument) -> Optional[PollDocument]:
        """
        Cast a vote on a poll.

        Args:
            poll_id: Poll ID
            vote: Vote data
            user: Authenticated user voting

        Returns:
            Updated poll or None
        """
        poll = await self.get_poll(poll_id)

        if not poll:
            return None

        # Check if poll is active
        if poll.status != "active":
            logger.warning(f"Cannot vote on inactive poll {poll_id}")
            return None

        # Check if poll expired
        if poll.expires_at and poll.expires_at < datetime.now(UTC):
            poll.status = "expired"
            await cosmos_repo.update(poll)
            return None

        # Validate option IDs
        valid_option_ids = {opt["id"] for opt in poll.options}
        for option_id in vote.option_ids:
            if option_id not in valid_option_ids:
                logger.warning(f"Invalid option ID: {option_id}")
                return None

        # Check poll type constraints
        if poll.poll_type == "single_choice" and len(vote.option_ids) > 1:
            logger.warning("Single choice poll allows only one vote")
            return None

        # Remove previous vote if exists
        if user.id in poll.votes:
            old_vote = poll.votes[user.id]
            for option_id in old_vote.get("option_ids", []):
                for opt in poll.options:
                    if opt["id"] == option_id:
                        opt["vote_count"] = max(0, opt.get("vote_count", 1) - 1)

        # Record new vote
        poll.votes[user.id] = {
            "option_ids": vote.option_ids,
            "comment": vote.comment,
            "voted_at": datetime.now(UTC).isoformat(),
        }

        # Update vote counts
        for option_id in vote.option_ids:
            for opt in poll.options:
                if opt["id"] == option_id:
                    opt["vote_count"] = opt.get("vote_count", 0) + 1

        updated = await cosmos_repo.update(poll)
        logger.info(f"User {user.id} voted on poll {poll_id}")

        return updated

    async def close_poll(self, poll_id: str, user: UserDocument) -> Optional[PollDocument]:
        """
        Close a poll and calculate results.

        Args:
            poll_id: Poll ID
            user: Authenticated user (must be creator)

        Returns:
            Closed poll with results
        """
        poll = await self.get_poll(poll_id)

        if not poll:
            return None

        if poll.creator_id != user.id:
            logger.warning(f"User {user.id} cannot close poll {poll_id}")
            return None

        # Calculate results
        poll.status = "closed"
        poll.result = self._calculate_results(poll)

        updated = await cosmos_repo.update(poll)
        logger.info(f"Closed poll {poll_id}")

        return updated

    async def delete_poll(self, poll_id: str, user: UserDocument) -> bool:
        """
        Delete a poll.

        Args:
            poll_id: Poll ID
            user: Authenticated user (must be creator)

        Returns:
            True if deleted
        """
        poll = await self.get_poll(poll_id)

        if not poll:
            return False

        if poll.creator_id != user.id:
            return False

        return await cosmos_repo.delete(poll_id, poll.pk)

    def _calculate_results(self, poll: PollDocument) -> dict[str, Any]:
        """Calculate poll results."""
        total_votes = len(poll.votes)

        # Find winning option(s)
        max_votes = 0
        winners = []

        for opt in poll.options:
            vote_count = opt.get("vote_count", 0)
            if vote_count > max_votes:
                max_votes = vote_count
                winners = [opt]
            elif vote_count == max_votes and vote_count > 0:
                winners.append(opt)

        return {
            "total_votes": total_votes,
            "winners": winners,
            "is_tie": len(winners) > 1,
            "calculated_at": datetime.now(UTC).isoformat(),
        }

    async def get_consensus_status(self, trip_id: str) -> dict[str, Any]:
        """
        Get overall consensus status for a trip.

        Args:
            trip_id: Trip ID

        Returns:
            Consensus summary
        """
        polls = await self.get_trip_polls(trip_id)

        active_polls = [p for p in polls if p.status == "active"]
        closed_polls = [p for p in polls if p.status == "closed"]

        # Calculate participation rate
        all_voters = set()
        for poll in polls:
            all_voters.update(poll.votes.keys())

        return {
            "trip_id": trip_id,
            "total_polls": len(polls),
            "active_polls": len(active_polls),
            "closed_polls": len(closed_polls),
            "unique_voters": len(all_voters),
            "consensus_reached": all(p.result and not p.result.get("is_tie", True) for p in closed_polls)
            if closed_polls
            else False,
        }
