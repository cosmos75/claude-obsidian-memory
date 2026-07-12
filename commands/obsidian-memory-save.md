---
description: Archive this conversation to your Obsidian vault — full record on first run, incremental since last time otherwise
---

Archive the current Claude Code session to the configured Obsidian vault.

Run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/obsidian_memory_archive.py"
```

Report the script's output line to the user as-is. If it says no vault is configured, tell the user to run `/obsidian-memory-init` first.
