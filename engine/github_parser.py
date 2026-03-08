"""
Week 2: GitHub URL Parser + README Fetcher
- Validates and normalizes GitHub URLs
- Fetches repo metadata via GitHub API
- Reads README content for LLM parsing (Week 3)
- Extracts env vars mentioned in README
"""

import re
import urllib.request
import urllib.error
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class RepoType(str, Enum):
    STANDARD = "standard"
    FORK = "fork"
    ARCHIVED = "archived"
    EMPTY = "empty"


@dataclass
class RepoInfo:
    owner: str
    repo: str
    clone_url: str
    description: Optional[str]
    default_branch: str
    stars: int
    repo_type: RepoType
    readme_content: Optional[str] = None
    detected_env_vars: list = field(default_factory=list)
    topics: list = field(default_factory=list)
    has_docker: bool = False
    has_requirements: bool = False
    has_package_json: bool = False
    language: Optional[str] = None


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Parse a GitHub URL into (owner, repo).
    Handles all common GitHub URL formats.

    Returns:
        (owner, repo) tuple

    Raises:
        ValueError if URL is not a valid GitHub repo URL
    """
    url = url.strip().rstrip("/")

    # Remove .git suffix
    if url.endswith(".git"):
        url = url[:-4]

    # Patterns to match
    patterns = [
        # https://github.com/owner/repo
        r"https?://(?:www\.)?github\.com/([^/]+)/([^/?\s#]+)",
        # github.com/owner/repo (no protocol)
        r"(?:www\.)?github\.com/([^/]+)/([^/?\s#]+)",
        # git@github.com:owner/repo
        r"git@github\.com:([^/]+)/([^/?\s#]+)",
        # Short: owner/repo
        r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.group(1), match.group(2)
            # Strip any fragment or query
            repo = re.split(r"[#?/]", repo)[0]
            return owner, repo

    raise ValueError(f"Not a valid GitHub URL: {url}")


def fetch_repo_metadata(owner: str, repo: str, github_token: Optional[str] = None) -> dict:
    """
    Fetch repo metadata from GitHub API.
    Works without a token (60 req/hr rate limit).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AppDrop/0.1",
    }
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"Repo not found: {owner}/{repo}")
        if e.code == 403:
            raise ValueError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN.")
        raise


def fetch_readme(owner: str, repo: str, branch: str = "main", github_token: Optional[str] = None) -> Optional[str]:
    """
    Fetch raw README content. Tries main and master branches.
    Returns None if no README found.
    """
    headers = {"User-Agent": "AppDrop/0.1"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    for readme_name in ["README.md", "readme.md", "README.rst", "README.txt", "README"]:
        for branch_try in [branch, "main", "master", "dev"]:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch_try}/{readme_name}"
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.read().decode("utf-8", errors="ignore")
            except (urllib.error.HTTPError, urllib.error.URLError):
                continue
    return None


def extract_env_vars_from_readme(readme: str) -> list[str]:
    """
    Scan README for commonly documented environment variables.
    Looks for patterns like:
      - `API_KEY=...`
      - export OPENAI_API_KEY=
      - ENV_VAR_NAME in code blocks
      - .env file examples
    """
    found = set()

    # Pattern 1: ALL_CAPS_VAR= or ALL_CAPS_VAR:
    env_pattern = re.compile(r'\b([A-Z][A-Z0-9_]{2,}(?:_KEY|_TOKEN|_SECRET|_URL|_HOST|_PORT|_ID|_PATH|_API)?)\s*[=:]', re.MULTILINE)

    # Pattern 2: known suffix vars mentioned anywhere (e.g. "Set GITHUB_TOKEN in...")
    suffix_pattern = re.compile(r'\b([A-Z][A-Z0-9_]{2,}(?:_KEY|_TOKEN|_SECRET))\b')

    # Also look inside code blocks
    for match in suffix_pattern.finditer(readme):
        found.add(match.group(1))

    for match in env_pattern.finditer(readme):
        var = match.group(1)
        # Filter out common false positives
        skip = {"FROM", "RUN", "ENV", "ARG", "COPY", "WORKDIR", "CMD", "EXPOSE",
                 "ADD", "USER", "LABEL", "VOLUME", "FOR", "IF", "ELSE", "TRUE", "FALSE"}
        if var not in skip and len(var) >= 4:
            found.add(var)

    # Explicit .env example blocks
    dotenv_block = re.compile(r'```(?:env|bash|sh)?\s*((?:[A-Z][A-Z0-9_]+=.*\n?)+)```', re.MULTILINE)
    for block in dotenv_block.finditer(readme):
        for line in block.group(1).splitlines():
            match = re.match(r'([A-Z][A-Z0-9_]+)=', line.strip())
            if match:
                found.add(match.group(1))

    return sorted(found)


def analyze_repo(github_url: str, github_token: Optional[str] = None) -> RepoInfo:
    """
    Full repo analysis pipeline:
    1. Parse URL
    2. Fetch metadata
    3. Fetch README
    4. Extract env vars
    Returns a RepoInfo dataclass.
    """
    owner, repo = parse_github_url(github_url)
    meta = fetch_repo_metadata(owner, repo, github_token)

    repo_type = RepoType.STANDARD
    if meta.get("archived"):
        repo_type = RepoType.ARCHIVED
    elif meta.get("fork"):
        repo_type = RepoType.FORK
    elif meta.get("size", 0) == 0:
        repo_type = RepoType.EMPTY

    default_branch = meta.get("default_branch", "main")
    readme = fetch_readme(owner, repo, default_branch, github_token)

    env_vars = []
    if readme:
        env_vars = extract_env_vars_from_readme(readme)

    return RepoInfo(
        owner=owner,
        repo=repo,
        clone_url=meta.get("clone_url", f"https://github.com/{owner}/{repo}.git"),
        description=meta.get("description"),
        default_branch=default_branch,
        stars=meta.get("stargazers_count", 0),
        repo_type=repo_type,
        readme_content=readme,
        detected_env_vars=env_vars,
        topics=meta.get("topics", []),
        language=meta.get("language"),
    )
