"""Load a project's protocol files from a local checkout or a GitHub repo."""

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"

# Project entry docs (spec §2): DISCOVERY.md is recommended; the autoresearch names that many
# projects already use are equal alternatives. In order of preference when several exist.
ENTRY_DOCS = ("DISCOVERY.md", "autoresearch.md", "AUTORESEARCH.md", "auto-research.md")


def existing_entry_doc(root):
    """The entry doc already in a local checkout's root, by exact name, or None. Compares
    names exactly, so a case-insensitive filesystem doesn't report one spelling as another."""
    try:
        names = set(os.listdir(root))
    except OSError:
        return None
    return next((n for n in ENTRY_DOCS if n in names), None)


class Source:
    """Reads repository files from a local directory or raw.githubusercontent.com."""

    def __init__(self, local=None, repo=None, ref="HEAD", root=""):
        if (local is None) == (repo is None):
            raise ValueError("give exactly one of local or repo")
        self.local = Path(local) if local is not None else None
        self.repo, self.ref = repo, ref
        self.root = root.strip("/")  # project subdirectory, when a repo holds several

    @classmethod
    def from_entry(cls, entry):
        """Source for a registry entry's home repository (its first `repos` item)."""
        home = entry["repos"][0]
        return cls(repo=home["repo"], ref=home.get("ref", "HEAD"), root=home.get("path", ""))

    def describe(self):
        where = str(self.local) if self.local else f"{self.repo}@{self.ref}"
        return f"{where}:{self.root}" if self.root else where

    def _p(self, path):
        return f"{self.root}/{path}" if self.root else path

    def read(self, path):
        """Return file text, or None if it does not exist."""
        path = self._p(path)
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

    def read_bytes(self, path, limit):
        """File bytes, or None if it doesn't exist; ValueError if larger than limit."""
        path = self._p(path)
        if self.local:
            p = self.local / path
            if not p.is_file():
                return None
            data = p.read_bytes()
        else:
            try:
                with urllib.request.urlopen(RAW.format(repo=self.repo, ref=self.ref, path=path), timeout=30) as r:
                    data = r.read(limit + 1)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                raise
        if len(data) > limit:
            raise ValueError(f"{path} is larger than {limit:,} bytes")
        return data

    def exists(self, path):
        if self.local:
            full = self.local / self._p(path)
            return any(self.local.glob(self._p(path))) if "*" in path else full.exists()
        if "*" in path:
            return None  # unknown remotely without a tree listing
        try:
            with urllib.request.urlopen(RAW.format(repo=self.repo, ref=self.ref, path=self._p(path)), timeout=30):
                return True  # any file, text or binary: only its presence matters here
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        return self._is_dir(path)

    def _is_dir(self, path):
        """Remotely, a directory has no raw URL: ask the contents API. None if it can't say."""
        url = f"https://api.github.com/repos/{self.repo}/contents/{self._p(path)}?ref={self.ref}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return isinstance(json.loads(r.read().decode("utf-8")), list)
        except urllib.error.HTTPError as e:
            return False if e.code == 404 else None
        except (urllib.error.URLError, OSError, ValueError):
            return None

    def last_modified(self, path):
        """Date (YYYY-MM-DD) of the last commit touching path, or None."""
        path = self._p(path)
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

    def versions(self, path, limit=50):
        """Commits that changed path, newest first: [(sha, date YYYY-MM-DD)]. Empty if unknown."""
        path = self._p(path)
        try:
            if self.local:
                out = subprocess.run(["git", "-C", str(self.local), "log", f"-{limit}", "--format=%H %cs",
                                      "--", path], capture_output=True, text=True, timeout=60)
                return [tuple(line.split()) for line in out.stdout.splitlines() if line.strip()]
            url = f"https://api.github.com/repos/{self.repo}/commits?path={path}&per_page={min(limit, 100)}"
            if self.ref != "HEAD":
                url += f"&sha={self.ref}"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=30) as r:
                commits = json.loads(r.read().decode("utf-8"))
            return [(c["sha"], c["commit"]["committer"]["date"][:10]) for c in commits][:limit]
        except Exception:
            return []

    def read_at(self, sha, path):
        """File text at a commit, or None."""
        if self.local:
            out = subprocess.run(["git", "-C", str(self.local), "show", f"{sha}:{self._p(path)}"],
                                 capture_output=True, timeout=30)
            return out.stdout.decode("utf-8", "replace") if out.returncode == 0 else None
        return Source(repo=self.repo, ref=sha, root=self.root).read(path)

    def raw_url(self, path):
        """Where a browser can fetch the file (raw.githubusercontent.com allows any origin)."""
        return None if self.local else RAW.format(repo=self.repo, ref=self.ref, path=self._p(path))

    def read_json(self, path):
        text = self.read(path)
        return None if text is None else json.loads(text)


def load_manifest(source, overlay=None):
    """Return (manifest, origin). The hub's adapter is used only if the repo has none."""
    manifest = source.read_json("discover.json")
    if manifest is not None:
        return manifest, "discover.json"
    if overlay is not None:
        return overlay, "adapter"
    return None, None
