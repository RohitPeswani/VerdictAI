"""
VerdictAI Fair-Weighing Service Package
Author: Akshay Purohit (202512033) - ML Engineer
"""

from backend.app.services.fair_weighing.scoring_service import (
    FairWeighingScoringService,
    fair_weighing_service,
)

__all__ = ["FairWeighingScoringService", "fair_weighing_service"]
