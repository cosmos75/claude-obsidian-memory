# Triage 標籤

Skill 在描述 issue 狀態時講的是五個標準角色。這份檔案把角色對應到這個 repo 實際使用的標籤字串。

**這個 repo 沒有做任何改名**——左右兩欄相同。

| Skill 裡的角色    | 本 repo 的標籤    | 意義                           |
| ----------------- | ----------------- | ------------------------------ |
| `needs-triage`    | `needs-triage`    | 維護者需要評估這個 issue       |
| `needs-info`      | `needs-info`      | 等回報者補充資訊               |
| `ready-for-agent` | `ready-for-agent` | 規格完整，AFK agent 可直接接手 |
| `ready-for-human` | `ready-for-human` | 需要人類實作                   |
| `wontfix`         | `wontfix`         | 不會處理                       |

Skill 提到某個角色時（例如「貼上 AFK-ready 的 triage 標籤」），就用這張表右欄的字串。

## 標籤的來歷

- `wontfix` 是 GitHub 建立 repo 時就有的預設標籤，直接沿用。
- `ready-for-agent` 在發布 issue #4 時建立。
- `needs-triage`、`needs-info`、`ready-for-human` 在跑 `/setup-matt-pocock-skills` 時建立。

日後若要改用別的命名，改這張表的右欄即可，不必重跑設定 skill——但記得同時把 GitHub 上既有 issue 的標籤一併換掉。
