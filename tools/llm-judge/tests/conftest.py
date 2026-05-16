import sys
import os

# Make shared/live_harness importable from the repo root
_repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, os.path.abspath(os.path.join(_repo_root, "shared")))

# Exclude live API tests from the standard pytest run (they need real API keys)
collect_ignore = ["test_llm_live_bulk_api.py", "test_live_api.py"]
