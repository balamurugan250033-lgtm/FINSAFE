"""
DebtGuard 2.0 - Database Models & ORM Setup
SQLite persistence layer for scans, history, webhooks, and audit logs
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

DB_PATH = Path("debtguard.db")

def init_database():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Scan History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        risk_tier TEXT NOT NULL,
        triggered_flags TEXT,
        estimated_unreported_debt REAL,
        recommended_action TEXT,
        risk_score INTEGER DEFAULT 0,
        scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        raw_data TEXT
    )
    """)
    
    # Alert Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER,
        alert_type TEXT,
        recipient TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scan_id) REFERENCES scan_history(id)
    )
    """)
    
    # Webhooks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webhooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        event_type TEXT,
        active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        user_id TEXT,
        resource_type TEXT,
        resource_id TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Risk Rules Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        enabled BOOLEAN DEFAULT 1,
        keywords TEXT,
        transaction_type TEXT,
        window_days INTEGER,
        threshold_count INTEGER,
        base_risk_score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # User Accounts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        hashed_password TEXT NOT NULL,
        role TEXT DEFAULT 'viewer',
        active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================

class ScanHistoryDB:
    """Database operations for scan history"""
    
    @staticmethod
    def insert_scan(
        account_id: str,
        customer_name: str,
        risk_tier: str,
        triggered_flags: List[str],
        estimated_unreported_debt: float,
        recommended_action: str,
        risk_score: int,
        raw_data: Dict[str, Any]
    ) -> int:
        """Insert a new scan record and return ID"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO scan_history 
        (account_id, customer_name, risk_tier, triggered_flags, 
         estimated_unreported_debt, recommended_action, risk_score, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account_id,
            customer_name,
            risk_tier,
            json.dumps(triggered_flags),
            estimated_unreported_debt,
            recommended_action,
            risk_score,
            json.dumps(raw_data)
        ))
        
        conn.commit()
        scan_id = cursor.lastrowid
        conn.close()
        return scan_id
    
    @staticmethod
    def get_scan_by_id(scan_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific scan by ID"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scan_history WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "account_id": row[1],
            "customer_name": row[2],
            "risk_tier": row[3],
            "triggered_flags": json.loads(row[4]),
            "estimated_unreported_debt": row[5],
            "recommended_action": row[6],
            "risk_score": row[7],
            "scan_timestamp": row[8],
            "raw_data": json.loads(row[9]),
        }
    
    @staticmethod
    def get_scans_by_account(account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve all scans for a specific account"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM scan_history 
        WHERE account_id = ? 
        ORDER BY scan_timestamp DESC 
        LIMIT ?
        """, (account_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "account_id": row[1],
                "customer_name": row[2],
                "risk_tier": row[3],
                "triggered_flags": json.loads(row[4]),
                "estimated_unreported_debt": row[5],
                "recommended_action": row[6],
                "risk_score": row[7],
                "scan_timestamp": row[8],
            }
            for row in rows
        ]
    
    @staticmethod
    def get_recent_scans(days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent scans from the last N days"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute(f"""
        SELECT * FROM scan_history 
        WHERE scan_timestamp >= datetime('now', '-{days} days')
        ORDER BY scan_timestamp DESC 
        LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "account_id": row[1],
                "customer_name": row[2],
                "risk_tier": row[3],
                "triggered_flags": json.loads(row[4]),
                "estimated_unreported_debt": row[5],
                "recommended_action": row[6],
                "risk_score": row[7],
                "scan_timestamp": row[8],
            }
            for row in rows
        ]

class AuditLogDB:
    """Database operations for audit logs"""
    
    @staticmethod
    def log_action(
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an action to audit log"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO audit_logs (action, user_id, resource_type, resource_id, details)
        VALUES (?, ?, ?, ?, ?)
        """, (
            action,
            user_id,
            resource_type,
            resource_id,
            json.dumps(details) if details else None
        ))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit logs"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM audit_logs 
        ORDER BY created_at DESC 
        LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "action": row[1],
                "user_id": row[2],
                "resource_type": row[3],
                "resource_id": row[4],
                "details": json.loads(row[5]) if row[5] else None,
                "created_at": row[6],
            }
            for row in rows
        ]

class WebhookDB:
    """Database operations for webhooks"""
    
    @staticmethod
    def register_webhook(url: str, event_type: str) -> bool:
        """Register a new webhook"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO webhooks (url, event_type)
            VALUES (?, ?)
            """, (url, event_type))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    @staticmethod
    def get_webhooks(active_only: bool = True) -> List[Dict[str, Any]]:
        """Retrieve registered webhooks"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM webhooks WHERE active = 1")
        else:
            cursor.execute("SELECT * FROM webhooks")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "url": row[1],
                "event_type": row[2],
                "active": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]
    
    @staticmethod
    def delete_webhook(webhook_id: int) -> bool:
        """Delete a webhook"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM webhooks WHERE id = ?", (webhook_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

class RuleDB:
    """Database operations for risk rules"""
    
    @staticmethod
    def upsert_rule(rule_data: Dict[str, Any]) -> bool:
        """Insert or update a risk rule"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR REPLACE INTO risk_rules 
        (rule_id, name, description, enabled, keywords, transaction_type, 
         window_days, threshold_count, base_risk_score, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            rule_data.get("rule_id"),
            rule_data.get("name"),
            rule_data.get("description"),
            rule_data.get("enabled", 1),
            json.dumps(rule_data.get("keywords", [])),
            rule_data.get("transaction_type"),
            rule_data.get("window_days"),
            rule_data.get("threshold_count"),
            rule_data.get("base_risk_score"),
        ))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_all_rules(active_only: bool = True) -> List[Dict[str, Any]]:
        """Retrieve all risk rules"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM risk_rules WHERE enabled = 1")
        else:
            cursor.execute("SELECT * FROM risk_rules")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "rule_id": row[1],
                "name": row[2],
                "description": row[3],
                "enabled": row[4],
                "keywords": json.loads(row[5]),
                "transaction_type": row[6],
                "window_days": row[7],
                "threshold_count": row[8],
                "base_risk_score": row[9],
                "updated_at": row[11],
            }
            for row in rows
        ]
