"""
API endpoint for listing available demo personas.
"""

from fastapi import APIRouter
from personas import list_personas

router = APIRouter()


@router.get("/personas")
def get_personas():
    """List all available demo personas."""
    return {"personas": list_personas()}

