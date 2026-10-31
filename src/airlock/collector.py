"""File collection: git index listing, reads, decoding, limits and startup checks.

Tasks 2.2 and 2.3 (`ARCHITECTURE.md` 6.1). Two rules from the essentials document live here
more than anywhere else: no file is ever skipped silently, and there are no default
directory skips. Every condition that stops the scanner from reading content produces a
finding with a path attached.

This module is one of only two allowed to call `subprocess`, always with a fixed argument
list and never through a shell. Scanned files are opened for reading only; nothing collected
here is imported, executed or followed.
"""

from __future__ import annotations

import codecs
import hashlib
import os
import shutil
import stat
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .fingerprint import PendingFinding, truncate_evidence
from .model import FileEntry, Policy, Severity
from .roles import SENSITIVE_ROLES, resolve_roles, roles_from_magic

#: Roles whose content is still worth a lenient decode when strict UTF-8 fails, so one bad
#: byte cannot hide a payload behind `non-utf8-text`.
SCANNABLE_ROLES = frozenset({"tooling-config", "editor-autorun", "source"})

HEAD_BYTES = 4096
MIN_PYTHON = (3, 11)

_GITLINK_MODE = "160000"
_SYMLINK_MODE = "120000"
GITMODULES_PATH = ".gitmodules"

#: Reason strings recorded on FileEntry, counted in ScanReport.files_skipped.
SKIP_OVERSIZE = "oversize"
SKIP_UNREADABLE = "unreadable"
SKIP_SYMLINK = "symlink"
SKIP_SUBMODULE = "submodule"
SKIP_ENCODING = "encoding"
SKIP_UNMERGED = "unmerged"
SKIP_NONPORTABLE_PATH = "nonportable-path"

#: Device stems Windows reserves in every directory, regardless of case or extension (7.8).
_WINDOWS_RESERVED_STEMS = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "CONIN$",
        "CONOUT$",
        *(f"COM{n}" for n in range(1, 10)),
        *(f"LPT{n}" for n in range(1, 10)),
        "COM\xb9",
        "COM\xb2",
        "COM\xb3",
        "LPT\xb9",
        "LPT\xb2",
        "LPT\xb3",
    }
)


@dataclass(frozen=True, slots=True)
class IndexEntry:
    """One path from `git ls-files --stage`, with the index stage it was seen at."""

    mode: str
    path: str
    stage: int = 0
    sha: str = ""

    @property
    def is_unmerged(self) -> bool:
        return self.stage != 0

    @property
    def is_symlink(self) -> bool:
        return self.mode == _SYMLINK_MODE

    @property
    def is_submodule(self) -> bool:
        return self.mode == _GITLINK_MODE


@dataclass(frozen=True, slots=True)
class _GitmoduleSection:
    """One section from `.gitmodules`, used to cross-check index gitlinks (task 7.2)."""

    header: str
    line: int
    valid_header: bool
    paths: tuple[str, ...]
    urls: tuple[str, ...]

    @property
    def is_well_formed(self) -> bool:
        return (
            self.valid_header
            and len(self.paths) == 1
            and bool(self.paths[0])
            and len(self.urls) == 1
            and bool(self.urls[0])
            and not any(ch.isspace() for ch in self.urls[0])
        )


