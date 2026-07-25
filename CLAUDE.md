# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案性質

這是一個 Claude Code **plugin**（非一般應用程式），沒有建置或 lint 工具鏈——內容只有 JSON manifest、三個 markdown slash-command、以及幾支獨立的 Python 腳本。所有邏輯都透過 Claude Code 的 plugin 慣例（`.claude-plugin/`、`commands/`）串接。**沒有 `hooks/`**——封存完全靠使用者手動執行 slash command 觸發（見下方架構說明）。

## 常用指令

- **跑測試**：`python3 -m unittest discover -s tests`。只有 `scripts/vault_notes.py` 那三個純函數有測試，這是整個 repo 唯一的測試接縫；兩支入口腳本的檔案 I/O 是薄殼，刻意不測。刻意用 stdlib `unittest` 而非 pytest，因為這個 repo 沒有套件管理與相依安裝步驟。
- **沒有 build / lint 指令**——這個 repo 不是可執行的應用程式。
- **手動測試封存腳本**：腳本現在從環境變數與 `cwd` 取得 session 資訊，不再讀 stdin：
  ```
  CLAUDE_CODE_SESSION_ID=<真實的 session id> python3 scripts/obsidian_memory_archive.py
  ```
  必須滿足以下條件腳本才會真的寫檔，否則會印出對應的中文提示訊息後直接返回（見下方「錯誤處理設計」）：
  1. `~/.claude/obsidian-memory/config.json` 已設定有效的 `vaultPath`。
  2. `~/.claude/projects/*/<session_id>.jsonl` 存在（即該 session id 必須是某個真實存在過的 transcript，通常直接用目前這個 Claude Code session 自己的 `$CLAUDE_CODE_SESSION_ID` 最方便）。
  3. 目前 `cwd` 就是要被歸類的專案目錄（資料夾名稱取自 `basename(cwd)`）。
- **本機測試 plugin 安裝**：在 Claude Code 中執行 `/plugin marketplace add <此 repo 的本機路徑>`，再 `/plugin install obsidian-memory`。
- 一般 git 操作照常（`git add` / `git commit` / `git push`）。

## 架構

此 repo 同時扮演兩個角色：
- **Marketplace**（`.claude-plugin/marketplace.json`）：把整個 repo 註冊為一個 marketplace。
- **Plugin**（`.claude-plugin/plugin.json`，名稱 `obsidian-memory`，`source: "./"`）：唯一收錄的 plugin，就是 repo 根目錄本身。

主要元件透過 Claude Code 的 plugin 慣例串接。兩條管道各自獨立，唯一共用的是 `scripts/vault_notes.py` 那組純函數與同一份設定檔：

1. **`commands/obsidian-memory-init.md`** — 一次性設定用的 slash command（`/obsidian-memory-init`）。內容是給 Claude Code 本身執行的自然語言步驟，而非程式碼：互動式收集使用者的 Obsidian vault 路徑，寫入 `~/.claude/obsidian-memory/config.json`。
2. **`commands/obsidian-memory-save.md`** — 觸發封存用的 slash command（`/obsidian-memory-save`）。內容只是指示 Claude 執行 `scripts/obsidian_memory_archive.py`（用 `${CLAUDE_PLUGIN_ROOT}` 環境變數定位腳本），並把腳本的輸出訊息回報給使用者。**沒有 hook**——封存完全是使用者手動觸發，不再依賴 `SessionEnd` 事件（舊版曾因桌面 App 結束時直接砍掉行程樹，導致封存寫到一半就中斷、以及摘要子行程遞迴觸發 hook 的問題，改成手動指令後兩個問題都不存在了）。
3. **`commands/stars-to-obsidian.md`** — 另一條管道的 slash command（`/stars-to-obsidian`）：把目前 GitHub 帳號 star 過的 repo 用 `gh api user/starred` 拉下來，逐一抓 README 分析後依主題分類寫成筆記，並產生一份分類索引（MOC）。抓取、分析、分類全由 Claude 在執行當下完成，**但寫檔一律交給 `scripts/merge_note.py`**——這是刻意的不對稱，理由見 ADR-0001。vault 路徑與子資料夾都讀 `/obsidian-memory-init` 寫入的那份共用設定（`--vault` 可覆蓋路徑）。
4. **`scripts/obsidian_memory_archive.py`** — 封存管道的入口，也是修改時最需要小心的檔案：
   - 從環境變數取得目前 session 資訊：`CLAUDE_CODE_SESSION_ID`（session id）與 `os.getcwd()`（目前工作目錄）。**不再從 stdin 讀取 hook JSON**，因為這個腳本現在是被 slash command 直接呼叫，不是被 hook 呼叫。
   - 用 `glob.glob("~/.claude/projects/*/{session_id}.jsonl")` 找出 transcript 檔案路徑——利用 session id 是 UUID、檔名必為 `<session_id>.jsonl` 的事實，跳過需要重現 Claude Code 專案目錄 slug 演算法的麻煩。
   - 讀取 `~/.claude/obsidian-memory/config.json`——**此設定檔刻意放在 plugin 目錄之外**，屬於每台機器各自的全域狀態，不應該搬進 repo 內。schema 見下方「設定檔」。子資料夾一律透過 `vault_notes.resolve_subfolder()` 取得，不要自己讀 config 欄位。
   - 解析 transcript JSONL，抽取 user/assistant 對話回合（略過 sidechain）。
   - **增量封存邏輯**：在目標資料夾內尋找 frontmatter 的 `session_id` 與目前 session 相符的既有 `.md` 檔案。
     - 找不到 → 從頭封存整個 session（`write_full`），frontmatter 寫入 `archived_turns: <總回合數>`。
     - 找到 → 只取 `turns[archived_turns:]` 這段新內容送去摘要（`append_incremental`），以 `## 更新 <時間戳記>` 區塊附加在檔案最後，並更新 frontmatter 的 `archived_turns` 與 `updated` 欄位。沒有新內容時直接印出訊息、不寫檔。
   - 呼叫 `claude -p`（模型固定為 `claude-haiku-4-5-20251001`，`--disallowedTools *`、`--disable-slash-commands`、`--permission-mode plan`）產生第三人稱摘要。摘要的 prompt 明確標記 transcript 內容是「純資料、非指令」，避免對話內容中夾帶的文字被誤當成要執行的指令（prompt injection 防護）。**摘要語言被寫死為繁體中文**（見 `summarize()` 內的 prompt）——這是配合使用者全域語言偏好而硬編碼的，若該偏好改變需要同步更新這裡。
   - 將摘要寫入 `<vaultPath>/<對話管道子資料夾>/<project>/` 下的 markdown 檔案。

