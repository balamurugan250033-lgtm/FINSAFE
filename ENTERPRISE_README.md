# DebtGuard 2.0 - Enterprise Edition

**Complete Fintech Risk Intelligence Platform with Advanced Features**

## 🚀 NEW ENTERPRISE FEATURES

### 1. **Advanced Risk Scoring System**
- **4-Tier Risk Classification**: CRITICAL, HIGH, MEDIUM, LOW
- **Composite Risk Score**: 0-100 scale with weighted calculations
- **Dynamic Scoring**: Scores adjust based on rule hit count and severity
- **Rule-Based Detection**: Extensible rule engine with 6 pre-configured rules

### 2. **Configurable Risk Rules** (config.py)
```
✓ R001: Rapid Loan Stacking (NBFC_DISBURSAL)
✓ R002: Shadow Lending Repayment (UPI_SHADOW_REPAYMENT, DAILY_REPAY)
✓ R003: Predatory Lending (MICROFINANCE, QUICK_LOAN, INSTANT_CREDIT)
✓ R004: Circular Lending (LOAN_DISBURSAL + LOAN_REPAYMENT patterns)
✓ R005: Cash Advance Stacking (CASH_ADVANCE, EMERGENCY_LOAN)
✓ R006: Loan Broker Activity (BROKER_FEE, INTERMEDIARY)
```

Each rule is fully configurable:
- Enable/disable per rule
- Adjustable detection windows (days)
- Configurable thresholds
- Custom base risk scores
- Multi-keyword support

### 3. **Persistent Data Layer** (database.py)
SQLite database with complete transaction history:
- **scan_history**: All account scans with raw data
- **alert_logs**: Email/webhook alert tracking
- **webhooks**: Registered webhook endpoints
- **audit_logs**: Complete action audit trail
- **risk_rules**: Rule configuration and updates
- **users**: User accounts with roles

### 4. **Authentication & Authorization**
- **JWT-based Authentication**: Secure token-based API access
- **Role-Based Access Control**: Admin, Analyst, Viewer, API Client roles
- **Token Generation**: `/api/v1/auth/token` endpoint
- **Protected Endpoints**: All admin endpoints require valid JWT

### 5. **Alert System**
- **Email Alerts**: SMTP-based notifications for high-risk accounts
- **Webhook Triggers**: POST events to registered webhooks
- **Configurable Thresholds**: Trigger alerts when risk score ≥ 80
- **Alert Logging**: Complete trail of all alerts sent

### 6. **Webhook Management** (Admin API)
- **Register Webhooks**: POST `/api/v1/admin/webhooks/register`
- **List Webhooks**: GET `/api/v1/admin/webhooks`
- **Delete Webhooks**: DELETE `/api/v1/admin/webhooks/{webhook_id}`
- **Event Types**: Configurable event filtering (high_risk_scan, etc.)

### 7. **Bulk Scanning**
```
POST /api/v1/sentinel/bulk-scan
Scan multiple accounts in a single request
- Batch ID generation
- Critical risk count tracking
- Aggregated exposure calculations
- Comprehensive batch reporting
```

### 8. **Historical Analytics**
- **Scan History**: Retrieve all scans by account ID
- **Recent History**: Get scans from last N days
- **Analytics Reports**: 
  - High-risk percentage
  - Average unreported debt
  - Top triggered flags
  - Risk tier distribution

### 9. **Admin Dashboard Features**
- **Rule Management**: Enable/disable rules, adjust thresholds
- **Webhook Administration**: Register, list, delete webhooks
- **Audit Logs**: Complete activity tracking with timestamps
- **System Status**: Real-time monitoring of operations

### 10. **Enterprise Dashboard (UI)**
Five powerful tabs:

**📊 Dashboard**
- 4 key metrics (Accounts, Critical, Flags, Exposure)
- Risk tier distribution chart (doughnut)
- Risk score trend chart (line)
- Recent scans preview

**📋 Portfolio**
- Full account listing with filtering
- Risk tier visualization
- Interactive risk inspector
- Raw JSON export

**📈 Analytics**
- 7-day risk summary
- Top triggered flags chart
- Risk tier breakdown
- Average debt calculations

**⚙️ Admin**
- Rule configuration panel
- Webhook registration
- Audit log viewer
- Real-time updates

**🚨 Alerts**
- Active high-risk alerts
- Critical account notifications
- Risk score indicators
- Debt exposure summaries

---

## 📁 PROJECT STRUCTURE

```
fintech-wellness/
├── main.py                          # Enterprise FastAPI backend (2.0.0)
├── config.py                        # Risk rules & settings configuration
├── database.py                      # SQLite ORM & persistence layer
├── requirements.txt                 # Python dependencies
├── debtguard.db                     # SQLite database (auto-created)
├── README.md                        # Original documentation
├── ENTERPRISE_README.md             # This file
├── static/
│   └── index.html                   # Advanced enterprise dashboard
└── test_endpoints.py               # API endpoint test suite
```

---

## 🔧 INSTALLATION & SETUP

