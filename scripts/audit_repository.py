"""Check candidate Git files for local credentials without printing secret values."""

import json
import re
import subprocess
from pathlib import Path

from dotenv import dotenv_values


def main():
    files = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
        )
        .decode("utf-8")
        .split("\0")
    )
    secrets = [
        value for key, value in dotenv_values(".env").items() if key.endswith("PASSWORD") and value
    ]
    issues = []
    patterns = [
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"gh[pousr]_[A-Za-z0-9]{30,}",
        r"sk-proj-[A-Za-z0-9_-]{30,}",
    ]
    for name in filter(None, files):
        path = Path(name)
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            issues.append({"file": name, "reason": "env candidate"})
        if path.is_file():
            content = path.read_text(encoding="utf-8-sig", errors="replace")
            if any(secret in content for secret in secrets):
                issues.append({"file": name, "reason": "local password found"})
            if any(re.search(pattern, content) for pattern in patterns):
                issues.append({"file": name, "reason": "secret-like token"})
    print(
        json.dumps(
            {
                "files_checked": len(list(filter(None, files))),
                "passed": not issues,
                "issues": issues,
            },
            indent=2,
        )
    )
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
