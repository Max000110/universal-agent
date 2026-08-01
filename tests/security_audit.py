import os
import re
import sys
from pathlib import Path

# Comprehensive security regex patterns for auditing credentials and secrets
SECRET_PATTERNS = [
    ("AWS Key", re.compile(r"(?i)(AKIA[0-9A-Z]{16})")),
    ("AWS Secret", re.compile(r"(?i)(aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40})")),
    ("GitHub Token", re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59})")),
    ("Generic Private Key", re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----")),
    ("JWT Token", re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")),
    ("OpenAI/Session Token", re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("Slack Webhook / Token", re.compile(r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+")),
    ("Hardcoded Password", re.compile(r"(?i)(password|passwd|secret)\s*[:=]\s*['\"]([^'\"]{8,})['\"]")),
    ("IPv4 Address", re.compile(r"\b(?!127\.0\.0\.1\b)(?!0\.0\.0\.0\b)(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")),
]

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".antigravitycli"}


def audit_directory(root_path: Path):
    findings = []
    scanned_files = 0

    for path in root_path.rglob("*"):
        if path.is_file():
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            scanned_files += 1
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for label, pattern in SECRET_PATTERNS:
                    matches = pattern.findall(content)
                    if matches:
                        for m in matches:
                            findings.append({
                                "file": str(path.relative_to(root_path)),
                                "label": label,
                                "match": str(m)[:30]
                            })
            except Exception as e:
                pass

    return scanned_files, findings


if __name__ == "__main__":
    repo_dir = Path("/home/ubuntu/antigravity-cli")
    count, results = audit_directory(repo_dir)
    print(f"Scanned {count} files in {repo_dir}.")
    if not results:
        print("✓ CLEAN AUDIT: 0 credentials or secret leaks found!")
        sys.exit(0)
    else:
        print(f"⚠️ FOUND {len(results)} POTENTIAL ISSUES:")
        for r in results:
            print(f"  - [{r['label']}] in {r['file']}: {r['match']}")
        sys.exit(1)
