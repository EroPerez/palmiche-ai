#!/usr/bin/env python3
"""JSON-line filter for misbehaving MCP servers that write debug output to stdout.

Usage:
    python -m jarvis.mcp_support.json_filter -- <command> [args...]

The wrapper spawns ``<command> [args...]``, reads its stdout line by line,
and writes only valid JSON lines to its own stdout. Everything else goes
to the wrapper's stderr.  The child's stderr is passed through as-is.

This lets ADK's ``McpToolset`` (which relies on the MCP SDK's
``stdio_client``) work with MCP servers that violate the protocol by
printing ``[DEBUG]``, stack traces, or other non-JSON text on stdout.
"""

import subprocess
import sys


def main():
    args = sys.argv[1:]
    if not args or args[0] != "--":
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    cmd = args[1:]
    if not cmd:
        print("[json_filter] No command specified.", file=sys.stderr)
        sys.exit(1)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Forward stderr in a non-blocking thread
    import threading

    def _pipe_stderr():
        for line in iter(proc.stderr.readline, b""):
            sys.stderr.buffer.write(line)
            sys.stderr.buffer.flush()

    t = threading.Thread(target=_pipe_stderr, daemon=True)
    t.start()

    # Filter stdout: only pass valid JSON lines
    for raw in iter(proc.stdout.readline, b""):
        line = raw.decode("utf-8", errors="replace").strip()
        if line.startswith("{"):
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
        elif line.startswith("["):
            # Some MCP servers return JSON arrays as top-level
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
        else:
            print(f"[json_filter] filtered: {line[:200]}", file=sys.stderr)

    proc.wait()
    t.join()
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
