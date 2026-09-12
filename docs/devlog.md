# 開發日誌

## 驗收條件與產品目標驗證

- [model_list](model/model_list.md) 中五種模型（DermoSegDiff、AutoDDPM、cDAL、CCDM、THOR）皆能成功完成推論。
- 同一張影像可透過不同 seed 重複推論，保留每次最終輸出，並轉成同座標的 `masks[N, H, W]` boolean 遮罩。
- [不確定度流程設計](xtool/uncertainty.md)中的三種視覺化皆能使用同一組遮罩產生結果：像素涵蓋比例熱圖、輪廓疊圖、CDclust 分群與代表圖及群比例。
- 前端可選擇模型與系統提供的範例影像；建立、修改、查看、刪除推論、視覺化分系、流程報表。

## 前端

- 語言與框架：TypeScript（strict）＋ React ＋ Vite
- UI：Tailwind CSS ＋ shadcn/ui
- 常用套件：React Router、TanStack Query、React Hook Form、Zod
- 測試工具：Vitest、Playwright
- 開發流程：Figma 設計 → AI 產生畫面草稿 → GitHub → AI coding agent 整合與測試
- 原則：推論操作、任務狀態與結果呈現以程式碼維護；視覺工具只負責介面與版面，畫面草稿使用 mock data。

AI 與雲端視覺工具只能使用合成或去識別資料，不得放入真實病患資料、模型權重、API 金鑰或內部端點。

## 後端

```text
React
  → FastAPI control plane
      ├─ PostgreSQL + JSONB
      ├─ S3-compatible object storage
      └─ Modal dispatcher
          ├─ model-specific GPU workers
          └─ CPU post-processing / visualization worker
```

- **FastAPI：**模型、範例影像的取得；參數與推論、不確定度分析、整體流程的建立、取得、修改、刪除。
- **PostgreSQL：**保存模型與工具版本、範例影像 metadata；參數與推論、不確定度分析、整體報表內容與關係。
- **Object Storage：**保存原始影像、模型輸出、共用遮罩與視覺化結果；資料庫只存 reference 與 hash。
- **Modal：**負責非同步推論與後處理。各模型使用獨立環境，將最終結果轉成共用遮罩後，由 CPU worker 統計與產生三種視覺化。

Control plane 使用 Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、psycopg 3。

- 測試工具：pytest

### 資料與任務

- 最小實體：模型／工具版本、系統範例資產（asset）、run、analysis、artifact。一份 asset 可建立多個 run；一個已完成 run 可提供多份 analysis 使用。
- Asset 由開發者匯入並登錄影像來源、適用的模型版本／目標與輸入規格。使用者只選擇系統範例；建立 run 前仍須檢查所選範例與模型是否相容。原始數值輸入與顯示預覽分開保存。
- Run 記錄模型版本、checkpoint hash、輸入 asset、目標結構、前處理與推論設定、樣本數及每份樣本的 ID／seed，保存 N 次完整推論的最終原始輸出與座標資訊。會影響模型運算的內部門檻屬於推論設定。
- Analysis 引用來源 run，記錄最終異常分數轉成遮罩的門檻（`final_anomaly_threshold`，僅適用異常偵測輸出）、遮罩轉換／座標規則、分群設定與分群 seed、分析工具版本及共用遮罩引用。三種視覺化使用同一組固定設定的遮罩；每次提交建立新 analysis，保留原有分析。推論 seed 與分群 seed 分開記錄。
- Artifact 記錄來源 run，以及適用時的來源 analysis，並保存 storage key、SHA-256、格式、shape、dtype 與 sample ID／座標映射等 metadata。原始數值輸出、共用遮罩與視覺化成果可互相追溯；實際欄位與結果清單依 [api.md](api.md)。
- 建立 run 時同時保存首次分析設定；本機後端確認推論完成後，自動建立一次首次 analysis。Run 與 analysis 的重試都建立新 ID 並保存來源關聯；run 重試複製原推論與首次分析設定，analysis 重試沿用同一個已完成 run 的輸出。
- Run 與 analysis **各自**使用 `QUEUED → RUNNING → COMPLETED` 狀態主線，另有 `FAILED`、`CANCELED`，並分別記錄 `phase`、更新時間與錯誤資訊。Run 的 `COMPLETED` 表示 N 份完整推論輸出已保存且可讀；analysis 的 `COMPLETED` 表示其必要分析成果已保存且可讀。推論進度以已保存的完整樣本數／總樣本數計算，不以 diffusion 時間步代替。
- 取消請求先記錄 `cancel_requested`；已派送工作須確認停止後才進入 `CANCELED`。取消 analysis 不改變已完成 run 的狀態，已確認的終態不被較晚回報覆寫。合法空遮罩或群組不穩定屬於結果資訊，不直接標為 `FAILED`；技術失敗回傳失敗階段與錯誤。細節依 [api.md](api.md)。
- API 涵蓋模型與系統範例清單、建立及查詢 run／analysis、各自重試／取消、讀取 artifact 資訊與下載成果。所有路徑使用 `/api/v1` 前綴，完整路徑、狀態欄位與成果規則依 [api.md](api.md)。第一版不提供使用者上傳 API，範例由專案的匯入腳本管理。
- 五種模型的推論與遮罩轉換依[不確定度流程設計](xtool/uncertainty.md)實作；固定後處理設定的單位為 analysis，三種視覺化讀取該 analysis 引用的同一份遮罩快取。
