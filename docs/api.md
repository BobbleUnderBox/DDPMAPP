# 專案中的 api

包含模型資訊、對應模型的可用影像範例、推論參數設定、推論實體、分析實體、流程實體。

## 各項定義

### 流程實體

一個流程實體會包含模型資訊、對應模型的可用影像範例、推論參數、random seed 設定，這三項是在流程建立時（初始設定）時會要求輸入或選擇。

流程實體會對應到最多一個推論實體、最多一個分析實體。

流程實體中，推論實體與分析實體完成後可產生報表。

### 推論實體

一個 run 對應到唯一一個流程實體，依照其實體內容跑推論。
run 會有其狀態，`status`，其值為 `QUEUED`、`RUNNING`、`COMPLETED`、`FAILED`、`CANCELING`、`CANCELED`。

### 分析實體

一個 analyse 對應到唯一一個流程實體，在 run 建立且完成後才可建立，所以會對應到唯一推論實體。
analyse 會有其狀態，`status`，其值為 `QUEUED`、`RUNNING`、`COMPLETED`、`FAILED`、`CANCELING`、`CANCELED`。
