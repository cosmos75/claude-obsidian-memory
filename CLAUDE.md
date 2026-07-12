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
2. **`commands/obsidian-memory-save.md`** — 觸發封存用的 slash command（`/obsidian-memory-save`）。內容只是指示 Claude 執行 `scripts/obsidian_memory_archive.py`（用 `${CLAUDE_PLUGIN_ROOT}` 環境變數定位腳本），並把腳本的輸出訊息回報給使用者。**沒有 hook**——封存完全是使用者手動觸發，不再依賴 `SessionEnd` 事件（舊版曾因桌面 App 結束時直接砍掉行程樹，導致封存寫到一半就中斷、以及摘要子行程遞迴觸發 hook 的問題，改成手動指令後兩個問題都不存在了）。
3. **`scripts/obsidian_memory_archive.py`** — 唯一的可執行邏輯，也是修改時最需要小心的檔案：
   - 從環境變數取得目前 session 資訊：`CLAUDE_CODE_SESSION_ID`（session id）與 `os.getcwd()`（目前工作目錄）。**不再從 stdin 讀取 hook JSON**，因為這個腳本現在是被 slash command 直接呼叫，不是被 hook 呼叫。
   - 用 `glob.glob("~/.claude/projects/*/{session_id}.jsonl")` 找出 transcript 檔案路徑——利用 session id 是 UUID、檔名必為 `<session_id>.jsonl` 的事實，跳過需要重現 Claude Code 專案目錄 slug 演算法的麻煩。
   - 讀取 `~/.claude/obsidian-memory/config.json`（欄位：`vaultPath`、`archiveSubfolder`）——**此設定檔刻意放在 plugin 目錄之外**，屬於每台機器各自的全域狀態，不應該搬進 repo 內。
   - 解析 transcript JSONL，抽取 user/assistant 對話回合（略過 sidechain）。
   - **增量封存邏輯**：在目標資料夾內尋找 frontmatter 的 `session_id` 與目前 session 相符的既有 `.md` 檔案。
     - 找不到 → 從頭封存整個 session（`write_full`），frontmatter 寫入 `archived_turns: <總回合數>`。
     - 找到 → 只取 `turns[archived_turns:]` 這段新內容送去摘要（`append_incremental`），以 `## 更新 <時間戳記>` 區塊附加在檔案最後，並更新 frontmatter 的 `archived_turns` 與 `updated` 欄位。沒有新內容時直接印出訊息、不寫檔。
   - 呼叫 `claude -p`（模型固定為 `claude-haiku-4-5-20251001`，`--disallowedTools *`、`--permission-mode plan`）產生第三人稱摘要。**摘要語言被寫死為繁體中文**（見 `summarize()` 內的 prompt）——這是配合使用者全域語言偏好而硬編碼的，若該偏好改變需要同步更新這裡。
   - 將摘要寫入 `<vaultPath>/<archiveSubfolder>/<project>/` 下的 markdown 檔案。

### 命名與分類慣例（修改時不要破壞）

- **檔名格式**：`{YYYY-MM-DD}-{HHMMSS}-{session_id 前 8 碼}.md`，只在該 session 第一次封存時決定，之後同一個 session 的增量封存都寫回同一個檔案。
- **資料夾分類**：以 `basename(cwd)` 作為專案資料夾名稱，而非任何設定檔內的專案識別碼。
- **Frontmatter 欄位**：`date`（首次建立時間，ISO 8601 含時區偏移）、`updated`（最後一次封存時間）、`project`、`session_id`、`cwd`、`archived_turns`（已封存的對話回合數，用來判斷下次要從哪裡繼續）、`source: claude-code`。

### 錯誤處理設計

`main()` 內的例外會被印出到 stderr 並以非零狀態結束（不再靜默吞掉）——因為封存現在是使用者主動執行的指令，出錯時應該讓使用者立即看到，而不是像舊版 hook 那樣為了不打斷 session 而刻意隱藏。個別檢查點（vault 未設定、transcript 找不到、沒有新內容等）則印出中文提示訊息並正常結束，不視為錯誤。
