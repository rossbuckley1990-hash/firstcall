from __future__ import annotations

import json

from firstcall.agents.probe import probe


def main():
    print("FIRSTCALL AGENT PROBE")
    print("=====================")

    result = probe("codex")

    print("Executable:", result.path)
    print("Version:", result.version)
    print()
    print("HELP")
    print("----")
    print(result.help_text)


if __name__ == "__main__":
    main()
