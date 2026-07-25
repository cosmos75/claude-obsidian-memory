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
     "pipelines": {
       "conversations": { "subfolder": "Claude Code" },
       "githubStars": { "subfolder": "GitHub Stars" }
     }
   }
   ```
   Create the parent directory first if it doesn't exist.

   `vaultPath` is shared by every pipeline; each pipeline declares its own subfolder under `pipelines`. Don't put a pipeline's subfolder at the top level — that shape was specific to the conversation pipeline and no longer applies.

   **If the file already exists with the old shape** (a top-level `archiveSubfolder`), preserve that value as `pipelines.conversations.subfolder` when rewriting, so an existing archive folder doesn't get orphaned. The scripts still read the old key as a fallback, so rewriting is a tidy-up, not a requirement.
4. Ensure both pipeline folders exist under the vault (create if missing) — conversations get archived under one subfolder per project (named after the project's working-directory basename), GitHub star notes go flat into the other.
5. Confirm to the user that the vault is configured, and tell them what each pipeline does:
   - `/obsidian-memory-save` writes an LLM-generated summary to `<vaultPath>/<conversations subfolder>/<project-name>/` — the first run for a session records the full conversation so far, later runs in the same session only append what happened since the last save.
   - `/stars-to-obsidian` writes one note per starred repo into `<vaultPath>/<githubStars subfolder>/`, plus a category index.
6. If the vault already contains star notes written before source markers existed, tell the user to run `scripts/backfill_source_marker.py` once (it defaults to a dry run; `--apply` writes). Without the marker those notes are treated as the user's own files and will never be refreshed.
