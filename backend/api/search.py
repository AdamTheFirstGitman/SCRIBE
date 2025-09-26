"""
Search API Endpoints - Placeholder
TODO: Implement full search functionality
"""

from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/health")
async def search_health():
    """Search service health check"""
    return {"status": "healthy", "service": "search", "message": "Search API placeholder"}