"""Terminal review status only. There is no automated human decision."""
from math import isfinite

from app.schemas.dispute import ResolutionStatus, Ruling


def route_ruling(ruling: Ruling, threshold: float) -> ResolutionStatus:
    ruling = Ruling.model_validate(ruling)
    if not isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Confidence threshold must be between 0 and 1")
    return (ResolutionStatus.RESOLVED if ruling.confidence >= threshold
            else ResolutionStatus.NEEDS_REVIEW)
