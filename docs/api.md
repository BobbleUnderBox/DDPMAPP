# 專案中的 api

所有路徑使用 `/api/v1` 前綴，以下表格省略此前綴。第一版只選擇系統事先準備的範例影像，`assets` 提供範例查詢，不提供使用者自行上傳。

| 用途 | 主要 API |
|---|---|
| 模型與參數要求 | `GET /models` |
| 系統範例清單與影像資訊 | `GET /assets`、`GET /assets/{id}` |
| 建立與查詢推論 | `POST /runs`、`GET /runs`、`GET /runs/{id}` |
| 建立與列出分析 | `POST /r1515uns/{id}/analyses`、`GET /runs/{id}/analyses` |
| 查詢分析進度與結果 | `GET /analyses/{id}` |
| 成果資訊與下載 | `GET /artifacts/{id}`、`GET /artifacts/{id}/download` |

| 推論相關 | API |
| 複製原推論設定、seeds 與首次分析設定，建立新 run，重新推論並接續分析 | `POST /runs/{run_id}/retry` |
| 請求取消尚未完成的推論，取消成功後不接續首次分析 | `POST /runs/{run_id}/cancel` |

| 分析相關 | API |
| 沿用同一份推論輸出與該分析的設定，建立新 analysis | `POST /analyses/{analysis_id}/retry` |
| 請求取消該分析，保留已完成的推論輸出 | `POST /analyses/{analysis_id}/cancel` |

## 補充

### 推論與分析的定義

一個 run 固定影像、模型版本、推論設定與 seeds；一個 run 可以建立多份 analysis。`POST /runs` 保存首次分析設定，推論完成後由後端自動建立一次 analysis。

### 推論與分析的資訊

`GET /runs/{id}` 與 `GET /analyses/{id}` 分別回傳該任務的狀態。`status` 表示整體狀態，`phase` 表示目前或最後執行的階段。

| 欄位 | 意義 |
|---|---|
| `id` | 本次 run 或 analysis 的 ID |
| `status` | `QUEUED`、`RUNNING`、`COMPLETED`、`FAILED`、`CANCELED` |
| `phase` | run 可為 `PREPARING`、`INFERENCE`、`SAVING`；analysis 可為 `MASK_CONVERSION`、`VISUALIZATION`、`SAVING`；尚未進入任何階段時為 `null` |
| `progress` | run 提供 `completed_samples` 與 `total_samples`；analysis 以 `phase` 呈現進度，此欄可為 `null` |
| `cancel_requested` | 是否已接受取消要求；不表示運算已停止 |
| `updated_at` | 後端最後確認並更新此任務資訊的 UTC 時間；前端可據此辨識進度是否仍在同步 |
| `error` | 正常時為 `null`；技術失敗時含 `code`、可讀的 `message` 與失敗 `phase` |
| `retry_of` | 重試來源任務 ID；首次建立時為 `null` |
| `run_id` | 僅 analysis 有，對應到其分析的 run |
| `model_id` | 僅 run 有，對應到其推論的 model |

推論進度範例：

```json
{
  "id": "run_001",
  "status": "RUNNING",
  "phase": "INFERENCE",
  "progress": {
    "completed_samples": 12,
    "total_samples": 32
  },
  "cancel_requested": false,
  "updated_at": "2026-09-11T02:00:00Z",
  "error": null,
  "retry_of": null,
  "model": "model_001"
}
```

`completed_samples` 只計入完成一次完整推論、且最終數值輸出已成功保存的樣本；擴散時間步或單輪的中間結果不算另一份樣本。總樣本數 `total_samples` 固定為本次要求的 N，不因失敗或取消縮小。

- **run 的 `COMPLETED`：** N 份最終推論輸出與必要索引已保存，能供分析使用。
- **analysis 的 `COMPLETED`：** 遮罩與分析成果清單已保存，三種視覺化使用的資料可讀取。分析失敗不改變來源 run 的完成狀態。

### 取消與重試

