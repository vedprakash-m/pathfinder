"""
AI-related background tasks for itinerary generation and processing.
Redis-free version using SQLite task queue.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.core.config import get_settings
from app.core.database import get_db
from app.services.ai_service import AIService
from app.services.trip_service import TripService
from app.core.logging_config import get_logger
from app.core.cache_alternatives import task_queue

logger = get_logger(__name__)
settings = get_settings()


def generate_itinerary_async(trip_id: str, preferences: Dict[str, Any], user_id: str):
    """
    Generate trip itinerary asynchronously using SQLite task queue.
    
    Args:
        trip_id: UUID of the trip
        preferences: Trip preferences and requirements
        user_id: User requesting the generation
    """
    try:
        logger.info(f"Starting async itinerary generation for trip {trip_id}")
        # Add to task queue for processing
        task_id = task_queue.add_task(
            "generate_itinerary",
            {"trip_id": trip_id, "preferences": preferences, "user_id": user_id}
        )
        logger.info(f"Queued itinerary generation task {task_id} for trip {trip_id}")
        return {"task_id": task_id, "status": "queued"}
    except Exception as exc:
        logger.error(f"Failed to queue itinerary generation for trip {trip_id}: {exc}")
        raise exc


async def _generate_itinerary_async(trip_id: str, preferences: Dict[str, Any], user_id: str):
    """Internal async function for itinerary generation."""
    async for db in get_db():
        try:
            # Initialize services
            ai_service = AIService()
            trip_service = TripService(db)
            
            # Get trip details
            trip = await trip_service.get_trip_by_id(trip_id, user_id)
            if not trip:
                raise ValueError(f"Trip {trip_id} not found")
            
            # Extract trip information
            destination = trip.destination
            duration_days = (trip.end_date - trip.start_date).days
            
            # Get families and their data
            families_data = []
            for participation in trip.participations:
                family = participation.family
                family_data = {
                    "name": family.name,
                    "members": []
                }
                
                for member in family.members:
                    if member.is_active:
                        member_data = {
                            "age": member.age,
                            "dietary_restrictions": json.loads(member.dietary_restrictions or "[]"),
                            "accessibility_needs": json.loads(member.accessibility_needs or "[]")
                        }
                        family_data["members"].append(member_data)
                
                families_data.append(family_data)
            
            # Generate itinerary using AI service
            logger.info(f"Starting AI itinerary generation for trip {trip_id}")
            itinerary = await ai_service.generate_itinerary(
                destination=destination,
                duration_days=duration_days,
                families_data=families_data,
                preferences=preferences
            )
            
            # Save itinerary to Cosmos DB
            if settings.COSMOS_DB_ENABLED:
                from app.core.cosmos_db import CosmosOperations
                cosmos_ops = CosmosOperations()
                await cosmos_ops.save_itinerary(trip_id, itinerary)
            
            # Update trip status
            await trip_service.update_trip_status(trip_id, "itinerary_ready", user_id)
            
            # Notify participants via WebSocket (if available)
            try:
                from app.api.websocket import websocket_manager
                await websocket_manager.broadcast_to_trip(trip_id, {
                    "type": "itinerary_generated",
                    "trip_id": trip_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "Your trip itinerary has been generated!"
                })
            except ImportError:
                logger.info("WebSocket manager not available - skipping notification")
            
            logger.info(f"Itinerary generation completed for trip {trip_id}")
            return {"status": "success", "trip_id": trip_id, "itinerary_id": itinerary.get("id")}
            
        except Exception as e:
            logger.error(f"Error in itinerary generation: {e}")
            
            # Notify of failure (if available)
            try:
                from app.api.websocket import websocket_manager
                await websocket_manager.broadcast_to_trip(trip_id, {
                    "type": "itinerary_generation_failed",
                    "trip_id": trip_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "Failed to generate itinerary. Please try again."
                })
            except ImportError:
                logger.info("WebSocket manager not available - skipping failure notification")
            
            raise e


def optimize_itinerary_async(trip_id: str, optimization_type: str, user_id: str):
    """
    Optimize existing itinerary based on new constraints or preferences.
    """
    try:
        task_id = task_queue.add_task(
            "optimize_itinerary",
            {"trip_id": trip_id, "optimization_type": optimization_type, "user_id": user_id}
        )
        logger.info(f"Queued itinerary optimization task {task_id} for trip {trip_id}")
        return {"task_id": task_id, "status": "queued"}
    except Exception as exc:
        logger.error(f"Failed to queue itinerary optimization for trip {trip_id}: {exc}")
        raise exc


async def _optimize_itinerary_async(trip_id: str, optimization_type: str, user_id: str):
    """Internal async function for itinerary optimization."""
    async for db in get_db():
        try:
            ai_service = AIService()
            
            # Get current itinerary
            if settings.COSMOS_DB_ENABLED:
                from app.core.cosmos_db import CosmosOperations
                cosmos_ops = CosmosOperations()
                current_itinerary = await cosmos_ops.get_itinerary(trip_id)
                
                if not current_itinerary:
                    raise ValueError(f"No itinerary found for trip {trip_id}")
                
                # Optimize itinerary
                optimized_itinerary = await ai_service.optimize_itinerary(
                    current_itinerary, optimization_type
                )
                
                # Save optimized version
                await cosmos_ops.save_itinerary(trip_id, optimized_itinerary, version="optimized")
                
                # Notify participants (if available)
                try:
                    from app.api.websocket import websocket_manager
                    await websocket_manager.broadcast_to_trip(trip_id, {
                        "type": "itinerary_optimized",
                        "trip_id": trip_id,
                        "optimization_type": optimization_type,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "message": f"Your itinerary has been optimized for {optimization_type}!"
                    })
                except ImportError:
                    logger.info("WebSocket manager not available - skipping notification")
                
                return {"status": "success", "trip_id": trip_id, "optimization_type": optimization_type}
            else:
                raise ValueError("Cosmos DB not enabled for itinerary storage")
                
        except Exception as e:
            logger.error(f"Error in itinerary optimization: {e}")
            raise e


def generate_daily_cost_report():
    """Generate daily AI cost usage report."""
    try:
        task_id = task_queue.add_task("generate_cost_report", {})
        logger.info(f"Queued daily cost report generation task {task_id}")
        return {"task_id": task_id, "status": "queued"}
    except Exception as exc:
        logger.error(f"Failed to queue daily cost report generation: {exc}")
        raise exc


async def _generate_daily_cost_report():
    """Internal async function for cost report generation."""
    try:
        from app.services.ai_service import CostTracker
        
        cost_tracker = CostTracker()
        today = datetime.now().date().isoformat()
        
        if today in cost_tracker.daily_usage:
            usage_data = cost_tracker.daily_usage[today]
            
            # Create report
            report = {
                "date": today,
                "total_cost": usage_data.get("cost", 0),
                "total_requests": usage_data.get("requests", 0),
                "models_used": usage_data.get("models", {}),
                "budget_limit": settings.AI_DAILY_BUDGET_LIMIT,
                "budget_remaining": settings.AI_DAILY_BUDGET_LIMIT - usage_data.get("cost", 0),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Daily cost report generated: {report}")
            
            # Store report for monitoring
            if usage_data.get("cost", 0) > settings.AI_DAILY_BUDGET_LIMIT * 0.8:
                logger.warning(f"AI costs approaching daily budget limit: {usage_data.get('cost', 0)}")
            
            return report
        else:
            return {"date": today, "total_cost": 0, "total_requests": 0}
            
    except Exception as e:
        logger.error(f"Error generating daily cost report: {e}")
        raise e


# Register task processors with the task queue
def register_task_processors():
    """Register all task processors with the SQLite task queue."""
    if task_queue:
        task_queue.register_processor("generate_itinerary", lambda **kwargs: 
            asyncio.run(_generate_itinerary_async(**kwargs)))
        task_queue.register_processor("optimize_itinerary", lambda **kwargs: 
            asyncio.run(_optimize_itinerary_async(**kwargs)))
        task_queue.register_processor("generate_cost_report", lambda **kwargs: 
            asyncio.run(_generate_daily_cost_report()))
        
        logger.info("Task processors registered with SQLite task queue")


# Auto-register processors on import
register_task_processors() 