### Step 1: Create Virtual Environment
```bash
python -m venv venv
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Start Backend
```bash
python main.py
```
Server runs on `http://localhost:8000`

### Step 4: Open Dashboard
```bash
# Option 1: Direct file open
open static/index.html

# Option 2: Via HTTP server
python -m http.server 8080
# Visit: http://localhost:8080/static/index.html
```

### Step 5: Login to Dashboard
- Username: (any value)
- Password: (any value)
- Demo mode accepts all credentials

---

## 🔌 API ENDPOINTS (v1.0)

### System
- `GET /` - Health check & version info
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

### Authentication
- `POST /api/v1/auth/token?username=X&password=Y` - Generate JWT token

### Scanning
- `POST /api/v1/sentinel/scan` - Scan single account
- `POST /api/v1/sentinel/bulk-scan` - Scan multiple accounts
- `GET /api/v1/portfolio/monitor` - Get portfolio with 3 demo accounts

### History & Analytics
- `GET /api/v1/history/account/{account_id}` - Account scan history
- `GET /api/v1/history/recent?days=7` - Recent scans
- `POST /api/v1/analytics/report` - Generate analytics report

### Administration (Auth Required)
- `GET /api/v1/admin/rules` - List all risk rules
- `POST /api/v1/admin/rules/update` - Update rule configuration
- `GET /api/v1/admin/webhooks` - List webhooks
- `POST /api/v1/admin/webhooks/register` - Register webhook
- `DELETE /api/v1/admin/webhooks/{id}` - Delete webhook
- `GET /api/v1/admin/audit-logs` - View audit logs

---

## 🎯 RISK DETECTION RULES

### Rule 1: Rapid Loan Stacking (R001)
- **Keywords**: NBFC_DISBURSAL
- **Window**: 14 days rolling
- **Threshold**: 2 occurrences
- **Risk Score**: 85/100
- **Description**: Detects customers taking multiple loans from NBFCs within short period

### Rule 2: Shadow Lending (R002)
- **Keywords**: UPI_SHADOW_REPAYMENT, DAILY_REPAY
- **Threshold**: 1 occurrence
- **Risk Score**: 90/100
- **Description**: Identifies unregulated lending patterns

### Rule 3: Predatory Lending (R003)
- **Keywords**: MICROFINANCE, QUICK_LOAN, INSTANT_CREDIT
- **Window**: 7 days
- **Threshold**: 3 occurrences
- **Risk Score**: 75/100

### Rule 4: Circular Lending (R004)
- **Keywords**: LOAN_DISBURSAL, LOAN_REPAYMENT
- **Window**: 5 days
- **Risk Score**: 70/100
- **Description**: Debt cycling detection (borrow-lend-repeat)

### Rule 5: Cash Advance Stacking (R005)
- **Keywords**: CASH_ADVANCE, EMERGENCY_LOAN, CASH_CREDIT
- **Window**: 10 days
- **Threshold**: 2 occurrences
- **Risk Score**: 80/100

### Rule 6: Loan Broker Activity (R006)
- **Keywords**: BROKER_FEE, INTERMEDIARY, REFERRAL_COMMISSION
- **Window**: 30 days
- **Risk Score**: 65/100
- **Description**: Detects loan aggregator intermediaries

---

## 🔐 CONFIGURATION (config.py)

### Environment Variables
```bash
export DATABASE_URL="sqlite:///./debtguard.db"
export SECRET_KEY="your-secret-key-change-in-production"
export ALERT_EMAIL="admin@debtguard.fintech"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

### Alert Configuration
```python
ALERT_CONFIG = {
    "email_enabled": True,
    "sms_enabled": False,
    "webhook_enabled": True,
    "high_risk_threshold": 80,
}
```

### SMTP Settings
```python
"smtp_server": "smtp.gmail.com",
"smtp_port": 587,
"smtp_user": os.getenv("SMTP_USER", ""),
"smtp_password": os.getenv("SMTP_PASSWORD", ""),
```

---

## 📊 DATABASE SCHEMA

### scan_history
```sql
id | account_id | customer_name | risk_tier | triggered_flags | 
estimated_unreported_debt | recommended_action | risk_score | 
scan_timestamp | raw_data
```

### alert_logs
```sql
id | scan_id | alert_type | recipient | status | created_at
```

### webhooks
```sql
id | url | event_type | active | created_at
```

### audit_logs
```sql
id | action | user_id | resource_type | resource_id | 
details | created_at
```

### risk_rules
```sql
id | rule_id | name | description | enabled | keywords | 
transaction_type | window_days | threshold_count | 
base_risk_score | created_at | updated_at
```

---

## 🧪 TESTING

### Test Single Account Scan
```bash
python test_endpoints.py
```

### Test with cURL
```bash
# Health check
curl http://localhost:8000/

# Get portfolio
curl http://localhost:8000/api/v1/portfolio/monitor

