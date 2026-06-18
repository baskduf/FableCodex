from __future__ import annotations

import shutil

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
        extract_ci_output_path,
        extract_ci_pin,
        extract_fable_coverage_source_arg,
        os,
        parse_ci_workflow_steps,
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
        extract_ci_output_path,
        extract_ci_pin,
        extract_fable_coverage_source_arg,
        os,
        parse_ci_workflow_steps,
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
        self.assertIn("codex_fable_state.py", workflow)
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

    def test_ci_workflow_fetch_and_validate_steps_are_semantically_linked(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        steps = parse_ci_workflow_steps(workflow)

        fetch = steps["Fetch pinned FABLE-5 source"]
        validate = steps["Validate coverage matrix"]
        fetched_path = extract_ci_output_path(fetch)

        self.assertEqual("build/fable5/CLAUDE-FABLE-5.md", fetched_path)
        self.assertEqual(read_readme_fable_pin(), extract_ci_pin(fetch))
        self.assertEqual(
            fetched_path,
            extract_fable_coverage_source_arg(validate),
            "CI must validate the exact pinned source file it fetched, not a different path or matrix-only run",
        )
        self.assertIn("grep -q \"Fable 5\"", fetch)
        self.assertNotIn("Authorization:", fetch)

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

    def test_version_command_reports_manifest_and_paths(self) -> None:
        env = {**os.environ, "PATH": f"{BIN}{os.pathsep}{os.environ['PATH']}"}
        plugin = json.loads((ROOT / "plugins" / "codex-fable5" / ".codex-plugin" / "plugin.json").read_text())

        result = subprocess.run(
            ["codex-fable5", "version"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"codex-fable5 {plugin['version']}", result.stdout)
        self.assertIn("plugin:", result.stdout)
        self.assertIn("skill:", result.stdout)
        self.assertIn("wrapper:", result.stdout)
        self.assertIn("git:", result.stdout)

    def test_update_command_updates_clean_checkout_to_requested_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "FableCodex"
            shutil.copytree(ROOT / "plugins", clone / "plugins")
            for command in [
                ["git", "init"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test User"],
                ["git", "add", "plugins"],
                ["git", "commit", "-m", "release"],
                ["git", "tag", "v0.4.4"],
            ]:
                result = subprocess.run(command, cwd=clone, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
            (clone / "NEXT.txt").write_text("next\n", encoding="utf-8")
            for command in [["git", "add", "NEXT.txt"], ["git", "commit", "-m", "next"]]:
                result = subprocess.run(command, cwd=clone, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)

            update = subprocess.run(
                [
                    str(clone / "plugins" / "codex-fable5" / "bin" / "codex-fable5"),
                    "update",
                    "--ref",
                    "v0.4.4",
                    "--no-fetch",
                ],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(update.returncode, 0, update.stderr)
            self.assertIn("updates the FableCodex checkout/plugin package only", update.stdout)
            self.assertIn("restart Codex", update.stdout)

            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )
            tag = subprocess.run(
                ["git", "rev-parse", "v0.4.4^{commit}"],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(head.returncode, 0, head.stderr)
            self.assertEqual(tag.returncode, 0, tag.stderr)
            self.assertEqual(head.stdout.strip(), tag.stdout.strip())

    def test_update_command_refuses_dirty_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "FableCodex"
            shutil.copytree(ROOT / "plugins", clone / "plugins")
            for command in [
                ["git", "init"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test User"],
                ["git", "add", "plugins"],
                ["git", "commit", "-m", "release"],
                ["git", "tag", "v0.4.4"],
            ]:
                result = subprocess.run(command, cwd=clone, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
            (clone / "DIRTY.txt").write_text("dirty\n", encoding="utf-8")

            update = subprocess.run(
                [
                    str(clone / "plugins" / "codex-fable5" / "bin" / "codex-fable5"),
                    "update",
                    "--ref",
                    "v0.4.4",
                    "--no-fetch",
                ],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(update.returncode, 0)
            self.assertIn("refusing to update a dirty checkout", update.stderr)

    def test_update_default_ignores_prerelease_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "FableCodex"
            shutil.copytree(ROOT / "plugins", clone / "plugins")
            for command in [
                ["git", "init"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test User"],
                ["git", "add", "plugins"],
                ["git", "commit", "-m", "stable release"],
                ["git", "tag", "v1.0.0"],
            ]:
                result = subprocess.run(command, cwd=clone, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
            (clone / "RC.txt").write_text("rc\n", encoding="utf-8")
            for command in [
                ["git", "add", "RC.txt"],
                ["git", "commit", "-m", "release candidate"],
                ["git", "tag", "v1.1.0-rc1"],
                ["git", "checkout", "-b", "work"],
            ]:
                result = subprocess.run(command, cwd=clone, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)

            update = subprocess.run(
                [
                    str(clone / "plugins" / "codex-fable5" / "bin" / "codex-fable5"),
                    "update",
                    "--no-fetch",
                ],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(update.returncode, 0, update.stderr)
            self.assertIn("updated to v1.0.0", update.stdout)

            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )
            stable = subprocess.run(
                ["git", "rev-parse", "v1.0.0^{commit}"],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(head.stdout.strip(), stable.stdout.strip())
