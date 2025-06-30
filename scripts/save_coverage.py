#!/usr/bin/env python

import os
import re
import traceback
import uuid
from pathlib import Path

try:
    if os.getenv("RUNNER_OS") == "Linux":
        coverage = Path("coverage.lcov").read_text()
        coverage = re.sub(
            r"^(SF:).*?/site-packages/", r"\1src/", coverage, flags=re.MULTILINE
        )
        os.makedirs("/output", exist_ok=True)
        Path(f"/output/.coverage.{uuid.uuid4().hex}.lcov").write_text(coverage)
except Exception:
    traceback.print_exc()
