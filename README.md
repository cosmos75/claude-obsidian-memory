# claude-obsidian-memory

一個 Claude Code plugin：自動將每次對話的摘要封存到本地 Obsidian vault，並依專案分類存放，讓過去的決策與脈絡可以在 Obsidian 中被搜尋與回顧。

## 功能

- **一次性初始化**：透過 `/obsidian-memory-init` 指令設定 Obsidian vault 路徑，設定值寫入 `~/.claude/obsidian-memory/config.json`。
- **自動封存**：每次對話結束（`SessionEnd`）時，hook 會呼叫 `claude -p`（使用 Haiku 模型）產生一份第三人稱摘要，並以繁體中文寫入 vault 中對應專案的資料夾；檔案同時保留該次對話中使用者輸入的原始提示詞全文（逐條列出，不經摘要）。
- **依專案分類**：封存路徑為 `<vaultPath>/<archiveSubfolder>/<專案名稱>/`，每個工作目錄（依 basename 判斷）各自獨立存放。
- **標準命名規則**：檔名格式為 `{YYYY-MM-DD}-{HHMMSS}-{session_id 前 8 碼}.md`，避免手動命名造成的重複或不一致。

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

之後每次 Claude Code 對話結束，摘要會自動寫入 `<vault>/Claude Code/<專案名稱>/` 資料夾。

## 檔案結構

```
.claude-plugin/
  plugin.json         # plugin manifest
  marketplace.json     # 讓此 repo 本身可作為 marketplace 安裝
commands/
  obsidian-memory-init.md   # /obsidian-memory-init 指令
hooks/
  hooks.json           # SessionEnd hook 設定
scripts/
  obsidian_memory_archive.py  # 實際執行封存與摘要產生的腳本
```

## 授權

MIT License，詳見 [LICENSE](LICENSE)。
