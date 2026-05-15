from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_validate_replay():
    result = subprocess.run([sys.executable, "scripts/validate.py", "replay"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0

def test_validate_token():
    result = subprocess.run([sys.executable, "scripts/validate.py", "token"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0

def test_validate_forensic():
    result = subprocess.run([sys.executable, "scripts/validate.py", "forensic"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0

def test_benchmarks():
    result = subprocess.run([sys.executable, "benchmarks/run_kvtc_v7_benchmarks.py", "--iterations", "1", "--warmups", "0"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0

def test_dashboard_startup():
    result = subprocess.run([sys.executable, "dashboard/industrial_dashboard.py", "--once"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