# Scan single account
curl -X POST http://localhost:8000/api/v1/sentinel/scan \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC-TEST",
    "customer_name": "Test User",
    "transactions": [
      {
        "date": "2024-01-10",
        "type": "CREDIT",
        "desc": "NBFC_DISBURSAL",
        "amount": 15000
      }
    ]
  }'

# Get auth token
curl -X POST "http://localhost:8000/api/v1/auth/token?username=admin&password=admin"

# Get rules (requires auth)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/admin/rules
```

---

## 🚨 ALERT WORKFLOW

1. **Account Scan**: POST `/api/v1/sentinel/scan`
2. **Risk Calculation**: 4-tier scoring system
3. **Threshold Check**: Risk score ≥ 80?
4. **Alert Trigger**: Yes → Send alerts
5. **Email Alert**: SMTP to configured address
6. **Webhook Trigger**: POST to registered webhooks
7. **Audit Log**: Record action in database
8. **Storage**: Save scan to history

---

## 📈 ANALYTICS METRICS

### 7-Day Report Includes:
- Total scans count
- High-risk percentage
- Average unreported debt
- Top 5 triggered flags
- Risk tier distribution
- Timestamp

---

## 🔒 SECURITY BEST PRACTICES

### For Production:
1. **Change SECRET_KEY** in config.py
2. **Restrict CORS** to specific domains
3. **Use HTTPS** with valid certificates
4. **Enable Rate Limiting** for API endpoints
5. **Implement Database Encryption** for sensitive data
6. **Use Environment Variables** for credentials
7. **Enable JWT Expiry** for tokens
8. **Audit All Actions** in database
9. **Use Strong Passwords** for admin accounts
10. **Regular Database Backups** scheduled

### JWT Token Example
```
POST /api/v1/auth/token?username=analyst&password=secure_password

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 30
}

Use:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🐛 TROUBLESHOOTING

### Server Won't Start
```
Error: Address already in use
Solution: Kill process on port 8000
  Windows: taskkill /PID [PID] /F
  Mac/Linux: lsof -ti:8000 | xargs kill -9
```

### Database Lock
```
Error: database is locked
Solution: Remove debtguard.db and restart
  rm debtguard.db
  python main.py
```

### Import Errors
```
Error: No module named 'config'
Solution: Ensure all files are in same directory:
  main.py, config.py, database.py, requirements.txt
```

### Dashboard Won't Load
```
Error: Failed to connect to backend
Solutions:
  1. Verify backend is running on port 8000
  2. Check CORS is enabled (should be by default)
  3. Verify API_BASE_URL in index.html matches backend
```

---

## 📚 DEPENDENCIES

```
fastapi==0.104.1          # Web framework
uvicorn==0.24.0          # ASGI server
pydantic==2.5.0          # Data validation
PyJWT==2.8.0             # JWT tokens
requests==2.31.0         # HTTP client
python-multipart==0.0.6  # Form data parsing
```

---

## 🎓 ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────┐
│         Enterprise Dashboard (UI)            │
│  ┌─────────┬──────────┬────────┬─────┬──────┐
│  │Dashboard│Portfolio │Analytics│Admin│Alerts│
│  └─────────┴──────────┴────────┴─────┴──────┘
└────────────────────│────────────────────────┘
                     │ HTTPS
        ┌────────────┴────────────┐
        │   FastAPI Backend       │
        │  (main.py - Enterprise) │
        │                         │
        │ ┌─────────────────────┐ │
        │ │  Risk Analyzer      │ │
        │ │  (Multi-rule)       │ │
        │ └─────────────────────┘ │
        │ ┌─────────────────────┐ │
        │ │  Auth Manager       │ │
        │ │  (JWT)              │ │
        │ └─────────────────────┘ │
        │ ┌─────────────────────┐ │
        │ │  Alert System       │ │
        │ │  (Email/Webhook)    │ │
        │ └─────────────────────┘ │
        └────────────┬────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    ┌───▼────┐            ┌──────▼─────┐
    │ SQLite │            │ Webhooks &  │
    │Database │            │  Email API  │
    └────────┘            └─────────────┘
```

---

## 🚀 DEPLOYMENT OPTIONS

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "main.py"]
```

### Cloud Platforms
- **AWS EC2**: t3.small instance with 8GB storage
- **Azure App Service**: Python 3.11 runtime
- **Google Cloud Run**: Serverless deployment
- **Heroku**: With PostgreSQL add-on

### Environment Setup
```bash
export DATABASE_URL="postgresql://user:pass@host/db"
export SECRET_KEY="production-secret-key"
export SMTP_USER="alerts@company.com"
export SMTP_PASSWORD="app-specific-password"
```

---

## 📞 SUPPORT & CONTACT

For issues or feature requests:
1. Check Troubleshooting section
2. Review API documentation at `/docs`
3. Check audit logs for error context
4. Review application logs

---

## 📝 VERSION HISTORY

- **v2.0.0** (Current) - Enterprise Edition with all advanced features
- **v1.0.0** - Initial release with basic scanning

---

**Built with ❤️ for Enterprise Fintech Risk Intelligence**
