# XDDPMAPP

本文件定義交付範圍；長期規劃另見[最終目標](docs/project_goal.md)，開發與測試工具及開發流程見[開發日誌](docs/devlog.md)，Git 命名規範見[Git 命名規範](docs/git_conventions.md)。

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

## 驗收條件與產品目標驗證

- [model_list](model/model_list.md) 中五種模型（DermoSegDiff、AutoDDPM、cDAL、CCDM、THOR）皆能成功完成推論。
- 同一張影像可透過不同 seed 重複推論，保留每次最終輸出
- 在 analyses 步驟中重複推論的輸出能轉成同座標的 `masks[N, H, W]` boolean 遮罩。
- [不確定度流程設計](xtool/uncertainty.md)中的三種視覺化皆能使用同一組遮罩產生結果：像素涵蓋比例熱圖、輪廓疊圖、CDclust 分群與代表圖及群比例。
- 前端可選擇模型與適用範例；管理流程、推論與分析，查看分析結果，並產生與查看流程報表。操作範圍依 API 定義。

## 規範文件

專案在 `docs` 下維護以下文件：

- [`framework.md`](docs/framework.md)：記錄目錄架構與各文件、檔案的功能。
- [`api.md`](docs/api.md)：記錄前後端介面。
- [model_list.md](docs/model/model_list.md)：模型清單與導入進度。
- [xtool_list.md](docs/xtool/xtool_list.md)：工具清單與實作進度；僅交付不確定度視覺化。
- [devlog.md](docs/devlog.md)：記錄開發與測試工具及開發流程。
- [git_conventions.md](docs/git_conventions.md)：定義 commit message 與 branch 命名規範。
- [code_style.md](docs/code_style.md)：共用程式風格、分層、資料契約、測試與文件規範。
- [uncertainty.md](docs/xtool/uncertainty.md)：紀錄專案所採用的可解釋(不確定性)方法。
