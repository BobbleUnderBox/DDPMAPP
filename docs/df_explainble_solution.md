# diffusion model 可解釋性解方

## 工具

### [Hallucination Index](https://pubmed.ncbi.nlm.nih.gov/40166669/?utm_source=chatgpt.com)

Hallucination Index 利用生成影像分布與「零幻覺參考分布」之間的 Hellinger distance，量化重建影像的幻覺程度。研究發現，增加反向去噪步驟雖然可能降低 MSE，卻同時提高 Hallucination Index，因此可以補足傳統品質指標無法反映幻覺的問題。

限制：主要提供整體分數，不一定精確指出幻覺出現的位置。
回答：這張影像的整體幻覺風險有多高？

### [SHAFE 幻覺熱圖](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_HalluGen_Synthesizing_Realistic_and_Controllable_Hallucinations_for_Evaluating_Image_Restoration_CVPR_2026_paper.pdf?utm_source=chatgpt.com)

2026年的 HalluGen 研究提出 SHAFE（Semantic Hallucination Assessment via Feature Evaluation），先產生具有已知位置與程度的可控幻覺，再訓練及評估幻覺偵測方法。

SHAFE 可以輸出局部 heatmap，指出哪些區域出現語義上不正確的結構。相較傳統指標，研究報告其幻覺偵測 AUC 提升0.25、假陰性率降低24個百分點；也能訓練不需要 ground truth 的 reference-free detector。

限制：對高頻 artifact 不敏感，或在腦部邊界等強度差異較大的地方產生錯誤反應。
回答：局部風險解釋；幻覺警示圖。

