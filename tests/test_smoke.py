"""Minimal smoke test for the reference implementation."""

import importlib
import unittest


class SmokeTest(unittest.TestCase):
    def test_module_imports(self):
        module = importlib.import_module("src.stream_index")
        self.assertTrue(hasattr(module, "__doc__"))


if __name__ == "__main__":
    unittest.main()
