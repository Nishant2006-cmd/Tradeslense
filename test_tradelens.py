import os
import subprocess
import json
import pytest

# Get the absolute path of the project root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "sample", "data")
RULES_PATH = os.path.join(ROOT_DIR, "sample", "rules.json")

def test_run_script(tmp_path):
    out_dir = tmp_path / "output"
    
    cmd = [
        "python", os.path.join(ROOT_DIR, "run.py"),
        "--data", DATA_DIR,
        "--rules", RULES_PATH,
        "--out", str(out_dir)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"
    
    assert (out_dir / "trades.csv").exists()
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "violations.csv").exists()
    assert (out_dir / "report.md").exists()

def test_summary_structure(tmp_path):
    out_dir = tmp_path / "output"
    subprocess.run([
        "python", os.path.join(ROOT_DIR, "run.py"),
        "--data", DATA_DIR,
        "--rules", RULES_PATH,
        "--out", str(out_dir)
    ], check=True)
    
    with open(out_dir / "summary.json", "r") as f:
        summary = json.load(f)
        
    assert "total_trades" in summary
    assert "win_rate" in summary
    assert "net_pnl_inr" in summary
    assert "by_asset_class" in summary
    assert "daily" in summary

def test_idempotency_rerun(tmp_path):
    out_dir1 = tmp_path / "output1"
    out_dir2 = tmp_path / "output2"
    
    subprocess.run(["python", os.path.join(ROOT_DIR, "run.py"), "--data", DATA_DIR, "--rules", RULES_PATH, "--out", str(out_dir1)], check=True)
    subprocess.run(["python", os.path.join(ROOT_DIR, "run.py"), "--data", DATA_DIR, "--rules", RULES_PATH, "--out", str(out_dir2)], check=True)
    
    with open(out_dir1 / "trades.csv", "rb") as f1, open(out_dir2 / "trades.csv", "rb") as f2:
        assert f1.read() == f2.read()