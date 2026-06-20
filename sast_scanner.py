import subprocess
import json
import os
import tempfile


def run_bandit_scan(code_content, filename):
    """
    Bandit is a free tool that finds security issues in Python code.
    We save the code to a temporary file, run Bandit on it,
    then read the results back.

    Think of it like: send your essay to a grammar checker,
    get back a list of mistakes.
    """

    # Only scan Python files
    if not filename.endswith(".py"):
        return []

    # Create a temporary file to store the code
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False,
        encoding='utf-8'
    ) as tmp:
        tmp.write(code_content)
        tmp_path = tmp.name

    try:
        # Run Bandit on that temporary file
        result = subprocess.run(
            ["bandit", "-f", "json", "-q", tmp_path],
            capture_output=True,
            text=True
        )

        # Parse the JSON results
        if result.stdout:
            data = json.loads(result.stdout)
            issues = []

            for issue in data.get("results", []):
                issues.append({
                    "type": "SAST",
                    "tool": "Bandit",
                    "severity": issue["issue_severity"],
                    "issue": issue["issue_text"],
                    "line": issue["line_number"],
                    "confidence": issue["issue_confidence"]
                })

            return issues
        return []

    except Exception as e:
        return [{"type": "error", "issue": str(e)}]

    finally:
        # Always delete the temporary file
        try:
            os.unlink(tmp_path)
        except:
            pass


def check_common_ai_mistakes(code_content):
    """
    The Copilot Auditor — Detects lazy and dangerous patterns
    that AI tools like ChatGPT and GitHub Copilot commonly introduce.

    Think of this as a police officer specifically trained to catch
    AI-generated mistakes — not just general bugs.
    """

    issues = []
    lines = code_content.split("\n")

    # ---- PATTERN 1: Hardcoded credentials ----
    credential_patterns = [
        ("password =", "Hardcoded password — AI tools commonly hardcode credentials"),
        ("api_key =", "Hardcoded API key — store in environment variables instead"),
        ("secret =", "Hardcoded secret detected"),
        ("token =", "Possible hardcoded token"),
        ("private_key =", "Hardcoded private key — critical security risk"),
        ("aws_access_key", "Hardcoded AWS key — will be scraped by bots within minutes if pushed to GitHub"),
    ]

    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower().strip()
        for pattern, message in credential_patterns:
            if pattern in line_lower and ('"' in line or "'" in line):
                issues.append({
                    "type": "AI-Code Risk",
                    "category": "Hardcoded Credential",
                    "severity": "HIGH",
                    "issue": message,
                    "line": line_num,
                    "confidence": "HIGH"
                })

    # ---- PATTERN 2: Generic AI variable names ----
    lazy_names = [
        "data", "res", "result", "temp", "tmp", "obj",
        "val", "var", "info", "stuff", "thing", "foo", "bar"
    ]

    lazy_found = []
    for line_num, line in enumerate(lines, 1):
        words = line.replace("=", " ").replace("(", " ").replace(")", " ").split()
        for word in words:
            clean_word = word.strip().lower()
            if clean_word in lazy_names:
                if clean_word not in lazy_found:
                    lazy_found.append(clean_word)

    if len(lazy_found) >= 2:
        issues.append({
            "type": "AI-Code Risk",
            "category": "Lazy AI Variable Names",
            "severity": "LOW",
            "issue": f"Generic variable names detected: {', '.join(lazy_found[:5])} — common sign of AI-generated code. Use descriptive names.",
            "line": 0,
            "confidence": "MEDIUM"
        })

    # ---- PATTERN 3: Missing error handling ----
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped in ["except:", "except Exception:", "except Exception as e:"]:
            next_lines = [l.strip() for l in lines[line_num:line_num+3] if l.strip()]
            if next_lines and next_lines[0] == "pass":
                issues.append({
                    "type": "AI-Code Risk",
                    "category": "Silent Error Swallowing",
                    "severity": "HIGH",
                    "issue": f"Line {line_num}: bare except/pass found — AI commonly suppresses all errors this way. Your app will fail silently. Always log the error at minimum.",
                    "line": line_num,
                    "confidence": "HIGH"
                })

    # ---- PATTERN 4: Hallucinated libraries ----
    import_lines = [l.strip() for l in lines if l.strip().startswith("import ") or l.strip().startswith("from ")]

    hallucinated = [
        ("import jwt_extended", "jwt_extended doesn't exist — AI hallucination. Use: flask-jwt-extended"),
        ("from flask.ext", "flask.ext is deprecated since 2016 — AI trained on old data. Use direct imports"),
        ("import sklearn.cross_validation", "cross_validation removed in 2017 — AI hallucination. Use: sklearn.model_selection"),
        ("from tensorflow.contrib", "tensorflow.contrib removed in TF2 — AI trained on old code"),
        ("import web3.auto", "web3.auto is deprecated — AI hallucination"),
    ]

    for import_line in import_lines:
        for pattern, message in hallucinated:
            if pattern in import_line:
                issues.append({
                    "type": "AI-Code Risk",
                    "category": "Hallucinated Library",
                    "severity": "HIGH",
                    "issue": message,
                    "line": 0,
                    "confidence": "HIGH"
                })

    # ---- PATTERN 5: SQL Injection ----
    if ("SELECT" in code_content.upper() or "INSERT" in code_content.upper()) and "%" in code_content:
        issues.append({
            "type": "AI-Code Risk",
            "category": "SQL Injection Risk",
            "severity": "HIGH",
            "issue": "SQL query built with string formatting — AI tools do this constantly. Use parameterized queries instead.",
            "line": 0,
            "confidence": "HIGH"
        })

    # ---- PATTERN 6: Weak cryptography ----
    if "md5" in code_content.lower():
        issues.append({
            "type": "AI-Code Risk",
            "category": "Weak Cryptography",
            "severity": "HIGH",
            "issue": "MD5 detected — broken since 2004. AI suggests this constantly. Use SHA-256 or bcrypt for passwords.",
            "line": 0,
            "confidence": "HIGH"
        })

    if "sha1" in code_content.lower():
        issues.append({
            "type": "AI-Code Risk",
            "category": "Weak Cryptography",
            "severity": "HIGH",
            "issue": "SHA1 detected — deprecated for security use. AI trained on old code suggests this. Use SHA-256 minimum.",
            "line": 0,
            "confidence": "HIGH"
        })

    # ---- PATTERN 7: No input validation ----
    has_user_input = any(x in code_content for x in ["input(", "request.args", "request.form", "request.json", "request.data"])
    has_validation = any(x in code_content.lower() for x in ["validate", "sanitize", "isinstance", "len(", "strip()"])

    if has_user_input and not has_validation:
        issues.append({
            "type": "AI-Code Risk",
            "category": "Missing Input Validation",
            "severity": "MEDIUM",
            "issue": "User input found but no validation detected — AI skips this step constantly. Always validate and sanitize user input.",
            "line": 0,
            "confidence": "MEDIUM"
        })

    # ---- PATTERN 8: Debug code left in ----
    debug_patterns = ["print(", "console.log(", "debugger;", "breakpoint()"]
    debug_found = []

    for line_num, line in enumerate(lines, 1):
        for pattern in debug_patterns:
            if pattern in line and not line.strip().startswith("#"):
                debug_found.append(line_num)

    if len(debug_found) > 3:
        issues.append({
            "type": "AI-Code Risk",
            "category": "Debug Code in Production",
            "severity": "LOW",
            "issue": f"Found {len(debug_found)} debug print/log statements (lines: {debug_found[:5]}). AI leaves these everywhere. Remove before production.",
            "line": debug_found[0],
            "confidence": "HIGH"
        })

    return issues


