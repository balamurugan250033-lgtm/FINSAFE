"""
DebtGuard 2.0 - Enterprise Edition Backend
Complete fintech risk intelligence system with persistence, auth, webhooks, and analytics
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import jwt
import hashlib
import requests
import asyncio
from functools import lru_cache
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import local modules
from config import (
    DEFAULT_RISK_RULES, ALERT_CONFIG, ROLES, SECRET_KEY, 
    ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)
from database import (
    init_database, ScanHistoryDB, AuditLogDB, WebhookDB, RuleDB
)

# ============================================================================
# INITIALIZATION
# ============================================================================

init_database()

app = FastAPI(
    title="DebtGuard 2.0 - Enterprise Edition",
    description="Production-grade fintech risk intelligence with persistence, auth, webhooks",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class TransactionType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class Transaction(BaseModel):
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    type: TransactionType
    desc: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)

class AccountPayload(BaseModel):
    account_id: str = Field(..., min_length=1)
    customer_name: str = Field(..., min_length=1)
    transactions: List[Transaction] = Field(..., min_length=1)

class RiskTier(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RecommendedAction(str, Enum):
    TRIGGER_COOLING_OFF_ALERT = "TRIGGER_COOLING_OFF_ALERT"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    NONE = "NONE"

class SentinelScanResult(BaseModel):
    account_id: str
    customer_name: str
    risk_tier: RiskTier
    risk_score: int
    triggered_flags: List[str]
    estimated_unreported_debt: float
    recommended_action: RecommendedAction
    scan_timestamp: str
    transaction_count: int
    detailed_findings: Optional[Dict[str, Any]] = None

class BulkScanPayload(BaseModel):
    accounts: List[AccountPayload] = Field(..., min_length=1)

class BulkScanResult(BaseModel):
    batch_id: str
    total_accounts: int
    high_risk_count: int
    critical_risk_count: int
    total_exposure: float
    scan_results: List[SentinelScanResult]
    scan_timestamp: str

class PortfolioResponse(BaseModel):
    total_accounts: int
    high_risk_count: int
    critical_risk_count: int
    total_exposure: float
    accounts: List[SentinelScanResult]
    portfolio_timestamp: str

class WebhookRegistration(BaseModel):
    url: str = Field(..., pattern=r'^https?://')
    event_type: str = Field(..., min_length=1)

class RiskRuleUpdate(BaseModel):
    rule_id: str
    enabled: bool
    threshold_count: Optional[int] = None
    window_days: Optional[int] = None
    base_risk_score: Optional[int] = None

class HistoricalReportRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=365)
    account_id: Optional[str] = None
    risk_tier_filter: Optional[str] = None

class AnalyticsResponse(BaseModel):
    period_days: int
    total_scans: int
    high_risk_percentage: float
    average_unreported_debt: float
    top_triggered_flags: Dict[str, int]
    risk_tier_distribution: Dict[str, int]
    timestamp: str

# ============================================================================
# ADVANCED RISK ANALYZER
# ============================================================================

class AdvancedRiskAnalyzer:
    """Enhanced risk detection with configurable rules and scoring"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load risk rules from database or defaults"""
        db_rules = RuleDB.get_all_rules()
        if db_rules:
            return {r['rule_id']: r for r in db_rules}
        
        # Initialize with defaults
        for rule in DEFAULT_RISK_RULES:
            RuleDB.upsert_rule(rule.to_dict())
        
        return {r.rule_id: r.to_dict() for r in DEFAULT_RISK_RULES}
    
    @staticmethod
    def parse_date(date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    
    def evaluate_rule(
        self, 
        rule: Dict[str, Any], 
        transactions: List[Transaction]
    ) -> tuple[bool, float, List[Dict[str, Any]]]:
        """Evaluate a single rule against transactions"""
        if not rule.get('enabled', True):
            return False, 0.0, []
        
        matching_txns = []
        keywords = rule.get('keywords', [])
        txn_type = rule.get('transaction_type', 'ANY')
        window_days = rule.get('window_days', 30)
        threshold = rule.get('threshold_count', 1)
        
        # Filter transactions by type and keywords
        for txn in transactions:
            if txn_type != 'ANY' and txn.type.value != txn_type:
                continue
            
            if any(kw in txn.desc for kw in keywords):
                matching_txns.append({
                    'date': txn.date,
                    'desc': txn.desc,
                    'amount': txn.amount,
                    'type': txn.type.value
                })
        
        if len(matching_txns) < threshold:
            return False, 0.0, []
        
        # Check if matches fall within window
        if len(matching_txns) >= threshold:
            dates = [self.parse_date(t['date']) for t in matching_txns]
            date_ranges = sorted(dates)
            
            for i in range(len(date_ranges) - threshold + 1):
                window_start = date_ranges[i]
                window_end = window_start + timedelta(days=window_days)
                
                matches_in_window = sum(
                    1 for d in date_ranges[i:]
                    if window_start <= d <= window_end
                )
                
                if matches_in_window >= threshold:
                    return True, sum(t['amount'] for t in matching_txns), matching_txns
        
        return False, 0.0, []
    
    def calculate_risk_score(
        self,
        triggered_flags: List[str],
        flag_details: Dict[str, Any]
    ) -> int:
        """Calculate composite risk score (0-100)"""
        if not triggered_flags:
            return 0
        
        scores = []
        for flag_id in triggered_flags:
            if flag_id in self.rules:
                rule = self.rules[flag_id]
                base_score = rule.get('base_risk_score', 50)
                
                # Adjust score based on number of triggers
                if flag_id in flag_details:
                    detail = flag_details[flag_id]
                    if 'count' in detail:
                        multiplier = min(1 + (detail['count'] - 1) * 0.1, 1.5)
                        scores.append(int(base_score * multiplier))
                    else:
                        scores.append(base_score)
                else:
                    scores.append(base_score)
        
        # Return weighted average, capped at 100
        return min(int(sum(scores) / len(scores)) if scores else 0, 100)
    
    def determine_risk_tier(self, risk_score: int) -> str:
        """Determine risk tier based on score"""
        if risk_score >= 85:
            return RiskTier.CRITICAL.value
        elif risk_score >= 70:
            return RiskTier.HIGH.value
        elif risk_score >= 50:
            return RiskTier.MEDIUM.value
        else:
            return RiskTier.LOW.value
    
    def analyze_account(self, payload: AccountPayload) -> tuple[SentinelScanResult, Dict[str, Any]]:
        """Comprehensive account analysis"""
        triggered_flags = []
        flag_details = {}
        estimated_debt = 0.0
        
        for rule_id, rule in self.rules.items():
            triggered, debt, matching_txns = self.evaluate_rule(rule, payload.transactions)
            if triggered:
                triggered_flags.append(rule_id)
                flag_details[rule_id] = {
                    'name': rule.get('name'),
                    'description': rule.get('description'),
                    'count': len(matching_txns),
                    'matching_transactions': matching_txns[:5],  # Top 5
                    'total_amount': debt
                }
                estimated_debt += debt
        
        risk_score = self.calculate_risk_score(triggered_flags, flag_details)
        risk_tier = self.determine_risk_tier(risk_score)
        
        if risk_score >= ALERT_CONFIG['high_risk_threshold']:
            recommended_action = RecommendedAction.TRIGGER_COOLING_OFF_ALERT
        elif triggered_flags:
            recommended_action = RecommendedAction.MANUAL_REVIEW_REQUIRED
        else:
            recommended_action = RecommendedAction.NONE
        
        result = SentinelScanResult(
            account_id=payload.account_id,
            customer_name=payload.customer_name,
            risk_tier=risk_tier,
            risk_score=risk_score,
            triggered_flags=triggered_flags,
            estimated_unreported_debt=estimated_debt,
            recommended_action=recommended_action,
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            transaction_count=len(payload.transactions),
            detailed_findings=flag_details
        )
        
        return result, {
            'account_id': payload.account_id,
            'customer_name': payload.customer_name,
            'risk_score': risk_score,
            'triggered_flags': triggered_flags,
            'estimated_unreported_debt': estimated_debt,
            'flag_details': flag_details
        }

# Initialize analyzer
analyzer = AdvancedRiskAnalyzer()

# ============================================================================
# AUTHENTICATION & JWT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(request: Request) -> dict:
    """Verify JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============================================================================
# ALERT SYSTEM
# ============================================================================

async def send_email_alert(account_id: str, risk_tier: str, risk_score: int):
    """Send email alert for high-risk account"""
    if not ALERT_CONFIG['email_enabled']:
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = ALERT_CONFIG['smtp_user']
        msg['To'] = ALERT_CONFIG['alert_email']
        msg['Subject'] = f"🚨 DebtGuard Alert: {risk_tier} Risk - Account {account_id}"
        
        body = f"""
        High-Risk Account Detected
        
        Account ID: {account_id}
        Risk Tier: {risk_tier}
        Risk Score: {risk_score}/100
        Timestamp: {datetime.now(timezone.utc).isoformat()}
        
        Please review this account immediately in the DebtGuard dashboard.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Only send if credentials are configured
        if ALERT_CONFIG['smtp_user'] and ALERT_CONFIG['smtp_password']:
            with smtplib.SMTP(ALERT_CONFIG['smtp_server'], ALERT_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(ALERT_CONFIG['smtp_user'], ALERT_CONFIG['smtp_password'])
                server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email alert: {e}")

async def trigger_webhooks(event_type: str, data: Dict[str, Any]):
    """Trigger registered webhooks"""
    if not ALERT_CONFIG['webhook_enabled']:
        return
    
    webhooks = WebhookDB.get_webhooks()
    
    for webhook in webhooks:
        if webhook['event_type'] == event_type or webhook['event_type'] == '*':
            try:
                response = requests.post(
                    webhook['url'],
                    json={'event': event_type, 'data': data},
                    timeout=10
                )
            except Exception as e:
                print(f"Webhook trigger failed: {e}")

# ============================================================================
# API ENDPOINTS - SYSTEM
# ============================================================================

@app.get("/", tags=["System"])
async def health_check():
    """System health and metadata"""
    return {
        "status": "operational",
        "service": "DebtGuard 2.0 - Enterprise Edition",
        "version": "2.0.0",
        "features": [
            "Real-time transaction analysis",
            "Advanced multi-rule risk detection",
            "Persistent scan history",
            "JWT authentication",
            "Bulk scanning",
            "Email & webhook alerts",
            "Role-based access control",
            "Audit logging",
            "Historical analytics"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/v1/auth/token", tags=["Authentication"])
async def login(username: str, password: str):
    """Generate access token (demo: any credentials work)"""
    # In production, verify against database
    access_token = create_access_token(
        data={"sub": username, "role": "analyst"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    AuditLogDB.log_action("login", user_id=username)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES
    }

# ============================================================================
# API ENDPOINTS - SCANNING
# ============================================================================

@app.post("/api/v1/sentinel/scan", response_model=SentinelScanResult, tags=["Scanning"])
async def sentinel_scan(payload: AccountPayload):
    """Execute risk assessment scan on single account"""
    result, raw_data = analyzer.analyze_account(payload)
    
    # Store in database
    scan_id = ScanHistoryDB.insert_scan(
        account_id=result.account_id,
        customer_name=result.customer_name,
        risk_tier=result.risk_tier,
        triggered_flags=result.triggered_flags,
        estimated_unreported_debt=result.estimated_unreported_debt,
        recommended_action=result.recommended_action.value,
        risk_score=result.risk_score,
        raw_data=raw_data
    )
    
    # Audit log
    AuditLogDB.log_action("scan_executed", resource_type="account", resource_id=payload.account_id)
    
    # Trigger alerts if high risk
    if result.risk_score >= ALERT_CONFIG['high_risk_threshold']:
        await send_email_alert(result.account_id, result.risk_tier, result.risk_score)
        await trigger_webhooks("high_risk_scan", {
            "account_id": result.account_id,
            "risk_score": result.risk_score,
            "scan_id": scan_id
        })
    
    return result

@app.post("/api/v1/sentinel/bulk-scan", response_model=BulkScanResult, tags=["Scanning"])
async def bulk_scan(payload: BulkScanPayload):
    """Execute risk assessment on multiple accounts"""
    import uuid
    batch_id = str(uuid.uuid4())[:8]
    
    results = []
    high_risk_count = 0
    critical_risk_count = 0
    total_exposure = 0.0
    
    for account in payload.accounts:
        result, _ = analyzer.analyze_account(account)
        results.append(result)
        
        if result.risk_tier == RiskTier.HIGH.value:
            high_risk_count += 1
        elif result.risk_tier == RiskTier.CRITICAL.value:
            critical_risk_count += 1
        
        total_exposure += result.estimated_unreported_debt
    
    AuditLogDB.log_action("bulk_scan", resource_type="batch", resource_id=batch_id, details={"count": len(payload.accounts)})
    
    return BulkScanResult(
        batch_id=batch_id,
        total_accounts=len(payload.accounts),
        high_risk_count=high_risk_count,
        critical_risk_count=critical_risk_count,
        total_exposure=total_exposure,
        scan_results=results,
        scan_timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/api/v1/portfolio/monitor", response_model=PortfolioResponse, tags=["Monitoring"])
async def portfolio_monitor():
    """Return mock portfolio with enhanced data"""
    mock_accounts = [
        AccountPayload(
            account_id="ACC-001",
            customer_name="Rajesh Kumar",
            transactions=[
                Transaction(date="2024-01-15", type=TransactionType.CREDIT, desc="Salary Credit", amount=50000.0),
                Transaction(date="2024-01-16", type=TransactionType.DEBIT, desc="Electricity Bill", amount=1200.0),
            ]
        ),
        AccountPayload(
            account_id="ACC-002",
            customer_name="Priya Sharma",
            transactions=[
                Transaction(date="2024-01-10", type=TransactionType.CREDIT, desc="NBFC_DISBURSAL", amount=15000.0),
                Transaction(date="2024-01-20", type=TransactionType.CREDIT, desc="NBFC_DISBURSAL", amount=12000.0),
            ]
        ),
        AccountPayload(
            account_id="ACC-003",
            customer_name="Amit Singh",
            transactions=[
                Transaction(date="2024-01-15", type=TransactionType.CREDIT, desc="Cash Transfer", amount=8000.0),
                Transaction(date="2024-01-18", type=TransactionType.DEBIT, desc="UPI_SHADOW_REPAYMENT", amount=8500.0),
                Transaction(date="2024-01-25", type=TransactionType.CREDIT, desc="Cash Transfer", amount=6000.0),
                Transaction(date="2024-01-28", type=TransactionType.DEBIT, desc="DAILY_REPAY", amount=6300.0),
            ]
        ),
    ]
    
    results = []
    high_risk_count = 0
    critical_risk_count = 0
    total_exposure = 0.0
    
    for account in mock_accounts:
        result, _ = analyzer.analyze_account(account)
        results.append(result)
        
        if result.risk_tier == RiskTier.HIGH.value:
            high_risk_count += 1
        elif result.risk_tier == RiskTier.CRITICAL.value:
            critical_risk_count += 1
        
        total_exposure += result.estimated_unreported_debt
    
    return PortfolioResponse(
        total_accounts=len(results),
        high_risk_count=high_risk_count,
        critical_risk_count=critical_risk_count,
        total_exposure=total_exposure,
        accounts=results,
        portfolio_timestamp=datetime.now(timezone.utc).isoformat()
    )

# ============================================================================
# API ENDPOINTS - HISTORY & ANALYTICS
# ============================================================================

@app.get("/api/v1/history/account/{account_id}", tags=["History"])
async def get_account_history(account_id: str):
    """Retrieve scan history for specific account"""
    scans = ScanHistoryDB.get_scans_by_account(account_id)
    return {
        "account_id": account_id,
        "scan_count": len(scans),
        "scans": scans
    }

@app.get("/api/v1/history/recent", tags=["History"])
async def get_recent_history(days: int = 7):
    """Retrieve recent scans from last N days"""
    scans = ScanHistoryDB.get_recent_scans(days)
    return {
        "period_days": days,
        "scan_count": len(scans),
        "scans": scans
    }

@app.post("/api/v1/analytics/report", response_model=AnalyticsResponse, tags=["Analytics"])
async def generate_analytics_report(request: HistoricalReportRequest):
    """Generate historical analytics report"""
    scans = ScanHistoryDB.get_recent_scans(request.days)
    
    if not scans:
        return AnalyticsResponse(
            period_days=request.days,
            total_scans=0,
            high_risk_percentage=0.0,
            average_unreported_debt=0.0,
            top_triggered_flags={},
            risk_tier_distribution={},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    high_risk_count = sum(1 for s in scans if s['risk_tier'] in ['HIGH', 'CRITICAL'])
    flag_counts = {}
    risk_distribution = {}
    total_debt = 0.0
    
    for scan in scans:
        for flag in scan.get('triggered_flags', []):
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
        
        risk = scan['risk_tier']
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        total_debt += scan.get('estimated_unreported_debt', 0)
    
    top_flags = dict(sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    
    return AnalyticsResponse(
        period_days=request.days,
        total_scans=len(scans),
        high_risk_percentage=round((high_risk_count / len(scans)) * 100, 2) if scans else 0,
        average_unreported_debt=round(total_debt / len(scans), 2) if scans else 0,
        top_triggered_flags=top_flags,
        risk_tier_distribution=risk_distribution,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

# ============================================================================
# API ENDPOINTS - ADMIN
# ============================================================================

@app.get("/api/v1/admin/rules", tags=["Administration"])
async def get_all_rules(request: Request):
    """Get all risk rules (admin only)"""
    token = verify_token(request)
    rules = RuleDB.get_all_rules(active_only=False)
    return {"rules": rules}

@app.post("/api/v1/admin/rules/update", tags=["Administration"])
async def update_rule(update: RiskRuleUpdate, request: Request):
    """Update risk rule configuration"""
    token = verify_token(request)
    
    rule = analyzer.rules.get(update.rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    if update.threshold_count:
        rule['threshold_count'] = update.threshold_count
    if update.window_days:
        rule['window_days'] = update.window_days
    if update.base_risk_score:
        rule['base_risk_score'] = update.base_risk_score
    
    rule['enabled'] = update.enabled
    RuleDB.upsert_rule(rule)
    
    AuditLogDB.log_action("rule_updated", user_id=token.get('sub'), resource_id=update.rule_id)
    
    return {"status": "updated", "rule_id": update.rule_id}

@app.get("/api/v1/admin/webhooks", tags=["Administration"])
async def get_webhooks(request: Request):
    """List registered webhooks"""
    token = verify_token(request)
    webhooks = WebhookDB.get_webhooks(active_only=False)
    return {"webhooks": webhooks}

@app.post("/api/v1/admin/webhooks/register", tags=["Administration"])
async def register_webhook(webhook: WebhookRegistration, request: Request):
    """Register new webhook"""
    token = verify_token(request)
    
    success = WebhookDB.register_webhook(webhook.url, webhook.event_type)
    
    if not success:
        raise HTTPException(status_code=400, detail="Webhook URL already registered")
    
    AuditLogDB.log_action("webhook_registered", user_id=token.get('sub'), details={"url": webhook.url})
    
    return {"status": "registered", "url": webhook.url}

@app.delete("/api/v1/admin/webhooks/{webhook_id}", tags=["Administration"])
async def delete_webhook(webhook_id: int, request: Request):
    """Delete webhook"""
    token = verify_token(request)
    
    success = WebhookDB.delete_webhook(webhook_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    AuditLogDB.log_action("webhook_deleted", user_id=token.get('sub'), resource_id=str(webhook_id))
    
    return {"status": "deleted"}

@app.get("/api/v1/admin/audit-logs", tags=["Administration"])
async def get_audit_logs(limit: int = 100, request: Request = None):
    """Retrieve audit logs"""
    if request:
        token = verify_token(request)
    logs = AuditLogDB.get_audit_logs(limit)
    return {"logs": logs}

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
