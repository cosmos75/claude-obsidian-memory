# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案性質

這是一個 Claude Code **plugin**（非一般應用程式），沒有建置、lint 或測試框架——內容只有 JSON manifest、一個 markdown slash-command、以及一支獨立的 Python 腳本。所有邏輯都透過 Claude Code 的 plugin 慣例（`.claude-plugin/`、`commands/`、`hooks/`）串接，彼此之間沒有程式碼層級的 import 關係。

## 常用指令

- **沒有 build / lint / test 指令**——這個 repo 不是可執行的應用程式。
- **手動測試封存腳本**：模擬 hook 傳入的 stdin JSON 直接呼叫 `scripts/obsidian_memory_archive.py`：
  ```
  echo '{"session_id":"test1234","transcript_path":"/path/to/transcript.jsonl","cwd":"/some/project"}' \
    | python3 scripts/obsidian_memory_archive.py
  ```
  必須先在 `~/.claude/obsidian-memory/config.json` 設定好 `vaultPath`，否則腳本會直接靜默返回（see 下方「靜默失敗」設計）。
- **本機測試 plugin 安裝**：在 Claude Code 中執行 `/plugin marketplace add <此 repo 的本機路徑>`，再 `/plugin install obsidian-memory`。
- 一般 git 操作照常（`git add` / `git commit` / `git push`）。

## 架構

此 repo 同時扮演兩個角色：
- **Marketplace**（`.claude-plugin/marketplace.json`）：把整個 repo 註冊為一個 marketplace。
- **Plugin**（`.claude-plugin/plugin.json`，名稱 `obsidian-memory`，`source: "./"`）：唯一收錄的 plugin，就是 repo 根目錄本身。

三個功能元件透過 Claude Code 的 plugin 慣例串接，彼此獨立、沒有共用程式碼：

1. **`commands/obsidian-memory-init.md`** — 一次性設定用的 slash command（`/obsidian-memory-init`）。內容是給 Claude Code 本身執行的自然語言步驟，而非程式碼：互動式收集使用者的 Obsidian vault 路徑，寫入 `~/.claude/obsidian-memory/config.json`。
2. **`hooks/hooks.json`** — 註冊一個 `SessionEnd` hook，執行 `scripts/obsidian_memory_archive.py`。指令路徑使用 `${CLAUDE_PLUGIN_ROOT}` 環境變數，確保無論 plugin 安裝在哪裡都能正確定位腳本。
3. **`scripts/obsidian_memory_archive.py`** — 唯一的可執行邏輯，也是修改時最需要小心的檔案：
   - 從 stdin 讀取 hook 傳入的 JSON（`session_id`、`transcript_path`、`cwd`）。
   - 讀取 `~/.claude/obsidian-memory/config.json`（欄位：`vaultPath`、`archiveSubfolder`）——**此設定檔刻意放在 plugin 目錄之外**，屬於每台機器各自的全域狀態，不應該搬進 repo 內。
   - 解析 transcript JSONL，抽取 user/assistant 對話回合（略過 sidechain）。
   - 呼叫 `claude -p`（模型固定為 `claude-haiku-4-5-20251001`，`--disallowedTools *`、`--permission-mode plan`）產生第三人稱摘要。**摘要語言被寫死為繁體中文**（見 `summarize()` 內的 prompt）——這是配合使用者全域語言偏好而硬編碼的，若該偏好改變需要同步更新這裡。
   - 將摘要寫入 `<vaultPath>/<archiveSubfolder>/<project>/` 下的 markdown 檔案。

### 命名與分類慣例（修改時不要破壞）

- **檔名格式**：`{YYYY-MM-DD}-{HHMMSS}-{session_id 前 8 碼}.md`。
- **資料夾分類**：以 `basename(cwd)` 作為專案資料夾名稱，而非任何設定檔內的專案識別碼。
- **Frontmatter 欄位**：`date`（ISO 8601、含時區偏移）、`project`、`session_id`、`cwd`、`source: claude-code`。

### 靜默失敗設計

`main()` 內的例外會被整個吞掉（`except Exception: pass`）——這是刻意設計，確保 vault 設定錯誤或 transcript 讀取失敗時，**絕不會**讓使用者的對話 session 出現可見的 hook 錯誤。未來調整錯誤處理時，應保留這個「永不打斷 session」的特性。
