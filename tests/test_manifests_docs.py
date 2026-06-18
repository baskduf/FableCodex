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


class ManifestDocsTests(ScriptTestBase):
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

    def test_repo_hygiene_files_cover_local_artifacts(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

        self.assertIn(".codex-fable5/", gitignore)
        self.assertIn("__pycache__/", gitignore)
        self.assertIn("* @baskduf", codeowners)
        self.assertIn('package-ecosystem: "github-actions"', dependabot)
