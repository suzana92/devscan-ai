import os
import time
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
GEN_TIMEOUT = int(os.getenv("OLLAMA_GEN_TIMEOUT", "300"))

_url_cache = {"url": None, "ts": 0.0}
_CACHE_TTL = 600

def _check_url(url):
    try:
        r = requests.get(f"{url}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[OLLAMA ERROR] {url} -> {e}")
        return False

def _candidate_urls():
    urls = []
    env_url = os.getenv("OLLAMA_URL")
    if env_url:
        urls.append(env_url.strip().rstrip("/"))
    for u in [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://ollama:11434",
        "http://host.docker.internal:11434",
    ]:
        if u not in urls:
            urls.append(u)
    return urls

def get_working_ollama_url(force=False):
    now = time.time()
    cached = _url_cache["url"]
    if not force and cached and (now - _url_cache["ts"] < _CACHE_TTL):
        if _check_url(cached):
            return cached
    for url in _candidate_urls():
        if _check_url(url):
            print(f"[OLLAMA OK] {url}")
            _url_cache["url"] = url
            _url_cache["ts"] = now
            return url
    _url_cache["url"] = None
    _url_cache["ts"] = 0.0
    return None

def check_ollama_running(force=False):
    return get_working_ollama_url(force=force) is not None

def reset_ollama_cache():
    _url_cache["url"] = None
    _url_cache["ts"] = 0.0

def _build_prompt(code_content, filename, sast_issues):
    sast_summary = ""
    if sast_issues:
        sast_summary = "\n\nSecurity scanner already found these issues:\n"
        for issue in sast_issues:
            sast_summary += f"- [{issue.get('severity','?')}] Line {issue.get('line','?')}: {issue.get('issue','?')}\n"

    return f"""You are a senior software security engineer. Review this code for REAL, specific issues only.
Do NOT invent issues. Reference exact line numbers from the code below.

File: {filename}

Code:
{code_content}
{sast_summary}

Respond in EXACTLY this format:

PURPOSE: [One sentence]

QUALITY SCORE: [X]/10

AI-GENERATED CODE RISKS:
[List patterns from ChatGPT/Copilot with line numbers. If none: None detected.]

TOP 3 BUGS:
1. [Line X: description]
2. [Line X: description]
3. [Line X: description or No third bug found]

HOW TO FIX THE BIGGEST PROBLEM:
[Corrected code snippet]

OVERALL VERDICT: [Production Ready / Needs Minor Fixes / Needs Major Fixes / Do Not Deploy]"""

def review_with_ollama(code_content, filename, sast_issues):
    working_url = "http://localhost:11434"

    try:
        test = requests.get(f"{working_url}/api/tags", timeout=3)
        print(f"[DEBUG] Connection status: {test.status_code}")
        if test.status_code != 200:
            print("[DEBUG] Connection failed - not 200")
            return None, "failed"
    except Exception as e:
        print(f"[DEBUG] Cannot connect to Ollama: {e}")
        return None, "failed"

    prompt = _build_prompt(code_content, filename, sast_issues)
    print(f"[DEBUG] Prompt built. Length: {len(prompt)}")
    print(f"[DEBUG] Model: {OLLAMA_MODEL}")
    print(f"[DEBUG] Sending to Ollama now...")

    try:
        response = requests.post(
            f"{working_url}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 1200,
                    "num_ctx": 4096,
                },
            },
            timeout=GEN_TIMEOUT,
        )
        print(f"[DEBUG] Ollama response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            print(f"[DEBUG] Result length: {len(result)}")
            print(f"[DEBUG] Result preview: {result[:200]}")
            if result and len(result) > 50:
                return result, "ollama"
            else:
                print("[DEBUG] Result too short or empty")
                return None, "failed"

        print(f"[DEBUG] Bad status: {response.status_code}")
        print(f"[DEBUG] Response body: {response.text[:200]}")
        return None, "failed"

    except requests.Timeout:
        print("[DEBUG] TIMEOUT - took longer than 300 seconds")
        return None, "timeout"
    except Exception as e:
        print(f"[DEBUG] Exception during generate: {e}")
        return None, "failed"

def review_with_gemini(code_content, filename, sast_issues):
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        return "Gemini API key not set.", "error"
    try:
        client = genai.Client(api_key=gemini_key)
        prompt = _build_prompt(code_content, filename, sast_issues)
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt,
        )
        result = response.text.strip()
        if result:
            return result, "gemini"
        return "Gemini returned empty response.", "error"
    except Exception as e:
        return f"Gemini review failed: {str(e)}", "error"

def analyze_file(code_content, filename, sast_issues, use_gemini=False):
    print(f"[DEBUG] analyze_file called for: {filename}")
    review, source = review_with_ollama(code_content, filename, sast_issues)

    if review:
        print(f"[DEBUG] Ollama review SUCCESS for {filename}")
        return review, "🖥️ Local AI (Private — Ollama)"

    print(f"[DEBUG] Ollama failed for {filename}. Source: {source}")

    if use_gemini:
        review, source = review_with_gemini(code_content, filename, sast_issues)
        if source != "error":
            return review, "☁️ Gemini (Cloud — you opted in)"
        return review, "⚠️ Gemini Error"

    return (
        "⚠️ **Local AI (Ollama) is currently offline.**\n\n"
        f"Model expected: `{OLLAMA_MODEL}`\n\n"
        "**Your code was NOT sent anywhere. It stayed on your machine.**\n\n"
        "The SAST Issues and AI-Code Risks tabs below still work.\n\n"
        "**To fix this:**\n"
        "1. Click **Recheck Ollama** in the sidebar\n"
        "2. Wait 30 seconds for model to load\n"
        "3. Click Recheck again\n\n"
        "Or enable **Gemini backup** in the sidebar."
    ), "⚡ SAST Only (Ollama offline)"