@dataclass(frozen=True, slots=True)
class Collection:
    """What a collect() run produced. Detectors read entries; the runner appends pending."""

    entries: tuple[FileEntry, ...]
    pending: tuple[PendingFinding, ...]

    @property
    def files_skipped(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            if entry.skip_reason:
                counts[entry.skip_reason] = counts.get(entry.skip_reason, 0) + 1
        return counts


def git_bytes(repo_root: Path, *args: str, timeout: int = 120) -> bytes:
    """Run one git command in the scanned repo and return raw stdout. Never uses a shell.

    Every git call in this module goes through here, so a timeout or a missing binary fails
    the same way whoever asked git. The CLI turns that `ValueError` into exit code 2.
    """
    argv = ["git", "-C", str(repo_root), *args]
    try:
        result = subprocess.run(argv, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"git failed to run: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(detail or f"git exited with code {result.returncode}")
    return result.stdout


def git_text(repo_root: Path, *args: str) -> str:
    """One git command as text, with the surrounding whitespace removed."""
    return git_bytes(repo_root, *args).decode("utf-8", errors="replace").strip()


def check_runtime(repo_root: Path) -> str:
    """Startup checks (2.3): interpreter, git on PATH, repository readable.

    Returns the HEAD commit of the scanned repository. Every failure raises `ValueError`
    with git's own explanation, which the CLI turns into exit code 2. A git `safe.directory`
    refusal lands here too, and its message names the fix.
    """
    if sys.version_info < MIN_PYTHON:
        needed = ".".join(str(part) for part in MIN_PYTHON)
        running = ".".join(str(part) for part in sys.version_info[:3])
        raise ValueError(f"airlock needs Python {needed} or newer, this run uses {running}")
    if shutil.which("git") is None:
        raise ValueError("airlock needs git on PATH to list tracked files")
    try:
        head = git_text(repo_root, "rev-parse", "--verify", "HEAD")
    except ValueError as exc:
        raise ValueError(f"cannot read the repository at {repo_root}: {exc}") from exc
    if len(head) != 40 or any(char not in "0123456789abcdef" for char in head):
        raise ValueError(f"git returned an unexpected HEAD reference: {head!r}")
    return head


def list_tracked_files(repo_root: Path) -> tuple[IndexEntry, ...]:
    """Tracked paths from the index, sorted, one record per path.

    An unmerged path is kept, flagged, and never dropped: git lists it once per staged
    version (stages 1, 2 and 3, with no stage 0), and a scanner that only read stage 0 would
    report nothing at all about a file sitting in a merge conflict. The repeat collapses into
    one entry so the path produces one finding.
    """
    raw = git_bytes(repo_root, "ls-files", "-z", "--stage", timeout=300)
    by_path: dict[str, IndexEntry] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        fields = meta.split(b" ")
        if len(fields) != 3:
            raise ValueError(f"unparsable git index entry: {record[:120]!r}")
        mode, sha, stage = fields
        entry = IndexEntry(
            mode=mode.decode(),
            path=os.fsdecode(path),
            stage=int(stage),
            sha=sha.decode("ascii", errors="replace"),
        )
        seen = by_path.get(entry.path)
        if seen is None or entry.stage < seen.stage:
            by_path[entry.path] = entry
    return tuple(sorted(by_path.values(), key=lambda entry: entry.path))


def _state(
    rule_id: str,
    severity: Severity,
    path: str,
    roles: tuple[str, ...],
    message: str,
    evidence: str | None = None,
    line: int = 0,
) -> PendingFinding:
    return PendingFinding(
        rule_id=rule_id,
        severity=severity,
        path=path,
        line=line,
        roles=roles,
        message=message,
        evidence=truncate_evidence(evidence),
        suppressible=False,
    )


def _sensitive(roles: tuple[str, ...]) -> bool:
    return bool(SENSITIVE_ROLES.intersection(roles))


def _decode(data: bytes) -> tuple[str, bool]:
    """BOM-aware decode. Returns the text and whether the strict decode failed."""
    if data.startswith(codecs.BOM_UTF8):
        try:
            return data[len(codecs.BOM_UTF8) :].decode("utf-8"), False
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace"), True
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        try:
            return data.decode("utf-16"), False
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace"), True
    try:
        return data.decode("utf-8"), False
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace"), True


def _reserved_windows_device(path: str) -> tuple[str, str] | None:
    """Return `(segment, device)` when any segment is a reserved Windows device name (7.8).

    Win32 strips trailing spaces and dots and treats everything after the first dot as an
    extension, so `NUL`, `nul.js`, `src/NUL` and `src/nul.postcss.config.mjs` resolve to kernel
    character devices when opened on Windows without an extended-length prefix (`NUL` reads as
    0 bytes and `CON`/`AUX` block indefinitely), while `git checkout` refuses to materialize
    them as regular files on NTFS.
    """
    for segment in path.replace("\\", "/").split("/"):
        stripped = segment.rstrip(" .")
        if not stripped:
            continue
        stem = stripped.partition(".")[0].upper()
        if stem in _WINDOWS_RESERVED_STEMS:
            return segment, stem
    return None


def _escape_backslash_path(raw_path: str) -> str:
    """Escape `\\` as `%5C` so a backslash-bearing index path satisfies `require_repo_path`
    without colliding with any forward-slash sibling path on `FileEntry` or `Finding`."""
    escaped = raw_path.replace("\\", "%5C").strip("/")
    if not escaped or escaped == ".":
        return "%5C"
    return escaped


def _actual_disk_relpath(resolved_root: Path, target: Path) -> str | None:
    """Return the case-preserved repo-relative path on disk, or `None` if resolution fails."""
    try:
        return target.resolve().relative_to(resolved_root).as_posix()
    except (OSError, ValueError):
        return None


def _collect_one(
    repo_root: Path,
    entry: IndexEntry,
    policy: Policy,
    role_globs: Mapping[str, tuple[str, ...]],
    *,
    resolved_root: Path | None = None,
    collided_casefolds: frozenset[str] = frozenset(),
    seen_case_inodes: dict[tuple[str, int, int], str] | None = None,
) -> tuple[FileEntry, tuple[PendingFinding, ...]]:
    findings: list[PendingFinding] = []

    if "\\" in entry.path:
        # Git emits forward slashes on every platform, so a backslash in `ls-files` output is a
        # literal filename character from a POSIX index that Windows treats as a directory
        # separator and `require_repo_path` refuses on `FileEntry` and `Finding` (task 7.8).
        safe_path = _escape_backslash_path(entry.path)
        role_probe = entry.path.replace("\\", "/").strip("/") or safe_path
        roles = resolve_roles(role_probe, b"", role_globs)
        findings.append(
            _state(
                "skipped-nonportable-path",
                Severity.HIGH,
                safe_path,
                roles,
                f"tracked path {entry.path!r} contains a backslash, which is a filename byte "
                "on POSIX and a directory separator on Windows; nothing was scanned",
                evidence=entry.path,
            )
        )
        return (
            FileEntry(
                path=safe_path,
                sha256=None,
                roles=roles,
                skip_reason=SKIP_NONPORTABLE_PATH,
            ),
            tuple(findings),
        )

    target = repo_root / entry.path

    if entry.is_unmerged:
        # Nothing here is read, not even the working copy: its conflict markers are a merge
        # result nobody has agreed on, and scanning them would report a file that does not
        # exist yet. The roles come from the path alone, so the severity still follows
        # whether this is a file a rule would have cared about.
        roles = resolve_roles(entry.path, b"", role_globs)
        findings.append(
            _state(
                "skipped-unmerged",
                Severity.HIGH if _sensitive(roles) else Severity.WARN,
                entry.path,
                roles,
                "unmerged in the index: the path has staged versions and no committed "
                "content, so nothing was scanned",
            )
        )
        return (
            FileEntry(
                path=entry.path,
                sha256=None,
                roles=roles,
                skip_reason=SKIP_UNMERGED,
            ),
            tuple(findings),
        )

    if entry.is_submodule:
        return (
            FileEntry(path=entry.path, sha256=None, roles=(), skip_reason=SKIP_SUBMODULE),
            (),
        )

    if entry.is_symlink:
        # The target path is never read, so a tracked link cannot point the scanner outside
        # the repository or at /home/*/.ssh.
        findings.append(
            _state(
                "skipped-symlink",
                Severity.INFO,
                entry.path,
                resolve_roles(entry.path, b"", role_globs),
                "symlink in the index; its target was not read",
            )
        )
        return (
            FileEntry(
                path=entry.path,
                sha256=None,
                roles=resolve_roles(entry.path, b"", role_globs),
                skip_reason=SKIP_SYMLINK,
            ),
            tuple(findings),
        )

    reserved = _reserved_windows_device(entry.path)
    if reserved is not None:
        segment, device = reserved
        roles = resolve_roles(entry.path, b"", role_globs)
        findings.append(
            _state(
                "skipped-nonportable-path",
                Severity.HIGH,
                entry.path,
                roles,
                f"tracked path {entry.path!r} uses Windows reserved device name {device} "
                f"in segment {segment!r} and cannot be trusted as a regular file; nothing "
                "was scanned",
                evidence=entry.path,
            )
        )
        return (
            FileEntry(
                path=entry.path,
                sha256=None,
                roles=roles,
                skip_reason=SKIP_NONPORTABLE_PATH,
            ),
            tuple(findings),
        )

    try:
        st = os.lstat(target)
        if not stat.S_ISREG(st.st_mode):
            raise OSError("not a regular file")
        size_bytes = st.st_size
        with target.open("rb") as handle:
            head = handle.read(HEAD_BYTES)
    except OSError as exc:
        findings.append(
            _state(
                "skipped-unreadable",
                Severity.HIGH,
                entry.path,
                resolve_roles(entry.path, b"", role_globs),
                f"file could not be read: {type(exc).__name__}",
            )
        )
        return (
            FileEntry(
                path=entry.path,
                sha256=None,
                roles=resolve_roles(entry.path, b"", role_globs),
                skip_reason=SKIP_UNREADABLE,
            ),
            tuple(findings),
        )

    folded = entry.path.casefold()
    if folded in collided_casefolds:
        root_for_rel = resolved_root if resolved_root is not None else repo_root.resolve()
        actual_rel = _actual_disk_relpath(root_for_rel, target)
        inode_key = (folded, st.st_dev, st.st_ino)
        prior = (
            seen_case_inodes.get(inode_key)
            if (seen_case_inodes is not None and st.st_ino != 0)
            else None
        )
        if (actual_rel is not None and actual_rel != entry.path) or prior is not None:
            other = prior or actual_rel or folded
            roles = resolve_roles(entry.path, b"", role_globs)
            findings.append(
                _state(
                    "skipped-nonportable-path",
                    Severity.HIGH,
                    entry.path,
                    roles,
                    f"tracked path {entry.path!r} collides case-insensitively with {other!r} "
                    "on the working tree and cannot be read as itself; nothing was scanned",
                    evidence=f"{entry.path} -> {other}",
                )
            )
            return (
                FileEntry(
                    path=entry.path,
                    sha256=None,
                    roles=roles,
                    skip_reason=SKIP_NONPORTABLE_PATH,
                ),
                tuple(findings),
            )
        if seen_case_inodes is not None and st.st_ino != 0:
            seen_case_inodes[inode_key] = entry.path

    roles = resolve_roles(entry.path, head, role_globs)

    if size_bytes > policy.max_file_bytes:
        findings.append(
            _state(
                "skipped-oversize",
                Severity.HIGH if _sensitive(roles) else Severity.WARN,
                entry.path,
                roles,
                f"file is {size_bytes} bytes, over the {policy.max_file_bytes} byte limit, "
                "and was not read past its first 4096 bytes",
            )
        )
        return (
            FileEntry(
                path=entry.path,
                sha256=None,
                roles=roles,
                skip_reason=SKIP_OVERSIZE,
            ),
            tuple(findings),
        )

    data = head
    if size_bytes > len(head):
        with target.open("rb") as handle:
            data = handle.read(size_bytes + 1)
        if len(data) > size_bytes:
            # The file grew while it was being read. The bytes on disk are untrusted either
            # way, so keep what was read and record the mismatch as an unreadable skip.
            findings.append(
                _state(
                    "skipped-unreadable",
                    Severity.HIGH,
                    entry.path,
                    roles,
                    "file changed size while being read",
                )
            )
            return (
                FileEntry(
                    path=entry.path,
                    sha256=None,
                    roles=roles,
                    skip_reason=SKIP_UNREADABLE,
                ),
                tuple(findings),
            )

    sha256 = hashlib.sha256(data).hexdigest()

    if roles_from_magic(head):
        # Wasm, native binaries and archives are hashed and role-tagged, not decoded. Their
        # detector rules work on bytes, and running text rules over them would only produce
        # noise. The roles came from magic, so nothing here depends on the extension.
        return (
            FileEntry(path=entry.path, sha256=sha256, roles=roles),
            tuple(findings),
        )

    text, strict_failed = _decode(data)

    if "\x00" in text:
        findings.append(
            _state(
                "nul-in-text",
                Severity.HIGH,
                entry.path,
                roles,
                "NUL byte after BOM handling: the file is not the text its extension claims",
                evidence=_window(text, text.index("\x00")),
            )
        )

    if strict_failed:
        findings.append(
            _state(
                "non-utf8-text",
                Severity.HIGH if _sensitive(roles) else Severity.WARN,
                entry.path,
                roles,
                "bytes are not valid UTF-8 even after BOM handling",
            )
        )
        if not SCANNABLE_ROLES.intersection(roles):
            return (
                FileEntry(
                    path=entry.path,
                    sha256=sha256,
                    roles=roles,
                    skip_reason=SKIP_ENCODING,
                ),
                tuple(findings),
            )
        # Scannable role: the lenient decode stays in `text`, so content rules still see the
        # line that broke the encoding.

    return (
        FileEntry(
            path=entry.path,
            sha256=sha256,
            roles=roles,
            text=text,
        ),
        tuple(findings),
    )


def _window(text: str, index: int, width: int = 40) -> str:
    start = max(0, index - width)
    return text[start : index + width].replace("\x00", "<NUL>")


def _is_submodule_header(stripped: str) -> bool:
    """True when `stripped` is `[submodule "<non-empty name>"]` with no regex backtracking."""
    if not (stripped.startswith("[") and stripped.endswith("]")):
        return False
    inner = stripped[1:-1].strip()
    head, sep, rest = inner.partition('"')
    return (
        head.strip().lower() == "submodule" and sep == '"' and rest.endswith('"') and len(rest) >= 2
    )


def _clean_gitconfig_value(raw: str) -> str:
    """Extract a `.gitmodules` value, honoring quotes and inline `#` / `;` comments."""
    text = raw.strip()
    if not text:
        return ""
    if text.startswith('"'):
        chars: list[str] = []
        escaped = False
        for index in range(1, len(text)):
            ch = text[index]
            if escaped:
                chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(ch, ch))
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                tail = text[index + 1 :].strip()
                if tail and not tail.startswith(("#", ";")):
                    return ""
                return "".join(chars).strip()
            chars.append(ch)
        return ""
    for index, ch in enumerate(text):
        if ch in ("#", ";"):
            return text[:index].strip()
    return text.strip()


def _parse_gitmodules(text: str, line_cap: int) -> tuple[_GitmoduleSection, ...]:
    """Parse `.gitmodules` into sections without regexes, respecting `line_cap`."""
    sections: list[_GitmoduleSection] = []
    header: str | None = None
    header_line = 0
    valid_header = False
    paths: list[str] = []
    urls: list[str] = []

    def flush() -> None:
        if header is not None:
            sections.append(
                _GitmoduleSection(
                    header=header,
                    line=header_line,
                    valid_header=valid_header,
                    paths=tuple(paths),
                    urls=tuple(urls),
                )
            )

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        if len(raw_line) > line_cap:
            if header is None:
                sections.append(
                    _GitmoduleSection(
                        header="<over-cap-line>",
                        line=line_no,
                        valid_header=False,
                        paths=(),
                        urls=(),
                    )
                )
            else:
                valid_header = False
            continue
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(("#", ";")):
            continue
        if stripped.startswith("["):
            flush()
            header = stripped
            header_line = line_no
            valid_header = _is_submodule_header(stripped)
            paths = []
            urls = []
            continue
        if header is None:
            header = stripped
            header_line = line_no
            valid_header = False
            paths = []
            urls = []
        key, sep, rhs = stripped.partition("=")
        if not sep:
            valid_header = False
            continue
        key_name = key.strip().lower()
        value = _clean_gitconfig_value(rhs)
        if key_name == "path":
            paths.append(value)
        elif key_name == "url":
            urls.append(value)

    flush()
    return tuple(sections)


def _submodule_findings(
    index_entries: tuple[IndexEntry, ...],
    gitmodules_entry: FileEntry | None,
    gitmodules_has_state_finding: bool,
    policy: Policy,
    role_globs: Mapping[str, tuple[str, ...]],
) -> tuple[PendingFinding, ...]:
    """Cross-check mode `160000` gitlinks against `.gitmodules` and `policy.submodules` (7.2).

    A gitlink in the index carries only a path and a commit SHA; the upstream URL lives in
    `.gitmodules`. Every disagreement between the two, and every gitlink whose URL is not
    authorized by the trusted `policy.submodules` list, produces its own scanner-state finding.
    """
    gitlinks = tuple(
        entry for entry in index_entries if entry.is_submodule and not entry.is_unmerged
    )
    gitmodules_text = (
        gitmodules_entry.text
        if (
            gitmodules_entry is not None
            and gitmodules_entry.skip_reason is None
            and not gitmodules_has_state_finding
        )
        else None
    )
    if not gitlinks and gitmodules_text is None:
        return ()

    sections = (
        _parse_gitmodules(gitmodules_text, policy.line_cap) if gitmodules_text is not None else ()
    )
    by_path: dict[str, list[_GitmoduleSection]] = {}
    for section in sections:
        if section.is_well_formed:
            by_path.setdefault(section.paths[0], []).append(section)

    gitlink_paths = {entry.path for entry in gitlinks}
    allowed_urls = frozenset(policy.submodules)
    out: list[PendingFinding] = []

    for entry in gitlinks:
        commit_ref = entry.sha[:12] if entry.sha else "unknown"
        matches = by_path.get(entry.path, [])
        if len(matches) != 1:
            detail = (
                "matches multiple entries in .gitmodules"
                if len(matches) > 1
                else "has no matching path and url in .gitmodules"
            )
            out.append(
                _state(
                    "submodule-unmapped",
                    Severity.HIGH,
                    entry.path,
                    (),
                    f"gitlink at {entry.path} (index commit {commit_ref}) {detail}; "
                    "its subtree is not scanned here",
                    evidence=f"{entry.path}@{commit_ref}",
                )
            )
            continue
        url = matches[0].urls[0]
        allowed = url in allowed_urls
        status = (
            "is allowed by policy.submodules" if allowed else "is not listed in policy.submodules"
        )
        out.append(
            _state(
                "submodule-present",
                Severity.WARN if allowed else Severity.HIGH,
                entry.path,
                (),
                f"gitlink at {entry.path} (index commit {commit_ref}, .gitmodules url {url!r}) "
                f"{status}; its subtree is not scanned here",
                evidence=f"{entry.path}@{commit_ref} {url}",
            )
        )

    gm_roles = (
        gitmodules_entry.roles
        if gitmodules_entry is not None
        else resolve_roles(GITMODULES_PATH, b"", role_globs)
    )
    for section in sections:
        if not section.is_well_formed:
            out.append(
                _state(
                    "submodule-orphan",
                    Severity.WARN,
                    GITMODULES_PATH,
                    gm_roles,
                    f".gitmodules section {section.header!r} at line {section.line} is missing "
                    "a single path and url",
                    evidence=section.header,
                    line=section.line,
                )
            )
            continue
        sub_path = section.paths[0]
        sub_url = section.urls[0]
        if sub_path not in gitlink_paths:
            out.append(
                _state(
                    "submodule-orphan",
                    Severity.WARN,
                    GITMODULES_PATH,
                    gm_roles,
                    f".gitmodules entry for {sub_path} (url {sub_url!r}) has no mode 160000 "
                    "gitlink in the index",
                    evidence=f"{sub_path} {sub_url}",
                    line=section.line,
                )
            )

    return tuple(out)


def collect(
    repo_root: Path,
    policy: Policy,
    role_globs: Mapping[str, tuple[str, ...]],
) -> Collection:
    """Read every tracked file once and resolve its roles.

    A file that cannot be read produces a finding and an entry with `text=None`; it never
    disappears from the report.
    """
    index_entries = list_tracked_files(repo_root)
    casefold_counts: dict[str, int] = {}
    for index_entry in index_entries:
        if not index_entry.is_unmerged and not index_entry.is_submodule:
            folded = index_entry.path.casefold()
            casefold_counts[folded] = casefold_counts.get(folded, 0) + 1
    collided_casefolds = frozenset(folded for folded, count in casefold_counts.items() if count > 1)
    resolved_root = repo_root.resolve() if collided_casefolds else None
    seen_case_inodes: dict[tuple[str, int, int], str] = {}
    entries: list[FileEntry] = []
    findings: list[PendingFinding] = []
    gitmodules_entry: FileEntry | None = None
    gitmodules_has_state_finding = False
    for index_entry in index_entries:
        entry, entry_findings = _collect_one(
            repo_root,
            index_entry,
            policy,
            role_globs,
            resolved_root=resolved_root,
            collided_casefolds=collided_casefolds,
            seen_case_inodes=seen_case_inodes,
        )
        entries.append(entry)
        findings.extend(entry_findings)
        if entry.path == GITMODULES_PATH and "\\" not in index_entry.path:
            gitmodules_entry = entry
            gitmodules_has_state_finding = bool(entry_findings)
    findings.extend(
        _submodule_findings(
            index_entries,
            gitmodules_entry,
            gitmodules_has_state_finding,
            policy,
            role_globs,
        )
    )
    return Collection(entries=tuple(entries), pending=tuple(findings))
