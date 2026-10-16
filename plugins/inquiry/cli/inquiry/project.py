"""Load a project's protocol files from a local checkout or a GitHub repo."""

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"


class Source:
    """Reads repository files from a local directory or raw.githubusercontent.com."""

    def __init__(self, local=None, repo=None, ref="HEAD"):
        if (local is None) == (repo is None):
            raise ValueError("give exactly one of local or repo")
        self.local = Path(local) if local is not None else None
        self.repo, self.ref = repo, ref

    def describe(self):
        return str(self.local) if self.local else f"{self.repo}@{self.ref}"

    def read(self, path):
        """Return file text, or None if it does not exist."""
        if self.local:
            p = self.local / path
            return p.read_text(encoding="utf-8") if p.is_file() else None
        url = RAW.format(repo=self.repo, ref=self.ref, path=path)
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def exists(self, path):
        if self.local:
            return any(self.local.glob(path)) if "*" in path else (self.local / path).exists()
        if "*" in path:
            return None  # unknown remotely without a tree listing
        return self.read(path) is not None

    def last_modified(self, path):
        """Date (YYYY-MM-DD) of the last commit touching path, or None."""
        try:
            if self.local:
                out = subprocess.run(["git", "-C", str(self.local), "log", "-1", "--format=%cs", "--", path],
                                     capture_output=True, text=True, timeout=30)
                return out.stdout.strip() or None
            url = f"https://api.github.com/repos/{self.repo}/commits?path={path}&per_page=1"
            if self.ref != "HEAD":
                url += f"&sha={self.ref}"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=30) as r:
                commits = json.loads(r.read().decode("utf-8"))
            return commits[0]["commit"]["committer"]["date"][:10] if commits else None
        except Exception:
            return None

    def read_json(self, path):
        text = self.read(path)
        return None if text is None else json.loads(text)


def load_manifest(source, overlay=None):
    """Return (manifest, origin). A registry overlay is used only if the repo has none."""
    manifest = source.read_json("inquiry.json")
    if manifest is not None:
        return manifest, "inquiry.json"
    if overlay is not None:
        return overlay, "registry overlay"
    return None, None