def get_security_score(sast_issues, ai_issues):
    """
    Calculate a security score based on issues found.

    Start at 100.
    Deduct points for each problem found.
    More serious problems = more points deducted.
    """

    score = 100

    for issue in sast_issues + ai_issues:
        severity = issue.get("severity", "LOW")
        if severity == "HIGH":
            score -= 15
        elif severity == "MEDIUM":
            score -= 8
        elif severity == "LOW":
            score -= 3

    return max(0, score)


def calculate_deterministic_quality_score(code_content, filename, sast_issues, ai_issues):
    """
    Calculate a consistent quality score based on measurable facts.
    Same code = same score. Every time. No AI randomness.

    Start at 10/10.
    Deduct points for each real problem found.
    """

    score = 10.0
    lines = code_content.split("\n")

    # Deduct for HIGH severity SAST issues
    high_sast = [i for i in sast_issues if i.get("severity") == "HIGH"]
    score -= min(len(high_sast) * 1.0, 3.0)

    # Deduct for MEDIUM severity SAST issues
    med_sast = [i for i in sast_issues if i.get("severity") == "MEDIUM"]
    score -= min(len(med_sast) * 0.5, 2.0)

    # Deduct for HIGH AI-code risks
    high_ai = [i for i in ai_issues if i.get("severity") == "HIGH"]
    score -= min(len(high_ai) * 0.8, 2.5)

    # Deduct for MEDIUM AI-code risks
    med_ai = [i for i in ai_issues if i.get("severity") == "MEDIUM"]
    score -= min(len(med_ai) * 0.4, 1.5)

    # Deduct for debug prints — always bad in production
    print_count = code_content.count("print(")
    if print_count > 0:
        score -= min(print_count * 0.2, 1.5)

    # Deduct for unused variable patterns
    lazy_assignments = 0
    for line in lines:
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            var_name = stripped.split("=")[0].strip().lower()
            if var_name in ["temp", "tmp", "data", "res", "result", "val", "obj"]:
                lazy_assignments += 1
    score -= min(lazy_assignments * 0.2, 0.8)

    # Deduct for missing docstrings
    func_count = len([l for l in lines if "def " in l])
    docstring_count = code_content.count('"""') // 2 + code_content.count("'''") // 2
    if func_count > 2 and docstring_count == 0:
        score -= 0.5

    # Deduct for very long file with no structure
    total_lines = len([l for l in lines if l.strip()])
    if total_lines > 200 and func_count < 3:
        score -= 0.5

    # Bonus for having tests
    if "unittest" in code_content or "pytest" in code_content:
        score = min(score + 0.3, 10.0)

    # Bonus for having docstrings
    if docstring_count > 2:
        score = min(score + 0.2, 10.0)

    return round(max(1.0, min(10.0, score)), 1)