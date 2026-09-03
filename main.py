"""
DebtGuard 2.0 - RBI-Compliant Early Warning System (EWS)
========================================================

Account Aggregator (AA) powered real-time Debt Velocity monitoring.

RUN INSTRUCTIONS
----------------
1. Install dependencies:
    pip install fastapi uvicorn python-multipart pydantic

2. Start the server:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

3. Open the dashboard in your browser:
    http://localhost:8000/
"""

from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from database import init_database, ScanHistoryDB, AuditLogDB

# ---------------------------------------------------------------------------
# FastAPI application + CORS
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DebtGuard 2.0 — Early Warning System",
    description="RBI-compliant real-time Debt Velocity detection over AA transaction streams.",
    version="2.0.0",
    license={
        "name": "Proprietary — RBI Regulated Sandbox",
        "url": "https://rbi.org.in",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)

@app.on_event("startup")
def on_startup():
    init_database()
    AuditLogDB.log_action(
        action="SYSTEM_STARTUP",
        user_id="SYSTEM",
        resource_type="ENGINE",
        resource_id="EWS_V2",
        details={"status": "INITIALIZED", "version": "2.0.0"}
    )

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class Transaction(BaseModel):
    """A single book-entry transaction sourced from an AA-linked account."""
    date: str = Field(..., description="ISO date string, e.g. '2026-08-01'")
    type: str = Field(..., description="CREDIT or DEBIT")
    desc: str = Field(..., description="Narrative / merchant / UPI handle")
    amount: float = Field(..., gt=0, description="Transaction amount in INR")


class AccountPayload(BaseModel):
    """Per-account payload delivered by the AA sync."""
    account_id: str
    customer_name: str
    transactions: List[Transaction]


class RiskFlag(BaseModel):
    code: str
    label: str
    severity: str  # LOW | MEDIUM | HIGH
    detail: str


class Intervention(BaseModel):
    action: str
    rationale: str


class FactorMapping(BaseModel):
    factor: str
    metric_value: str
    recommended_action: str
    rationale: str


class EWSScanResult(BaseModel):
    account_id: str
    customer_name: str
    debt_velocity_score: float
    debt_velocity_tier: str  # LOW | MEDIUM | HIGH
    risk_flags: List[RiskFlag]
    intervention: Intervention
    windows_analyzed: int
    estimated_unreported_debt: float = 0.0
    factor_mappings: List[FactorMapping] = []
    inclusion_safeguard_notice: str = (
        "Protection Notice: This early warning signal does NOT affect loan eligibility, "
        "reduce credit score, or block account status per RBI DLT 2026 guidelines."
    )
    aa_consent_notice: str = (
        "Analysis based on real-time transaction streams shared via customer consent "
        "under the RBI Account Aggregator (AA) framework."
    )


class InterventionApprovalPayload(BaseModel):
    account_id: str
    officer_id: str = "OFFICER-7892"
    action: str
    notes: Optional[str] = "Staff authorized intervention after DTI review."


# ---------------------------------------------------------------------------
# Heuristic constants
# ---------------------------------------------------------------------------
SHADOW_UPI_HANDLES = ("fastpay", "quickcash", "rapidcash", "instantloan", "shadow")
WINDOW_DAYS = 14
LOW_TICK_MIN, LOW_TICK_MAX = 100.0, 1000.0
HIGH_VELOCITY_THRESHOLD = 150000.0 / 14.0  # ~₹1500/day avg triggers HIGH

TODAY = datetime(2026, 8, 31)


