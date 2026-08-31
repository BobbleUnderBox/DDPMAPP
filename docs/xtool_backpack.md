# diffusion model 可解釋性解方

## 工具

以下「必要」指實際執行工具時的最低輸入；「視情況」指只有在特定方法、訓練或驗證時才需要的資訊。若資料或模型已在專案中，提供可定位的檔案路徑、checkpoint 名稱或版本 ID 即可。

### [Saliency／feature attribution](https://www.sciencedirect.com/science/article/pii/S3050577126000290)

Saliency 與 feature attribution 估計影像區域或輸入特徵對分類結果的影響。常見方法包含 gradient-based 的 Grad-CAM、LRP、Integrated Gradients，以及 perturbation-based 的 occlusion、SHAP。它們補充 DAAM 與 I2AM：後兩者追蹤 Diffusion Model 的文字或影像條件，而這一類方法主要解釋臨床分類器依賴哪些影像證據。

限制：heatmap 看起來符合臨床直覺，不代表它忠實反映模型的決策；結果也可能對微小輸入擾動或方法參數不穩定，應另外檢驗 fidelity 與 robustness。
回答：哪些區域或特徵最推動這次預測？遮蔽該區域後，結果是否真的改變？

**使用時需提供的資訊：**

- **必要：** 要解釋的影像或特徵資料、已訓練分類器及其模型檔／程式框架、與模型訓練一致的前處理，以及一個明確的 scalar target，例如分類 logit、segmentation 的指定 class／pixel／ROI 分數或下游任務分數。
- **視方法：** Grad-CAM 需指定卷積層並能取得 activation 與 gradient；LRP 需模型各層資訊與傳播規則；Integrated Gradients 需 baseline；occlusion 需遮蔽值、區塊大小與步幅；SHAP 需 background/reference dataset 與取樣預算。
- **若要驗證：** 需提供可做遮蔽或刪除測試的資料、允許的擾動範圍，以及 ground truth／專家標註或重複擾動設定，以檢查 fidelity 與 robustness。

### [Hallucination Index](https://pubmed.ncbi.nlm.nih.gov/40166669/?utm_source=chatgpt.com)

Hallucination Index 利用生成影像分布與「零幻覺參考分布」之間的 Hellinger distance，量化重建影像的幻覺程度。研究發現，增加反向去噪步驟雖然可能降低 MSE，卻同時提高 Hallucination Index，因此可以補足傳統品質指標無法反映幻覺的問題。

限制：主要提供整體分數，不一定精確指出幻覺出現的位置。
回答：這張影像的整體幻覺風險有多高？

**使用時需提供的資訊：**

- **必要：** 一組 clean ground truth、由同一 ground truth 產生的多次雜訊量測、對應的多次生成式重建，以及建立「零幻覺參考分布」所需的 forward diffusion／雜訊設定；還需指定反向去噪停止步驟，並由樣本估計均值、共變異數或 noise power spectrum。
- **視情況：** 若要比較不同成像條件，需提供 measurement SNR、空間解析度／MTF 與正規化方式；若要同時評估準確度，另提供 MSE 等指標設定。
- **重要：** 原論文版本需要 ground truth 與重複抽樣，是資料集層級的評估方法，不能只靠單張重建影像計算可靠的 Hallucination Index。

### [SHAFE 幻覺熱圖](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_HalluGen_Synthesizing_Realistic_and_Controllable_Hallucinations_for_Evaluating_Image_Restoration_CVPR_2026_paper.pdf?utm_source=chatgpt.com)

2026年的 HalluGen 研究提出 SHAFE（Semantic Hallucination Assessment via Feature Evaluation），先產生具有已知位置與程度的可控幻覺，再訓練及評估幻覺偵測方法。

SHAFE 可以輸出局部 heatmap，指出哪些區域出現語義上不正確的結構。相較傳統指標，研究報告其幻覺偵測 AUC 提升0.25、假陰性率降低24個百分點；也能訓練不需要 ground truth 的 reference-free detector。

