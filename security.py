"""
security.py — Input sanitization, rate limiting, prompt injection protection.
Rate limiter uses a JSON file so it survives Streamlit reruns.
"""

import hashlib
import time
import re
import json
import os
from pathlib import Path

RATE_LIMIT_FILE = Path("devscan_ratelimit.json")


# ---------------------------------------------------------------------------
# Rate limiter — persists across Streamlit reruns
# ---------------------------------------------------------------------------
def _load_rate_data():
    if RATE_LIMIT_FILE.exists():
        try:
            return json.loads(RATE_LIMIT_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_rate_data(data):
    RATE_LIMIT_FILE.write_text(json.dumps(data))


def rate_limit_check(session_id, max_requests=10, window_seconds=3600):
    """
    Returns True if allowed, False if rate limited.
    Uses file storage so limits survive page reruns.
    session_id: unique per user session.
    """
    now = time.time()
    key  = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    data = _load_rate_data()

    if key not in data:
        data[key] = []

    # Remove entries outside the window
    data[key] = [t for t in data[key] if now - t < window_seconds]

    if len(data[key]) >= max_requests:
        _save_rate_data(data)
        return False

    data[key].append(now)
    _save_rate_data(data)
    return True


# ---------------------------------------------------------------------------
# URL sanitization
# ---------------------------------------------------------------------------
def sanitize_github_url(url):
    """
    Validate and clean a GitHub URL.
    Blocks path traversal, non-GitHub URLs, and malformed input.
    Returns (clean_url, error_message).
    """
    if not url or not url.strip():
        return None, "Please enter a GitHub repository URL."

    url = url.strip().rstrip("/")

    if len(url) > 300:
        return None, "URL is too long."

    if not url.startswith("https://github.com/"):
        return None, "Must be a valid https://github.com/ URL."

    if ".." in url or "~" in url:
        return None, "Invalid URL — path traversal detected."

    # Strip query params and fragments
    url = url.split("?")[0].split("#")[0]

    pattern = r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$'
    if not re.match(pattern, url):
        return None, "Invalid GitHub URL format. Use: https://github.com/owner/repo"

    return url, None


# ---------------------------------------------------------------------------
# API key sanitization
# ---------------------------------------------------------------------------
def sanitize_api_key(key, key_type="API"):
    """Validate that an API key looks legitimate."""
    if not key:
        return None, f"{key_type} key is empty."

    key = key.strip()
    clean_key = re.sub(r'[^a-zA-Z0-9\-_.]', '', key)

    if len(clean_key) < 10:
        return None, f"{key_type} key is too short."

    if len(clean_key) > 500:
        return None, f"{key_type} key is too long."

    return clean_key, None


# ---------------------------------------------------------------------------
# Code sanitization for AI prompts
# ---------------------------------------------------------------------------
INJECTION_PATTERNS = [
    "IGNORE ALL PREVIOUS",
    "ignore previous instructions",
    "you are now",
    "forget your instructions",
    "new instructions:",
    "system prompt",
    "jailbreak",
    "DAN mode",
]

def sanitize_code_for_ai(code_content, max_chars=6000):
    """
    Prepare code for AI prompt.
    - Limit length (not too aggressive — 6000 chars covers most files)
    - Flag prompt injection attempts
    """
    if not code_content:
        return ""

    code_content = code_content[:max_chars]

    injection_found = False
    for pattern in INJECTION_PATTERNS:
        if pattern.lower() in code_content.lower():
            injection_found = True
            code_content = re.sub(
                re.escape(pattern), "[FILTERED]", code_content, flags=re.IGNORECASE
            )

    if injection_found:
        code_content = "# NOTE: Prompt injection attempt filtered from this code.\n\n" + code_content

    return code_content


# ---------------------------------------------------------------------------
# Request ID
# ---------------------------------------------------------------------------
def generate_request_id():
    """Create a unique ID for each analysis request."""
    timestamp = str(time.time()).encode()
    return hashlib.sha256(timestamp).hexdigest()[:12]