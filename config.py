"""
DebtGuard 2.0 - Configuration Management
Centralized settings for risk rules, alert thresholds, and system behavior
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import os

# ============================================================================
# ENVIRONMENT & DATABASE
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./debtguard.db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================================================
# RISK RULE CONFIGURATION
# ============================================================================

@dataclass
class RiskRule:
    """Risk rule definition with threshold and severity"""
    rule_id: str
    name: str
    description: str
    enabled: bool
    keywords: List[str]
    transaction_type: str  # CREDIT, DEBIT, or ANY
    window_days: int  # Rolling window for detection
    threshold_count: int  # Minimum occurrences to trigger
    base_risk_score: int  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "keywords": self.keywords,
            "transaction_type": self.transaction_type,
            "window_days": self.window_days,
            "threshold_count": self.threshold_count,
            "base_risk_score": self.base_risk_score,
        }


# ============================================================================
# DEFAULT RISK RULES
# ============================================================================

DEFAULT_RISK_RULES: List[RiskRule] = [
    # Existing Rules
    RiskRule(
        rule_id="R001",
        name="Rapid Loan Stacking",
        description="Multiple NBFC disbursals within short timeframe",
        enabled=True,
        keywords=["NBFC_DISBURSAL"],
        transaction_type="CREDIT",
        window_days=14,
        threshold_count=2,
        base_risk_score=85,
    ),
    RiskRule(
        rule_id="R002",
        name="Shadow Lending Repayment",
        description="Unregulated shadow lending repayment patterns detected",
        enabled=True,
        keywords=["UPI_SHADOW_REPAYMENT", "DAILY_REPAY"],
        transaction_type="DEBIT",
        window_days=30,
        threshold_count=1,
        base_risk_score=90,
    ),
    # New Rules
    RiskRule(
        rule_id="R003",
        name="Predatory Lending",
        description="High-frequency microfinance disbursals",
        enabled=True,
        keywords=["MICROFINANCE", "QUICK_LOAN", "INSTANT_CREDIT"],
        transaction_type="CREDIT",
        window_days=7,
        threshold_count=3,
        base_risk_score=75,
    ),
    RiskRule(
        rule_id="R004",
        name="Circular Lending",
        description="Same amount borrowed and lent back (debt cycling)",
        enabled=True,
        keywords=["LOAN_DISBURSAL", "LOAN_REPAYMENT"],
        transaction_type="ANY",
        window_days=5,
        threshold_count=2,
        base_risk_score=70,
    ),
    RiskRule(
        rule_id="R005",
        name="Cash Advance Stacking",
        description="Multiple cash advances from different lenders",
        enabled=True,
        keywords=["CASH_ADVANCE", "EMERGENCY_LOAN", "CASH_CREDIT"],
        transaction_type="CREDIT",
        window_days=10,
        threshold_count=2,
        base_risk_score=80,
    ),
    RiskRule(
        rule_id="R006",
        name="Loan Broker Activity",
        description="Pattern consistent with loan aggregator intermediaries",
        enabled=True,
        keywords=["BROKER_FEE", "INTERMEDIARY", "REFERRAL_COMMISSION"],
        transaction_type="DEBIT",
        window_days=30,
        threshold_count=2,
        base_risk_score=65,
    ),
]

# ============================================================================
# ALERT THRESHOLDS
# ============================================================================

ALERT_CONFIG = {
    "email_enabled": True,
    "sms_enabled": False,
    "webhook_enabled": True,
    "high_risk_threshold": 80,  # Risk score >= 80 triggers alerts
    "alert_email": os.getenv("ALERT_EMAIL", "admin@debtguard.fintech"),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_user": os.getenv("SMTP_USER", ""),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
}

# ============================================================================
# WEBHOOK CONFIGURATION
# ============================================================================

WEBHOOK_CONFIG = {
    "enabled": True,
    "retry_attempts": 3,
    "timeout_seconds": 10,
    "registered_webhooks": []  # Will be populated from database
}

# ============================================================================
# AUTHENTICATION & ROLES
# ============================================================================

ROLES = {
    "admin": {"permissions": ["read", "write", "configure", "view_audit"]},
    "analyst": {"permissions": ["read", "write", "view_audit"]},
    "viewer": {"permissions": ["read"]},
    "api_client": {"permissions": ["read", "scan"]},
}

# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

ANALYTICS_CONFIG = {
    "daily_report_enabled": True,
    "daily_report_time": "08:00",  # UTC
    "weekly_report_enabled": True,
    "weekly_report_day": "Monday",
    "retention_days": 365,  # Keep scan history for 1 year
    "aggregation_interval_minutes": 60,  # Aggregate metrics every hour
}

# ============================================================================
# API RATE LIMITING
# ============================================================================

RATE_LIMIT_CONFIG = {
    "enabled": True,
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "burst_size": 10,
}
