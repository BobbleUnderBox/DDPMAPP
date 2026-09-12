# XDDPMAPP

本文件定義交付範圍；長期規劃另見[最終目標](docs/project_goal.md)，開發與測試規劃見[開發日誌](docs/devlog.md)。

## 使用者情境

使用者檢視一張影像的分割或異常區域結果，想了解哪些邊界在重複推論時變化較大。系統呈現原圖、多次推論輪廓與分歧區域，協助使用者辨識需要進一步確認的位置。

## 專案功能

- 導入 [model_list](docs/model/model_list.md) 中的五種模型：DermoSegDiff、AutoDDPM、cDAL、CCDM、THOR。
- 使用者選擇模型與影像、設定推論參數，對同一張影像執行多次完整推論，形成目標遮罩。
- 實作 [xtool_list](docs/xtool/xtool_list.md) 中的不確定度視覺化，依[不確定度流程設計](docs/xtool/uncertainty.md)提供三種方式：像素涵蓋比例熱圖、輪廓疊圖、CDclust 分群與代表圖及群比例。
- 三種視覺化共用同一組目標遮罩
- 最後會產生全部流程下來的報表。

以 2D 影像與固定模型權重為範圍；cDAL 的目標為肺野或細胞核，AutoDDPM 與 THOR 的最終異常分數圖須依固定門檻轉成遮罩。模型支援範圍與圖表解讀依不確定度流程設計。

## 大方向流程

```
選擇模型與設定推論參數
    ↓
選擇模型適用的範例
    ↓
開始推論
    ↓
進行不確定度分析
    ↓
查看結果與產生報表
```

## 前端

- 語言與框架：TypeScript（strict）＋ React ＋ Vite
- UI：Tailwind CSS ＋ shadcn/ui

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

- **FastAPI：** 模型、範例影像的取得、模型參數的設定；推論、不確定度分析、整體流程的建立、取得、修改、刪除。
- **PostgreSQL：** 保存模型與工具版本、範例影像 metadata；推論、不確定度分析、流程內容。
- **Object Storage：** 保存原始影像、模型輸出、共用遮罩與視覺化結果；資料庫只存 reference 與 hash。
- **Modal：** 負責非同步推論與後處理。各模型使用獨立環境，將最終結果轉成共用遮罩後，由 CPU worker 統計與產生三種視覺化。

Control plane 使用 Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、psycopg 3。

## 規範文件

專案在 `docs` 下維護以下文件：

- `framework.md`：記錄目錄架構與各文件、檔案的功能。
- `api.md`：記錄前後端介面。
- [model_list.md](docs/model/model_list.md)：模型清單與導入進度。
- [xtool_list.md](docs/xtool/xtool_list.md)：工具清單與實作進度；僅交付不確定度視覺化。
- [devlog.md](docs/devlog.md)：記錄開發、測試、前後端技術與套件
- [uncertainty.md](docs/xtool/uncertainty.md)：紀錄專案所採用的可解釋(不確定性)方法。
