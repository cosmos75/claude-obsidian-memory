# claude-obsidian-memory

一個 Claude Code plugin：自動將每次對話的摘要封存到本地 Obsidian vault，並依專案分類存放，讓過去的決策與脈絡可以在 Obsidian 中被搜尋與回顧。

## 功能

- **一次性初始化**：透過 `/obsidian-memory-init` 指令設定 Obsidian vault 路徑，設定值寫入 `~/.claude/obsidian-memory/config.json`。
- **手動封存**：執行 `/obsidian-memory-save` 時，腳本會呼叫 `claude -p`（使用 Haiku 模型）產生一份第三人稱摘要，並以繁體中文寫入 vault 中對應專案的資料夾；檔案同時保留使用者輸入的原始提示詞全文（逐條列出，不經摘要）。
  - **第一次執行**：從對話開頭完整封存整個 session。
  - **同一個 session 再次執行**：只封存上次封存之後新增的內容，附加到既有檔案，不重複記錄。
- **依專案分類**：封存路徑為 `<vaultPath>/<archiveSubfolder>/<專案名稱>/`，每個工作目錄（依 basename 判斷）各自獨立存放。
- **標準命名規則**：檔名格式為 `{YYYY-MM-DD}-{HHMMSS}-{session_id 前 8 碼}.md`，避免手動命名造成的重複或不一致。
- **GitHub Stars 匯入**：執行 `/stars-to-obsidian` 時，拉取目前 GitHub 帳號 star 過的所有 repo，逐一抓 README 分析用途、安裝方式、適用平台後依主題分類寫入 vault，並產生一份分類索引筆記；沿用 `/obsidian-memory-init` 設定的同一個 vault 路徑。
- **你寫的東西不會被蓋掉**：每篇 star 筆記結尾都有一個 `## 我的笔记` 分界，這行以下是你的地盤。重新生成（`--refresh`）只會更新分界以上的機器產生內容，你手寫的部分由腳本原樣保留——不是靠提示詞約束，是結構上碰不到（見 [ADR-0001](docs/adr/0001-machine-region-merged-by-script.md)）。
- **不會誤動你自己的檔案**：管道只認 frontmatter 裡的來源標記，不看檔案放在哪個資料夾。沒有標記的檔案一律視為你自己的東西，即使它就放在管道的資料夾裡（見 [ADR-0002](docs/adr/0002-identify-pipeline-output-by-marker.md)）。

## 安裝

```
/plugin marketplace add cosmos75/claude-obsidian-memory
/plugin install obsidian-memory
```

## 使用方式

安裝後執行：

```
/obsidian-memory-init /path/to/your/obsidian/vault
```

之後想封存目前的對話時，隨時執行：

```
/obsidian-memory-save
```

摘要會寫入 `<vault>/Claude Code/<專案名稱>/` 資料夾；同一個 session 內重複執行只會附加新內容。

想把 GitHub star 過的 repo 整理進同一個 vault，隨時執行：

```
/stars-to-obsidian
```

預設處理最近 50 個 star（按時間倒序），可加 `--limit all` 處理全部、`--refresh` 覆蓋已存在的筆記、`--no-readme` 跳過 README 深度分析加速執行。筆記會寫入 `<vault>/GitHub Stars/`，並依主題分類產生索引筆記 `GitHub Stars.md`。

## 檔案結構

```
.claude-plugin/
  plugin.json         # plugin manifest
  marketplace.json     # 讓此 repo 本身可作為 marketplace 安裝
commands/
  obsidian-memory-init.md   # /obsidian-memory-init 指令
  obsidian-memory-save.md   # /obsidian-memory-save 指令
  stars-to-obsidian.md      # /stars-to-obsidian 指令
scripts/
  vault_notes.py              # 純函數：合併、設定解析、來源判斷（唯一有測試的地方）
  obsidian_memory_archive.py  # 執行封存與摘要產生
  merge_note.py               # 安全寫入筆記，保留人類區
  backfill_source_marker.py   # 一次性遷移：替舊筆記補來源標記
tests/
  test_vault_notes.py         # python3 -m unittest discover -s tests
CONTEXT.md                    # 領域詞彙表
docs/adr/                     # 架構決策紀錄
```

## 授權

MIT License，詳見 [LICENSE](LICENSE)。
