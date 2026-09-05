# Python 後端

參考：[產品規劃](./project_draft.md) · [模型清單](./model_backpack.md) · [解釋工具清單](./xtool_backpack.md)

## 已確認範圍

- **MVP：**分割不確定性，依序導入 DermoSegDiff、CCDM。
- **資料：**只處理去識別研究資料與預備案例；可接收去識別 DICOM，不接收 PHI。
- **模型：**只執行平台內建、已審核的 adapter 與 checkpoint；不接受任意 Python、pickle 或 `.pt`。

## 技術架構

```text
React
  → FastAPI control plane
      ├─ PostgreSQL + JSONB + pgvector
      ├─ S3-compatible object storage
      └─ Modal dispatcher
          ├─ model-specific GPU workers
          └─ CPU post-processing / report worker
```

- **FastAPI：**驗證、權限、案例、執行計畫、任務狀態與報表 API。
- **PostgreSQL：**保存 metadata、版本、任務狀態、能力、註記與稽核紀錄。
- **Object Storage：**保存影像、mask、tensor、heatmap、快照與報表；資料庫只存 reference 與 hash。
- **Modal：**只負責非同步運算。各模型使用獨立環境；需要 gradient、activation 或 attention 的工具與模型在同一 worker 執行。
- **Adapter：**宣告模型能力與工具需求；規劃階段先檢查相容性，再允許執行。

Control plane 使用 Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、psycopg 3；測試使用 pytest。

## 資料與任務

- 最小實體：模型／工具版本、資產、解釋 session、plan、run、artifact、report、annotation、audit event。
- Artifact 記錄來源 run、storage key、SHA-256、格式、shape、dtype 與保留期限。
- Run 鎖定 adapter、checkpoint hash、參數與 seed；續跑從已完成 step 的 artifact 開始，不保存 GPU 記憶體。
- 狀態主線：`DRAFT → VALIDATING → APPROVED → QUEUED → RUNNING → COMPLETED`，另有 `FAILED`、`CANCELED`、`WAITING_INPUT`。
- API 只需涵蓋：presigned upload、建立 session／plan、批准與啟動 run、查詢狀態／事件、重試／取消、讀取 artifact、建立 report。

## 第一版模型

| 階段 | 模型 | 最小範圍 |
|---|---|---|
| Sprint 1 | DermoSegDiff | 單張 2D 推論與 5 次 stochastic sampling |
| 下一里程碑 | CCDM | 8 個合理 masks、majority mask 與像素 agreement／entropy |

## 第一版工具

| 工具 | 輸出 |
|---|---|
| 不確定性分析 | 平均 mask、邊界 disagreement、predictive entropy |
| 去噪歷程 | timestep snapshots |
| Seed robustness | 不同 seed 的輸出差異 |
| 人工註記 | 案例與 artifact 的研究註記 |
| 報表 | 版本化 HTML、PDF、JSON，附模型、checkpoint、參數與產物來源 |

第一版不納入需要文字 cross-attention、完整訓練集 gradient、未審核 checkpoint 或任意程式執行的工具。

## 第一版完成條件

```text
去識別影像 → 相容性驗證 → DermoSegDiff × 5
→ mask / disagreement / entropy / snapshots
→ Seed robustness
→ 人工註記 → 版本化報表
```

全流程必須可非同步查詢、失敗重試、取消及稽核，且不得在 worker payload 或 log 中包含病患識別資訊。
