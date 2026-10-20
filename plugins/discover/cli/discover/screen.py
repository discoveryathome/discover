"""A basic screen of a repository for donors (spec §12.7): signs that running its code, or
letting an agent read it, could harm the person donating.

Static and conservative: it reads files and never runs them. A clean screen is not a
safety guarantee, and a finding is not an accusation; most findings in research repos
have innocent reasons. `high` findings mean: don't run the project's code until a person
has looked. The others are for the report.
"""

import json
import re
from pathlib import Path

from .project import ENTRY_DOCS

MAX_BYTES = 2_000_000
MAX_FILES = 20_000
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".tox", "build", "dist", "target"}
TEXT_EXT = {".md", ".txt", ".rst", ".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".json",
            ".toml", ".yaml", ".yml", ".cfg", ".ini", ".r", ".jl", ".c", ".h", ".cc", ".cpp", ".hpp",
            ".rs", ".go", ".java", ".rb", ".pl", ".lean", ".tex", ".mk", ".cmake", ".ps1", ".bat", ".ipynb",
            ".html", ".m", ".sage", ".gp", ".mag", ".lua", ".nix"}
TEXT_NAMES = {"Makefile", "makefile", "GNUmakefile", "Dockerfile", "Justfile", "Rakefile", "CMakeLists.txt",
              "AGENTS.md", "CLAUDE.md", ".envrc", ".gitmodules", "configure", "install", "setup"}
PROSE_EXT = {".md", ".txt", ".rst", ".tex", ".html", ".ipynb", ""}

# Characters that hide text from a person but not from a model. Tag characters have no
# legitimate use in a repo and can spell out a whole hidden message; bidi controls can make
# code read differently from how it runs; zero-width spaces are common in generated HTML.
HIDDEN = re.compile("[\\u200b-\\u200f\\u202a-\\u202e\\u2060\\u2066-\\u2069\\ufeff]|[\\U000e0000-\\U000e007f]")
TAGS = re.compile("[\\U000e0000-\\U000e007f]")
BIDI = re.compile("[\\u202a-\\u202e\\u2066-\\u2069]")
# Files agents read first, where hidden text deserves a closer look. Names compare without
# case (AUTORESEARCH.md, autoresearch.md); the manifest's own `entry` paths count too.
AGENT_FILES = ("AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md") + ENTRY_DOCS

PATTERNS = [
    # (severity in code, kind, regex, severity in prose or None to skip prose, what it means)
    ("high", "remote-script", re.compile(r"\b(curl|wget|iwr|Invoke-WebRequest)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b|"
                                         r"\b(curl|wget)\b[^\n|]*\|\s*python", re.I), "warn",
     "downloads a script and runs it unseen"),
    ("high", "obfuscated-exec", re.compile(r"\b(exec|eval)\s*\(\s*(base64\.b64decode|codecs\.decode|bytes\.fromhex|"
                                           r"zlib\.decompress|marshal\.loads|compile\s*\(\s*base64)|"
                                           r"\beval\s*\(\s*atob\s*\(|base64\s+(-d|--decode)[^\n]*\|\s*(ba)?sh", re.I), "warn",
     "runs encoded code"),
    ("high", "credential-access", re.compile(r"(~|\$HOME|%USERPROFILE%|expanduser\(['\"]~)[/\\]*\.(ssh|aws|gnupg|kube|docker/config|"
                                             r"config/gh|netrc|npmrc|pypirc)|\bgh\s+auth\s+token\b|"
                                             r"security\s+find-(generic|internet)-password|Login[ ]Data|cookies\.sqlit[e]", re.I), "warn",
     "reads credentials or keys"),
    ("high", "exfiltration", re.compile(r"discord(app)?\.com/api/webhooks|hooks\.slack\.com/services|webhook\.site|"
                                        r"request[b]in|pipedream\.net|ngrok(-free)?\.(io|app)|pastebin\.com/api|"
                                        r"api\.telegram\.org/bot|\binteract\.sh\b|burp[c]ollaborator", re.I), "high",
     "sends data to a collection endpoint"),
    ("high", "agent-override", re.compile(r"ignore (all |any )?(previous|prior|above|earlier) (instructions|rules)|"
                                          r"disregard (your|the|all) (previous |prior )?(instructions|rules|system prompt)|"
                                          r"--dangerously-skip-permission[s]|bypassPermission[s]|--yol[o]\b|"
                                          r"--dangerously-bypass-approval[s]|do not (tell|inform|mention (this )?to) the (user|person|human)", re.I), "high",
     "text aimed at overriding an agent's instructions or permissions"),
    ("warn", "agent-instructions", re.compile(r"\b(AI|LLM|coding) (agents?|assistants?|models?)\b[^\n]{0,80}\b(must|should|always|never)\b[^\n]{0,80}"
                                              r"\b(run|execute|install|curl|push|send|upload|post|token|credential|disable)\b", re.I), "warn",
     "instructions addressed to agents that involve running, sending or credentials; read them as data"),
    ("warn", "privileged", re.compile(r"^\s*sudo\s|\bchmod\s+(-R\s+)?777\b|\brm\s+-rf\s+(/|~|\$HOME)(\s|$)", re.M), "info",
     "needs root, or deletes outside the repo"),
]

