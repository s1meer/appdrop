"""
Week 2 Tests — GitHub Parser
Tests URL parsing and env var extraction without hitting live GitHub API.
Run: pytest tests/test_github_parser.py -v
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

from github_parser import parse_github_url, extract_env_vars_from_readme, RepoInfo, RepoType


# ─── URL Parsing ──────────────────────────────────────────────────────────────

class TestParseGitHubURL:

    def test_standard_https_url(self):
        owner, repo = parse_github_url("https://github.com/comfyanonymous/ComfyUI")
        assert owner == "comfyanonymous"
        assert repo == "ComfyUI"

    def test_url_with_trailing_slash(self):
        owner, repo = parse_github_url("https://github.com/openai/whisper/")
        assert owner == "openai"
        assert repo == "whisper"

    def test_url_with_git_suffix(self):
        owner, repo = parse_github_url("https://github.com/ollama/ollama.git")
        assert owner == "ollama"
        assert repo == "ollama"

    def test_url_with_tree_path(self):
        owner, repo = parse_github_url("https://github.com/AUTOMATIC1111/stable-diffusion-webui")
        assert owner == "AUTOMATIC1111"
        assert repo == "stable-diffusion-webui"

    def test_ssh_url(self):
        owner, repo = parse_github_url("git@github.com:anthropics/claude-code.git")
        assert owner == "anthropics"
        assert repo == "claude-code"

    def test_short_owner_repo_format(self):
        owner, repo = parse_github_url("comfyanonymous/ComfyUI")
        assert owner == "comfyanonymous"
        assert repo == "ComfyUI"

    def test_url_without_www(self):
        owner, repo = parse_github_url("github.com/openai/whisper")
        assert owner == "openai"
        assert repo == "whisper"

    def test_url_with_http(self):
        owner, repo = parse_github_url("http://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_invalid_url_raises_valueerror(self):
        with pytest.raises(ValueError):
            parse_github_url("https://gitlab.com/owner/repo")

    def test_invalid_url_no_repo_raises(self):
        with pytest.raises(ValueError):
            parse_github_url("https://github.com/justowner")

    def test_non_github_domain_raises(self):
        with pytest.raises(ValueError):
            parse_github_url("https://google.com/owner/repo")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_github_url("")

    def test_url_with_fragment_stripped(self):
        owner, repo = parse_github_url("https://github.com/owner/repo#readme")
        assert owner == "owner"
        assert repo == "repo"

    def test_url_with_query_stripped(self):
        owner, repo = parse_github_url("https://github.com/owner/repo?tab=readme")
        assert owner == "owner"
        assert repo == "repo"

    def test_hyphenated_repo_name(self):
        owner, repo = parse_github_url("https://github.com/AUTOMATIC1111/stable-diffusion-webui")
        assert repo == "stable-diffusion-webui"

    def test_dotted_repo_name(self):
        owner, repo = parse_github_url("https://github.com/owner/my.project")
        assert repo == "my.project"

    def test_whitespace_trimmed(self):
        owner, repo = parse_github_url("  https://github.com/owner/repo  ")
        assert owner == "owner"
        assert repo == "repo"


# ─── Env Var Extraction ───────────────────────────────────────────────────────

class TestExtractEnvVars:

    def test_detects_api_key_vars(self):
        readme = """
## Setup
Create a `.env` file:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
```
"""
        vars = extract_env_vars_from_readme(readme)
        assert "OPENAI_API_KEY" in vars
        assert "ANTHROPIC_API_KEY" in vars

    def test_detects_export_style(self):
        readme = "Run `export DATABASE_URL=postgres://...` before starting."
        vars = extract_env_vars_from_readme(readme)
        assert "DATABASE_URL" in vars

    def test_ignores_docker_keywords(self):
        readme = "FROM python:3.11\nRUN pip install\nENV DEBUG=1\n"
        vars = extract_env_vars_from_readme(readme)
        # FROM, RUN should be filtered; ENV might be edge case
        assert "FROM" not in vars
        assert "RUN" not in vars

    def test_detects_token_vars(self):
        readme = "Set GITHUB_TOKEN and SLACK_TOKEN in your environment."
        vars = extract_env_vars_from_readme(readme)
        assert "GITHUB_TOKEN" in vars
        assert "SLACK_TOKEN" in vars

    def test_empty_readme_returns_empty(self):
        assert extract_env_vars_from_readme("") == []

    def test_no_env_vars_returns_empty(self):
        readme = "This is a simple app with no configuration needed."
        assert extract_env_vars_from_readme(readme) == []

    def test_detects_vars_in_code_blocks(self):
        readme = """
```bash
export API_SECRET=myvalue
```
"""
        vars = extract_env_vars_from_readme(readme)
        assert "API_SECRET" in vars

    def test_results_are_sorted(self):
        readme = "ZEBRA_KEY=1 ALPHA_TOKEN=2 MIDDLE_URL=3"
        vars = extract_env_vars_from_readme(readme)
        assert vars == sorted(vars)

    def test_no_duplicates(self):
        readme = "OPENAI_API_KEY=1\nOPENAI_API_KEY=2\nOPENAI_API_KEY=3"
        vars = extract_env_vars_from_readme(readme)
        assert vars.count("OPENAI_API_KEY") == 1

    def test_short_var_names_ignored(self):
        # Less than 4 chars should not be included
        readme = "Set AB=1 in environment"
        vars = extract_env_vars_from_readme(readme)
        assert "AB" not in vars


# ─── RepoInfo Dataclass ───────────────────────────────────────────────────────

class TestRepoInfo:

    def test_default_values(self):
        info = RepoInfo(
            owner="test", repo="app",
            clone_url="https://github.com/test/app.git",
            description="A test app",
            default_branch="main",
            stars=100,
            repo_type=RepoType.STANDARD,
        )
        assert info.detected_env_vars == []
        assert info.topics == []
        assert info.readme_content is None
        assert info.has_docker is False

    def test_env_vars_populated(self):
        info = RepoInfo(
            owner="test", repo="app",
            clone_url="https://github.com/test/app.git",
            description=None,
            default_branch="main",
            stars=0,
            repo_type=RepoType.STANDARD,
            detected_env_vars=["OPENAI_API_KEY", "PORT"],
        )
        assert "OPENAI_API_KEY" in info.detected_env_vars
        assert len(info.detected_env_vars) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
