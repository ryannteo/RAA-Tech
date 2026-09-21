from typing import Optional

from pydantic import BaseModel


class DisputeSubmission(BaseModel):
    category: str  # route_deviation | no_show | property_damage | safety_incident
    trip_id: str
    rider_id: str
    driver_id: str
    rider_statement: str
    driver_statement: Optional[str] = None
