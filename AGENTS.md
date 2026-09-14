# codex 用 agent 檔案

此份檔案長度維護在一百行以下。

## 使用者介紹

是一名資工系大四學生，但毫無醫療背景，對於軟體工程以及機器學習等也只有最基礎的見解。機器學習知道 diffusion 圖像模型最初淺的運作原理但不知道數學公式具體邏輯；並且對於可解釋畫機器學習也只知道個大概；而軟體工程更是只碰過 vibe coding。

## plugin 用途

- [@Undermind](plugin://app-6a60df60877081919ad4a8109d27535d@openai-curated-remote) 可以用來讀論文

- [@Hugging Face](plugin://hugging-face@openai-curated-remote) 可以用來了解模型、資料

- [@Modal](plugin://modal@openai-curated-remote) 可以用來知道 Modal 這個雲端算力服務平台的細節

## 專案重要檔案與用途

- [`README.md`](README.md)：定義目前交付範圍、使用者情境、主要功能、大方向流程與驗收條件；執行一般開發任務時優先以此為準。
- [`project_goal.md`](docs/project_goal.md)：記錄專案的長期產品目標、完整可解釋性使用情境與最終報表內容；不要將尚未交付的長期規劃當成目前需求。
- [`framework.md`](docs/framework.md)：說明前端、後端、資料庫、物件儲存、Modal workers 的技術架構、目錄分工、部署位置與任務接續規則。
- [`api.md`](docs/api.md)：定義前後端共用的資料概念、流程／run／analyse／報表的操作、狀態、取消、刪除與重新執行規則；API 實作需遵循此行為契約。
- [`model_list.md`](docs/model/model_list.md)：維護目前預計支援及導入中的模型清單，並記錄各模型需要確認的安全性、實作限制與來源。
- [`xtool_list.md`](docs/xtool/xtool_list.md)：維護可解釋性／不確定度工具的規劃與實作清單，並記錄安全性、實作限制與來源等待確認事項。
- [`devlog.md`](docs/devlog.md)：記錄開發工具、測試工具與開發流程，供追蹤實作及驗證方式。
- [`code_style.md`](docs/code_style.md)：定義前後端、worker、資料契約、測試與文件的共用程式風格基準。