### Posterior uncertainty map
[連結1](https://onlinelibrary.wiley.com/doi/10.1002/mrm.29624?utm_source=chatgpt.com)
[連結2](https://pubmed.ncbi.nlm.nih.gov/36912453/?utm_source=chatgpt.com)

Diffusion Model 可以針對同一筆量測資料多次採樣，再根據樣本間的變異產生 pixel-wise uncertainty map。
Luo 等人的 Bayesian MRI reconstruction 由 posterior distribution 取樣，同時輸出重建影像與每個像素的不確定性。

限制：高不確定性代表模型不穩定；低不確定性不一定代表模型正確。若模型在所有樣本中都一致地產生同一個錯誤結構，不確定性圖仍可能偏低。因此最好與 SHAFE 或 measurement-consistency residual 一起使用。

回答：模型在哪些區域對重建結果沒有把握？



## 組合拳

### [HalluGen](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_HalluGen_Synthesizing_Realistic_and_Controllable_Hallucinations_for_Evaluating_Image_Restoration_CVPR_2026_paper.pdf?utm_source=chatgpt.com)
PSNR、SSIM、MSE主要衡量像素或整體結構相似度，可能無法察覺範圍小但臨床意義重大的錯誤。

HalluGen 的對應方式是人工控制：幻覺位置；幻覺範圍；幻覺嚴重程度；intrinsic hallucination；extrinsic hallucination。
因此可以建立有標註的幻覺 benchmark，測試某個品質指標到底能不能偵測局部錯誤。研究也發現，既有像素與知覺指標經常忽略語義幻覺。

較完整的評估組合應包含：
PSNR／SSIM：整體影像品質。Measurement residual：是否符合原始量測。SHAFE／Hallucination Index：幻覺程度。Posterior variance：模型不確定性。下游任務：病灶分割、組織體積、診斷結果是否正確。醫師評估：影像是否具有臨床合理性。

這是評估框架，不是單一 XAI 方法。

### 臨床信任與責任歸屬：反事實＋不確定性＋臨床驗證

這個問題沒有單一解法。較適合的是「多種解釋同時呈現」。針對醫療分類任務，Favero 等人使用 class-conditional Diffusion Model：以不同疾病條件的重建誤差進行分類；產生 counterfactual image；以 entropy 表示預測不確定性。

因此能同時展示「什麼影像變化會改變診斷」以及「模型有多確定」。但這是分類任務專用，不能直接解釋所有生成與重建模型。
[連結一](https://proceedings.mlr.press/v301/favero26a.html?utm_source=chatgpt.com)

近期放射學 XAI 回顧建議，臨床解釋應結合：saliency／attribution；concept-based explanation；prototype；counterfactual；uncertainty；fidelity、robustness 與人因測試；workflow-integrated structured reporting。

回顧也警告，heatmap 即使看起來合理，也可能不穩定或不忠於模型。
[連結二](https://www.sciencedirect.com/science/article/pii/S3050577126000290?utm_source=chatgpt.com)

## 去噪過程追蹤

### [Diffusion Explainer](https://arxiv.org/abs/2305.03509?utm_source=chatgpt.com)

Diffusion Explainer 將文字編碼、latent representation 與各個 timestep 的影像變化視覺化，並允許比較不同 prompt 如何改變生成過程。56人的使用者研究顯示，這套工具能幫助非專家理解 Stable Diffusion 的生成機制。

限制：主要解釋「模型怎麼運作」，不一定能忠實說明某張醫療影像的因果來源。
回答：教學；prompt 比較；找出概念在哪個 timestep 出現；檢查某個條件何時開始影響生成結果。

### [去噪過程中的概念與區域視覺化](https://www.sciencedirect.com/science/article/pii/S0957417424000964?utm_source=chatgpt.com)

Park 等人利用內部及外部視覺分析，觀察每個 timestep 恢復哪些區域、概念與細節。他們發現模型通常先恢復具有語義資訊的區域，再逐漸形成細節。

回答：病灶在第幾個 timestep 出現；解剖輪廓與細節的生成順序；幻覺是早期 latent layout 造成，還是後期 detail enhancement 造成；某個 timestep 之後是否開始偏離 measurement。

這是目前最具通用性的 Diffusion Model 過程解釋方向之一。

## prompt 與條件追蹤

### [DAAM：文字—影像歸因圖](https://aclanthology.org/2023.acl-long.310/?utm_source=chatgpt.com)

DAAM 將多個 timestep 與 cross-attention layer 的資訊聚合，為每個文字 token 產生 pixel-level attribution map。

回答：「tumor」影響影像的哪個區域？「left」是否真的與左側區域對應？某個病灶描述是否完全沒有被模型使用？兩個詞的注意區域是否錯誤重疊？

限制：不過 attention map 不必然等於因果解釋。若要驗證忠實度，應遮蔽或修改高歸因 token，觀察生成結果是否確實改變。
DAAM 在名詞分割任務達到58.8–64.8 mIoU，並發現描述性形容詞的 attention 經常過度分散。

### [I2AM：影像條件歸因](https://arxiv.org/abs/2407.12331?utm_source=chatgpt.com)
若模型輸入不是文字，而是低品質 MRI、參考影像或其他 modality，可以使用 I2AM。它聚合 image-to-image latent diffusion 中不同 timestep、attention head 與 layer 的 patch-level cross-attention，顯示參考影像的哪些區域影響了輸出。

### [Attend-and-Excite：從解釋進一步修正](https://arxiv.org/abs/2301.13826?utm_source=chatgpt.com)

Attend-and-Excite 會先利用 cross-attention 判斷哪些 prompt token 沒有受到足夠注意，再於推論過程提高這些 token 的 activation。

它能減少：物件或概念被忽略；catastrophic neglect；顏色、屬性綁定錯誤。

## 訓練資料

### [Memorization token attribution](https://mlanthology.org/iclr/2024/wen2024iclr-detecting/?utm_source=chatgpt.com)

Wen 等人發現，可以利用 text-conditional prediction 的 magnitude 在第一個生成步驟偵測記憶風險，並進一步計算每個 token 對記憶現象的貢獻。

例如可顯示：某個人名；醫院名稱；特殊病例描述；特定罕見疾病詞彙；是否使模型更容易重建特定訓練影像。該研究也提出推論階段最小化相關訊號，以及訓練階段過濾高風險樣本的方法。

這是少數同時提供「偵測、解釋、緩解」的記憶問題解法。

### [D-TRAK：訓練資料歸因](https://proceedings.iclr.cc/paper_files/paper/2024/hash/50be7e77b9c883144940be925b608acc-Abstract-Conference.html?utm_source=chatgpt.com)

D-TRAK 嘗試為生成結果找出最具影響力的訓練影像，即：哪幾張訓練影像對這張輸出貢獻最大？

它可以協助：病患影像來源追蹤；尋找近似複製品；著作權歸因；找出造成錯誤結構的訓練樣本。
但研究也發現，在非凸 Diffusion Model 中，一些理論上看似合理的資料歸因設計反而表現較差，顯示目前方法尚未完全成熟。

### [Diffusion Attribution Score](https://mlanthology.org/iclr/2025/lin2025iclr-diffusion/?utm_source=chatgpt.com)

DAS 直接比較模型預測分布之間的差異，用來衡量某筆訓練資料對生成結果的影響，並在 ICLR 2025 的實驗中優於先前基準。D-TRAK 和 DAS 都屬於 training-data attribution，但計算成本及大型醫療資料的可擴展性仍是問題。