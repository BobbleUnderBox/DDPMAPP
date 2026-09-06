[briefing.md](docs/paper_reviews/Baysian_MRI_2023/briefing.md) 中的研究方法說到用 Langevin MCMC 與 MAP、ℓ1-ESPIRiT 及 XPDNet 三者比較，所以這四個是不同方法嗎? 還是說是將 Langevin MCMC 部分替代，MMSE v.s. MAP, 原本量測模型 v.s. ℓ1-ESPIRiT, refineNet v.s. XPDNet

**你的第一組「MMSE vs. MAP」大致正確；後兩組並不是那樣替換。**briefing 的句子把不同層次的名稱放在一起，確實容易誤解。「與三者比較」指的是**比較重建結果**，不是把 Langevin MCMC 與三個同類演算法直接比較。

先把本文的方法拆開：

> **RefineNet 學到的影像先驗＋MRI 量測模型 → Langevin MCMC 抽樣 → 樣本平均得到 MMSE，樣本變異得到不確定性。**

各比較方法的關係如下：

| 重建方式 | 影像知識從哪裡來？ | 如何產生重建？ |
|---|---|---|
| **本文的 MMSE 重建** | RefineNet 學到的擴散先驗 | Langevin MCMC 抽取多張影像，再平均。 |
| **本文的 MAP 比較版本** | 沿用擴散先驗 | 改用確定性更新，尋找後驗密度的峰值。 |
| **ℓ1-ESPIRiT** | 小波稀疏性等數學假設 | 結合多線圈量測限制，求解正則化最佳化問題。 |
| **XPDNet** | 訓練資料學到的重建規則 | 透過自身的展開式神經網路完成重建。 |

這些比較分別安排在原文 §3.3.5、§3.3.6、§3.3.8，並非一次把三個元件逐一替換的實驗。[原文比較實驗](https://ggluo.github.io/assets/pdf/Luo_Magn.Reson.Med._2023.pdf#page=8)

1. **MMSE vs. MAP：主要改變「如何從同一個後驗分布得到答案」。**

   你的理解在這裡最接近原文：

   - **MMSE 路線：**抽取多個可能答案，再取平均。
   - **MAP 路線：**尋找後驗密度最高的答案。

   論文的 MAP 比較沿用擴散先驗與量測限制，關閉更新中的隨機噪聲，進行確定性迭代。因此可以把它理解為**同一框架內，改變推論方式**。但這種最佳化可能只到達局部峰值，也不是從抽出的樣本中挑最好的一張。[原文 §3.3.5](https://ggluo.github.io/assets/pdf/Luo_Magn.Reson.Med._2023.pdf#page=8)

2. **量測模型 vs. ℓ1-ESPIRiT：不是替換量測模型。**

   量測模型描述的是「一張 MRI 影像會產生什麼量測訊號」。**ℓ1-ESPIRiT 同樣需要這份物理關係**，才能檢查重建是否符合實測資料。

   真正改變的是：本文使用**學到的影像先驗＋後驗抽樣**；ℓ1-ESPIRiT 使用**小波稀疏性正則化＋最佳化求解**。[ESPIRiT 原論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4142121/)

   而且，作者自己的擴散方法也使用 **ESPIRiT 估計線圈敏感度**。所以要區分「ESPIRiT 校正工具」與「ℓ1-ESPIRiT 重建方法」。[原文 §3.2](https://ggluo.github.io/assets/pdf/Luo_Magn.Reson.Med._2023.pdf#page=7)

3. **RefineNet vs. XPDNet：是子網路與完整重建網路的不同層次。**

   RefineNet 在本文只負責提供 **score 調整方向**，後面還需要量測校正與 Langevin 抽樣。

   XPDNet 則有自己的完整重建流程，將迭代最佳化展開成可訓練網路。因此論文比較的是 **「本文整套擴散重建流程 vs. XPDNet」**，沒有把 RefineNet 換成 XPDNet 後繼續使用原本的 Langevin 流程。[XPDNet 原論文](https://arxiv.org/html/2010.07290v2)