- 取消 API 接受要求後，設定 `cancel_requested=true`，前端顯示「取消中」；後端確認雲端運算已停止、或確認尚未派送且已阻止派送，才標為 `CANCELED`。連線中斷或查詢逾時本身不代表已取消。
- `COMPLETED`、`FAILED`、`CANCELED` 都是終態。對終態任務提出取消要求時，回傳既有狀態，不覆寫結果；若完成與取消同時發生，以後端確認的實際終態為準。
- 取消 run 成功後不建立首次 analysis。取消 analysis 只停止該分析，保留來源 run 與其推論輸出。
- 重試 API 建立並回傳新任務 ID，設定 `retry_of` 指向來源，原任務保留。run 重試沿用推論設定、seeds 與首次分析設定，重新執行整次推論；analysis 重試沿用來源 run 的輸出與該分析設定。分群的隨機 seed 也屬於分析設定。

### 可互動的分析結果

完成後提供成果清單（manifest）。大型陣列與輪廓資料以 artifact ID 引用，由 artifact API 取得。前端依這份清單載入同一份分析的資料。

| 成果清單內容 | 必須保留的資訊 |
|---|---|
| 來源與格式版本 | `schema_version`、`analysis_id`、`run_id`、`asset_id` |
| 共用遮罩 | `masks_artifact_id`，內容為同座標的 boolean `masks[N, H, W]`；三種方法均引用這份遮罩 |
| 樣本索引 `samples` | 每份樣本的 `sample_id`、`seed`、`mask_index`、原始輸出 `raw_artifact_id`，能從遮罩或代表樣本找回原始推論結果 |
| 座標資訊 | H、W、軸順序、座標原點與單位，以及遮罩／輪廓映回輸入影像和預覽圖的轉換規則，供前端正確疊圖 |
| 涵蓋比例 | 數值熱圖的 artifact ID；除顯示用圖片，也保留像素涵蓋比例數值 |
| 輪廓 | 輪廓資料的 artifact ID；依 `sample_id` 保留各連通區域的外框與孔洞邊界，支援單一樣本醒目顯示與縮放 |
| 分群 | 分群資料的 artifact ID；含群成員 `sample_id`、代表樣本 `sample_id`、各群樣本數／比例、空遮罩數／比例、分群穩定性與原因 |
| 實際設定與版本 | 可追溯本次套用的模型版本、checkpoint hash、推論設定、前處理／座標轉換規則、分析設定（含分群 seed）及工具版本；可引用來源 run 的固定紀錄 |

群比例以全部 N 份樣本為分母，另列空遮罩比例，所有比例加總為 1。群組代表須指向實際樣本。`群組不穩定` 或全部空遮罩是可呈現的分析結果，不等同程式執行失敗；應提供分群狀態與原因，保留熱圖與輪廓供觀察。詳細計算及特殊情況依[不確定度流程設計](xtool/uncertainty.md)，此處只約定 API 必須交付的資訊。

### 成果檔案與追溯

`GET /artifacts/{id}` 回傳檔案資訊；`GET /artifacts/{id}/download` 取得對應內容。

| Artifact 資訊 | 意義 |
|---|---|
| `id`、`kind` | 檔案識別與用途，例如原始輸出、遮罩、輪廓或分群結果 |
| `run_id`、`analysis_id` | 來源推論與分析；直接由推論產生的成果，其 `analysis_id` 為 `null` |
| `source_artifact_ids` | 產生此成果所使用的檔案 ID，供追溯與共用既有成果 |
| `storage_key`、`sha256`、`format` | 物件儲存位置、完整性雜湊與檔案格式 |
| `shape`、`dtype` | 陣列的維度與數值型別；非陣列檔案可為 `null` |
| `schema_version`、`producer_version` | 資料格式版本與產生此成果的程式／工具版本 |

影像、原始模型數值輸出與分析陣列保存在物件儲存，資料庫保存索引與上述資訊。每次推論的最終分數圖等原始數值必須保留，不能只保存著色或疊圖後的 PNG；前端預覽圖是另外的顯示成果。資料保存責任見[開發日誌](devlog.md)。
