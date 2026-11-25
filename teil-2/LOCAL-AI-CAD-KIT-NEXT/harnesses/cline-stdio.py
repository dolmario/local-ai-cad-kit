"""Forward Cline's stdio connection using the original Windows argument vector."""

import json
import os
import subprocess
import sys


def main():
    argv = json.loads(os.environ.pop("CAD_MCP_ARGV_JSON"))
    if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv):
        raise ValueError("Invalid CAD MCP argument list")
    return subprocess.run(argv, shell=False).returncode


if __name__ == "__main__":
    sys.exit(main())