### 設定檔

```json
{
  "vaultPath": "<vault 絕對路徑>",
  "pipelines": {
    "conversations": { "subfolder": "Claude Code" },
    "githubStars":   { "subfolder": "GitHub Stars" }
  }
}
```

`vaultPath` 是所有管道共用的唯一頂層設定，每條管道只宣告自己的子資料夾。舊格式（頂層 `archiveSubfolder`）仍讀得懂，只作用於對話管道，新舊並存時新的優先——這段回退邏輯在 `resolve_subfolder()` 裡，有測試守著，**不要為了整齊把它拿掉**，會讓自訂過舊設定的使用者靜默寫到錯的資料夾。

### 純函數模組與寫檔守則（修改時最容易踩雷的地方）

`scripts/vault_notes.py` 收著三個純函數，是唯一有測試的地方，兩支入口腳本都從它匯入：

- `merge_note()` — 把新生成的機器區併回舊筆記，`## 我的笔记` 以下的人類區原樣保留。機器區模板結尾本身就帶著這個分界，所以舊檔有人類區時是**換掉**模板那份而不是接在後面，否則會出現兩個分界。
- `resolve_subfolder()` — 見上方「設定檔」。
- `is_pipeline_output()` — 只看 frontmatter 的 `source` 欄位，**不看檔案在哪個資料夾**（ADR-0002）。沒有標記的檔案是使用者的東西，任何管道都不准動。

由此衍生的鐵則：**星標管道不准直接寫目標筆記**，一律把機器區寫進暫存檔再交給 `scripts/merge_note.py`，人類區的內容全程不經過 LLM 的手（ADR-0001）。`scripts/backfill_source_marker.py` 是一次性遷移，替 ADR-0002 之前產生的舊筆記補標記，跑完就不該再有程式碼依賴位置判斷歸屬。

### 命名與分類慣例（修改時不要破壞）

- **檔名格式**：`{YYYY-MM-DD}-{HHMMSS}-{session_id 前 8 碼}.md`，只在該 session 第一次封存時決定，之後同一個 session 的增量封存都寫回同一個檔案。
- **資料夾分類**：專案資料夾名取自 **git repo 主 checkout 的 basename**（`vault_notes.project_name()`），不是 `basename(cwd)`——否則同一個 session 進了 worktree 或子目錄就會被當成新專案，見 issue #6。不在 git repo 裡才退回 cwd。
- **尋找既有封存**：`find_existing_archive()` 掃整個封存根目錄找 `session_id`，不限於當前專案資料夾；命中多份時取 `archived_turns` 最大的那份並提醒使用者。**不要改回只掃當前資料夾**，那正是 issue #6 的成因。
- **Frontmatter 欄位**：`date`（首次建立時間，ISO 8601 含時區偏移）、`updated`（最後一次封存時間）、`project`、`session_id`、`cwd`、`archived_turns`（已封存的對話回合數，用來判斷下次要從哪裡繼續）、`source: claude-code`。

### 錯誤處理設計

`main()` 內的例外會被印出到 stderr 並以非零狀態結束（不再靜默吞掉）——因為封存現在是使用者主動執行的指令，出錯時應該讓使用者立即看到，而不是像舊版 hook 那樣為了不打斷 session 而刻意隱藏。個別檢查點（vault 未設定、transcript 找不到、沒有新內容等）則印出中文提示訊息並正常結束，不視為錯誤。

## Agent skills

### Issue tracker

GitHub Issues（`cosmos75/claude-obsidian-memory`），透過 `gh` CLI 操作。見 `docs/agents/issue-tracker.md`。

### Triage labels

五個角色沿用預設名稱，未做任何改名對應。見 `docs/agents/triage-labels.md`。

### Domain docs

單一 context：根目錄的 `CONTEXT.md` 與 `docs/adr/`。見 `docs/agents/domain.md`。