限制：對高頻 artifact 不敏感，或在腦部邊界等強度差異較大的地方產生錯誤反應。
回答：局部風險解釋；幻覺警示圖。

**使用時需提供的資訊：**

- **Full-reference SHAFE：** 必須提供重建影像、與其像素對齊的 clean ground truth、預訓練特徵編碼器及其前處理；另需指定 low-pass filter 與 heatmap 聚合參數。
- **Reference-free detector：** 必須提供重建影像、原始低品質量測，以及已在相近資料域訓練好的 detector/checkpoint；使用者不需再提供 ground truth。
- **若要自行訓練或換資料域：** 需提供 clean 影像集、量測退化的 forward operator、生成幻覺所用的 diffusion model／feature encoder，以及幻覺位置、類型與程度的 mask／標籤。

### Posterior uncertainty map

[連結1](https://onlinelibrary.wiley.com/doi/10.1002/mrm.29624?utm_source=chatgpt.com)
[連結2](https://pubmed.ncbi.nlm.nih.gov/36912453/?utm_source=chatgpt.com)

Diffusion Model 可以針對同一筆量測資料多次採樣，再根據樣本間的變異產生 pixel-wise uncertainty map。
Luo 等人的 Bayesian MRI reconstruction 由 posterior distribution 取樣，同時輸出重建影像與每個像素的不確定性。

限制：高不確定性代表模型不穩定；低不確定性不一定代表模型正確。若模型在所有樣本中都一致地產生同一個錯誤結構，不確定性圖仍可能偏低。因此最好與 SHAFE 或 measurement-consistency residual 一起使用。

回答：模型在哪些區域對重建結果沒有把握？

**使用時需提供的資訊：**

- **必要：** 原始量測 \(y\)、完整 forward operator 與校正資訊、可做 posterior sampling 的 diffusion／score model checkpoint、與訓練一致的正規化方式，以及 sampler、noise schedule、step size、data-consistency strength、隨機種子與抽樣次數。MRI 還需提供 undersampling mask；多線圈資料另需 coil sensitivity maps。
- **視情況：** 指定要輸出的統計量，例如 pixel-wise variance、standard deviation 或 credible interval；若輸出是 segmentation，需提供每次抽樣的 class probability 或 mask，並指定 probability、agreement 或 entropy，不能直接對整數類別標籤計算 variance。ground truth 只在製作 error map、PSNR／SSIM 或校準不確定性時需要。

### Measurement-consistency residual：量測一致性檢查

[連結1](https://papers.neurips.cc/paper_files/paper/2022/hash/a48e5877c7bf86a513950ab23b360498-Abstract-Conference.html)
[連結2](https://pubmed.ncbi.nlm.nih.gov/33950837/)

將重建影像經已知的 forward operator 投影回量測空間，再計算原始量測與預測量測之間的 residual，例如 \(r=y-A\hat{x}\)。Residual norm 可以作為整體警示分數；在 sinogram、k-space 或其他量測域呈現 residual map，則能指出模型輸出在哪些量測位置缺乏資料支持。

限制：低 residual 只代表符合已觀測到的量測，不代表影像一定正確；位於 forward operator null space 的錯誤結構仍可能通過一致性檢查。量測雜訊、校正誤差或 forward-model mismatch 也可能造成高 residual，不能直接等同於模型幻覺。
回答：重建結果是否符合原始量測？不一致主要出現在哪些量測位置？

**使用時需提供的資訊：**

- **必要：** 重建影像 \(\hat{x}\)、未經替換的原始量測 \(y\)，以及可執行且已校正的 forward operator \(A\)。需一併提供資料單位、正規化、量測幾何與 operator 參數，例如 MRI 的 sampling mask／coil sensitivity、CT 的投影幾何，或去模糊的 kernel。
- **視情況：** 量測雜訊分布或 covariance，用來選擇 \(L_2\)、加權 norm 或 likelihood-based residual；若要把 residual 轉成警示門檻，還需正常案例或校準資料。計算 residual 本身不需要 diffusion checkpoint 或 ground truth。

### [Class-conditional Diffusion Model：反事實影像](https://proceedings.mlr.press/v301/favero26a.html)

Favero 等人對輸入影像加噪後，分別以預測類別與另一疾病類別進行條件式重建，產生 factual reconstruction、counterfactual image 與 difference map。兩種重建的差異會標出模型認為需要增加、移除或改變哪些影像特徵，診斷才會切換到另一類。

限制：目前主要適用於 class-conditional 醫療影像分類，而且多次加噪與去噪的推論成本高。反事實影像看起來合理，也不代表它是唯一、最小或具有因果性的改變。
回答：如果診斷改成另一類，影像需要出現或消失哪些特徵？哪些區域最影響分類？

**使用時需提供的資訊：**

- **必要：** 待解釋影像、所有候選診斷類別與要比較的反事實類別、可接受這些類別條件的 diffusion model checkpoint，以及對應的影像前處理、class prompt／label mapping、noise schedule、加噪 timestep、sampler、guidance scale 與 seed。
- **視情況：** 若要做 majority vote 或 uncertainty，需指定重複抽樣次數與多組 noise／seed；若沒有可用 checkpoint，需提供帶類別標籤的訓練資料來訓練或微調模型。真實診斷標籤只在評估分類、反事實與 uncertainty 的正確性時需要；一般 unconditional、重建或分割 diffusion checkpoint 不能直接代替 class-conditional image classifier。

### 去噪過程追蹤

#### [Diffusion Explainer](https://arxiv.org/abs/2305.03509?utm_source=chatgpt.com)

Diffusion Explainer 將文字編碼、latent representation 與各個 timestep 的影像變化視覺化，並允許比較不同 prompt 如何改變生成過程。56人的使用者研究顯示，這套工具能幫助非專家理解 Stable Diffusion 的生成機制。

限制：主要解釋「模型怎麼運作」，不一定能忠實說明某張醫療影像的因果來源。
回答：教學；prompt 比較；找出概念在哪個 timestep 出現；檢查某個條件何時開始影響生成結果。

**使用時需提供的資訊：**

- **使用作者介面：** 只需從內建清單選 prompt、guidance scale 與 timestep；Stable Diffusion 模型、seed 和中間資料皆由介面預先提供，不能直接分析任意醫療模型或自由輸入的 prompt。
- **若要重現於自己的模型：** 需提供 prompt／條件、完整 checkpoint（含 tokenizer、text encoder、UNet、VAE）、seed／initial latent、scheduler、步數與 guidance scale，並允許擷取每一步的 text embedding、noise prediction 與 intermediate latent。只有最終影像不足以重建這些資訊。

#### [去噪過程中的概念與區域視覺化](https://www.sciencedirect.com/science/article/pii/S0957417424000964?utm_source=chatgpt.com)

Park 等人利用內部及外部視覺分析，觀察每個 timestep 恢復哪些區域、概念與細節。他們發現模型通常先恢復具有語義資訊的區域，再逐漸形成細節。

回答：病灶在第幾個 timestep 出現；解剖輪廓與細節的生成順序；幻覺是早期 latent layout 造成，還是後期 detail enhancement 造成；某個 timestep 之後是否開始偏離 measurement。

這是目前最具通用性的 Diffusion Model 過程解釋方向之一。

**使用時需提供的資訊：**

- **必要：** 可重現的生成／重建案例（prompt、影像條件或量測、seed）、模型 checkpoint 與架構、完整 sampler／scheduler 設定，以及可存取的各 timestep latent、activation、noise prediction 或 attention map。
- **視方法：** DF-CAM 類方法需 UNet activation 與 gradient；DF-RISE 類方法需 mask 數量／策略，並能遮蔽 latent 後重跑模型；概念分析另需追蹤的概念／token 或概念分類器。若要找出何時偏離量測，還需原始量測 \(y\) 與 forward operator \(A\)。

### prompt 與條件追蹤

#### [DAAM：文字—影像歸因圖](https://aclanthology.org/2023.acl-long.310/?utm_source=chatgpt.com)

DAAM 將多個 timestep 與 cross-attention layer 的資訊聚合，為每個文字 token 產生 pixel-level attribution map。

回答：「tumor」影響影像的哪個區域？「left」是否真的與左側區域對應？某個病灶描述是否完全沒有被模型使用？兩個詞的注意區域是否錯誤重疊？

限制：不過 attention map 不必然等於因果解釋。若要驗證忠實度，應遮蔽或修改高歸因 token，觀察生成結果是否確實改變。
DAAM 在名詞分割任務達到58.8–64.8 mIoU，並發現描述性形容詞的 attention 經常過度分散。

**使用時需提供的資訊：**

- **必要：** 完整 prompt 與要解釋的 token、相容的 text-conditioned diffusion checkpoint／tokenizer、seed 或 initial latent，以及 scheduler、去噪步數、guidance scale 等可重現的生成設定；還必須能在推論時讀取各 timestep、layer 與 head 的 cross-attention。
- **視情況：** 若要比較 prompt 或驗證忠實度，需提供修改／刪除 token 的對照 prompt，並固定 seed 與其他推論參數。只有最終影像、黑箱 API，或模型沒有 text cross-attention 時，不能計算 DAAM。

#### [I2AM：影像條件歸因](https://arxiv.org/abs/2407.12331?utm_source=chatgpt.com)
若模型輸入不是文字，而是低品質 MRI、參考影像或其他 modality，可以使用 I2AM。它聚合 image-to-image latent diffusion 中不同 timestep、attention head 與 layer 的 patch-level cross-attention，顯示參考影像的哪些區域影響了輸出。

**使用時需提供的資訊：**

- **必要：** conditioning／reference image、相容且使用 patch-level cross-attention 的 image-to-image latent diffusion checkpoint、影像 encoder 與前處理、生成輸出或可重現的 seed／initial noise 與 sampler 設定，以及推論中各 timestep、layer、head 的 attention tensor。
- **視任務：** super-resolution 另需 low-quality input；inpainting／virtual try-on 另需 mask 或 agnostic map。還需說明要看 output-to-reference、特定 output patch、layer 或 timestep；ground truth／region mask 只在量化歸因品質時需要。若模型以 concatenation 等方式注入影像條件、沒有 image cross-attention，則不能直接套用 I2AM。

#### [Attend-and-Excite：從解釋進一步修正](https://arxiv.org/abs/2301.13826?utm_source=chatgpt.com)

Attend-and-Excite 會先利用 cross-attention 判斷哪些 prompt token 沒有受到足夠注意，再於推論過程提高這些 token 的 activation。

它能減少：物件或概念被忽略；catastrophic neglect；顏色、屬性綁定錯誤。

**使用時需提供的資訊：**

- **必要：** 完整 text prompt、希望加強的 subject token／token index、可對 latent 求梯度且能讀取 cross-attention 的 text-to-image diffusion checkpoint／tokenizer、seed／initial latent，以及 sampler、步數與 guidance scale。
- **視情況：** attention 目標門檻、介入的 timestep 範圍、latent update step size、平滑參數與最大迭代次數；若要和原生成結果比較，需固定同一 seed 並保留未介入的 baseline。

#### [Memorization token attribution](https://mlanthology.org/iclr/2024/wen2024iclr-detecting/?utm_source=chatgpt.com)

Wen 等人發現，可以利用 text-conditional prediction 的 magnitude 在第一個生成步驟偵測記憶風險，並進一步計算每個 token 對記憶現象的貢獻。

例如可顯示：某個人名；醫院名稱；特殊病例描述；特定罕見疾病詞彙；是否使模型更容易重建特定訓練影像。該研究也提出推論階段最小化相關訊號，以及訓練階段過濾高風險樣本的方法。

這是少數同時提供「偵測、解釋、緩解」的記憶問題解法。

**使用時需提供的資訊：**

- **必要：** 待測 prompt 與 tokenizer、可執行的 text-conditioned classifier-free-guidance diffusion checkpoint、第一個反向去噪步驟的 initial noise／seed，以及該步驟的 conditional、unconditional noise predictions 與其差值／magnitude。
- **視情況：** 若要把分數轉成警示，需提供或先用同模型、同資料域的校準資料建立判定門檻；token 歸因需允許逐一移除／替換 token 並重算分數。驗證是否複製特定訓練影像時，需可搜尋的訓練資料或影像索引與相似度規則；做推論期緩解時，另需指定要抑制的 token 與抑制強度。高分只表示 memorization risk，不能單獨證明輸出複製了某位病患的影像。

#### [Concept-based explanation：概念式解釋](https://www.sciencedirect.com/science/article/pii/S3050577126000290)

Concept-based explanation 將模型的內部表徵或輸出對應到臨床可理解的概念，例如病灶邊界、形狀、密度或解剖結構；TCAV 是代表方法之一。它呈現各概念與預測的關聯，避免只給出缺乏語意的像素熱圖。

限制：需要可信且涵蓋充分的概念定義、範例或標註；概念分數可能受資料偏差或概念間相關性影響，也不等於因果解釋。
回答：模型依賴哪些臨床概念？各概念如何影響診斷？

**使用時需提供的資訊：**

- **必要：** 已訓練模型／checkpoint、要分析的內部 layer、目標輸出或類別、與模型一致的前處理，以及每個臨床概念的明確定義、正例影像／區域、負例或 random counterexamples、用來計算分數的測試案例。
- **視情況：** 若模型不是分類器，需先定義可微分的 scalar target score；若使用 TCAV 並要做可靠推論，需多組 random sets、重複訓練 CAV 與統計顯著性檢定。像素或區域標註不是基本 TCAV 的硬性需求，但有助於驗證概念是否正確。

### example base & training base

#### [D-TRAK：訓練資料歸因](https://proceedings.iclr.cc/paper_files/paper/2024/hash/50be7e77b9c883144940be925b608acc-Abstract-Conference.html?utm_source=chatgpt.com)

D-TRAK 嘗試為生成結果找出最具影響力的訓練影像，即：哪幾張訓練影像對這張輸出貢獻最大？

它可以協助：病患影像來源追蹤；尋找近似複製品；著作權歸因；找出造成錯誤結構的訓練樣本。
但研究也發現，在非凸 Diffusion Model 中，一些理論上看似合理的資料歸因設計反而表現較差，顯示目前方法尚未完全成熟。

**使用時需提供的資訊：**

- **必要：** 要歸因的生成影像、候選訓練資料全集或已篩選集合及其穩定 ID、可微分的模型架構與確切 checkpoint，以及能對每筆訓練樣本和目標影像計算 gradient 的程式；conditional model 另需各樣本與目標的 prompt／condition。
- **計算設定：** 選取的 diffusion timesteps、noise samples、歸因 loss、random projection dimension、regularization，以及足以儲存 \(N \times k\) projected gradients 的運算與空間。重訓刪除高影響樣本只用於反事實驗證，不是基本歸因的必要輸入。

#### [Diffusion Attribution Score](https://mlanthology.org/iclr/2025/lin2025iclr-diffusion/?utm_source=chatgpt.com)

DAS 直接比較模型預測分布之間的差異，用來衡量某筆訓練資料對生成結果的影響，並在 ICLR 2025 的實驗中優於先前基準。D-TRAK 和 DAS 都屬於 training-data attribution，但計算成本及大型醫療資料的可擴展性仍是問題。

**使用時需提供的資訊：**

- **必要：** 要歸因的生成影像、候選訓練樣本與穩定 ID、確切 diffusion checkpoint／noise predictor，以及對模型參數計算 target 與逐筆 training-sample gradients 的白箱存取；conditional model 另需對應 prompt／condition。
- **計算設定：** timestep 與 Gaussian noise 的取樣策略、gradient projection dimension、damping／regularization、正規化方式及運算預算。可先用影像 embedding 篩選候選集；leave-one-out 或重訓只用於驗證 DAS，不是計算分數的必要條件。

#### [Prototype／example-based explanation：原型與案例式解釋](https://www.sciencedirect.com/science/article/pii/S3050577126000290)

Prototype／example-based explanation 以具代表性的病例或影像區域作為 prototype，將目前個案與相似原型、反例或不同類別的原型並列，說明模型依據哪些已知模式做出判斷。

限制：原型可能不具代表性，或把資料偏差包裝成看似合理的案例；需要確認模型使用的相似度確實對應到臨床語意，而不是掃描器、文字標記等捷徑特徵。
回答：這個個案最像哪些代表性病例？模型依據哪些共同特徵判斷？

**使用時需提供的資訊：**

- **必要：** 待解釋個案、已訓練的 prototype／embedding model checkpoint、可追溯到來源病例或影像區塊的 prototype bank、類別／病例 ID、與模型一致的前處理，以及使用的 embedding layer、distance／similarity metric 與取回數量。
- **視情況：** 若尚未建立 prototype bank，需提供有類別標籤的訓練或參考 cohort；若要做臨床驗證，另需病例 metadata、病灶／解剖標註或專家判讀，以檢查代表性與 scanner、文字標記等 shortcut。若只用外部 embedding 做最近鄰檢索，還需 fidelity 測試；否則只能說案例相似，不能宣稱原模型真的依賴該案例。

## 組合拳

### [HalluGen](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_HalluGen_Synthesizing_Realistic_and_Controllable_Hallucinations_for_Evaluating_Image_Restoration_CVPR_2026_paper.pdf?utm_source=chatgpt.com)
PSNR、SSIM、MSE主要衡量像素或整體結構相似度，可能無法察覺範圍小但臨床意義重大的錯誤。

HalluGen 的對應方式是人工控制：幻覺位置；幻覺範圍；幻覺嚴重程度；intrinsic hallucination；extrinsic hallucination。
因此可以建立有標註的幻覺 benchmark，測試某個品質指標到底能不能偵測局部錯誤。研究也發現，既有像素與知覺指標經常忽略語義幻覺。

較完整的評估組合應包含：
PSNR／SSIM：整體影像品質。Measurement residual：是否符合原始量測。SHAFE／Hallucination Index：幻覺程度。Posterior variance：模型不確定性。下游任務：病灶分割、組織體積、診斷結果是否正確。醫師評估：影像是否具有臨床合理性。

這是評估框架，不是單一 XAI 方法。

**若要執行此評估框架，需提供的資訊：**

- **建立 benchmark：** clean ground-truth 影像集、明確的量測退化 forward operator、在同資料域可用的 diffusion model 與 feature encoder，以及要合成的幻覺類型、位置、範圍與嚴重度設定；框架會產生對應的 hallucination masks／labels。
- **評估工具或訓練 detector：** 待評估的 restoration outputs、相對應的量測／ground truth 與 hallucination labels；另需指定要比較的品質指標或 detector 架構、資料切分與評估指標。

### 臨床信任與責任歸屬：反事實＋不確定性＋臨床驗證

這個問題沒有單一解法。較適合的是「多種解釋同時呈現」。針對醫療分類任務，Favero 等人使用 class-conditional Diffusion Model：以不同疾病條件的重建誤差進行分類；產生 counterfactual image；以 entropy 表示預測不確定性。

因此能同時展示「什麼影像變化會改變診斷」以及「模型有多確定」。但這是分類任務專用，不能直接解釋所有生成與重建模型。
[連結一](https://proceedings.mlr.press/v301/favero26a.html?utm_source=chatgpt.com)

近期放射學 XAI 回顧建議，臨床解釋應結合：saliency／attribution；concept-based explanation；prototype；counterfactual；uncertainty；fidelity、robustness 與人因測試；workflow-integrated structured reporting。

回顧也警告，heatmap 即使看起來合理，也可能不穩定或不忠於模型。
[連結二](https://www.sciencedirect.com/science/article/pii/S3050577126000290?utm_source=chatgpt.com)