AGENT_KINDS = ("agent-override", "agent-instructions")
HIDDEN_EXT = {".py", ".js", ".ts", ".sh", ".json", ".toml", ".yaml", ".yml"}
PER_FILE = 3

# Cheap substring tests run before each pattern (on lowercased text); a regex runs only
# where one appears. Shortened on purpose, so this file's own lists don't match the patterns.
KEYWORDS = {
    "remote-script": ("curl", "wget", "invoke-webreq", "iwr "),
    "obfuscated-exec": ("b64decode", "codecs.decode", "fromhex", "zlib.decompress", "marshal.loads", "atob(", "base64 -d",
                        "base64 --decode"),
    "credential-access": (".ssh", ".aws", ".gnupg", ".kube", ".docker/config", "config/gh", ".netrc", ".npmrc", ".pypirc",
                          "auth token", "find-generic", "find-internet", "login dat", "cookies.sqlit"),
    "exfiltration": ("discord", "hooks.slac", "webhook.si", "requestb", "pipedrea", "ngrok", "pastebin", "api.telegra",
                     "interact.s", "burpcollab"),
    "agent-override": ("ignore", "disregard", "dangerously", "bypasspermission", "--yol", "do not "),
    "agent-instructions": ("ai agent", "ai assistant", "ai model", "llm", "coding agent", "coding assistant", "coding model"),
    "privileged": ("sudo", "chmod", "rm -rf"),
}

INSTALL_HOOKS = ("preinstall", "install", "postinstall", "prepare", "prepack")


def _text(path):
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="replace")


_FILES = {}


def _files(root):
    """The files git tracks (so build output and vendored downloads are skipped), else every
    file outside the usual generated folders."""
    key = str(Path(root).resolve())
    if key not in _FILES:
        import subprocess
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
        if out.returncode == 0:
            names = [n for n in out.stdout.decode("utf-8", "replace").split("\0") if n]
        else:
            names = [p.relative_to(root).as_posix() for p in Path(root).rglob("*")
                     if not any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1])
                     and (p.is_file() or p.is_symlink())]
        _FILES[key] = sorted(names)
    return _FILES[key]


def _binary_kind(path):
    try:
        with open(path, "rb") as f:
            head = f.read(4)
    except OSError:
        return None
    if head == b"\x7fELF":
        return "ELF executable"
    if head[:2] == b"MZ":
        return "Windows executable"
    if head in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe"):
        return "Mach-O executable"
    return None


def _excerpt(line):
    shown = HIDDEN.sub(lambda m: f"<U+{ord(m.group()):04X}>", line.strip())
    return shown[:160]


