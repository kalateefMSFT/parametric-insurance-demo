"""
Data models for Parametric Insurance Demo
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class OutageStatus(Enum):
    """Outage status enumeration"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    INVESTIGATING = "investigating"


class ClaimStatus(Enum):
    """Claim status enumeration"""
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"


class PayoutStatus(Enum):
    """Payout status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Location:
    """Geographic location"""
    latitude: float
    longitude: float
    zip_code: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)


@dataclass
class OutageEvent:
    """Power outage event"""
    event_id: str
    utility_name: str
    location: Location
    affected_customers: int
    outage_start: datetime
    outage_end: Optional[datetime]
    duration_minutes: Optional[int]
    status: OutageStatus
    cause: Optional[str] = None
    reported_cause: Optional[str] = None
    data_source: str = "poweroutage.us"
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['outage_start'] = self.outage_start.isoformat()
        data['outage_end'] = self.outage_end.isoformat() if self.outage_end else None
        data['last_updated'] = self.last_updated.isoformat() if self.last_updated else None
        data['status'] = self.status.value
        data['location'] = self.location.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        data['outage_start'] = datetime.fromisoformat(data['outage_start'])
        if data.get('outage_end'):
            data['outage_end'] = datetime.fromisoformat(data['outage_end'])
        if data.get('last_updated'):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        data['status'] = OutageStatus(data['status'])
        data['location'] = Location.from_dict(data['location'])
        return cls(**data)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class WeatherData:
    """Weather condition data"""
    location: Location
    timestamp: datetime
    temperature_f: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    wind_gust_mph: Optional[float] = None
    precipitation_inches: Optional[float] = None
    humidity_percent: Optional[int] = None
    conditions: Optional[str] = None
    severe_weather_alert: Optional[bool] = False
    alert_type: Optional[str] = None
    lightning_strikes: Optional[int] = None
    
    def severity_score(self) -> str:
        """Calculate weather severity"""
        score = 0
        
        if self.wind_speed_mph and self.wind_speed_mph > 40:
            score += 2
        elif self.wind_speed_mph and self.wind_speed_mph > 25:
            score += 1
        
        if self.wind_gust_mph and self.wind_gust_mph > 60:
            score += 2
        elif self.wind_gust_mph and self.wind_gust_mph > 45:
            score += 1
        
        if self.precipitation_inches and self.precipitation_inches > 2:
            score += 1
        
        if self.severe_weather_alert:
            score += 2
        
        if self.lightning_strikes and self.lightning_strikes > 10:
            score += 1
        
        if score >= 5:
            return "severe"
        elif score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        else:
            return "low"
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['location'] = self.location.to_dict()
        data['severity'] = self.severity_score()
        return data


@dataclass
class Policy:
    """Insurance policy"""
    policy_id: str
    business_name: str
    location: Location
    threshold_minutes: int
    hourly_rate: float
    max_payout: float
    status: str = "active"
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    business_type: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if policy is currently active"""
        if self.status != "active":
            return False
        
        now = datetime.utcnow()
        
        if self.effective_date and now < self.effective_date:
            return False
        
        if self.expiration_date and now > self.expiration_date:
            return False
        
        return True
    
    def calculate_payout(
        self, 
        duration_minutes: int, 
        severity_multiplier: float = 1.0
    ) -> float:
        """Calculate payout for given outage duration"""
        if duration_minutes <= self.threshold_minutes:
            return 0.0
        
        hours_over_threshold = (duration_minutes - self.threshold_minutes) / 60.0
        base_payout = hours_over_threshold * self.hourly_rate
        adjusted_payout = base_payout * severity_multiplier
        
        return min(adjusted_payout, self.max_payout)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['location'] = self.location.to_dict()
        if self.effective_date:
            data['effective_date'] = self.effective_date.isoformat()
        if self.expiration_date:
            data['expiration_date'] = self.expiration_date.isoformat()
        return data


@dataclass
class Claim:
    """Insurance claim"""
    claim_id: str
    policy_id: str
    outage_event_id: str
    status: ClaimStatus
    filed_at: datetime
    validated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    denied_at: Optional[datetime] = None
    denial_reason: Optional[str] = None
    payout_amount: Optional[float] = None
    ai_confidence_score: Optional[float] = None
    ai_reasoning: Optional[str] = None
    fraud_flags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['filed_at'] = self.filed_at.isoformat()
        if self.validated_at:
            data['validated_at'] = self.validated_at.isoformat()
        if self.approved_at:
            data['approved_at'] = self.approved_at.isoformat()
        if self.denied_at:
            data['denied_at'] = self.denied_at.isoformat()
        return data


@dataclass
class AIValidationResult:
    """Result from AI agent validation"""
    decision: str  # "approve" or "deny"
    confidence_score: float
    payout_amount: float
    reasoning: str
    evidence: List[Dict[str, Any]]
    fraud_signals: List[str]
    severity_assessment: str
    weather_factor: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)


@dataclass
class Payout:
    """Payout record"""
    payout_id: str
    claim_id: str
    policy_id: str
    amount: float
    status: PayoutStatus
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    payment_method: str = "ACH"
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['initiated_at'] = self.initiated_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class SocialSignal:
    """Social media signal (e.g., Twitter mention)"""
    signal_id: str
    platform: str
    text: str
    location: Optional[Location]
    timestamp: datetime
    user_id: str
    engagement_count: int
    relevance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.location:
            data['location'] = self.location.to_dict()
        return data


# Utility functions

def create_claim_id(policy_id: str, event_id: str) -> str:
    """Generate unique claim ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"CLM-{policy_id}-{timestamp}"


def create_payout_id(claim_id: str) -> str:
    """Generate unique payout ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"PAY-{claim_id}-{timestamp}"


def create_event_id(utility: str, timestamp: datetime) -> str:
    """Generate unique event ID"""
    ts = timestamp.strftime("%Y%m%d%H%M%S")
    utility_code = utility.replace(" ", "")[:10].upper()
    return f"OUT-{utility_code}-{ts}"
