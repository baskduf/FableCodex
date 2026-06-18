from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "codex-fable5" / "skills" / "codex-fable5"
SCRIPTS = SKILL_ROOT / "scripts"
BIN = ROOT / "plugins" / "codex-fable5" / "bin"


def load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_skill_body() -> str:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n.*?\r?\n---\r?\n(?P<body>.*)\Z", skill, re.DOTALL)
    if match is None:
        raise AssertionError("SKILL.md frontmatter block not found")
    return match.group("body")


def parse_routing_map(body: str) -> list[tuple[str, str]]:
    match = re.search(r"^## Routing Map\r?\n\r?\n(?P<table>.*?)(?:\r?\n## |\Z)", body, re.DOTALL | re.MULTILINE)
    if match is None:
        raise AssertionError("Routing Map section not found")
    rows: list[tuple[str, str]] = []
    for line in match.group("table").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or cells[0] == "Signal" or set(cells[0]) == {"-"}:
            continue
        rows.append((cells[0], cells[1]))
    return rows


def read_readme_fable_pin() -> str:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(
        r"`elder-plinius/CL4R1T4S`\s+`ANTHROPIC/CLAUDE-FABLE-5\.md`\s+"
        r"at commit\s+`([0-9a-f]{40})`",
        readme,
    )
    if match is None:
        raise AssertionError("pinned FABLE-5 SHA not found in README")
    return match.group(1)


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fable_coverage = load_script("fable_coverage")
        cls.codex_goals = load_script("codex_goals")
        cls.codex_findings = load_script("codex_findings")
        cls.make_litellm_config = load_script("make_litellm_config")

    def test_manifest_json_files_are_valid(self) -> None:
        manifest_paths = [
            ROOT / ".agents" / "plugins" / "marketplace.json",
            ROOT / "plugins" / "codex-fable5" / ".codex-plugin" / "plugin.json",
            ROOT / "examples" / "hooks.json",
        ]
        for path in manifest_paths:
            with self.subTest(path=path):
                parsed = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(parsed, dict)

    def test_marketplace_plugin_paths_resolve_to_skill(self) -> None:
        marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        root = ROOT.resolve()
        for plugin_entry in marketplace["plugins"]:
            with self.subTest(plugin=plugin_entry["name"]):
                plugin_root = (ROOT / plugin_entry["source"]["path"]).resolve()
                self.assertTrue(plugin_root.is_relative_to(root))

                plugin_manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
                plugin_manifest = json.loads(plugin_manifest_path.read_text(encoding="utf-8"))
                skills_root = (plugin_root / plugin_manifest["skills"]).resolve()
                skill_path = skills_root / plugin_manifest["name"] / "SKILL.md"

                self.assertTrue(plugin_root.is_dir())
                self.assertTrue(plugin_manifest_path.is_file())
                self.assertTrue(skills_root.is_relative_to(plugin_root))
                self.assertTrue(skills_root.is_dir())
                self.assertTrue(skill_path.is_file())

    def test_license_contains_full_agpl_text(self) -> None:
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", text)
        self.assertIn("Version 3, 19 November 2007", text)
        self.assertIn("TERMS AND CONDITIONS", text)
        self.assertIn("END OF TERMS AND CONDITIONS", text)
        self.assertGreaterEqual(len(text.splitlines()), 600)

    def test_license_metadata_declares_agpl_or_later(self) -> None:
        plugin = json.loads(
            (ROOT / "plugins" / "codex-fable5" / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")

        self.assertEqual(plugin["license"], "AGPL-3.0-or-later")
        self.assertIn("AGPL-3.0-or-later", readme)
        self.assertIn("AGPL-3.0-or-later", notice)

    def test_readme_localizations_cover_core_workflow(self) -> None:
        readmes = [
            "README.md",
            "README.ko.md",
            "README.ja.md",
            "README.zh-CN.md",
            "README.zh-TW.md",
        ]
        required_snippets = [
            "codex-fable5 goals create",
            "codex-fable5 findings gate",
            ".codex-fable5/",
            "AGPL-3.0-or-later",
        ]

        for relative in readmes:
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                for other in readmes:
                    if other != relative:
                        self.assertIn(other, text)
                for snippet in required_snippets:
                    self.assertIn(snippet, text)

    def test_skill_body_keeps_core_loop_concise(self) -> None:
        body = read_skill_body()
        routes = parse_routing_map(body)
        route_text = "\n".join(f"{signal} => {target}" for signal, target in routes)

        self.assertLessEqual(len(body.splitlines()), 90)
        self.assertLessEqual(len(body.split()), 950)
        for heading in ["## Non-Negotiables", "## Core Loop", "## Routing Map"]:
            self.assertIn(heading, body)

        self.assertIn("final verification gate", body)
        self.assertIn("Require the findings gate before final completion", body)
        self.assertIn("Communicate in Codex style", body)

        self.assertRegex(route_text, r"Multi-step.*task-routing\.md.*goal and findings gates")
        for target in [
            "references/task-routing.md",
            "references/operating-structure.md",
            "references/fable-to-codex-map.md",
            "references/coverage-matrix.md",
            "scripts/fable_coverage.py --source",
            "references/provider-bridge.md",
            "references/currentness-safety.md",
            "references/artifact-and-tooling.md",
            "references/connectors-and-mcp.md",
            "references/state-memory.md",
            "references/provenance.md",
        ]:
            self.assertIn(target, route_text)

    def test_plugin_version_is_documented_in_changelog(self) -> None:
        plugin = json.loads(
            (ROOT / "plugins" / "codex-fable5" / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn(f"## {plugin['version']}", changelog)

    def test_oss_community_files_exist(self) -> None:
        required_paths = [
            "CODE_OF_CONDUCT.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "GOVERNANCE.md",
            "ROADMAP.md",
            "SECURITY.md",
            "SUPPORT.md",
            ".gitignore",
            ".github/CODEOWNERS",
            ".github/dependabot.yml",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/ISSUE_TEMPLATE/config.yml",
            ".github/pull_request_template.md",
            ".github/workflows/ci.yml",
            "docs/RELEASING.md",
        ]
        for relative in required_paths:
            with self.subTest(path=relative):
                path = ROOT / relative
                self.assertTrue(path.exists(), f"missing {relative}")
                self.assertGreater(path.stat().st_size, 0, f"empty {relative}")

    def test_ci_workflow_runs_project_verification(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v6", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertIn("python3 -m unittest discover -s tests -v", workflow)
        self.assertIn("python3 -m py_compile", workflow)
        self.assertIn("codex_findings.py", workflow)
        self.assertIn("sh -n plugins/codex-fable5/bin/codex-fable5", workflow)
        self.assertIn("sh -n plugins/codex-fable5/bin/codex-findings", workflow)
        self.assertIn("sh -n plugins/codex-fable5/bin/codex-goals", workflow)
        self.assertIn("fable_coverage.py", workflow)
        self.assertIn('python-version: ["3.11", "3.12", "3.13"]', workflow)

    def test_repo_hygiene_files_cover_local_artifacts(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

        self.assertIn(".codex-fable5/", gitignore)
        self.assertIn("__pycache__/", gitignore)
        self.assertIn("* @baskduf", codeowners)
        self.assertIn('package-ecosystem: "github-actions"', dependabot)

    def test_coverage_matrix_is_valid(self) -> None:
        script = SCRIPTS / "fable_coverage.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("coverage matrix valid", result.stdout)
        self.assertIn("implemented=", result.stdout)

    def test_coverage_matrix_validates_against_pinned_source(self) -> None:
        """When --source points at the pinned upstream FABLE-5, headings
        must match the matrix exactly. The README pins the upstream commit
        SHA; this test fetches the same bytes the CI workflow fetches and
        runs the validator against the local matrix."""
        script = SCRIPTS / "fable_coverage.py"
        pin = read_readme_fable_pin()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "CLAUDE-FABLE-5.md"
            url = (
                f"https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/"
                f"{pin}/ANTHROPIC/CLAUDE-FABLE-5.md"
            )
            download = subprocess.run(
                ["curl", "-fsSL", url, "-o", str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
            if download.returncode != 0:
                self.skipTest(f"could not fetch pinned source (network?): {download.stderr[:200]}")
            result = subprocess.run(
                [sys.executable, str(script), "--source", str(source)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                result.returncode, 0,
                f"matrix/source mismatch:\nstdout={result.stdout}\nstderr={result.stderr}",
            )
            self.assertIn("source headings", result.stdout)
            self.assertIn("matrix rows", result.stdout)

    def test_ci_workflow_validates_against_pinned_source(self) -> None:
        """The CI workflow must fetch the pinned upstream source and pass
        it to the validator. Without this, the default `--matrix`-only run
        is self-consistent and can hide a fabricated row."""
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("CLAUDE-FABLE-5.md", workflow)
        self.assertIn("elder-plinius/CL4R1T4S", workflow)
        fetch_step = re.search(
            r"      - name: Fetch pinned FABLE-5 source\n(?P<body>.*?)(?:\n      - name: |\Z)",
            workflow,
            re.DOTALL,
        )
        self.assertIsNotNone(fetch_step, "CI workflow must define the pinned source fetch step")
        assert fetch_step is not None  # for type checkers
        fetch_step_body = fetch_step.group("body")
        self.assertIn(
            "raw.githubusercontent.com/elder-plinius/CL4R1T4S/${PIN}/ANTHROPIC/CLAUDE-FABLE-5.md",
            fetch_step_body,
            "CI should fetch the public pinned source directly, matching the release checklist",
        )
        self.assertNotIn(
            "Authorization: Bearer",
            fetch_step_body,
            "CI source fetch should not rely on a hand-built Authorization header; malformed quoting can hide curl failures",
        )
        pin_match = re.search(r'PIN="([0-9a-f]{40})"', workflow)
        self.assertIsNotNone(pin_match, "CI workflow must define the pinned upstream SHA")
        assert pin_match is not None  # for type checkers
        self.assertEqual(
            read_readme_fable_pin(),
            pin_match.group(1),
            "CI workflow pin must match README source note pin",
        )
        # The validator invocation must include --source.
        # Look for lines that invoke fable_coverage.py and contain --source.
        has_source_arg = False
        for line in workflow.splitlines():
            if "fable_coverage.py" in line and "--source" in line:
                has_source_arg = True
                break
        self.assertTrue(
            has_source_arg,
            "CI workflow must pass --source to fable_coverage.py "
            "so the matrix is validated against the upstream FABLE-5 source",
        )

    def test_release_checklist_validates_against_pinned_source(self) -> None:
        releasing = (ROOT / "docs" / "RELEASING.md").read_text(encoding="utf-8")

        self.assertIn("README.md", releasing)
        self.assertIn("raw.githubusercontent.com/elder-plinius/CL4R1T4S/${PIN}", releasing)
        self.assertIn("--source build/fable5/CLAUDE-FABLE-5.md", releasing)
        self.assertIn(r"\s+`ANTHROPIC/CLAUDE-FABLE-5\.md`\s+at commit\s+", releasing)
        self.assertNotIn(r"\\s+", releasing)

    def test_user_facing_wrappers_run_from_path(self) -> None:
        env = {**os.environ, "PATH": f"{BIN}{os.pathsep}{os.environ['PATH']}"}
        for command in ["codex-fable5", "codex-findings", "codex-goals"]:
            with self.subTest(command=command):
                wrapper = BIN / command
                self.assertTrue(wrapper.is_file())
                self.assertTrue(os.access(wrapper, os.X_OK))

                syntax = subprocess.run(
                    ["sh", "-n", str(wrapper)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(syntax.returncode, 0, syntax.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            status = subprocess.run(
                ["codex-fable5", "status"],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn("0 findings", status.stdout)
            self.assertIn("no goal plan", status.stdout)

            created = subprocess.run(
                [
                    "codex-fable5",
                    "goals",
                    "create",
                    "--brief",
                    "Wrapper smoke",
                    "--goal",
                    "inspect::Check wrapper path",
                ],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertIn("plan created", created.stdout)

            started = subprocess.run(
                ["codex-fable5", "goals", "next"],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(started.returncode, 0, started.stderr)

            added = subprocess.run(
                [
                    "codex-fable5",
                    "findings",
                    "add",
                    "--title",
                    "Wrapper finding",
                    "--evidence",
                    "PATH wrapper should call the findings script.",
                ],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            self.assertIn("goal=G001", added.stdout)

            status_with_plan = subprocess.run(
                ["codex-fable5", "status"],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(status_with_plan.returncode, 0, status_with_plan.stderr)
            self.assertIn("1 open", status_with_plan.stdout)
            self.assertIn("0/1 complete", status_with_plan.stdout)

    def test_coverage_helpers_parse_headings_and_matrix_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.md"
            matrix = tmp_path / "matrix.md"
            source.write_text(
                textwrap.dedent(
                    """\
                    # Root
                    ## alpha
                    ### beta
                    ## gamma
                    """
                ),
                encoding="utf-8",
            )
            matrix.write_text(
                textwrap.dedent(
                    """\
                    | Source section | Status | Codex surface | Decision |
                    | --- | --- | --- | --- |
                    | `alpha` | adapted | `x.md` | Keep behavior. |
                    | `alpha > beta` | implemented | `y.py` | Direct support. |
                    | `gamma` | not_applicable | `z.md` | Excluded. |
                    """
                ),
                encoding="utf-8",
            )

            sections = self.fable_coverage.extract_source_sections(source)
            rows = self.fable_coverage.extract_matrix(matrix)

        self.assertEqual(sections, ["alpha", "alpha > beta", "gamma"])
        self.assertEqual(
            rows,
            {"alpha": "adapted", "alpha > beta": "implemented", "gamma": "not_applicable"},
        )

    def test_coverage_helpers_parse_sources_without_h1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.md"
            source.write_text(
                textwrap.dedent(
                    """\
                    ## alpha
                    ### beta
                    ## gamma
                    """
                ),
                encoding="utf-8",
            )

            sections = self.fable_coverage.extract_source_sections(source)

        self.assertEqual(sections, ["alpha", "alpha > beta", "gamma"])

    def test_goal_ledger_flow_and_final_verification_gate(self) -> None:
        script = SCRIPTS / "codex_goals.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            created = run(
                "create",
                "--brief",
                "Smoke",
                "--goal",
                "inspect::Check state",
                "--goal",
                "verify::Confirm final state",
            )
            self.assertEqual(created.returncode, 0, created.stderr)

            first = run("next")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("G001 inspect", first.stdout)

            done_first = run(
                "checkpoint",
                "--id",
                "G001",
                "--status",
                "complete",
                "--evidence",
                "first story evidence",
            )
            self.assertEqual(done_first.returncode, 0, done_first.stderr)

            final = run("next")
            self.assertEqual(final.returncode, 0, final.stderr)
            self.assertIn("Final story", final.stdout)

            missing_verify = run(
                "checkpoint",
                "--id",
                "G002",
                "--status",
                "complete",
                "--evidence",
                "final evidence",
            )
            self.assertNotEqual(missing_verify.returncode, 0)
            self.assertIn("final story requires", missing_verify.stderr)

            done_final = run(
                "checkpoint",
                "--id",
                "G002",
                "--status",
                "complete",
                "--evidence",
                "final evidence",
                "--verify-cmd",
                "smoke",
                "--verify-evidence",
                "accepted",
            )
            self.assertEqual(done_final.returncode, 0, done_final.stderr)

            status = run("status")
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn("2/2 complete", status.stdout)

    def test_goal_ledger_failed_story_is_not_reported_complete(self) -> None:
        script = SCRIPTS / "codex_goals.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            created = run("create", "--brief", "Smoke", "--goal", "inspect::Check state")
            self.assertEqual(created.returncode, 0, created.stderr)

            first = run("next")
            self.assertEqual(first.returncode, 0, first.stderr)

            failed = run("checkpoint", "--id", "G001", "--status", "failed")
            self.assertEqual(failed.returncode, 0, failed.stderr)
            self.assertIn("plan is not complete", failed.stdout)
            self.assertNotIn("all stories complete", failed.stdout)

            next_story = run("next")
            self.assertEqual(next_story.returncode, 0, next_story.stderr)
            self.assertIn("Reopened G001 from failed", next_story.stdout)
            self.assertNotIn("all stories complete", next_story.stdout + next_story.stderr)

            recovered = run(
                "checkpoint",
                "--id",
                "G001",
                "--status",
                "complete",
                "--evidence",
                "retry evidence",
                "--verify-cmd",
                "smoke",
                "--verify-evidence",
                "accepted",
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertIn("all stories complete", recovered.stdout)

    def test_goal_ledger_failed_story_blocks_later_pending_stories(self) -> None:
        script = SCRIPTS / "codex_goals.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            created = run(
                "create",
                "--brief",
                "Smoke",
                "--goal",
                "inspect::Check state",
                "--goal",
                "verify::Confirm final state",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(run("next").returncode, 0)

            failed = run("checkpoint", "--id", "G001", "--status", "failed")
            self.assertEqual(failed.returncode, 0, failed.stderr)
            self.assertIn("open stories remain blocked", failed.stdout)

            next_story = run("next")
            self.assertEqual(next_story.returncode, 0, next_story.stderr)
            self.assertIn("Reopened G001 from failed", next_story.stdout)
            self.assertIn("G001 inspect", next_story.stdout)
            self.assertNotIn("G002", next_story.stdout + next_story.stderr)

            recovered = run(
                "checkpoint",
                "--id",
                "G001",
                "--status",
                "complete",
                "--evidence",
                "retry evidence",
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)

            next_after_recovery = run("next")
            self.assertEqual(next_after_recovery.returncode, 0, next_after_recovery.stderr)
            self.assertIn("G002 verify", next_after_recovery.stdout)

    def test_goal_ledger_blocked_story_can_be_reopened(self) -> None:
        script = SCRIPTS / "codex_goals.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            created = run("create", "--brief", "Smoke", "--goal", "inspect::Check state")
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(run("next").returncode, 0)

            blocked = run("checkpoint", "--id", "G001", "--status", "blocked")
            self.assertEqual(blocked.returncode, 0, blocked.stderr)
            self.assertIn("plan is not complete", blocked.stdout)

            reopened = run("next")
            self.assertEqual(reopened.returncode, 0, reopened.stderr)
            self.assertIn("Reopened G001 from blocked", reopened.stdout)

    def test_findings_flow_blocks_gate_until_resolved(self) -> None:
        script = SCRIPTS / "codex_findings.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            added = run(
                "add",
                "--title",
                "Final gate ignores unresolved review issue",
                "--severity",
                "high",
                "--source",
                "subagent",
                "--evidence",
                "Review found an accepted finding without a closeout gate.",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            self.assertIn("added F001", added.stdout)

            gate_failed = run("gate")
            self.assertNotEqual(gate_failed.returncode, 0)
            self.assertIn("findings gate failed", gate_failed.stdout)
            self.assertIn("F001 [open] high", gate_failed.stdout)

            missing_verification = run(
                "resolve",
                "--id",
                "F001",
                "--evidence",
                "Added findings gate.",
            )
            self.assertNotEqual(missing_verification.returncode, 0)
            self.assertIn("verify-evidence", missing_verification.stderr)

            resolved = run(
                "resolve",
                "--id",
                "F001",
                "--evidence",
                "Added findings gate.",
                "--verify-cmd",
                "python3 -m unittest discover -s tests -v",
                "--verify-evidence",
                "targeted tests passed",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)

            gate_passed = run("gate")
            self.assertEqual(gate_passed.returncode, 0, gate_passed.stderr)
            self.assertIn("findings gate passed", gate_passed.stdout)

            status = run("status")
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn("1 resolved", status.stdout)

    def test_findings_auto_attach_to_active_goal_and_blocked_gate_policy(self) -> None:
        goals_script = SCRIPTS / "codex_goals.py"
        findings_script = SCRIPTS / "codex_findings.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            self.assertEqual(
                run(
                    goals_script,
                    "create",
                    "--brief",
                    "Smoke",
                    "--goal",
                    "inspect::Check state",
                ).returncode,
                0,
            )
            self.assertEqual(run(goals_script, "next").returncode, 0)

            added = run(
                findings_script,
                "add",
                "--title",
                "Unresolved issue tied to active goal",
                "--evidence",
                "The active goal should be inferred when no --goal is provided.",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            self.assertIn("goal=G001", added.stdout)

            findings = json.loads((cwd / ".codex-fable5" / "findings.json").read_text())
            self.assertEqual(findings["findings"][0]["goal"], "G001")

            blocked = run(
                findings_script,
                "block",
                "--id",
                "F001",
                "--reason",
                "Needs user decision.",
            )
            self.assertEqual(blocked.returncode, 0, blocked.stderr)

            default_gate = run(findings_script, "gate")
            self.assertNotEqual(default_gate.returncode, 0)
            self.assertIn("F001 [blocked]", default_gate.stdout)

            allow_blocked_gate = run(findings_script, "gate", "--allow-blocked")
            self.assertEqual(allow_blocked_gate.returncode, 0, allow_blocked_gate.stderr)

    def test_findings_parallel_adds_do_not_lose_entries(self) -> None:
        script = SCRIPTS / "codex_findings.py"
        with tempfile.TemporaryDirectory() as tmp:
            processes = [
                subprocess.Popen(
                    [
                        sys.executable,
                        str(script),
                        "add",
                        "--title",
                        f"Finding {index}",
                        "--evidence",
                        "Parallel add should persist exactly once.",
                    ],
                    cwd=tmp,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for index in range(20)
            ]
            results = [process.communicate() + (process.returncode,) for process in processes]

            for stdout, stderr, returncode in results:
                self.assertEqual(returncode, 0, stderr or stdout)

            data = json.loads((Path(tmp) / ".codex-fable5" / "findings.json").read_text())
            ids = [finding["id"] for finding in data["findings"]]

        self.assertEqual(len(ids), 20)
        self.assertEqual(len(set(ids)), 20)
        self.assertEqual(ids, [f"F{index:03d}" for index in range(1, 21)])

    def test_lock_fallback_times_out_on_stale_lockdir(self) -> None:
        for module in [self.codex_findings, self.codex_goals]:
            with self.subTest(module=module.__name__):
                with tempfile.TemporaryDirectory() as tmp:
                    cwd = Path(tmp)
                    state_dir = cwd / ".codex-fable5"
                    state_dir.mkdir()
                    (state_dir / "state.lockdir").mkdir()

                    old_cwd = Path.cwd()
                    original_fcntl = module.fcntl
                    original_timeout = module.LOCK_TIMEOUT_SECONDS
                    try:
                        os.chdir(cwd)
                        module.fcntl = None
                        module.LOCK_TIMEOUT_SECONDS = 0.01
                        with self.assertRaises(SystemExit) as raised:
                            with module.locked_state():
                                pass
                    finally:
                        module.fcntl = original_fcntl
                        module.LOCK_TIMEOUT_SECONDS = original_timeout
                        os.chdir(old_cwd)

                    self.assertIn("timed out waiting for state lock", str(raised.exception))

    def test_goal_final_checkpoint_requires_findings_gate(self) -> None:
        goals_script = SCRIPTS / "codex_goals.py"
        findings_script = SCRIPTS / "codex_findings.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            created = run(
                goals_script,
                "create",
                "--brief",
                "Smoke",
                "--goal",
                "verify::Confirm final state",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(run(goals_script, "next").returncode, 0)

            added = run(
                findings_script,
                "add",
                "--title",
                "Open review issue",
                "--evidence",
                "The final checkpoint should fail while this is open.",
            )
            self.assertEqual(added.returncode, 0, added.stderr)

            blocked_checkpoint = run(
                goals_script,
                "checkpoint",
                "--id",
                "G001",
                "--status",
                "complete",
                "--evidence",
                "final evidence",
                "--verify-cmd",
                "smoke",
                "--verify-evidence",
                "accepted",
            )
            self.assertNotEqual(blocked_checkpoint.returncode, 0)
            self.assertIn("final story requires findings gate", blocked_checkpoint.stderr)
            self.assertIn("F001", blocked_checkpoint.stderr)

            resolved = run(
                findings_script,
                "resolve",
                "--id",
                "F001",
                "--evidence",
                "Closed the review issue.",
                "--verify-evidence",
                "manual verification accepted",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)

            complete = run(
                goals_script,
                "checkpoint",
                "--id",
                "G001",
                "--status",
                "complete",
                "--evidence",
                "final evidence",
                "--verify-cmd",
                "smoke",
                "--verify-evidence",
                "accepted",
            )
            self.assertEqual(complete.returncode, 0, complete.stderr)

    def test_goal_final_checkpoint_rejects_malformed_findings_ledger(self) -> None:
        goals_script = SCRIPTS / "codex_goals.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(goals_script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            self.assertEqual(
                run("create", "--brief", "Smoke", "--goal", "verify::Confirm final state").returncode,
                0,
            )
            self.assertEqual(run("next").returncode, 0)
            findings_path = cwd / ".codex-fable5" / "findings.json"
            findings_path.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "id": "F001",
                                "goal": "G001",
                                "title": "Malformed status",
                                "severity": "high",
                                "source": "review",
                                "status": "OPEN",
                                "location": "",
                                "evidence": "Uppercase status should not be accepted by final gate.",
                                "resolution": "",
                                "verify_cmd": "",
                                "verify_evidence": "",
                                "created": "test",
                                "updated": "",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            complete = run(
                "checkpoint",
                "--id",
                "G001",
                "--status",
                "complete",
                "--evidence",
                "final evidence",
                "--verify-cmd",
                "smoke",
                "--verify-evidence",
                "accepted",
            )

            self.assertNotEqual(complete.returncode, 0)
            self.assertIn("invalid status", complete.stderr)
            self.assertNotIn("Traceback", complete.stderr)

    def test_force_create_archives_stale_findings_before_new_plan(self) -> None:
        goals_script = SCRIPTS / "codex_goals.py"
        findings_script = SCRIPTS / "codex_findings.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)

            def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            self.assertEqual(
                run(
                    goals_script,
                    "create",
                    "--brief",
                    "Old",
                    "--goal",
                    "verify::Old final",
                ).returncode,
                0,
            )
            self.assertEqual(run(goals_script, "next").returncode, 0)
            self.assertEqual(
                run(
                    findings_script,
                    "add",
                    "--title",
                    "Old finding",
                    "--evidence",
                    "This belongs to the old forced-away plan.",
                ).returncode,
                0,
            )

            bad_replace = run(
                goals_script,
                "create",
                "--force",
                "--brief",
                "Bad",
                "--goal",
                "missing delimiter",
            )
            self.assertNotEqual(bad_replace.returncode, 0)
            self.assertTrue((cwd / ".codex-fable5" / "findings.json").exists())
            self.assertFalse(list((cwd / ".codex-fable5").glob("findings.*.archive.json")))

            replaced = run(
                goals_script,
                "create",
                "--force",
                "--brief",
                "New",
                "--goal",
                "verify::New final",
            )
            self.assertEqual(replaced.returncode, 0, replaced.stderr)
            self.assertTrue(list((cwd / ".codex-fable5").glob("findings.*.archive.json")))

            gate = run(findings_script, "gate")
            self.assertEqual(gate.returncode, 0, gate.stderr)
            self.assertIn("findings gate passed", gate.stdout)

            self.assertEqual(run(goals_script, "next").returncode, 0)
            complete = run(
                goals_script,
                "checkpoint",
                "--id",
                "G001",
                "--status",
                "complete",
                "--evidence",
                "new final evidence",
                "--verify-cmd",
                "smoke",
                "--verify-evidence",
                "accepted",
            )
            self.assertEqual(complete.returncode, 0, complete.stderr)

    def test_force_create_keeps_findings_when_goal_write_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            state_dir = cwd / ".codex-fable5"
            state_dir.mkdir()
            goals_path = state_dir / "goals.json"
            findings_path = state_dir / "findings.json"
            goals_path.write_text(
                json.dumps(
                    {
                        "brief": "Old",
                        "created": "test",
                        "goals": [
                            {
                                "id": "G001",
                                "title": "old",
                                "objective": "Old objective",
                                "status": "in_progress",
                                "evidence": "",
                                "verify_cmd": "",
                                "verify_evidence": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            findings_path.write_text(
                json.dumps(
                    {
                        "created": "test",
                        "findings": [
                            {
                                "id": "F001",
                                "goal": "G001",
                                "title": "Old finding",
                                "severity": "high",
                                "source": "review",
                                "status": "open",
                                "location": "",
                                "evidence": "Must remain active if replacement fails.",
                                "resolution": "",
                                "verify_cmd": "",
                                "verify_evidence": "",
                                "created": "test",
                                "updated": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            original_write_json = self.codex_goals.write_json

            def fail_write(*_: object) -> None:
                raise OSError("simulated write failure")

            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                self.codex_goals.write_json = fail_write
                with self.assertRaises(OSError):
                    self.codex_goals.cmd_create(
                        SimpleNamespace(brief="New", goal=["verify::New final"], force=True)
                    )
            finally:
                self.codex_goals.write_json = original_write_json
                os.chdir(old_cwd)

            self.assertTrue(findings_path.exists())
            self.assertFalse(list(state_dir.glob("findings.*.archive.json")))
            self.assertIn("Old objective", goals_path.read_text(encoding="utf-8"))

    def test_malformed_ledger_json_reports_controlled_error(self) -> None:
        goals_script = SCRIPTS / "codex_goals.py"
        findings_script = SCRIPTS / "codex_findings.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            state_dir = cwd / ".codex-fable5"
            state_dir.mkdir()

            (state_dir / "findings.json").write_text("{bad json", encoding="utf-8")
            findings_status = subprocess.run(
                [sys.executable, str(findings_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(findings_status.returncode, 0)
            self.assertIn("findings ledger is not valid JSON", findings_status.stderr)
            self.assertNotIn("Traceback", findings_status.stderr)

            (state_dir / "findings.json").unlink()
            (state_dir / "goals.json").write_text("{bad json", encoding="utf-8")
            goals_status = subprocess.run(
                [sys.executable, str(goals_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(goals_status.returncode, 0)
            self.assertIn("goal plan is not valid JSON", goals_status.stderr)
            self.assertNotIn("Traceback", goals_status.stderr)

    def test_malformed_ledger_schema_reports_controlled_error(self) -> None:
        goals_script = SCRIPTS / "codex_goals.py"
        findings_script = SCRIPTS / "codex_findings.py"
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            state_dir = cwd / ".codex-fable5"
            state_dir.mkdir()

            (state_dir / "findings.json").write_text("[]", encoding="utf-8")
            findings_status = subprocess.run(
                [sys.executable, str(findings_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(findings_status.returncode, 0)
            self.assertIn("findings ledger must be a JSON object", findings_status.stderr)
            self.assertNotIn("Traceback", findings_status.stderr)

            (state_dir / "findings.json").write_text('{"findings": "bad"}', encoding="utf-8")
            findings_bad_list = subprocess.run(
                [sys.executable, str(findings_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(findings_bad_list.returncode, 0)
            self.assertIn("field 'findings' must be a list", findings_bad_list.stderr)
            self.assertNotIn("Traceback", findings_bad_list.stderr)

            (state_dir / "findings.json").write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "id": "F001",
                                "goal": "",
                                "title": "Bad status",
                                "severity": "medium",
                                "source": "review",
                                "status": [],
                                "evidence": "Status must not crash validation.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            findings_bad_status = subprocess.run(
                [sys.executable, str(findings_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(findings_bad_status.returncode, 0)
            self.assertIn("invalid status", findings_bad_status.stderr)
            self.assertNotIn("Traceback", findings_bad_status.stderr)

            (state_dir / "goals.json").write_text("[]", encoding="utf-8")
            goals_status = subprocess.run(
                [sys.executable, str(goals_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(goals_status.returncode, 0)
            self.assertIn("goal plan must be a JSON object", goals_status.stderr)
            self.assertNotIn("Traceback", goals_status.stderr)

            (state_dir / "goals.json").write_text('{"brief": "bad", "goals": "bad"}', encoding="utf-8")
            goals_bad_list = subprocess.run(
                [sys.executable, str(goals_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(goals_bad_list.returncode, 0)
            self.assertIn("field 'goals' must be a list", goals_bad_list.stderr)
            self.assertNotIn("Traceback", goals_bad_list.stderr)

            (state_dir / "goals.json").write_text(
                json.dumps(
                    {
                        "brief": "bad",
                        "goals": [
                            {
                                "id": "G001",
                                "title": "bad",
                                "objective": "Bad status should not crash validation.",
                                "status": [],
                                "evidence": "",
                                "verify_cmd": "",
                                "verify_evidence": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            goals_bad_status = subprocess.run(
                [sys.executable, str(goals_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(goals_bad_status.returncode, 0)
            self.assertIn("invalid status", goals_bad_status.stderr)
            self.assertNotIn("Traceback", goals_bad_status.stderr)

            (state_dir / "goals.json").write_text('{"brief": "empty", "goals": []}', encoding="utf-8")
            goals_empty = subprocess.run(
                [sys.executable, str(goals_script), "status"],
                cwd=cwd,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(goals_empty.returncode, 0)
            self.assertIn("field 'goals' must contain at least one goal", goals_empty.stderr)
            self.assertNotIn("Traceback", goals_empty.stderr)

    def test_litellm_config_generation(self) -> None:
        plain = self.make_litellm_config.build_config("claude-test", "test-alias")
        prefixed = self.make_litellm_config.build_config("anthropic/claude-test", "test-alias")

        self.assertIn('model_name: "test-alias"', plain)
        self.assertIn('model: "anthropic/claude-test"', plain)
        self.assertEqual(plain, prefixed)


if __name__ == "__main__":
    unittest.main()
