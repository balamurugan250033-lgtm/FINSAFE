# DebtGuard 2.0 - Continuous Background Sentinel

**Production-Ready Fintech Backend & Dashboard for Real-Time Loan Stacking Detection**

DebtGuard 2.0 is a comprehensive risk intelligence system that scans customer bank account transaction streams in real-time to detect multi-lender loan stacking and unregulated shadow lending exposure before credit bureaus update. Built with FastAPI (Python) and a cybersecurity-themed dark-mode dashboard.

---

## 🎯 System Architecture

### Backend (Python/FastAPI)
- **Framework**: FastAPI with Pydantic v2 for schema validation
- **Risk Engine**: Multi-rule detection system for loan stacking and shadow lending
- **API Design**: RESTful endpoints with comprehensive error handling
- **CORS**: Enabled for all origins for seamless frontend integration

### Frontend (HTML/JS/Tailwind)
- **Dashboard**: Dark-mode cybersecurity UI with Tailwind CSS
- **Real-Time Monitoring**: Portfolio view with risk metrics
- **Risk Inspector**: Interactive account analysis with transaction audit trail
- **JSON Display**: Raw scan data visualization

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- A terminal/command prompt

### Step 1: Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### Step 2: Install Dependencies

```bash
pip install fastapi uvicorn pydantic
```

Or install from a requirements.txt if provided:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Backend Server

```bash
python main.py
```

You should see output similar to:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The backend is now running on `http://localhost:8000`

### Step 4: Open the Dashboard

1. Navigate to the project directory
2. Open `static/index.html` in your web browser
3. Or use a simple HTTP server from the project root:

```bash
# Python 3
python -m http.server 8080

# Then open http://localhost:8080/static/index.html
```

---

## 📊 API Endpoints

### 1. System Health Check
```
GET /
```
Returns system status and metadata.

**Response:**
```json
{
  "status": "operational",
  "service": "DebtGuard 2.0 - Continuous Background Sentinel",
  "version": "1.0.0",
  "capabilities": [...],
  "timestamp": "2024-01-15T10:30:45Z"
}
```

### 2. Sentinel Scan (Single Account)
```
POST /api/v1/sentinel/scan
```
Evaluates a single account's transaction history for risk.

**Request Body:**
```json
{
  "account_id": "ACC-001",
  "customer_name": "Rajesh Kumar",
  "transactions": [
    {
      "date": "2024-01-15",
      "type": "CREDIT",
      "desc": "Salary Credit",
      "amount": 50000.0
    },
    {
      "date": "2024-01-20",
      "type": "DEBIT",
      "desc": "Grocery Purchase",
      "amount": 2500.0
    }
  ]
}
```

**Response:**
```json
{
  "account_id": "ACC-001",
  "customer_name": "Rajesh Kumar",
  "risk_tier": "LOW",
  "triggered_flags": [],
  "estimated_unreported_debt": 0.0,
  "recommended_action": "NONE",
  "scan_timestamp": "2024-01-15T10:32:15Z",
  "transaction_count": 2
}
```

### 3. Portfolio Monitor (Mock Data)
```
GET /api/v1/portfolio/monitor
```
Returns a mock portfolio of 3 evaluated accounts for demonstration.

**Response:**
```json
{
  "total_accounts": 3,
  "high_risk_count": 2,
  "total_exposure": 27000.0,
  "accounts": [
    {
      "account_id": "ACC-001",
      "customer_name": "Rajesh Kumar",
      "risk_tier": "LOW",
      "triggered_flags": [],
      "estimated_unreported_debt": 0.0,
      "recommended_action": "NONE",
      "scan_timestamp": "2024-01-15T10:32:15Z",
      "transaction_count": 4
    },
    ...
  ],
  "portfolio_timestamp": "2024-01-15T10:32:15Z"
}
```

---

## 🔍 Risk Detection Rules

### Rule 1: Rapid Loan Stacking
- **Trigger**: 2 or more transactions with `NBFC_DISBURSAL` in description within a 14-day rolling window
- **Flag**: `RAPID_LOAN_STACKING`
- **Impact**: Sets risk tier to `HIGH` and recommended action to `TRIGGER_COOLING_OFF_ALERT`
- **Debt Calculation**: Sum of all NBFC disbursal amounts

**Example:**
```json
{
  "date": "2024-01-10",
  "type": "CREDIT",
  "desc": "NBFC_DISBURSAL",
  "amount": 15000.0
}
```

### Rule 2: Shadow Lending Detection
- **Trigger**: Any transaction with `UPI_SHADOW_REPAYMENT` or `DAILY_REPAY` in description
- **Flag**: `SHADOW_LENDING_REPAYMENT_DETECTED`
- **Impact**: Sets risk tier to `HIGH` and recommended action to `TRIGGER_COOLING_OFF_ALERT`

**Example:**
```json
{
  "date": "2024-01-18",
  "type": "DEBIT",
  "desc": "UPI_SHADOW_REPAYMENT",
  "amount": 8500.0
}
```

---

## 📋 Portfolio Demo Data

The mock portfolio includes 3 accounts:

1. **ACC-001 - Rajesh Kumar** (LOW Risk)
   - Regular salary deposits and household expenses
   - No flags triggered
   - No unreported debt

