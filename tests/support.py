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
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name: str):
    if name in sys.modules:
        return sys.modules[name]
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
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


def parse_ci_workflow_steps(workflow: str) -> dict[str, str]:
    steps: dict[str, str] = {}
    matches = list(
        re.finditer(
            r"^      - name: (?P<name>.+?)\r?\n(?P<body>.*?)(?=^      - name: |\Z)",
            workflow,
            re.DOTALL | re.MULTILINE,
        )
    )
    for match in matches:
        steps[match.group("name")] = match.group("body")
    return steps


def extract_ci_pin(step_body: str) -> str:
    match = re.search(r'PIN="([0-9a-f]{40})"', step_body)
    if match is None:
        raise AssertionError("workflow step does not define a 40-character PIN")
    return match.group(1)


def extract_ci_output_path(step_body: str) -> str:
    match = re.search(r"\s-o\s+([^\s]+)", step_body)
    if match is None:
        raise AssertionError("workflow fetch step does not write to a concrete -o path")
    return match.group(1).strip('"')


def extract_fable_coverage_source_arg(step_body: str) -> str:
    match = re.search(r"fable_coverage\.py\s+--source\s+([^\s]+)", step_body)
    if match is None:
        raise AssertionError("workflow validate step does not pass --source to fable_coverage.py")
    return match.group(1).strip('"')


class ScriptTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.codex_fable_state = load_script("codex_fable_state")
        cls.fable_coverage = load_script("fable_coverage")
        cls.codex_goals = load_script("codex_goals")
        cls.codex_findings = load_script("codex_findings")
        cls.make_litellm_config = load_script("make_litellm_config")
