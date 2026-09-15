---
name: refactoring-cleanup
description: Audit and implement behavior-preserving refactors and code cleanup for XDDPMAPP when the user asks to reduce technical debt, improve maintainability, or simplify existing code; do not use for new features, bug fixes, or documentation-only work.
---

# Refactoring & Cleanup

協助 XDDPMAPP 以小批次、可驗證的方式消除技術債，提升可擴充性與易讀性，同時維持既有可觀察行為與專案契約。

## 使用時機

在使用者要求重構、代碼清理、降低技術債、拆分責任、移除死碼、降低耦合或改善既有程式可維護性時使用。若請求是新增功能、修正明確錯誤、完整安全審查、效能調校或只整理文件，使用相應的工作流程，不要把它們默認擴大成重構工作。

## 工作邊界

- 預設先盤點，再在使用者明確授權的範圍內實作；只要求盤點或建議時保持唯讀。
- 範圍可包含 `frontend/`、`backend/`、`workers/`、`contracts/`，以及保護重構所需的測試與設定；不主動建立技術債 backlog 或整理文件。
- 維持既有 API、資料契約、資料庫結構、任務狀態、穩定 ID、取消／重試／重啟行為、模型參數與 random seed，以及 `masks[N, H, W]` 的 shape、型別與語意。任何需要改變這些契約的工作都要先獨立標示，不能隱含在清理中。
- 不修改 generated、vendor、build、cache 或依賴目錄；不安裝套件、不接觸外部服務、不 commit，也不執行遠端或不可逆操作，除非使用者另行明確授權。

## 工作流程

### 1. 建立上下文與基線

先讀取適用的 `AGENTS.md`、`README.md`、`docs/code_style.md`；若涉及系統邊界或 API，再讀取 `docs/framework.md` 與 `docs/api.md`，只在涉及模型、不確定度或 worker contract 時讀取相應領域文件。

檢查 `git status --short --branch`、staged／unstaged diff、未追蹤的程式碼檔案、實際 caller、設定與測試。記錄既有修改並保留它們，不使用 reset、checkout、clean、stash 或覆蓋檔案來建立基線。若目前只有文件而沒有可執行程式碼，直接回報沒有可重構的程式，不要自行 scaffold。

### 2. 盤點並界定批次

只根據程式碼與 caller 的證據提出候選項目，優先檢查：

- 模組或函式同時承擔多個責任，違反 frontend／API／service／db／integration／worker 的邊界。
- 重複邏輯、過度耦合、難以命名的資料流、弱型別、死碼、隱藏副作用、資源未清理或錯誤處理不一致。
- 會讓新增模型、分析工具、流程狀態或前端 feature 需要重複修改多處的結構性問題。

每個候選項目說明證據、影響、風險、預計改動與驗證方式，區分「可安全清理」和「其實是功能／錯誤修正」。選擇一個可獨立驗證的小批次，明確列出不會處理的項目；若實作途中需要超出原範圍，先停下來說明，不自行擴張。

### 3. 實作行為保持的重構

- 優先透過清楚的責任分層、窄介面、明確型別、共用純函式與移除已證實無用的程式來改善設計。
- FastAPI router 保持薄層，業務規則留在 `services/`，資料庫與外部整合維持隔離；React feature、`lib/api/`、model worker、analysis worker 與 `contracts/` 遵循 `docs/framework.md` 的責任邊界。
- 移除死碼前確認沒有 import、route、設定、動態載入或其他有效 caller；不確定時保留並回報。
- 不以大範圍搜尋取代理解，不為了形式上的簡化犧牲可讀性，也不把公共名稱或資料欄位直接改名而沒有相容策略。
- 只有在重構需要時才新增或調整測試與設定；測試應驗證公開行為、邊界與失敗路徑，而不是綁定私有實作細節。

### 4. 驗證與收尾

先依實際專案設定找出可用的測試、型別檢查、lint 或 formatter；`docs/devlog.md` 提到的工具不是已安裝的證明。能執行時先記錄相關基線，再跑受影響測試與必要的消費者／契約測試；不要為了通過而弱化 assertion、跳過案例或更新不相關 snapshot。資料庫、物件儲存、Modal、網路與模型推論以 mock 或小型 fake 隔離。

最後重新檢查 diff、status 與本次產生的暫存物，只保留授權的程式碼、測試與設定變更。報告應包含：

1. 按優先級排列的技術債發現與證據。
2. 已完成的重構、未處理項目與任何契約風險。
3. 實際執行的命令、通過／失敗／未執行結果，以及失敗是產品問題、測試問題、環境限制或可能的既有問題。
4. 尚未評估的範圍與後續建議；不要宣稱未執行的驗證已通過。

需要撰寫或執行測試時，若專案中的 `$unit-test` 可用，交由它處理測試範圍與測試工件清理；需要獨立檢查變更品質時，可使用 `$code-review`，但不要把 review 工作當成實作授權。
