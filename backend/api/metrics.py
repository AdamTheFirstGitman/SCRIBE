"""
Metrics API endpoints
Dashboard metrics for usage tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from utils.logger import get_logger
from services.storage import supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


# Models
class MetricsPeriod(BaseModel):
    tokens: int
    cost_eur: float


class DashboardMetrics(BaseModel):
    total_notes: int
    total_conversations: int
    total_tokens: int
    total_cost_eur: float
    last_30_days: MetricsPeriod


# Endpoints
@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get metrics for dashboard"""

    try:
        logger.info("Getting dashboard metrics")

        # Count notes
        notes_result = supabase_client.client.table('notes') \
            .select('id', count='exact') \
            .eq('user_id', 'king_001') \
            .execute()
        total_notes = notes_result.count or 0

        # Count conversations
        convs_result = supabase_client.client.table('conversations') \
            .select('id', count='exact') \
            .eq('user_id', 'king_001') \
            .execute()
        total_conversations = convs_result.count or 0

        # TODO: Get token usage from messages metadata when table exists
        # For now, return 0 values as messages table not yet created
        total_tokens = 0
        total_cost = 0.0
        last_30_days_tokens = 0
        last_30_days_cost = 0.0

        logger.info("Dashboard metrics retrieved",
                   total_notes=total_notes,
                   total_conversations=total_conversations,
                   total_tokens=total_tokens)

        return DashboardMetrics(
            total_notes=total_notes,
            total_conversations=total_conversations,
            total_tokens=total_tokens,
            total_cost_eur=round(total_cost, 2),
            last_30_days=MetricsPeriod(
                tokens=last_30_days_tokens,
                cost_eur=round(last_30_days_cost, 2)
            )
        )

    except Exception as e:
        logger.error("Failed to get dashboard metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )
