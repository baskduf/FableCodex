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


class CoverageTests(ScriptTestBase):
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
