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


class FindingsLedgerTests(ScriptTestBase):
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
