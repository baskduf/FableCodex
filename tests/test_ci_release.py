from __future__ import annotations

try:
    from tests.support import (
        BIN,
        Path,
        ROOT,
        SCRIPTS,
        SKILL_ROOT,
        ScriptTestBase,
        SimpleNamespace,
        json,
        os,
        parse_routing_map,
        read_readme_fable_pin,
        read_skill_body,
        re,
        subprocess,
        sys,
        tempfile,
        textwrap,
    )
except ModuleNotFoundError:  # unittest discovery with tests/ as top-level.
    from support import (
        BIN,
        Path,
        ROOT,
        SCRIPTS,
        SKILL_ROOT,
        ScriptTestBase,
        SimpleNamespace,
        json,
        os,
        parse_routing_map,
        read_readme_fable_pin,
        read_skill_body,
        re,
        subprocess,
        sys,
        tempfile,
        textwrap,
    )


class CiReleaseTests(ScriptTestBase):
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