2. **ACC-002 - Priya Sharma** (HIGH Risk)
   - Multiple NBFC disbursals within 14 days (Jan 10, Jan 20)
   - Flag: `RAPID_LOAN_STACKING`
   - Exposure: ₹27,000

3. **ACC-003 - Amit Singh** (HIGH Risk)
   - UPI shadow repayment and daily repay patterns
   - Flag: `SHADOW_LENDING_REPAYMENT_DETECTED`
   - Exposure: ₹0 (based on rules)

---

## 🎨 Dashboard Features

### Metrics Panel
- **Monitored Accounts**: Count of active portfolio accounts
- **High-Risk Flags**: Number of accounts with triggered flags
- **Estimated Unreported Debt**: Total detected exposure across portfolio

### Portfolio Monitor (Left Panel)
- Table view of all accounts
- Click any row to inspect account details
- Real-time risk tier indicators
- Exposure amounts for HIGH-risk accounts

### Risk Inspector (Right Panel)
- Detailed account information
- Triggered flags with visual highlighting
- Key metrics (unreported debt, recommended actions)
- Raw JSON scan data for audit trail
- Transaction history view (expandable)

---

## 🔧 Configuration & Customization

### Backend Configuration
Edit `main.py` to customize:

**CORS Settings** (Line ~60):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Server Configuration** (Line ~260):
```python
uvicorn.run(
    app,
    host="0.0.0.0",  # Change for network isolation
    port=8000,
    reload=False  # Set to True for development
)
```

**Risk Rules** (Lines ~95-130):
Modify detection windows and keywords:
```python
RAPID_LOAN_STACKING_WINDOW_DAYS = 14
RAPID_LOAN_STACKING_THRESHOLD = 2
NBFC_DISBURSAL_KEYWORD = "NBFC_DISBURSAL"
SHADOW_REPAYMENT_KEYWORDS = ["UPI_SHADOW_REPAYMENT", "DAILY_REPAY"]
```

### Frontend Customization
Edit `static/index.html`:

**API Endpoint** (Line ~350):
```javascript
const API_BASE_URL = "http://localhost:8000";  // Update for production
```

**Color Scheme** (Lines ~34-42):
```javascript
colors: {
    'neon-blue': '#00d9ff',
    'neon-purple': '#b300ff',
    'neon-red': '#ff0066',
}
```

---

## 🧪 Testing the System

### Test the Backend API
Using cURL or a REST client like Postman:

```bash
# Health check
curl http://localhost:8000/

# Get portfolio
curl http://localhost:8000/api/v1/portfolio/monitor

# Scan a single account
curl -X POST http://localhost:8000/api/v1/sentinel/scan \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "TEST-001",
    "customer_name": "Test User",
    "transactions": [
      {
        "date": "2024-01-10",
        "type": "CREDIT",
        "desc": "NBFC_DISBURSAL",
        "amount": 10000.0
      },
      {
        "date": "2024-01-20",
        "type": "CREDIT",
        "desc": "NBFC_DISBURSAL",
        "amount": 12000.0
      }
    ]
  }'
```

### Test the Dashboard
1. Open `static/index.html` in your browser
2. Verify metrics load correctly
3. Click each account row in the portfolio table
4. Verify Risk Inspector populates with account details

---

## 📁 Project Structure

```
fintech-wellness/
├── main.py                 # FastAPI backend (production-ready)
├── static/
│   └── index.html         # Cybersecurity dashboard UI
└── README.md              # This file
```

---

## 🔐 Security Considerations

### For Production Deployment
1. **CORS**: Restrict `allow_origins` to specific frontend domains
2. **Authentication**: Add API key or OAuth2 authentication
3. **HTTPS**: Use TLS/SSL certificates
4. **Rate Limiting**: Implement request throttling
5. **Data Encryption**: Encrypt sensitive transaction data
6. **Audit Logging**: Log all scans and flag triggers

### Example Production CORS:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

---

## 🐛 Troubleshooting

### Backend Won't Start
```
Error: Address already in use
→ Change port in main.py (line 263) or kill process using port 8000
```

### Dashboard Can't Connect to Backend
```
Error: Failed to load portfolio. Ensure backend is running on :8000
→ Ensure main.py is running
→ Check API_BASE_URL in static/index.html (line 350)
→ Verify CORS is enabled in backend
```

### Python Version Issues
```
Error: No module named 'fastapi'
→ Ensure virtual environment is activated
→ Run: pip install fastapi uvicorn pydantic
```

---

## 📚 Dependencies

- **fastapi** (^0.104.0): Web framework
- **uvicorn** (^0.24.0): ASGI server
- **pydantic** (^2.0.0): Data validation

Install all at once:
```bash
pip install fastapi uvicorn pydantic
```

---

## 📜 API Schema Documentation

The backend includes auto-generated API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Access these in your browser after starting the server for interactive API exploration.

---

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic v2**: https://docs.pydantic.dev/
- **Uvicorn**: https://www.uvicorn.org/
- **Tailwind CSS**: https://tailwindcss.com/

---

## 📝 License

This project is provided as-is for fintech integration and educational purposes.

---

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all dependencies are installed
3. Ensure virtual environment is activated
4. Check that port 8000 is available

---

**Built with ❤️ for Fintech Risk Intelligence**