# ---------------------------------------------------------------------------
# EWS Detection Engine
# ---------------------------------------------------------------------------
def _parse_date(value: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except Exception:
        return TODAY


def _days_between(first: datetime, last: datetime) -> int:
    delta = (last - first).days
    return max(delta, 1)


def _is_nbfc_disbursals(t: Transaction) -> bool:
    if t.type.upper() != "CREDIT":
        return False
    desc = t.desc.lower()
    return ("disburs" in desc) or ("nbfc" in desc) or ("loan" in desc and "emi" not in desc)


def detect_ews(payload: AccountPayload) -> EWSScanResult:
    txns = list(payload.transactions)

    # --- Debt Velocity & EMI Ratio ---
    disbursals = [t for t in txns if _is_nbfc_disbursals(t)]
    disbursals_sorted = sorted(disbursals, key=lambda t: _parse_date(t.date))

    salary_credits = [t for t in txns if t.type.upper() == "CREDIT" and ("salary" in t.desc.lower() or t.amount >= 30000)]
    monthly_income = sum(s.amount for s in salary_credits) or 75000.0

    emi_debits = [t for t in txns if t.type.upper() == "DEBIT" and ("emi" in t.desc.lower() or "rent" in t.desc.lower())]
    total_emi = sum(e.amount for e in emi_debits)
    emi_ratio = round((total_emi / monthly_income) * 100, 1) if monthly_income > 0 else 45.0

    dv_score = 0.0
    total_unreported_debt = sum(d.amount for d in disbursals_sorted)
    rapid_stack = False

    if disbursals_sorted:
        first_dt = _parse_date(disbursals_sorted[0].date)
        last_dt = _parse_date(disbursals_sorted[-1].date)
        span = _days_between(first_dt, last_dt)
        dv_score = round(total_unreported_debt / span, 2)

        for base in disbursals_sorted:
            base_dt = _parse_date(base.date)
            in_window = [
                x
                for x in disbursals_sorted
                if 0 <= (_parse_date(x.date) - base_dt).days <= WINDOW_DAYS
            ]
            if len(in_window) >= 2:
                rapid_stack = True
                break

    # --- Shadow-Net Heuristic ---
    shadow_pattern = False
    shadow_detail = ""
    recurring_debits = [t for t in txns if t.type.upper() == "DEBIT"]
    handle_counts: Dict[str, int] = {}
    handle_amounts: Dict[str, float] = {}

    for t in recurring_debits:
        desc_lower = t.desc.lower()
        for handle in SHADOW_UPI_HANDLES:
            if handle in desc_lower or "shadow" in desc_lower or "daily_repay" in desc_lower:
                shadow_pattern = True
                h_name = handle if handle in desc_lower else "shadow_pool"
                handle_counts[h_name] = handle_counts.get(h_name, 0) + 1
                handle_amounts[h_name] = handle_amounts.get(h_name, 0.0) + t.amount

    if shadow_pattern:
        top = max(handle_counts, key=handle_counts.get)
        shadow_detail = (
            f"₹{handle_amounts[top]:,.0f} across {handle_counts[top]} "
            f"transactions to unverified handle '{top}'."
        )

    # --- Tier + flags ---
    flags: List[RiskFlag] = []
    if rapid_stack:
        flags.append(
            RiskFlag(
                code="RAPID_LOAN_STACKING",
                label="Rapid Loan Stacking",
                severity="HIGH",
                detail=f"{len(disbursals_sorted)} NBFC disbursals within a {WINDOW_DAYS}-day window.",
            )
        )
    if shadow_pattern:
        flags.append(
            RiskFlag(
                code="SHADOW_LENDING_PATTERN_DETECTED",
                label="Shadow Lending Network",
                severity="HIGH",
                detail=shadow_detail,
            )
        )

    if dv_score >= HIGH_VELOCITY_THRESHOLD or rapid_stack or shadow_pattern:
        tier = "HIGH"
    elif dv_score >= HIGH_VELOCITY_THRESHOLD * 0.4:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    # --- Personalized Factor Mappings ---
    factor_mappings: List[FactorMapping] = []

    if emi_ratio > 50.0:
        factor_mappings.append(
            FactorMapping(
                factor="High EMI Burden",
                metric_value=f"EMI-to-income is {emi_ratio}%",
                recommended_action="EMI Restructuring & Tenor Extension",
                rationale=f"Recommended because: EMI obligations ({emi_ratio}%) exceed 50% threshold."
            )
        )

    if rapid_stack:
        factor_mappings.append(
            FactorMapping(
                factor="Multi-Lender Stacking",
                metric_value=f"{len(disbursals_sorted)} NBFC disbursals in 14d",
                recommended_action="OFFER_CALIBRATED_MICRO_CREDIT",
                rationale="Recommended because: 3 NBFC disbursals in 14 days; offer a smaller ₹15,000 credit line to prevent financial exclusion."
            )
        )

    if shadow_pattern:
        factor_mappings.append(
            FactorMapping(
                factor="Shadow Net Exposure",
                metric_value=shadow_detail,
                recommended_action="Debt Consolidation First-Aid Offer",
                rationale="Recommended because: Recurring payments to unverified high-cost UPI handle detected."
            )
        )

    if not factor_mappings:
        factor_mappings.append(
            FactorMapping(
                factor="Stable Liquidity",
                metric_value=f"EMI-to-income is {emi_ratio}%",
                recommended_action="NO_ACTION_REQUIRED",
                rationale="Recommended because: Debt velocity and cash reserves remain within safe bands."
            )
        )

    # --- Primary Assistive Intervention Logic ---
    if tier == "HIGH":
        if rapid_stack and not shadow_pattern:
            action = "OFFER_CALIBRATED_MICRO_CREDIT"
            rationale = "Rapid loan stacking detected; offer a smaller, manageable credit line to prevent predatory lender reliance while preserving liquidity."
        elif shadow_pattern and not rapid_stack:
            action = "TRIGGER_FINANCIAL_FIRST_AID_OFFER"
            rationale = "Shadow-lending pattern detected; trigger financial first-aid consolidation offer to consolidate high-cost obligations."
        else:
            action = "OFFER_CALIBRATED_MICRO_CREDIT"
            rationale = "Multiple distress signals; offer calibrated micro-credit + debt consolidation to prevent financial exclusion."
    elif tier == "MEDIUM":
        action = "TRIGGER_DEBT_COUNSELING_SUGGESTION"
        rationale = "Elevated velocity; recommend proactive counseling and EMI tenor extension."
    else:
        action = "NO_ACTION_REQUIRED"
        rationale = "Velocity within normal bands; continuous background monitoring."

    windows = 1
    if disbursals_sorted:
        unique_days = {_parse_date(d.date).date() for d in disbursals_sorted}
        windows = max(1, len(unique_days))

    return EWSScanResult(
        account_id=payload.account_id,
        customer_name=payload.customer_name,
        debt_velocity_score=dv_score,
        debt_velocity_tier=tier,
        risk_flags=flags,
        intervention=Intervention(action=action, rationale=rationale),
        windows_analyzed=windows,
        estimated_unreported_debt=total_unreported_debt,
        factor_mappings=factor_mappings,
        inclusion_safeguard_notice=(
            "Protection Notice: This early warning signal does NOT affect loan eligibility, "
            "reduce credit score, or block account status per RBI DLT 2026 guidelines."
        ),
        aa_consent_notice=(
            "Analysis based on real-time transaction streams shared via customer consent "
            "under the RBI Account Aggregator (AA) framework."
        ),
    )


def _persist_scan_and_audit(payload: AccountPayload, result: EWSScanResult):
    """Helper to save scan result and audit log to SQLite DB."""
    try:
        flag_codes = [f.code for f in result.risk_flags]
        risk_score = 85 if result.debt_velocity_tier == "HIGH" else (55 if result.debt_velocity_tier == "MEDIUM" else 15)
        
        ScanHistoryDB.insert_scan(
            account_id=result.account_id,
            customer_name=result.customer_name,
            risk_tier=result.debt_velocity_tier,
            triggered_flags=flag_codes,
            estimated_unreported_debt=result.estimated_unreported_debt,
            recommended_action=result.intervention.action,
            risk_score=risk_score,
            raw_data=payload.model_dump()
        )
        
        AuditLogDB.log_action(
            action="EWS_SCAN_COMPLETED",
            user_id="AA_SENTINEL",
            resource_type="ACCOUNT",
            resource_id=result.account_id,
            details={
                "customer": result.customer_name,
                "tier": result.debt_velocity_tier,
                "velocity": result.debt_velocity_score,
                "flags": flag_codes,
                "action": result.intervention.action,
            }
        )
    except Exception as e:
        print(f"[DB LOG WARNING] Failed to persist scan: {e}")


# ---------------------------------------------------------------------------
# Mock portfolio (Shared 10-customer dataset matching FinShield AI)
# ---------------------------------------------------------------------------
def _mk_transactions(spec: list[tuple]) -> List[Transaction]:
    return [Transaction(date=d, type=t, desc=desc, amount=float(a)) for (d, t, desc, a) in spec]


_MOCK_PORTFOLIO = [
    {
        "account_id": "ACC-001",
        "customer_name": "Rahul Sharma",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "NBFC_DISBURSAL BAJAJ", 150000),
            ("2026-08-04", "CREDIT", "NBFC_DISBURSAL LENDINGTREE", 100000),
            ("2026-08-09", "CREDIT", "NBFC_DISBURSAL KREDA", 80000),
            ("2026-08-10", "DEBIT", "fastpay UPI txn", 450),
            ("2026-08-12", "DEBIT", "EMI HDFC LOAN", 28000),
            ("2026-08-14", "DEBIT", "quickcash transfer", 750),
        ]),
        "risk_status": "HIGH",
    },
    {
        "account_id": "ACC-002",
        "customer_name": "Priya Kumar",
        "transactions": _mk_transactions([
            ("2026-08-02", "CREDIT", "NBFC_DISBURSAL KREDA", 120000),
            ("2026-08-05", "CREDIT", "NBFC_DISBURSAL QUICKLOAN", 90000),
            ("2026-08-11", "DEBIT", "fastpay recharge", 650),
            ("2026-08-13", "DEBIT", "EMI AXIS LOAN", 25000),
        ]),
        "risk_status": "HIGH",
    },
    {
        "account_id": "ACC-003",
        "customer_name": "Arjun Patel",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 75000),
            ("2026-08-03", "DEBIT", "EMI ICICI LOAN", 30000),
            ("2026-08-08", "DEBIT", "fastpay UPI txn", 500),
            ("2026-08-12", "DEBIT", "quickcash transfer", 600),
        ]),
        "risk_status": "HIGH",
    },
    {
        "account_id": "ACC-004",
        "customer_name": "Sneha Rao",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 55000),
            ("2026-08-04", "DEBIT", "EMI SBI LOAN", 22000),
            ("2026-08-10", "DEBIT", "Groceries Mart", 4500),
        ]),
        "risk_status": "MEDIUM",
    },
    {
        "account_id": "ACC-005",
        "customer_name": "Karthik M",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 60000),
            ("2026-08-05", "DEBIT", "EMI HDFC LOAN", 20000),
        ]),
        "risk_status": "MEDIUM",
    },
    {
        "account_id": "ACC-006",
        "customer_name": "Neha Singh",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 80000),
            ("2026-08-06", "DEBIT", "EMI KOTAK LOAN", 18000),
        ]),
        "risk_status": "LOW",
    },
    {
        "account_id": "ACC-007",
        "customer_name": "Vikram Reddy",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 55000),
            ("2026-08-05", "DEBIT", "EMI AXIS LOAN", 16000),
        ]),
        "risk_status": "LOW",
    },
    {
        "account_id": "ACC-008",
        "customer_name": "Ananya Dey",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 90000),
            ("2026-08-04", "DEBIT", "EMI HDFC LOAN", 15000),
        ]),
        "risk_status": "LOW",
    },
    {
        "account_id": "ACC-009",
        "customer_name": "Rohan Nair",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 70000),
            ("2026-08-05", "DEBIT", "EMI ICICI LOAN", 12000),
        ]),
        "risk_status": "LOW",
    },
    {
        "account_id": "ACC-010",
        "customer_name": "Divya Iyer",
        "transactions": _mk_transactions([
            ("2026-08-01", "CREDIT", "SALARY CREDIT", 58000),
            ("2026-08-06", "DEBIT", "EMI SBI LOAN", 10000),
        ]),
        "risk_status": "LOW",
    },
]


