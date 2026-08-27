from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def test_fault_probe_module_loads():
    path = Path("eval/run_fault_probe.py")
    spec = importlib.util.spec_from_file_location("run_fault_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert callable(module.main)
