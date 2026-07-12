---
description: Initialize or change the Obsidian vault path used for automatic conversation archiving
argument-hint: [vault-path]
---

Initialize Obsidian Memory archiving.

Vault path argument: $ARGUMENTS

Steps:
1. If the argument is empty, ask the user for their Obsidian vault's absolute path.
2. Verify the path exists and is a directory (list it to confirm).
3. Write `~/.claude/obsidian-memory/config.json` as:
   ```json
   {
     "vaultPath": "<absolute path>",
     "archiveSubfolder": "Claude Code"
   }
   ```
   Create the parent directory first if it doesn't exist.
4. Ensure `<vaultPath>/Claude Code` exists (create if missing) — this is the root folder conversations get archived under, with one subfolder per project (named after the project's working-directory basename).
5. Confirm to the user that archiving is configured, and that a SessionEnd hook will write an LLM-generated summary to `<vaultPath>/Claude Code/<project-name>/` after each session ends.
