# skill 建立的草稿

## codex 用 agent.md

說明專案目標、技術架構、目錄架構，並加註此三項要和 README.md 同步。

提到有哪些 basic skill。
指名技能進入點在哪、skill 型式規範在哪；並提到技能進入點檔案列為必讀，建立skill、修改 skill 時候 skill 型式規範必讀。

agent.md 更新時維持在一千字以下。

## basic skill

以下 skill 是在一開始預設的 skill

Code Review 技能：自動審查新加入的程式碼，確保符合專案既有的程式風格。
Unit Testing 技能：自動撰寫與執行單元測試，避免新修改破壞既有功能。
Issue Triage 技能：自動分類使用者回報的 Bug，並與 GitHub Issues 同步。
Documentation 技能：自動產出或更新 API 文件、維護指引，省去人工記錄的負擔。
版本控制與分支策略：熟練 Git 操作，制定清晰的 branching model（如 Git Flow），管理修復分支與穩定版本。
重構與代碼清理：定期消除技術債（Technical Debt），提升系統的可擴充性與易讀性。


## skill 的進入點

要設一個說明所有根目錄中所有 skill 使用情境、功能的檔案。

其形式為 YAML Frontmatter (觸發機制與元資料)

Frontmatter 位於檔案頂部，採用 YAML 格式。AI 代理在對話初始化階段，僅會讀取並解析所有技能的 Frontmatter，透過其中的描述來決定是否啟用該技能。

核心欄位包含:

name: "技能的唯一識別碼（通常與資料夾名稱一致，採用小寫與連字號）。"
description:
"""
決定技能啟動與否的關鍵樞紐。必須明確指出技能的功能、觸發關鍵字以及範圍邊界。

不良範例：「一個幫助進行擴散模型研究的技能」。過於模糊，缺乏觸發關鍵字，可能導致技能被錯誤地頻繁載入或完全不載入 。
優良範例：「當使用者提及 DDPM 文獻統合、注意力權重矩陣 (Attention weights) 特徵提取、Latent trajectory 平滑化，或要求生成 PyTorch Hook 腳本時使用。涵蓋 U-Net 與 DiT 架構的可解釋性任務」。
"""
location:"指向該技能在專案中的實際位置"

## skill 形式

要建立一個檔案，說明 skill 格式的定義。

使用 Markdown 型式來建立 skill，並且規定格式為以下所述：

Overview: "任務背景與目標的高階描述。"
Decision Trees: "提供明確的分支邏輯，協助代理在不同情況下（例如：處理圖像分割與處理特徵向量提取時）選擇合適的策略。"
Boundaries:
"""
定義 AI 的權限與絕對不可侵犯的規則。通常採用三層系統劃分：
Always do（必須執行）：例如「在提交 PyTorch 程式碼前，必須撰寫驗證張量維度的斷言（Assertions）」。
Ask first（先詢問）：例如「在修改預訓練模型的權重檔案前，必須取得人類研究者的確認」。
Never do（絕對不可執行）：例如「絕不可以在未紀錄隨機種子（Random Seed）的情況下進行潛在軌跡（Latent Trajectory）的採樣實驗」。
"""

Workflow:"將複雜任務拆解為具體、可執行的離散步驟，避免代理在龐大任務中迷失方向。其中可以包含要運行的腳本要在哪個階段運行。"
Output Convention: "嚴格規範輸出的檔案路徑、Markdown 格式或資料結構，確保後續分析的相容性。"