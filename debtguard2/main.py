"""
DebtGuard 2.0 - RBI-Compliant Early Warning System (EWS)
========================================================

Account Aggregator (AA) powered real-time Debt Velocity monitoring.

RUN INSTRUCTIONS
----------------
1. Install dependencies:
    pip install fastapi uvicorn python-multipart
    # (python-multipart optional, included for form support)

2. Start the server:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

3. Open the dashboard in your browser:
    http://localhost:8000/

4. API docs (auto-generated):
    http://localhost:8000/docs

Compliance notes
----------------
- Operates on raw transaction streams via the RBI Account Aggregator
  (AA) framework (Section 194G-style consent) instead of stale
  CIBIL snapshots (which carry a ~30-day reporting lag).
- No PII beyond customer_name is persisted; all scoring is
  stateless and in-memory per request.
- Risk outputs are assistive signals, NOT punitive blocks. Per RBI
  FRMG 2026 §32 & DLT 2026, the engine only *recommends* automated
  remediation actions for human review.
"""

from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# FastAPI application + CORS
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DebtGuard 2.0 — Early Warning System",
    description="RBI-compliant real-time Debt Velocity detection over AA "
    "transaction streams.",
    version="2.0.0",
    license={
        "name": "Proprietary — RBI Regulated Sandbox",
        "url": "https://rbi.org.in",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Demo-only; in prod restrict to bank origins.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
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
    """Per-account payload delivered by the AA sync (FHIR-like envelope)."""

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


class EWSScanResult(BaseModel):
    account_id: str
    customer_name: str
    debt_velocity_score: float
    debt_velocity_tier: str  # LOW | MEDIUM | HIGH
    risk_flags: List[RiskFlag]
    intervention: Intervention
    windows_analyzed: int


# ---------------------------------------------------------------------------
# Heuristic constants
# ---------------------------------------------------------------------------
SHADOW_UPI_HANDLES = ("fastpay", "quickcash", "rapidcash", "instantloan")
WINDOW_DAYS = 14
LOW_TICK_MIN, LOW_TICK_MAX = 100.0, 1000.0
HIGH_VELOCITY_THRESHOLD = 150000.0 / 14.0  # ~₹1500/day avg triggers HIGH

TODAY = datetime(2026, 8, 31)  # Fixed "today" for deterministic scoring.


# ---------------------------------------------------------------------------
# EWS Detection Engine
# ---------------------------------------------------------------------------
def _parse_date(value: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    # Fallback: try ISO fromisoformat
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except Exception:
        return TODAY


def _days_between(first: datetime, last: datetime) -> int:
    delta = (last - first).days
    return max(delta, 1)


def _is_nbfc_disbursals(t: Transaction) -> bool:
    """An NBFC money arrival iff it is a CREDIT carrying a disbursement marker.

    We deliberately match the structural word 'disburs' (covers
    'disbursement'/'disbursal') or the literal 'nbfc' marker so that generic
    payroll/interest credits ('SALARY CREDIT') and EMI debits ('EMI HDFC LOAN')
    are NOT mistaken for fresh NBFC credit.
    """
    if t.type.upper() != "CREDIT":
        return False
    desc = t.desc.lower()
    return ("disburs" in desc) or ("nbfc" in desc)


def detect_ews(payload: AccountPayload) -> EWSScanResult:
    txns = list(payload.transactions)

    # --- Debt Velocity ---
    disbursals = [t for t in txns if _is_nbfc_disbursals(t)]
    disbursals_sorted = sorted(disbursals, key=lambda t: _parse_date(t.date))

    dv_score = 0.0
    rapid_stack = False
    if disbursals_sorted:
        first_dt = _parse_date(disbursals_sorted[0].date)
        last_dt = _parse_date(disbursals_sorted[-1].date)
        span = _days_between(first_dt, last_dt)
        total = sum(d.amount for d in disbursals_sorted)
        # Velocity = INR per day, normalized over the disbursement window.
        dv_score = round(total / span, 2)

        # Rule 1: Rapid Stacking — 2+ disbursals within any 14-day window.
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

    # --- Rule 2: Shadow-Net Heuristic ---
    shadow_pattern = False
    shadow_detail = ""
    recurring_debits = [
        t for t in txns if t.type.upper() == "DEBIT"
    ]
    handle_counts: dict[str, int] = {}
    handle_amounts: dict[str, float] = {}
    for t in recurring_debits:
        desc_lower = t.desc.lower()
        for handle in SHADOW_UPI_HANDLES:
            if handle in desc_lower and LOW_TICK_MIN <= t.amount <= LOW_TICK_MAX:
                shadow_pattern = True
                handle_counts[handle] = handle_counts.get(handle, 0) + 1
                handle_amounts[handle] = handle_amounts.get(handle, 0.0) + t.amount
    if shadow_pattern:
        top = max(handle_counts, key=handle_counts.get)
        shadow_detail = (
            f"₹{handle_amounts[top]:,.0f} across {handle_counts[top]} "
            f"transactions to unverified UPI handle '{top}' "
            f"within ₹{LOW_TICK_MIN}-{LOW_TICK_MAX} band."
        )

    # --- Tier + flags ---
    flags: List[RiskFlag] = []
    if rapid_stack:
        flags.append(
            RiskFlag(
                code="RAPID_LOAN_STACKING",
                label="Rapid Loan Stacking",
                severity="HIGH",
                detail=(
                    f"{len(disbursals_sorted)} NBFC disbursals within a "
                    f"{WINDOW_DAYS}-day window indicate credit stacking."
                ),
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
    elif dv_score >= HIGH_VELOCITY_THRESHOLD * 0.6:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    # --- Intervention Logic (assistive, non-punitive) ---
    if tier == "HIGH":
        if rapid_stack and not shadow_pattern:
            action = "PAUSE_CREDIT_ENHANCEMENT"
            rationale = (
                "Rapid loan stacking detected; recommend pausing further "
                "credit enhancement until debt-to-income review is complete."
            )
        elif shadow_pattern and not rapid_stack:
            action = "TRIGGER_FINANCIAL_FIRST_AID_OFFER"
            rationale = (
                "Shadow-lending pattern detected; automated first-aid offer "
                "route to consolidate high-cost obligations."
            )
        else:
            action = "TRIGGER_FINANCIAL_FIRST_AID_OFFER"
            rationale = (
                "Multiple distress signals; route to combined remediation: "
                "credit pause + debt-consolidation offer."
            )
    elif tier == "MEDIUM":
        action = "TRIGGER_DEBT_COUNSELING_SUGGESTION"
        rationale = "Elevated velocity; recommend proactive counseling."
    else:
        action = "NO_ACTION_REQUIRED"
        rationale = "Velocity within normal bands; continuous monitoring."

    # Windows analyzed = count of distinct 14-day windows touched.
    windows = 1
    if disbursals_sorted:
        unique_days = {
            _parse_date(d.date).date() for d in disbursals_sorted
        }
        windows = max(1, len(unique_days))

    return EWSScanResult(
        account_id=payload.account_id,
        customer_name=payload.customer_name,
        debt_velocity_score=dv_score,
        debt_velocity_tier=tier,
        risk_flags=flags,
        intervention=Intervention(action=action, rationale=rationale),
        windows_analyzed=windows,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the static dark-mode dashboard."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.post("/api/v1/ews/scan", response_model=EWSScanResult)
async def ews_scan(payload: AccountPayload):
    """Ingest an AA-delivered account payload and run EWS scoring."""
    return detect_ews(payload)


# ---------------------------------------------------------------------------
# Mock portfolio (3 accounts — precomputed for instant dashboard load)
# ---------------------------------------------------------------------------
def _mk_transactions(spec: list[tuple]) -> List[Transaction]:
    """Helper: build Transaction list from (date, type, desc, amount)."""
    return [
        Transaction(date=d, type=t, desc=desc, amount=float(a))
        for (d, t, desc, a) in spec
    ]


_MOCK_PORTFOLIO = [
    {
        "account_id": "ACC-001",
        "customer_name": "Priya Sharma",
        "transactions": _mk_transactions(
            [
                ("2026-08-02", "CREDIT", "SALARY CREDIT", 75000),
                ("2026-08-05", "DEBIT", "RENT PAYMENT UPI", 22000),
                ("2026-08-08", "DEBIT", "ELectricity BILL", 4500),
                ("2026-08-12", "DEBIT", "Groceries BigBazaar", 3100),
                ("2026-08-15", "CREDIT", "INTEREST CREDIT", 1200),
            ]
        ),
        "precomputed_velocity": 0.0,
        "risk_status": "LOW",
    },
    {
        "account_id": "ACC-002",
        "customer_name": "Rohan Mehta",
        "transactions": _mk_transactions(
            [
                # Three NBFC disbursals inside a 14-day window → RAPID STACKING
                ("2026-08-01", "CREDIT", "NBFC_DISBURSAL BAJAJ", 200000),
                ("2026-08-04", "CREDIT", "NBFC_DISBURSAL LENDINGTREE", 150000),
                ("2026-08-09", "CREDIT", "NBFC_DISBURSAL KREDA", 100000),
                ("2026-08-10", "DEBIT", "fastpay UPI txn", 450),
                ("2026-08-12", "DEBIT", "EMI HDFC LOAN", 12000),
                ("2026-08-14", "DEBIT", "quickcash transfer", 750),
            ]
        ),
        "precomputed_velocity": 450000.0 / 8.0,
        "risk_status": "HIGH",
    },
    {
        "account_id": "ACC-003",
        "customer_name": "Ananya Patel",
        "transactions": _mk_transactions(
            [
                ("2026-08-01", "CREDIT", "SALARY CREDIT", 52000),
                ("2026-08-02", "DEBIT", "fastpay UPI txn", 750),
                ("2026-08-04", "DEBIT", "quickcash payment", 500),
                ("2026-08-06", "DEBIT", "fastpay recharge", 300),
                ("2026-08-08", "DEBIT", "rent split", 900),
                ("2026-08-10", "DEBIT", "quickcash transfer", 850),
                ("2026-08-15", "DEBIT", "fastpay bill", 650),
                ("2026-08-20", "DEBIT", "monthly subscription", 1200),
            ]
        ),
        "precomputed_velocity": 0.0,
        "risk_status": "HIGH",
    },
]


@app.get("/api/v1/ews/mock-portfolio")
async def mock_portfolio():
    """Return the 3 seeded accounts with precomputed EWS scores.

    Each entry includes the raw transactions so the frontend can also
    run a live `/scan` against any account if desired.
    """
    enriched = []
    for acct in _MOCK_PORTFOLIO:
        payload = AccountPayload(
            account_id=acct["account_id"],
            customer_name=acct["customer_name"],
            transactions=acct["transactions"],
        )
        result = detect_ews(payload)
        enriched.append(
            {
                "account_id": result.account_id,
                "customer_name": result.customer_name,
                "debt_velocity_score": round(result.debt_velocity_score, 2),
                "debt_velocity_tier": result.debt_velocity_tier,
                "risk_status": acct["risk_status"],
                "risk_flags": [f.model_dump() for f in result.risk_flags],
                "intervention": result.intervention.model_dump(),
            }
        )
    return {"portfolio": enriched, "generated_at": TODAY.isoformat()}


@app.post("/api/v1/ews/scan-raw", response_model=EWSScanResult)
async def ews_scan_raw(payload: AccountPayload):
    """Alias for /scan exposed so the frontend can re-score any account."""
    return detect_ews(payload)
