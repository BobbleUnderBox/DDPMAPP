---
name: git-operations
description: 執行 XDDPMAPP 專案的 Git 檢查、分支與 commit 操作，並遵循 docs/devlog.md 的 Git 命名規範；不處理未明確授權的破壞性或遠端操作。
metadata:
  short-description: 依專案規範安全檢查、命名與執行 Git 操作
---

# Git Operations

本 skill 用於 XDDPMAPP 專案中需要檢查狀態、建立或檢查分支、整理 commit、檢視 diff，或執行其他 Git 操作的工作。專案 Git 規範的唯一來源是 [`docs/devlog.md`](../../../docs/devlog.md)；每次需要命名、commit 或分支操作時，先讀取該文件的「Git 命名規範」，不要自行創造另一套規則。

## 工作邊界

- 先讀取適用的 `AGENTS.md` 與 `docs/devlog.md`，再執行會改變工作樹或歷史的操作。
- 先執行 `git status --short --branch`，必要時查看 `git diff`、`git diff --cached` 與未追蹤檔案；保留使用者既有修改，不任意 reset、checkout、clean、stash、rebase 或覆蓋檔案。
- 只處理使用者明確指定的檔案與範圍，不把無關或既有修改混入 staging 或 commit。
- 遠端 push、force push、刪除分支、改寫歷史及其他不可逆操作，除非使用者明確要求，否則不要執行；需要執行時先確認精確目標與風險。
- 不修改既有 commit 或分支名稱；Git 自動產生的 merge 訊息保留原格式。本階段不新增 hooks、CI 或發布流程。
- 若規範文件不存在、內容互相矛盾，或工作樹的所有權不清楚，停止相關 mutation，說明阻礙與需要的決策。

## Git 規範來源

任何需要建立或檢查分支、撰寫或檢查 commit message 的工作，都必須先讀取 [`docs/devlog.md`](../../../docs/devlog.md) 的 `## Git 命名規範`，並依該節底下的 `### Commit message` 或 `### Branch` 執行。不要在本 skill 重述、複製或自行推導 Git 命名規則；`devlog.md` 是唯一規範來源。

若該文件或指定章節不存在、內容無法讀取或規範互相矛盾，停止相關命名或 mutation，回報問題，不要自行補規則。

## 常見操作流程

### 只讀檢查

1. `git status --short --branch`
2. 依需求查看 `git diff`、`git diff --cached`、`git log --oneline -n <n>` 或指定檔案歷史。
3. 將工作樹現況、相關差異與限制清楚回報；沒有可檢查的變更時，不臆測 commit 內容。

### 建立分支

1. 先讀取 `docs/devlog.md` 的 `### Branch`，依其中規範產生名稱。
2. 用 `git check-ref-format --branch <branch-name>` 驗證 Git 語法，再依同一節人工核對專案規範。
3. 只有在使用者要求建立或切換時才執行 `git switch -c` 或 `git switch`。

### 建立 commit

1. 先讀取 `docs/devlog.md` 的 `### Commit message`，再依實際變更產生訊息。
2. 檢查 status、完整 diff 與 staged diff，確認沒有混入無關修改。
3. 使用者明確要求 commit 時才 stage／commit；commit 後回報 commit id、訊息與剩餘工作樹狀態。

### Merge、rebase 與遠端

這些操作可能改變歷史或影響其他人。除非使用者明確指定來源、目標與操作，否則只提供檢查結果或操作建議；不要自行 push，也不要 force push。
