import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "api" if (ROOT / "api").exists() else ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Keep automated tests deterministic and independent of the hosted database.
os.environ.setdefault("DATABASE_URL", "sqlite:///./sahachari_test.db")
