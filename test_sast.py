from sast_scanner import run_bandit_scan, check_common_ai_mistakes, get_security_score

# A deliberately bad piece of code with common AI mistakes
bad_code = """
import hashlib

# Hardcoded password - AI commonly does this
password = "admin123"
api_key = "sk-abc123secretkey"

def login(username, user_input):
    # No input validation - AI skips this
    # Weak crypto - AI suggests MD5
    hashed = hashlib.md5(user_input.encode()).hexdigest()
    
    try:
        result = check_database(username, hashed)
    except:
        pass  # AI commonly does this - swallows all errors

def build_query(user_id):
    # SQL injection - AI uses string formatting
    query = "SELECT * FROM users WHERE id = %s" % user_id
    return query
"""

sast_issues = run_bandit_scan(bad_code, "test.py")
ai_issues = check_common_ai_mistakes(bad_code)
score = get_security_score(sast_issues, ai_issues)

print(f"Security Score: {score}/100")
print(f"\nSAST Issues Found: {len(sast_issues)}")
for issue in sast_issues:
    print(f"  - [{issue['severity']}] Line {issue['line']}: {issue['issue']}")

print(f"\nAI-Code Risks Found: {len(ai_issues)}")
for issue in ai_issues:
    print(f"  - [{issue['severity']}] {issue['issue']}")