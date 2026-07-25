# Issue tracker：GitHub

這個 repo 的 issue 與規格（PRD）都放在 GitHub Issues，一律用 `gh` CLI 操作。

Repo：`cosmos75/claude-obsidian-memory`。`gh` 在 clone 內執行時會自己從 `git remote -v` 推斷，通常不必顯式指定。

## 慣例

- **建立 issue**：`gh issue create --title "..." --body "..."`。多行內文用 heredoc，或先寫成檔案再用 `--body-file`。
- **讀取 issue**：`gh issue view <number> --comments`，需要時用 `jq` 過濾留言並一併取出 labels。
- **列出 issue**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，搭配 `--label`、`--state` 過濾。
- **留言**：`gh issue comment <number> --body "..."`
- **貼上／移除標籤**：`gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **關閉**：`gh issue close <number> --comment "..."`

## 當 skill 說「發布到 issue tracker」

建立一個 GitHub issue。

## 當 skill 說「取回相關的 ticket」

執行 `gh issue view <number> --comments`。

## 這個 repo 的現況

- Issue #4「vault 護欄：人類區保護、來源標記、設定檔對稱化」是 `/to-spec` 產出的第一份規格，貼有 `ready-for-agent`。要寫新規格時可以拿它當格式參照。
- 除了 triage 用的標籤之外，repo 裡其餘標籤（`bug`、`enhancement`、`question` 等）都是 GitHub 建立 repo 時給的預設值，不構成任何流程約定。
