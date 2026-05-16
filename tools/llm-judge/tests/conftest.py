import sys
import os

# Make live_harness importable when pytest collects this directory
sys.path.insert(0, os.path.dirname(__file__))

# Exclude live API tests from the standard pytest run (they need real API keys)
collect_ignore = ["test_llm_live_bulk_api.py", "test_live_api.py"]
