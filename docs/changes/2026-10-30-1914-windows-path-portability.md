---
date: 2026-10-30 19:14 UTC
tasks: 7.8, 2.2, 2.4
summary: Close #28 (7.8): the collector refuses a tracked path it cannot read as itself as skipped-nonportable-path HIGH, for Windows reserved device names, a literal backslash in a filename and case-insensitive index collisions.
---

Close #28 (task 7.8): reproduce all three Windows and non-portable path failure modes on
a real Windows 11 (`win32`, CPython 3.12.10, NTFS) runner and settle the reserved-
device-name, literal-backslash and case-collision behavior across platforms. Empirical
reproduction on `main` before the fix: (1) staging `100644,<payload_blob>,NUL` (and
`nul.js`, `src/NUL`, `src/nul.postcss.config.mjs`) via `git -c core.protectNTFS=false
update-index --add --cacheinfo` with no file on disk caused `os.stat` to return `st_mode
= 0o20000` (`S_ISCHR = True`, `S_ISREG = False`), `os.path.getsize` to return `0` and
`target.open("rb").read()` to read `b""` from `\\.\NUL` (`sha256 = e3b0c44...`, `text =
""`, `skip_reason = None`, `pending = ()`), silently scanning zero bytes instead of the
staged payload, while staging `CON` or `aux.js` hung `collect()` indefinitely waiting on
the Windows console/serial character device and opening `\\?\<repo>\NUL` bypassed DOS
device translation and raised `FileNotFoundError` (`[WinError 2]`); (2) staging
`dir\postcss.config.mjs` crashed `collect()` inside `FileEntry.__post_init__`
(`model.require_repo_path`) with `ValueError: path must be repo-relative with forward
slashes: 'dir\\postcss.config.mjs'`, while on Windows `repo_root /
"dir\\postcss.config.mjs"` also treated `\` as a directory separator; and (3) staging
both `postcss.config.MJS` (`eval(x)`) and `postcss.config.mjs` (`export default {}` on
disk) on NTFS resolved both paths to the same working-tree file (`os.path.samefile ==
True`, `(repo / "postcss.config.MJS").resolve().name == "postcss.config.mjs"`), reading
the clean file twice and dropping the staged payload, while `roles._segment_pattern`
missed `POSTCSS.CONFIG.MJS` because it lacked `re.IGNORECASE`.

Fix: `STATE_RULE_IDS` in `model.py` gains `skipped-nonportable-path` (counted under
`SKIP_NONPORTABLE_PATH = "nonportable-path"` in `files_skipped`, always `Severity.HIGH`
and non-suppressible because a crafted path name hides its own role);
`roles._segment_pattern` compiles with `re.IGNORECASE`; `collector.py` rejects any
tracked path containing a literal `\` (normalizing `\` to `/` in `FileEntry.path` and
`Finding.path` so `model.require_repo_path` holds while quoting the raw index path in
`evidence`), any path segment whose stem before the first dot matches a Windows DOS
device name (`CON`, `PRN`, `AUX`, `NUL`, `COM1`..`COM9`, `LPT1`..`LPT9`, superscripts
`COM¹`..`COM³`/`LPT¹`..`LPT³`, `CONIN$`, `CONOUT$`, case-insensitively and before any
`os.lstat` or `open` call on every OS), any index collision where multiple stage-0 paths
share `path.casefold()`, any working-tree lookup whose on-disk case spelling
(`Path.resolve()`) or `(st_dev, st_ino)` collides or whose working-tree `git` blob SHA-1
disagrees with the staged index SHA, and any working-tree file where `not
stat.S_ISREG(os.lstat(target).st_mode)` (`skipped-unreadable`).
`TestWindowsAndPathPortability` in `tests/unit/test_collector.py` (16 cases, including
the positive-and-negative temporary-repository fixture gate for `skipped-nonportable-
path`) and `TestGlob` in `tests/unit/test_roles.py` (2 cases) cover every case, and
`test_collector.py` now collects and passes on Windows as well as Linux after guarding
`os.geteuid()` and falling back to `120000` index entries when unprivileged Windows
symlink creation raises `[WinError 1314]`.

Updated `ARCHITECTURE.md` 6.1, 6.2 and 8, `ARCHITECTURE_ESSENTIALS.md` 6, `README.md`,
`site/index.html`, `site/trust.html` and `ROADMAP.md`
