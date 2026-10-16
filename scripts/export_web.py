"""Compatibility entry point: reconcile and republish the committed warehouse."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analytics.publication import main  # noqa: E402

if __name__ == "__main__":
    main()
