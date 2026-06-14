from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "codex-fable5" / "skills" / "codex-fable5"
SCRIPTS = SKILL_ROOT / "scripts"


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
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("python -m py_compile", workflow)
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

    def test_litellm_config_generation(self) -> None:
        plain = self.make_litellm_config.build_config("claude-test", "test-alias")
        prefixed = self.make_litellm_config.build_config("anthropic/claude-test", "test-alias")

        self.assertIn('model_name: "test-alias"', plain)
        self.assertIn('model: "anthropic/claude-test"', plain)
        self.assertEqual(plain, prefixed)


if __name__ == "__main__":
    unittest.main()
