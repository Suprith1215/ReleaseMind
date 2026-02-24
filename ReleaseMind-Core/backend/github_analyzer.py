"""
ReleaseMind — GitHub Analyzer (Phase 1)
Fetches real commit/PR data and maps changed files to services.
"""

import os
import re
from datetime import datetime, timezone
from collections import Counter
from typing import Optional

import requests

from config_loader import load_config

cfg = load_config()
_github_cfg = cfg.get("github", {})
_service_map = cfg.get("service_prefix_map", {})

BASE_URL = _github_cfg.get("base_url", "https://api.github.com")
COMMITS_PER_PAGE = _github_cfg.get("commits_per_page", 10)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _map_file_to_service(filename: str) -> str:
    """Return the service name that owns a changed file path."""
    for service, prefixes in _service_map.items():
        if service == "default":
            continue
        if isinstance(prefixes, list):
            for prefix in prefixes:
                if filename.startswith(prefix):
                    return service
        elif isinstance(prefixes, str) and filename.startswith(prefixes):
            return service
    return _service_map.get("default", "unknown")


def _classify_commit_intent(message: str) -> str:
    """
    Lightweight NLP commit classifier.
    Falls back gracefully if LLM is unavailable.
    """
    message_lower = message.lower()
    patterns = {
        "hotfix":        r"\b(hotfix|critical fix|patch|urgent|emergency)\b",
        "breaking_change": r"\b(breaking|break|incompatible|major bump)\b",
        "refactor":      r"\b(refactor|cleanup|reorganize|restructure|rename)\b",
        "experiment":    r"\b(experiment|wip|spike|poc|try|prototype)\b",
        "feature":       r"\b(feat|feature|add|new|implement|introduce)\b",
    }
    for intent, pattern in patterns.items():
        if re.search(pattern, message_lower):
            return intent
    return "unknown"


def _author_commit_frequency(owner: str, repo: str, author: str) -> int:
    """Count how many recent commits the author has on main branch."""
    try:
        url = f"{BASE_URL}/repos/{owner}/{repo}/commits"
        params = {"author": author, "per_page": 30}
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if resp.status_code == 200:
            return len(resp.json())
    except Exception:
        pass
    return 0


def _developer_experience_score(commit_count: int) -> float:
    """
    Normalise a developer's commit count to a 0.0–1.0 experience score.
    0–5 commits  → new   (0.0–0.3)
    6–20 commits → mid   (0.3–0.7)
    21+          → senior (0.7–1.0)
    """
    if commit_count >= 30:
        return 1.0
    return min(round(commit_count / 30, 2), 1.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_repo(
    owner: str,
    repo: str,
    branch: str = "main",
    github_token: Optional[str] = None
) -> dict:
    """
    Fetch the latest commit on `branch`, extract code metrics,
    and return a structured analysis dict.

    Returns:
        {
          "files_changed": int,
          "lines_added": int,
          "lines_deleted": int,
          "developer_experience_score": float,
          "affected_services": list[str],
          "commit_type_detected": str,
          "author": str,
          "commit_sha": str,
          "commit_message": str,
          "commit_frequency": int,
          "pr_count_open": int,
          "error": str | None
        }
    """

    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token

    result = {
        "files_changed": 0,
        "lines_added": 0,
        "lines_deleted": 0,
        "developer_experience_score": 0.5,
        "affected_services": [],
        "commit_type_detected": "unknown",
        "author": "unknown",
        "commit_sha": "",
        "commit_message": "",
        "commit_frequency": 0,
        "pr_count_open": 0,
        "error": None
    }

    try:
        # ---- 1. Fetch latest commit on branch ----
        commits_url = f"{BASE_URL}/repos/{owner}/{repo}/commits"
        params = {"sha": branch, "per_page": 1}
        resp = requests.get(commits_url, headers=_headers(), params=params, timeout=10)

        if resp.status_code == 401:
            result["error"] = "GitHub token missing or invalid."
            return result
        if resp.status_code == 404:
            result["error"] = f"Repository '{owner}/{repo}' not found or is private."
            return result
        if resp.status_code != 200:
            result["error"] = f"GitHub API error: {resp.status_code}"
            return result

        commits = resp.json()
        if not commits:
            result["error"] = "No commits found on this branch."
            return result

        commit = commits[0]
        sha = commit["sha"]
        author = (commit.get("commit", {})
                       .get("author", {})
                       .get("name", "unknown"))
        message = (commit.get("commit", {})
                        .get("message", "")
                        .split("\n")[0])  # first line only

        result["commit_sha"] = sha
        result["author"] = author
        result["commit_message"] = message
        result["commit_type_detected"] = _classify_commit_intent(message)

        # ---- 2. Fetch commit detail (files changed) ----
        detail_url = f"{BASE_URL}/repos/{owner}/{repo}/commits/{sha}"
        detail_resp = requests.get(detail_url, headers=_headers(), timeout=10)

        if detail_resp.status_code == 200:
            detail = detail_resp.json()
            stats = detail.get("stats", {})
            result["lines_added"]   = stats.get("additions", 0)
            result["lines_deleted"] = stats.get("deletions",  0)

            files = detail.get("files", [])
            result["files_changed"] = len(files)

            # Map files to services
            services_hit = set()
            for f in files:
                svc = _map_file_to_service(f.get("filename", ""))
                if svc != "unknown":
                    services_hit.add(svc)
            result["affected_services"] = list(services_hit) or ["unknown"]

        # ---- 3. Developer commit frequency ----
        freq = _author_commit_frequency(owner, repo, author)
        result["commit_frequency"] = freq
        result["developer_experience_score"] = _developer_experience_score(freq)

        # ---- 4. Open PRs ----
        pr_url = f"{BASE_URL}/repos/{owner}/{repo}/pulls"
        pr_resp = requests.get(pr_url, headers=_headers(),
                               params={"state": "open", "per_page": 5},
                               timeout=10)
        if pr_resp.status_code == 200:
            result["pr_count_open"] = len(pr_resp.json())

    except requests.exceptions.ConnectionError:
        result["error"] = "Cannot reach GitHub API. Check internet connection."
    except requests.exceptions.Timeout:
        result["error"] = "GitHub API timed out."
    except Exception as e:
        result["error"] = str(e)

    return result
