# 開發日誌

## 驗收條件與產品目標驗證

- [model_list](model/model_list.md) 中五種模型（DermoSegDiff、AutoDDPM、cDAL、CCDM、THOR）皆能成功完成推論。
- 同一張影像可透過不同 seed 重複推論，保留每次最終輸出，並轉成同座標的 `masks[N, H, W]` boolean 遮罩。
- [不確定度流程設計](xtool/uncertainty.md)中的三種視覺化皆能使用同一組遮罩產生結果：像素涵蓋比例熱圖、輪廓疊圖、CDclust 分群與代表圖及群比例。
- 前端可選擇模型與影像、設定推論參數、查看任務狀態，並呈現原圖與視覺化結果。
- 視覺化驗證涵蓋相同遮罩、空遮罩、已知形狀與比例、多物件與孔洞，以及相同設定與 seed 的重現性；細節依不確定度流程設計。

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

- **FastAPI：**輸入與參數驗證、模型清單、推論任務啟動、狀態查詢與結果讀取 API。
- **PostgreSQL：**保存模型與工具版本、輸入資產 metadata、推論設定、任務狀態與結果索引。
- **Object Storage：**保存原始影像、模型輸出、共用遮罩與視覺化結果；資料庫只存 reference 與 hash。
- **Modal：**負責非同步推論與後處理。各模型使用獨立環境，將最終結果轉成共用遮罩後，由 CPU worker 統計與產生三種視覺化。

Control plane 使用 Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、psycopg 3。

- 測試工具：pytest

### 資料與任務

- 最小實體：模型／工具版本、輸入資產、run、artifact。
- Artifact 記錄來源 run、storage key、SHA-256、格式、shape 與 dtype，讓原始輸出、共用遮罩與視覺化結果可互相追溯。
- Run 記錄模型版本、模型 checkpoint hash、輸入影像、目標結構、推論與後處理參數、樣本數與每個樣本的 seed；同一組樣本固定遮罩門檻與座標轉換規則。
- 狀態主線：`QUEUED → RUNNING → COMPLETED`，另有 `FAILED`、`CANCELED`；執行前由 API 驗證輸入與參數，失敗時提供錯誤資訊。
- API 涵蓋：模型清單、presigned upload、建立並啟動 run、查詢狀態、重試／取消、讀取 artifact；重試重新執行該次任務。
- 五種模型的推論與遮罩轉換依[不確定度流程設計](xtool/uncertainty.md)實作；三種視覺化讀取同一份遮罩快取。