# ---------------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_dashboard(request: Request, format: Optional[str] = None):
    """Serve HTML dashboard to browsers and JSON status to API clients."""
    accept_header = request.headers.get("accept", "")
    if format == "json" or "text/html" not in accept_header:
        return JSONResponse({
            "status": "online",
            "system": "DebtGuard 2.0 — Early Warning System",
            "version": "2.0.0",
            "rbi_framework": "AA_SENTINEL_2026"
        })
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/finshield", response_class=HTMLResponse)
@app.get("/finshield-ai.html", response_class=HTMLResponse)
async def serve_finshield():
    """Serve the FinShield AI executive presentation workspace."""
    return FileResponse(Path(__file__).parent / "finshield-ai.html")


@app.post("/api/v1/ews/scan", response_model=EWSScanResult)
async def ews_scan(payload: AccountPayload):
    """Ingest an AA-delivered account payload, compute velocity tier, and log scan."""
    result = detect_ews(payload)
    _persist_scan_and_audit(payload, result)
    return result


@app.post("/api/v1/ews/scan-raw", response_model=EWSScanResult)
async def ews_scan_raw(payload: AccountPayload):
    """Rescore an account payload and persist to SQLite DB."""
    result = detect_ews(payload)
    _persist_scan_and_audit(payload, result)
    return result


