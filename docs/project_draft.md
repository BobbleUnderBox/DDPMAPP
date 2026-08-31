# 專案草稿

## 使用者情境

提供醫療人員在使用 diffusion model 時候能評判 diffusion model 所生成結果是否合理。

## 專案功能

提供多種可解釋性工具，醫療人員要提供 model、要解釋的 instance、model 訓練相關資訊 (optional)。Given 使用者給的資訊多寡、想要解釋的方向，會自動生出可解釋性工具使用的途徑，指導使用者流程化操作。

流程化操作結束後會生成可解釋性的報表，另外，若沒有完成可解釋性操作也會提供暫存點。

## 使用技術架構

前端：網頁(我想用視覺化寫網頁工具+AI輔助撰寫前端網頁)
後端：Python
基礎設施：用 modal 來進行模型部署與可解釋工具部署。

## 規範文件
關於 Documentation，整個專案會在 \docs 中有:

framework.md: 記錄目錄架構下每一個文件或檔案詳盡的功能。
api.md: 交接前後端。
model_list.md: 目前先要 demo 用的 model 清單。
xtool_list.md: 目前要先實作出的 xai tool 清單。
