import json
import os
from datetime import datetime

ANALYTICS_FILE = "devscan_analytics.json"

def load_analytics():
    """Load existing analytics data from file"""
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    
    # Default empty analytics
    return {
        "total_scans": 0,
        "total_files_analyzed": 0,
        "total_bugs_found": 0,
        "total_security_issues": 0,
        "total_ai_risks_found": 0,
        "scans_history": [],
        "first_scan_date": None,
        "last_scan_date": None
    }


def save_scan_result(repo_name, files_analyzed, bugs_found, security_issues, ai_risks):
    """
    Save results of each scan to build up analytics over time.
    Every time someone runs a scan, we record what was found.
    This builds the dashboard data automatically.
    """
    
    data = load_analytics()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Update totals
    data["total_scans"] += 1
    data["total_files_analyzed"] += files_analyzed
    data["total_bugs_found"] += bugs_found
    data["total_security_issues"] += security_issues
    data["total_ai_risks_found"] += ai_risks
    data["last_scan_date"] = now
    
    if not data["first_scan_date"]:
        data["first_scan_date"] = now
    
    # Add to history
    data["scans_history"].append({
        "date": now,
        "repo": repo_name,
        "files": files_analyzed,
        "bugs": bugs_found,
        "security": security_issues,
        "ai_risks": ai_risks
    })
    
    # Keep only last 50 scans in history
    data["scans_history"] = data["scans_history"][-50:]
    
    # Save back to file
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return data


def calculate_roi(data):
    """
    Calculate money and time saved by using DevScan locally.
    
    This is what makes managers want to keep your tool.
    ROI = Return on Investment = how much value did this give us?
    
    We calculate:
    - Money saved vs using CodeRabbit ($15-29/month)
    - Money saved vs sending code to OpenAI API
    - Developer hours saved by catching bugs early
    """
    
    total_scans = data["total_scans"]
    total_bugs = data["total_bugs_found"]
    total_security = data["total_security_issues"]
    
    # Average cost per 1000 tokens with GPT-4 = ~$0.03
    # Average code file = ~500 tokens
    # We assume each file costs $0.015 if sent to cloud
    estimated_api_cost_saved = data["total_files_analyzed"] * 0.015
    
    # CodeRabbit costs $15/month minimum
    # We estimate months based on scan history
    months_active = max(1, total_scans // 10)
    coderabbit_cost_saved = months_active * 15
    
    # Each bug caught early saves ~2 hours of debugging
    # Average developer rate = $50/hour (conservative)
    hours_saved = total_bugs * 2
    money_from_hours = hours_saved * 50
    
    # Security issues are more expensive — average breach costs $200/incident
    security_savings = total_security * 200
    
    total_saved = estimated_api_cost_saved + coderabbit_cost_saved + money_from_hours + security_savings
    
    return {
        "api_cost_saved": round(estimated_api_cost_saved, 2),
        "coderabbit_cost_saved": round(coderabbit_cost_saved, 2),
        "developer_hours_saved": round(hours_saved, 1),
        "security_savings": round(security_savings, 2),
        "total_saved_usd": round(total_saved, 2)
    }