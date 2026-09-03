import requests
import json
import sys

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Testing DebtGuard 2.0 Backend Endpoints")
print("=" * 60)

# Test 1: Health Check
print("\n1. Testing GET / (Health Check)")
response = requests.get(f"{BASE_URL}/")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test 2: Portfolio Monitor
print("\n2. Testing GET /api/v1/portfolio/monitor")
response = requests.get(f"{BASE_URL}/api/v1/portfolio/monitor")
data = response.json()
print(f"Status: {response.status_code}")
print(f"Total Accounts: {data['total_accounts']}")
print(f"High Risk Count: {data['high_risk_count']}")
print(f"Total Exposure: ₹{data['total_exposure']}")
print("\nAccounts:")
for account in data['accounts']:
    print(f"  - {account['account_id']}: {account['customer_name']} | Risk: {account['risk_tier']} | Exposure: ₹{account['estimated_unreported_debt']}")
    if account['triggered_flags']:
        print(f"    Flags: {', '.join(account['triggered_flags'])}")

# Test 3: Sentinel Scan - High Risk (Rapid Loan Stacking)
print("\n3. Testing POST /api/v1/sentinel/scan (High Risk Scenario)")
payload = {
    "account_id": "RISK-TEST-001",
    "customer_name": "High Risk User",
    "transactions": [
        {"date": "2024-01-10", "type": "CREDIT", "desc": "NBFC_DISBURSAL", "amount": 20000},
        {"date": "2024-01-12", "type": "DEBIT", "desc": "Groceries", "amount": 500},
        {"date": "2024-01-20", "type": "CREDIT", "desc": "NBFC_DISBURSAL", "amount": 15000}
    ]
}
response = requests.post(f"{BASE_URL}/api/v1/sentinel/scan", json=payload)
data = response.json()
print(f"Status: {response.status_code}")
print(f"Risk Tier: {data['risk_tier']}")
print(f"Triggered Flags: {', '.join(data['triggered_flags']) if data['triggered_flags'] else 'None'}")
print(f"Unreported Debt: ₹{data['estimated_unreported_debt']}")
print(f"Recommended Action: {data['recommended_action']}")

# Test 4: Sentinel Scan - Low Risk
print("\n4. Testing POST /api/v1/sentinel/scan (Low Risk Scenario)")
payload = {
    "account_id": "SAFE-TEST-001",
    "customer_name": "Safe User",
    "transactions": [
        {"date": "2024-01-15", "type": "CREDIT", "desc": "Salary Deposit", "amount": 50000},
        {"date": "2024-01-16", "type": "DEBIT", "desc": "Electricity Bill", "amount": 1200},
        {"date": "2024-01-20", "type": "DEBIT", "desc": "Grocery Shopping", "amount": 2500}
    ]
}
response = requests.post(f"{BASE_URL}/api/v1/sentinel/scan", json=payload)
data = response.json()
print(f"Status: {response.status_code}")
print(f"Risk Tier: {data['risk_tier']}")
print(f"Triggered Flags: {', '.join(data['triggered_flags']) if data['triggered_flags'] else 'None'}")
print(f"Unreported Debt: ₹{data['estimated_unreported_debt']}")
print(f"Recommended Action: {data['recommended_action']}")

# Test 5: Sentinel Scan - Shadow Lending Risk
print("\n5. Testing POST /api/v1/sentinel/scan (Shadow Lending Risk)")
payload = {
    "account_id": "SHADOW-TEST-001",
    "customer_name": "Shadow Lending Victim",
    "transactions": [
        {"date": "2024-01-15", "type": "CREDIT", "desc": "Cash Transfer", "amount": 8000},
        {"date": "2024-01-18", "type": "DEBIT", "desc": "UPI_SHADOW_REPAYMENT", "amount": 8500},
        {"date": "2024-01-25", "type": "DEBIT", "desc": "DAILY_REPAY", "amount": 6300}
    ]
}
response = requests.post(f"{BASE_URL}/api/v1/sentinel/scan", json=payload)
data = response.json()
print(f"Status: {response.status_code}")
print(f"Risk Tier: {data['risk_tier']}")
print(f"Triggered Flags: {', '.join(data['triggered_flags']) if data['triggered_flags'] else 'None'}")
print(f"Unreported Debt: ₹{data['estimated_unreported_debt']}")
print(f"Recommended Action: {data['recommended_action']}")

print("\n" + "=" * 60)
print("✓ All endpoint tests completed successfully!")
print("=" * 60)
