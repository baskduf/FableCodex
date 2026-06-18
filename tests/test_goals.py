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


class GoalLedgerTests(ScriptTestBase):
    def test_goal_and_findings_scripts_share_state_helpers(self) -> None:
        state = self.codex_fable_state
        for helper in ["locked_state", "read_json", "write_json", "append_event", "require_object", "now"]:
            with self.subTest(helper=helper):
                self.assertIs(getattr(self.codex_goals, helper), getattr(state, helper))
                self.assertIs(getattr(self.codex_findings, helper), getattr(state, helper))

        for constant in ["STATE_DIR", "GOALS_FILE", "FINDINGS_FILE", "LEDGER_FILE", "LOCK_FILE"]:
            with self.subTest(constant=constant):
                self.assertEqual(getattr(self.codex_goals, constant), getattr(state, constant))
                self.assertEqual(getattr(self.codex_findings, constant), getattr(state, constant))

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

    def test_lock_fallback_times_out_on_stale_lockdir(self) -> None:
        for module in [self.codex_fable_state]:
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
