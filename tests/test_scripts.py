"""Compatibility module for the split test suite.

Tests were moved into focused modules under tests/. Keep this file so existing
py_compile commands that name tests/test_scripts.py continue to work.

Directly targeting this module now runs zero tests; use unittest discovery or a
focused module such as tests.test_ci_release instead.
"""
