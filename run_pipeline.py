#!/usr/bin/env python3
"""
Root Shortcut Launcher: Sinhala-Script Language Identification (LangID) Pipeline
---------------------------------------------------------------------------------
Delegates directly to pipeline/run_pipeline.py for full one-click reproducibility.
"""

import os
import sys
import subprocess

if __name__ == "__main__":
    pipeline_script = os.path.join(os.path.dirname(__file__), "pipeline", "run_pipeline.py")
    if not os.path.exists(pipeline_script):
        print(f"Error: {pipeline_script} not found.")
        sys.exit(1)
    
    cmd = [sys.executable, pipeline_script] + sys.argv[1:]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)
