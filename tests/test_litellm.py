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


class LiteLLMConfigTests(ScriptTestBase):
    def test_litellm_config_generation(self) -> None:
        plain = self.make_litellm_config.build_config("claude-test", "test-alias")
        prefixed = self.make_litellm_config.build_config("anthropic/claude-test", "test-alias")

        self.assertIn('model_name: "test-alias"', plain)
        self.assertIn('model: "anthropic/claude-test"', plain)
        self.assertEqual(plain, prefixed)
