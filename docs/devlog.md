# 開發日誌

## 開發工具

- 前端測試工具：Vitest、Playwright
- 前端開發流程：Figma 設計 → AI 產生畫面草稿 → GitHub → AI coding agent 整合與測試
- 後端測試工具：pytest

## Git 命名規範

本規範適用於往後新建的工作分支及人工撰寫的 commit message。Git 自動產生的 merge 訊息保留原格式；既有 commit 歷史及分支名稱不追溯修改。本階段以文件約定執行，不新增 hooks、CI 或發布流程。

### Commit message

標題格式為 `type(scope): 描述`，scope 可省略，如 `type: 描述`。type、scope 使用小寫英文；scope 表示修改範圍，例如 `api`、`frontend`、`worker`。

| Type | 用途 |
| --- | --- |
| `feat` | 新增功能 |
| `fix` | 修正錯誤 |
| `docs` | 新增或修改文件 |
| `refactor` | 重構程式碼，不新增功能或修正錯誤 |
| `test` | 新增或修改測試 |
| `style` | 調整排版、縮排等不影響程式行為的格式，不用於 UI 外觀功能變更 |
| `build` | 修改建置系統或相依套件 |
| `ci` | 修改持續整合設定或腳本 |
| `perf` | 改善效能 |
| `chore` | 其他不屬於上述類型的維護工作 |
| `revert` | 還原先前的 commit |

- 描述使用繁體中文，以「新增、修正、移除」等動詞開頭，具體說明修改內容，不加結尾句號。
- 完整標題（含 type、scope 與標點）以 50 字元內為目標；中文不套用英文首字大寫要求。
- 本文選填，與標題空一行，使用繁體中文說明修改原因及影響。中文按語意換行；若有英文段落，每行以 72 字元內為原則。
- 不相容變更在 type 或 scope 後加上 `!`，如 `feat(api)!: 調整任務回應格式`，並以 `BREAKING CHANGE:` 說明影響及必要的遷移方式。此標記用於破壞相容性的變更，非泛指大型修改。
- Footer 與前文空一行。有相關 issue 時，可使用 `Refs: #123` 表示關聯，或在解決該 issue 時使用 `Closes: #123`。

正確範例：

```text
docs: 新增 Git 命名規範
fix(api): 修正取消任務後的狀態更新
```

含不相容變更的完整範例（僅示範訊息格式）：

```text
feat(api)!: 重新命名任務回應欄位

統一回應欄位命名，方便前端辨識任務狀態。

BREAKING CHANGE: 將 state 改為 status，呼叫端需同步更新欄位讀取方式
Refs: #123
```

| 錯誤範例 | 原因 |
| --- | --- |
| `更新文件` | 缺少 type 與冒號 |
| `Fix(API): 修正任務狀態` | type、scope 未使用小寫英文 |
| `docs: 新增命名規範。` | 描述加了結尾句號 |
| `fix: 修改一些東西` | 未具體說明修改內容 |

### Branch

工作分支格式為 `<type>/<description>`。現有主分支 `main` 保留原名，免用類型前綴。

| Type | 用途 | 範例 |
| --- | --- | --- |
| `feature` | 新功能 | `feature/add-report-export` |
| `fix` | 錯誤修正 | `fix/cancel-run` |
| `hotfix` | 正式環境緊急修正 | `hotfix/restore-report-download` |
| `docs` | 文件 | `docs/git-conventions` |
| `refactor` | 重構 | `refactor/task-service` |
| `test` | 測試 | `test/run-cancellation` |
| `chore` | 維護 | `chore/update-dependencies` |

- 固定使用表中的分支類型；例如新功能使用 `feature/`，不混用 `feat/`。
- description 簡短描述工作目的，只使用小寫英文字母、數字及連字號，並以英文字母或數字開頭與結尾。
- 不使用空白、底線、連續連字號或結尾連字號；`/` 僅用於分隔 type 與 description。
- 有 issue 時使用 `<type>/<issue-number>-<description>`，例如 `fix/123-cancel-run`；編號不含 `#`，沒有 issue 時省略編號。

| 錯誤範例 | 原因 |
| --- | --- |
| `feature/AddReport` | 描述含大寫字母 |
| `fix/cancel_run` | 使用底線 |
| `docs/git--conventions` | 使用連續連字號 |
| `docs/git-conventions-` | 使用結尾連字號 |
| `feat/add-report-export` | 未使用本專案固定的 `feature` 類型 |

可用 `git check-ref-format --branch <branch-name>` 檢查 Git 語法是否合法；此指令不會檢查本專案的類型、小寫與連字號等命名約定，仍需依上述規範核對。