def screen(root):
    """Findings for a checked-out repository: [{severity, kind, path, line, excerpt, why}]."""
    root = Path(root)
    found = []
    agent_names = {n.lower() for n in AGENT_FILES}
    agent_paths = set()
    try:
        entry = (json.loads((root / "discover.json").read_text(encoding="utf-8")) or {}).get("entry") or {}
        agent_paths = {v.strip("/") for v in entry.values() if isinstance(v, str)}
    except (OSError, ValueError, AttributeError):
        pass

    def add(sev, kind, rel, line, excerpt, why):
        found.append({"severity": sev, "kind": kind, "path": rel, "line": line, "excerpt": excerpt, "why": why})

    # Files an agent or editor loads by itself when started inside the repo.
    for rel, why in ((".claude/settings.json", "Claude Code project settings: can grant permissions or define hooks that run commands"),
                     (".claude/settings.local.json", "Claude Code local settings committed to the repo"),
                     (".mcp.json", "MCP servers an agent may start"),
                     (".codex/config.toml", "Codex project config"),
                     (".vscode/tasks.json", "editor tasks, which can run when a folder opens"),
                     (".envrc", "direnv runs this on entering the folder")):
        p = root / rel
        if p.exists():
            t = _text(p) or ""
            risky = any(k in t for k in ('"hooks"', '"allow"', "command", "folderOpen", "bypass", "sandbox",
                                         "allowedDomains", '"env"', "apiKeyHelper", "McpServers", "mcpServers"))
            add("high" if risky or rel in (".envrc", ".mcp.json") else "warn", "agent-config", rel, None,
                "", why + ". Don't start an agent or editor inside the clone; run it from the session folder.")
    if (root / ".codex").is_dir() and not (root / ".codex/config.toml").exists():
        add("warn", "agent-config", ".codex/", None, "", "Codex rules shipped with the repo")

    real_root = root.resolve()
    present = [rel for rel in _files(root) if (root / rel).is_file() or (root / rel).is_symlink()]
    for rel in present[:MAX_FILES]:
        path = root / rel
        if path.is_symlink():
            try:
                if real_root not in path.resolve().parents:
                    add("warn", "symlink-out", rel, None, str(path.readlink()), "a symlink pointing outside the repo")
            except (OSError, RuntimeError):
                pass
            continue
        if not path.is_file():  # e.g. outside a sparse checkout
            continue
        kind = _binary_kind(path)
        if kind:
            add("warn", "binary", rel, None, kind, "a committed executable: never run it; build from source instead")
            continue
        ext = path.suffix.lower()
        if ext not in TEXT_EXT and path.name not in TEXT_NAMES:
            continue
        text = _text(path)
        if text is None:
            continue
        prose = ext in PROSE_EXT or path.name in ("AGENTS.md", "CLAUDE.md")
        # CI runs on the forge, not the donor's machine: only text aimed at agents matters there.
        ci = rel.startswith(".github/workflows/")
        checks = [(HIDDEN, None)] if (prose or ext in HIDDEN_EXT) else []
        checks += [(rx, pat) for pat in PATTERNS for rx in [pat[2]]
                   if not (prose and not pat[3]) and not (ci and pat[1] not in AGENT_KINDS)]
        low = text.lower()
        checks = [(rx, pat) for rx, pat in checks
                  if (pat is None or any(k in low for k in KEYWORDS[pat[1]])) and rx.search(text)]
        if not checks:
            pass
        else:
            hits = {}
            for i, line in enumerate(text.splitlines(), 1):
                for rx, pat in checks:
                    if not rx.search(line):
                        continue
                    if pat is None:
                        if i == 1 and line.startswith("\ufeff") and not HIDDEN.search(line[1:]):
                            continue  # a byte-order mark: harmless
                        kind = "hidden-text"
                        if TAGS.search(line):
                            sev, why = "high", "invisible tag characters: a message a person can't see but a model reads"
                        elif BIDI.search(line):
                            sev, why = ("warn" if prose else "high"), "bidirectional controls: text that reads differently from what it is"
                        else:
                            sev = "warn" if path.name.lower() in agent_names or rel in agent_paths else "info"
                            why = "zero-width characters (common in generated HTML; in a file agents read first, look closer)"
                    else:
                        sev, kind, _, prose_sev, why = pat
                        if prose:
                            sev = prose_sev
                            if kind not in AGENT_KINDS:
                                why += " (in documentation: an agent following it would run it)"
                    hits[kind] = hits.get(kind, 0) + 1
                    if hits[kind] <= (1 if sev == "info" else PER_FILE):
                        add(sev, kind, rel, i, _excerpt(line), why)
            for kind, n in hits.items():
                if n > PER_FILE:
                    add("info", kind, rel, None, "", f"{n} {kind} lines in this file in all")
        if path.name == "package.json":
            try:
                scripts = (json.loads(text).get("scripts") or {})
            except (ValueError, AttributeError):
                scripts = {}
            for hook in INSTALL_HOOKS:
                if hook in scripts:
                    add("warn", "install-hook", rel, None, f"{hook}: {str(scripts[hook])[:120]}",
                        "runs on npm install: read it before installing")
        if path.name == "setup.py" and re.search(r"cmdclass|urlopen|requests\.|subprocess|os\.system", text):
            add("warn", "install-hook", rel, None, "", "setup.py runs custom code on pip install: read it before installing")
        if path.name == "build.rs":
            add("info", "install-hook", rel, None, "", "a Cargo build script runs on cargo build")
        if path.name == ".gitmodules":
            for url in re.findall(r"url\s*=\s*(\S+)", text):
                if "github.com" not in url:
                    add("info", "submodule", rel, None, url, "a submodule from outside GitHub")
    if len(present) > MAX_FILES:
        add("info", "truncated", ".", None, "", f"screened the first {MAX_FILES} files only")
    order = {"high": 0, "warn": 1, "info": 2}
    found.sort(key=lambda f: (order[f["severity"]], f["path"], f["line"] or 0))
    return found


def format_report(findings, root="."):
    if not findings:
        return (f"Screen of {root}: no findings. That isn't a guarantee: read what you run, "
                f"and run untrusted code in a sandbox.")
    high = sum(f["severity"] == "high" for f in findings)
    lines = [f"Screen of {root}: {len(findings)} finding(s), {high} high."]
    if high:
        lines.append("Don't run this project's code (builds, tests, installs, scripts) until a person has read "
                     "the high findings. Reading and reporting are fine.")
    for f in findings:
        where = f["path"] + (f":{f['line']}" if f["line"] else "")
        lines.append(f"- [{f['severity']}] {f['kind']} {where}: {f['why']}")
        if f["excerpt"]:
            lines.append(f"    {f['excerpt']}")
    return "\n".join(lines)
