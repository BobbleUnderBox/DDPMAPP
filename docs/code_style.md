# 專案程式風格

本文件是 XDDPMAPP 的第一版程式風格基準，供開發與 Code Review 共用。專案目前尚無實作程式碼或 formatter/linter 設定，因此以下規則是依既定技術架構與 API 契約建立的通用基準；日後若有明確工具設定或穩定的既有寫法，應同步更新本文件。

## 規則優先順序

- 使用者明確需求與驗收條件優先。
- `AGENTS.md` 的代理工作規則優先於一般風格建議。
- 功能行為依 `README.md` 與 `docs/api.md`；分層與責任依 `docs/framework.md`。
- formatter/linter 的機械格式以專案設定為準；沒有設定時依本文件，再參考同一模組附近已採用且一致的寫法。
- 審查只要求新修改符合規範，不因本次修改順便重寫無關的舊程式碼。

## 共通原則

- 優先選擇容易閱讀、容易測試、容易追蹤的明確寫法；避免為了抽象而抽象。
- 一個函式、元件或模組應有清楚且有限的責任；跨層行為放在正確的邊界處理。
- 名稱表達領域概念與資料意義，避免沒有上下文的 `data`、`temp`、`helper`、`utils`。
- 函式與方法以動詞表達行為，型別、類別與資料物件以名詞表達。
- 布林值使用 `is`、`has`、`can`、`should` 等可直接讀懂的前綴；常數使用 `UPPER_SNAKE_CASE`。
- 註解說明原因、限制或不直觀的決策，不重複翻譯程式碼本身。

## 語言與命名

### Python、FastAPI 與 worker

- 模組、函式、方法、變數與參數使用 `snake_case`；類別與例外使用 `PascalCase`。
- 公開函式、服務邊界、資料模型與 worker contract 優先提供型別註記；避免以 `Any` 掩蓋未釐清的資料形狀。
- FastAPI 的 request/response schema 使用 Pydantic model；資料庫 ORM model 不直接作為對外回應型別。
- API router 處理 HTTP 邊界與驗證；流程規則放在 `services/`；資料庫操作放在 `db/`；外部服務連接放在 `integrations/`。
- 不使用寬泛的 `except Exception` 靜默吞錯；捕捉例外時要保留原因、補充上下文，並在適當邊界轉成可理解的錯誤。

### TypeScript、React 與前端

- 變數、函式、props 欄位與 hooks 使用 `camelCase`；React 元件、類別與型別使用 `PascalCase`。
- React hook 以 `use` 開頭；事件處理函式以 `handle` 或 `on` 表達其角色；避免無意義的型別斷言與 `any`。
- 維持 TypeScript strict 的型別資訊，尤其是在 API、表單、任務狀態與分析結果等邊界。
- UI 程式依功能放在 `frontend/src/features/`；全域路由與設定放在 `app/`；API 呼叫集中於 `lib/api/`。
- 伺服器狀態使用既定的 query/data-fetching 邊界；表單驗證與 UI 狀態不要散落成互相衝突的第二套規則。

## 專案邊界與資料契約

- 後端不可讓 API 層直接承擔資料庫、Modal 或物件儲存的細節；跨層溝通透過既定 service、integration 與 contract。
- worker 與 control plane 交換的資料遵守 `contracts/` 定義；新增欄位或改變形狀時，同步更新生產端、消費端與契約文件。
- `run` 與 `analyse` 的狀態、相依關係、取消、刪除、重新執行與穩定 ID 必須符合 `docs/api.md`。
- 任務先保存必要紀錄再派送；取消、重啟、重試與舊工作回報不可造成新狀態被覆寫或重複建立對外物件。
- 分析流程使用同一組座標一致的 `masks[N, H, W]` boolean 遮罩；模型特定輸出轉換與共用視覺化不可混為一層。
- migration 必須是可追蹤的版本化變更；不可用執行期程式碼偷偷修改資料庫結構。

## 品質、測試與文件

- 新增或修改行為時，補上能驗證該行為的測試；優先涵蓋邊界輸入、錯誤路徑、狀態轉換與前後端/worker 契約。
- 依賴 random seed、模型輸出或影像形狀的測試，應固定必要設定並明確檢查資料形狀與型別。
- 不吞掉驗證錯誤、外部服務錯誤或任務失敗原因；紀錄需足以追查流程、任務與 correlation ID，但不得寫入秘密或不必要的敏感資料。
- 修改 API、資料格式、資料庫結構、流程狀態或使用者可見結果時，同步檢查 `README.md`、`docs/api.md`、`docs/framework.md` 與相關領域文件是否需要更新。
- 本文件不取代完整安全、效能或醫療正確性審計；若變更涉及這些風險，應另外標註需要專門審查。
