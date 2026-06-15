from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


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


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fable_coverage = load_script("fable_coverage")
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

    def test_litellm_config_generation(self) -> None:
        plain = self.make_litellm_config.build_config("claude-test", "test-alias")
        prefixed = self.make_litellm_config.build_config("anthropic/claude-test", "test-alias")

        self.assertIn('model_name: "test-alias"', plain)
        self.assertIn('model: "anthropic/claude-test"', plain)
        self.assertEqual(plain, prefixed)


if __name__ == "__main__":
    unittest.main()
