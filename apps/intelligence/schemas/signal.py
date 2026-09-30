from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    WEATHER = "weather"
    OFFICIAL_ALERT = "official_alert"
    TRANSPORT = "transport"
    INFRASTRUCTURE = "infrastructure"
    PUBLIC_REPORT = "public_report"
    MEDIA = "media"
    SEISMIC = "seismic"
    HEALTH = "health"
    INDUSTRIAL = "industrial"
    ENVIRONMENTAL = "environmental"


class SourceCategory(str, Enum):
    OFFICIAL = "official"
    WEATHER = "weather"
    TRANSPORT = "transport"
    MEDIA = "media"
    PUBLIC = "public"
    INFRASTRUCTURE = "infrastructure"
    SEISMIC = "seismic"
    HEALTH = "health"
    INDUSTRIAL = "industrial"
    ENVIRONMENTAL = "environmental"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    REPUTABLE = "reputable"
    INDEPENDENT = "independent"
    UNVERIFIED = "unverified"


class ProvenanceLabel(str, Enum):
    OBSERVED = "observed"
    CORROBORATED = "corroborated"
    INFERRED = "inferred"
    FORECAST = "forecast"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"


class AuditEntry(BaseModel):
    timestamp: datetime
    action: str  # 'created', 'updated', 'reclassified', 'corroborated', 'contradicted'
    actor: str  # system component or user
    details: str


class SignalLocation(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    region: Optional[str] = None

    # Estimated geographic uncertainty of this signal.
    precision_km: float = Field(default=5.0, ge=0)


class SignalSource(BaseModel):
    id: str
    name: str

    category: SourceCategory
    verification: VerificationStatus


class Signal(BaseModel):
    id: str

    source: SignalSource

    type: SignalType

    title: str
    description: str

    location: SignalLocation

    timestamp: datetime

    # Entities mentioned by the signal.
    # Examples: cities, roads, rivers, infrastructure assets.
    entities: list[str] = Field(default_factory=list)

    # Severity reported by the source.
    # This is NOT the severity of the final incident.
    severity: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )
    
    provenance: ProvenanceLabel = Field(default=ProvenanceLabel.OBSERVED)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    language: str = Field(default="en")
    domain: str = Field(default="general")
    version: int = Field(default=1)
    audit_trail: list[AuditEntry] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    parent_signal_id: Optional[str] = Field(default=None)
    contradicts: list[str] = Field(default_factory=list)