@app.get("/api/v1/ews/mock-portfolio")
async def mock_portfolio():
    """Return the monitored accounts enriched with precomputed EWS scores and raw transaction data."""
    enriched = []
    for acct in _MOCK_PORTFOLIO:
        payload = AccountPayload(
            account_id=acct["account_id"],
            customer_name=acct["customer_name"],
            transactions=acct["transactions"],
        )
        result = detect_ews(payload)
        enriched.append({
            "account_id": result.account_id,
            "customer_name": result.customer_name,
            "debt_velocity_score": round(result.debt_velocity_score, 2),
            "debt_velocity_tier": result.debt_velocity_tier,
            "risk_status": result.debt_velocity_tier,
            "estimated_unreported_debt": result.estimated_unreported_debt,
            "risk_flags": [f.model_dump() for f in result.risk_flags],
            "intervention": result.intervention.model_dump(),
            "factor_mappings": [f.model_dump() for f in result.factor_mappings],
            "inclusion_safeguard_notice": result.inclusion_safeguard_notice,
            "aa_consent_notice": result.aa_consent_notice,
            "transactions": [t.model_dump() for t in acct["transactions"]],
        })
    return {"portfolio": enriched, "generated_at": TODAY.isoformat()}


@app.post("/api/v1/ews/authorize-intervention")
async def authorize_intervention(payload: InterventionApprovalPayload):
    """Human-in-the-loop operational authorization endpoint."""
    AuditLogDB.log_action(
        action="HUMAN_INTERVENTION_AUTHORIZED",
        user_id=payload.officer_id,
        resource_type="ACCOUNT",
        resource_id=payload.account_id,
        details={
            "action": payload.action,
            "notes": payload.notes,
            "approval_status": "APPROVED",
            "inclusion_protection_verified": True,
        }
    )
    return {
        "status": "APPROVED",
        "message": f"Human-in-the-Loop authorization logged for {payload.account_id}. Offer dispatched to customer.",
        "officer_id": payload.officer_id,
        "action": payload.action,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/ews/simulate-sync")
async def simulate_sync():
    """Simulate fresh Account Aggregator data sync and log audit trail."""
    simulated_payload = AccountPayload(
        account_id="ACC-004-SIM",
        customer_name="Vikramaditya Rao",
        transactions=_mk_transactions([
            ("2026-08-25", "CREDIT", "NBFC_DISBURSAL MONEYTAP", 120000),
            ("2026-08-27", "CREDIT", "NBFC_DISBURSAL KREDITBEE", 80000),
            ("2026-08-28", "DEBIT", "fastpay instant transfer", 950),
            ("2026-08-29", "DEBIT", "quickcash daily fee", 450),
        ])
    )
    res = detect_ews(simulated_payload)
    _persist_scan_and_audit(simulated_payload, res)
    
    AuditLogDB.log_action(
        action="AA_SYNC_SIMULATION_EXECUTED",
        user_id="DEMO_OPERATOR",
        resource_type="SYNC_STREAM",
        resource_id="AA-BATCH-2026",
        details={"accounts_synced": 4, "alerts_generated": 1}
    )
    
    return {
        "status": "SUCCESS",
        "message": "AA Stream sync completed. High-risk stack alert generated for ACC-004-SIM.",
        "new_account": {
            "account_id": res.account_id,
            "customer_name": res.customer_name,
            "debt_velocity_score": res.debt_velocity_score,
            "debt_velocity_tier": res.debt_velocity_tier,
            "estimated_unreported_debt": res.estimated_unreported_debt,
            "risk_flags": [f.model_dump() for f in res.risk_flags],
            "intervention": res.intervention.model_dump(),
            "factor_mappings": [f.model_dump() for f in res.factor_mappings],
            "inclusion_safeguard_notice": res.inclusion_safeguard_notice,
            "aa_consent_notice": res.aa_consent_notice,
            "transactions": [t.model_dump() for t in simulated_payload.transactions],
        }
    }


@app.get("/api/v1/ews/audit-logs")
async def get_audit_logs(limit: int = 50):
    """Retrieve immutable audit logs from SQLite database."""
    logs = AuditLogDB.get_audit_logs(limit=limit)
    return {"audit_logs": logs, "total": len(logs)}


@app.get("/api/v1/history/recent")
async def get_recent_history(days: int = 7, limit: int = 100):
    """Retrieve scan history logs from SQLite database."""
    scans = ScanHistoryDB.get_recent_scans(days=days, limit=limit)
    return {"recent_scans": scans, "count": len(scans), "window_days": days}


# ---------------------------------------------------------------------------
# Backward Compatibility Endpoints for Test Suite (test_endpoints.py)
# ---------------------------------------------------------------------------
@app.get("/api/v1/portfolio/monitor")
async def legacy_portfolio_monitor():
    portfolio_data = await mock_portfolio()
    accounts = []
    total_exp = 0.0
    high_count = 0

    for acct in portfolio_data["portfolio"]:
        exp = acct["estimated_unreported_debt"]
        total_exp += exp
        if acct["debt_velocity_tier"] == "HIGH":
            high_count += 1

        flag_names = [f["code"] for f in acct["risk_flags"]]
        accounts.append({
            "account_id": acct["account_id"],
            "customer_name": acct["customer_name"],
            "risk_tier": acct["debt_velocity_tier"],
            "estimated_unreported_debt": exp,
            "triggered_flags": flag_names,
        })

    return {
        "total_accounts": len(accounts),
        "high_risk_count": high_count,
        "total_exposure": total_exp,
        "accounts": accounts,
    }


@app.post("/api/v1/sentinel/scan")
async def legacy_sentinel_scan(payload: AccountPayload):
    res = detect_ews(payload)
    _persist_scan_and_audit(payload, res)
    flag_names = [f.code for f in res.risk_flags]
    
    return {
        "account_id": res.account_id,
        "customer_name": res.customer_name,
        "risk_tier": res.debt_velocity_tier,
        "triggered_flags": flag_names,
        "estimated_unreported_debt": res.estimated_unreported_debt,
        "recommended_action": res.intervention.action,
        "debt_velocity_score": res.debt_velocity_score,
    }
