"""
github_reader.py — Reads public GitHub repositories.
Handles missing tokens gracefully (goes unauthenticated, not broken).
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

CODE_EXTENSIONS = [
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rb", ".php",
    ".cs", ".cpp", ".c", ".rs",
    ".swift", ".kt", ".sh",
]

SKIP_DIRS   = {"node_modules", ".git", "vendor", "dist", "build", "__pycache__", ".venv", "venv"}
SKIP_FILES  = {"package-lock.json", "yarn.lock", "poetry.lock"}


def _get_headers():
    """Build headers — include token only if it exists and is non-empty."""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    return {"Accept": "application/vnd.github+json"}


def get_repo_info(owner, repo, token=None):
    """Get basic info about a repository."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=_get_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return None
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            raise Exception(f"GitHub rate limit hit (remaining: {remaining}). Add GITHUB_TOKEN to .env")
        return None
    except Exception as e:
        raise e


def get_repo_files(owner, repo, token=None, path="", depth=0):
    """
    Recursively get all code files from a repository.
    Skips known junk directories to stay fast and focused.
    """
    if depth > 3:
        return []

    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers=_get_headers(),
            timeout=10
        )
        if response.status_code != 200:
            return []
    except Exception:
        return []

    items = response.json()
    if not isinstance(items, list):
        return []

    code_files = []

    for item in items:
        if not isinstance(item, dict):
            continue

        name = item.get("name", "")

        # Skip known junk directories
        if item["type"] == "dir":
            if name in SKIP_DIRS or name.startswith("."):
                continue
            sub_files = get_repo_files(owner, repo, token, item["path"], depth + 1)
            code_files.extend(sub_files)

        elif item["type"] == "file":
            if name in SKIP_FILES:
                continue
            if any(name.endswith(ext) for ext in CODE_EXTENSIONS):
                # Skip very large files (> 100KB)
                if item.get("size", 0) < 100000:
                    code_files.append(item)

    return code_files


def download_file(download_url):
    """Download the actual code content of a file."""
    if not download_url:
        return None
    try:
        response = requests.get(download_url, timeout=15)
        if response.status_code == 200:
            return response.text
    except Exception:
        pass
    return None


def parse_github_url(url):
    """
    Extract owner and repo from a GitHub URL.
    https://github.com/facebook/react → ("facebook", "react")
    """
    url = url.strip().rstrip("/")
    url = url.replace("https://github.com/", "").replace("http://github.com/", "")
    url = url.split("?")[0].split("#")[0]
    parts = [p for p in url.split("/") if p]
    if len(parts) >= 2:
        return parts[0], parts[1].rstrip(".git")
    return None, None