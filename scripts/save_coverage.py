#!/usr/bin/env python

import os
import shutil
import traceback
import uuid

try:
    if os.getenv("RUNNER_OS") == "Linux":
        os.makedirs("/output", exist_ok=True)
        shutil.move("coverage.lcov", f"/output/coverage.{uuid.uuid4().hex}.lcov")
except Exception:
    traceback.print_exc()
