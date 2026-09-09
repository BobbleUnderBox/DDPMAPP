# Posterior variance：Diffusion MRI 重建的後驗變異數

> 查核日期：2026-09-07。本文延伸 [xtool_backpack.md](./xtool_backpack.md) 的 posterior uncertainty map，聚焦同一筆 MRI 量測下的重建不確定性。
> 程式、模型權重與資料的授權分別判斷；安全性採公開文件與部分原始碼的靜態查核，未安裝外部專案、執行模型、下載大型權重或完成漏洞掃描。

## 1. 對 diffusion model 的可解釋性目的

**要回答的問題是：「給定這次量測與這個模型，哪些位置仍存在多種可能的重建結果？」**

Diffusion／score model 提供影像先驗，MRI 的 forward operator 與量測 likelihood 提供資料約束。對相同量測重複進行條件抽樣，再計算各像素在最終樣本之間的 variance 或 standard deviation，可將重建歧義呈現成 uncertainty map。Luo 等人的 Bayesian MRI 工作便以抽樣均值與像素變異圖同時呈現重建及不確定性。[Luo et al., 2023](https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.29624)

這是**輸出層級的統計解釋**：指出結構、邊界或細節是否在不同可能解中穩定。它本身不會找出是哪個神經元、訓練病例或因果因素造成差異。

| 可以解釋 | 不能單憑此方法宣稱 |
| --- | --- |
| 在既定量測、先驗與 sampler 下，某區域的重建分散程度 | 高值代表病灶、幻覺或模型必然錯誤 |
| 多個重建是否對同一結構有不同判斷 | 低值代表真實解剖一定正確 |
| 不同取樣率或 reconstruction 設定下，不確定性如何改變 | 色圖數值就是已校準的臨床錯誤機率 |

它與另兩種方法互補：[measurement residual](./xtool_measurement_consistency_residual.md) 檢查是否符合已取得的量測；[credible interval](./xtool_credible_interval.md) 把樣本分布轉成有後驗機率質量解釋的區間。Variance 濃縮分布的分散程度，本身沒有「95%」涵義。

## 2. 方法、必要輸入與輸出

### 2.1 先定義是哪一個 posterior

以多線圈 MRI 為例：

$$
y=Ax+\varepsilon,\qquad A=PFS,
\qquad p_\theta(x\mid y)\propto p(y\mid x,A,\Sigma_\varepsilon)\,p_\theta(x).
$$

其中 $P$ 為 sampling operator、$F$ 為 Fourier transform、$S$ 為 coil sensitivity operator，$\theta$ 是固定的 diffusion 模型權重。$\Sigma_\varepsilon$ 描述量測雜訊；若將複數資料拆成實、虛部堆疊的實向量，Gaussian likelihood 可寫為：

$$
\log p(y\mid x)=-\tfrac12(y-Ax)^T\Sigma_\varepsilon^{-1}(y-Ax)+C.
$$

複數 Gaussian 的 covariance 定義與實向量版本係數不同，實作時必須統一 convention。只有 magnitude 影像時，也不能假設原始複數 k-space 的 Gaussian noise 直接變成同樣的 magnitude likelihood。[MRI likelihood 與 Bayesian formulation](https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.29624)

實際 sampler 產生的往往是某個近似分布 $q_{\theta,\mathcal S}(x\mid y)$，其差異受到離散步數、data consistency、noise temperature、最後去噪與模型誤差影響。
因此應分開記錄：

- **樣本分散度：** 實際生成結果的 variance，可直接計算。
- **近似後驗變異數：** 有合理的 posterior sampler 與 likelihood，但仍存在近似誤差。
- **經驗校準結果：** 在獨立驗證集檢查不確定性與誤差／區間 coverage 的關係。校準過某項指標，不代表已證明整個 joint posterior 正確。

多個 seed 只提供不同隨機路徑；若沒有量測條件化，或 sampler 沒有對應的 posterior 目標，就應稱為「重複生成的分散度」。此外，diffusion timestep 的 $\beta_t$、$\tilde\beta_t$ 或 reverse-step variance 描述單步轉移，**不是**最終影像的 $\operatorname{Var}(X\mid y)$。[Luo et al.：第 2.2–2.5 節](https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.29624)

### 2.2 最低輸入

| 使用情況 | 必須提供 |
| --- | --- |
| 已有可追溯的最終樣本，只計算 variance | 同一案例、同一量測與模型設定下的 $K\ge2$ 份最終重建；樣本軸、空間座標、單位、正規化與複數／magnitude 定義；抽樣設定紀錄 |
| 需要從 MRI 量測重新抽樣 | 原始 $y$、可執行的 $A$ 與 adjoint、mask、coil sensitivity maps、likelihood／noise 設定、checkpoint、架構與一致的前處理 |
| 重現與判斷抽樣品質 | sampler、schedule、步數、step size、data-consistency strength、最終去噪設定、seed、樣本數、是否共享起始路徑／burn-in |
| 要驗證可靠性或建立警示門檻 | 相同資料域的獨立驗證集、對齊且定義相容的 reference、量測退化設定；ROI 分析另需 ROI 定義 |

**基本 variance 計算不需要 ground truth；主張它能預示重建誤差，則需要驗證。** 若只有一張最終影像，不能由它可靠推回此方法需要的樣本變異。

### 2.3 像素與 ROI 統計量

對同一 $y$ 取得 $x^{(1)},\ldots,x^{(K)}$，令 $z^{(k)}=T(x^{(k)})$ 是要呈現的實值量，例如 MRI magnitude。每個像素 $j$ 計算：

$$
\bar z_j=\frac1K\sum_{k=1}^{K}z_j^{(k)},\qquad
\widehat v_j=\frac1{K-1}\sum_{k=1}^{K}(z_j^{(k)}-\bar z_j)^2,
\qquad \widehat s_j=\sqrt{\widehat v_j}.
$$

$K-1$ 對獨立同分布樣本提供常見的不偏 sample variance；相依 MCMC 樣本不能僅靠此分母宣稱有限樣本不偏。Variance 的單位是影像強度的平方；SD 與影像同單位，通常更易閱讀。

MRI 的表示方式必須明列：

- **Magnitude variance：** 先對每份複數重建取絕對值，再計算 $\operatorname{Var}(|X_j|\mid y)$。一般而言，$|\mathbb E[X]|\ne\mathbb E[|X|]$。
- **Complex variance：** 使用 $\sum_k|x_j^{(k)}-\bar x_j|^2/(K-1)$，等於實部與虛部 variance 的總和；它與 magnitude variance 不同。
- **Phase uncertainty：** 相位有角度週期，不能直接對跨越 $-\pi,\pi$ 的角度套一般實數 variance。
- **ROI／下游量：** 對每個完整樣本先計算 $g(x^{(k)})$，再統計其 variance。例如 ROI 均值的 variance 含像素間 covariance，不能用 ROI 內 variance map 的平均取代。

### 2.4 實作流程

1. **固定推論條件。** 保存 $y,A,\Sigma_\varepsilon,\theta$ 與所有 sampler 設定；同一組 posterior samples 不混入不同 mask、不同測量雜訊 realization 或不同 guidance 設定。
2. **執行條件抽樣。** 使用不同完整隨機路徑取得最終影像；不可把同一次去噪過程的不同 timesteps 當作同分布 posterior samples。
3. **檢查抽樣品質。** 比較獨立批次的均值、variance 與 ROI 分布；增加樣本及步數後確認結果穩定。對固定目標分布的 MCMC 保留鏈識別，檢查 mixing、ESS 與適用的 $\widehat R$。
4. **統一表示與尺度。** 使用相同空間座標、共同強度縮放與一致的 coil combination。不要每份影像各自 min–max normalize；這會改變分散度。
5. **計算統計量。** 輸出均值、variance、SD；大體積資料可用線上均值／variance 累積降低記憶體，但仍保留足夠樣本供視覺與分布檢查。
6. **疊圖與對照。** 同時呈現重建、SD map、幾份代表樣本及 residual；固定跨病例比較的色階，並清楚標示遮罩與單位。
7. **獨立驗證。** 在未參與調參的資料上比較 uncertainty 與 error；若用 variance 校準模型或門檻，保留另一個測試集報告結果。

MCMC 的 ESS 與 Monte Carlo standard error 反映估計本身的精確度；它們不能證明 likelihood 或影像先驗符合真實資料。不同噪聲尺度的 diffusion 軌跡也不符合固定目標鏈的直接診斷前提。[Stan：Posterior analysis](https://mc-stan.org/docs/reference-manual/analysis.html)

建議輸出至少包含：

| 輸出 | 解釋與紀錄 |
| --- | --- |
| `mean`、`variance`、`std` | 指明是實值、magnitude 或 complex 統計，以及 sample axis／單位 |
| 代表性最終樣本 | 檢查高變異是邊界位移、紋理變化還是不同結構假設 |
| ROI 統計與樣本分布 | 保存 ROI 定義，避免只用全圖平均掩蓋小病灶風險 |
| 抽樣與版本紀錄 | seed、樣本數、sampler 設定、checkpoint hash、程式 commit、前處理與色階 |
| 驗證狀態 | 標記「sample spread／近似 posterior／已有指定資料域校準證據」 |

## 3. 實作限制與解讀邊界

### 抽樣近似不等於真實 posterior

score-MRI 的 `get_pc_fouriercs_fast` 在 predictor／corrector 更新後置換已採樣的 Fourier 值，屬於 data-consistency projection。它不是一個任意有噪 likelihood 的通用、已校準 posterior sampler；如果量測有顯著雜訊，強制精確符合資料可能低估不確定性。應檢查使用的 real、complex 或 multi-coil solver 是否符合實際問題。[sampling.py 的實作](https://github.com/hyungjin-chung/score-MRI/blob/main/sampling.py)

Luo 等人的實驗亦因未知量測雜訊而以經驗選定 $\lambda$ 平衡 prior 與 data consistency。這支持將其視為研究上的近似後驗不確定性來源，不能直接沿用結果聲稱新醫院或新掃描設定已校準。[論文第 2.4 節](https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.29624)

### 低變異可能只是共同犯錯

所有樣本可能一起漏掉罕見病灶、採納錯誤 prior，或落在同一個 mode。強 guidance、最後去噪或過早共享／分裂抽樣路徑，也可能壓縮樣本差異。Variance 小只能描述這個生成程序的分布集中，不能保證真值位於其中。

固定 $\theta$ 的 $\operatorname{Var}(X\mid y,\theta)$ 包含 likelihood 與欠定逆問題下的解歧義，**不等於純 epistemic uncertainty**，也不會自動涵蓋模型權重、coil calibration 或 forward model 的未知程度。若要納入這些因素，須另建立模型並對其共同抽樣／積分；任意混合多模型結果仍需要統計定義。

### 樣本數、運算與估計誤差

若每份最終樣本需要 $T$ 次模型評估，$K$ 份樣本的工作量約隨 $KT$ 成長；batch 平行化可減少延遲但提高記憶體需求。不可把特定論文硬體上的時間當成本專案效能保證。

可用 32、64、128 份樣本作為逐次加量的工程試驗，觀察 ROI variance 和熱圖穩定性；這些數字不是通用充分條件。即使抽樣獨立且邊際近似 Gaussian，sample variance 的相對標準誤仍約為 $\sqrt{2/(K-1)}$，例如 $K=32$ 時約 25%；厚尾、多峰或相依性還會改變精確度。

增加樣本降低的是 variance **估計值**的 Monte Carlo 誤差，不會自然消除後驗分布本身的不確定性。均值估計的 MCSE 約為 $s/\sqrt{K_{\mathrm{eff}}}$，不是供顯示的 posterior SD。[Stan：ESS 與 MCSE](https://mc-stan.org/docs/reference-manual/analysis.html#effective-sample-size)

### 圖像表示與驗證可能誤導

- 非剛性配準會把不同重建中的邊界位移消除；除非它本來就是研究定義的一部分，不應為了讓 uncertainty map 變小而使用。
- 平均影像可能平滑掉兩種互斥的結構；相同 variance 也可能來自完全不同的分布形狀，應保留樣本並搭配 credible interval／分布圖。
- 經驗 error 與 predicted variance 的比較需以案例或病患分組；大量相關像素不能冒充大量獨立驗證病例。
- 高 uncertainty 是否值得警示需用對應任務驗證；全圖 error correlation 不能取代小病灶、不同 scanner／contrast 或 OOD 情境的評估。

## 4. 開源來源：程式、權重與資料分開看

### 官方程式

| 來源 | 適用範圍 | 授權及採用限制 |
| --- | --- | --- |
| [SPRECO](https://github.com/mrirecon/spreco) | Luo 等人的 generative image prior 訓練與 MRI 重建研究；與 BART 工作流程相連 | 主體為 BSD-3-Clause；指定 BART、TensorFlow、OpenAI 衍生檔另依 BSD、Apache-2.0、MIT。這是逐檔適用，不能任選一種授權。見 [LICENSE](https://raw.githubusercontent.com/mrirecon/spreco/main/LICENSE)。 |
| [score-MRI](https://github.com/hyungjin-chung/score-MRI) | 作者的 PyTorch accelerated MRI 實作，提供 real、single-coil 及 multi-coil 推論入口；可包裝為重複抽樣來源 | 根目錄 [LICENSE](https://github.com/hyungjin-chung/score-MRI/blob/main/LICENSE) 為 Apache-2.0；但 [fastmri_utils.py](https://github.com/hyungjin-chung/score-MRI/blob/main/fastmri_utils.py) 明列 Facebook MIT 來源，須另保留第三方聲明。 |

**兩者都是重建／抽樣基礎，不應直接描述為已提供完整校準驗證的 variance 工具。** 核心的均值、sample variance、SD 與 ROI 統計可自行撰寫；複用作者程式時則依其授權保留相應聲明。

SPRECO 於 **2025-12-30 封存為唯讀**，採用者需自行承擔相容性修復與維護。它適合作為方法參考；目前已有 PyTorch reconstruction pipeline 時，score-MRI 的介面通常較容易整合，但仍需處理下節的依賴及 checkpoint 問題。[SPRECO 封存狀態](https://github.com/mrirecon/spreco)

本次對照的程式版本為 score-MRI [`8359aae`](https://github.com/hyungjin-chung/score-MRI/tree/8359aae5a4eca1e6d9447d35820e07f5188f9b00) 與 SPRECO [`7673d2b`](https://github.com/mrirecon/spreco/tree/7673d2bfd5b2d79eea8925ed2f569b19e3f1794e)；採用時應再鎖定完整 commit，避免以浮動的 `main` 作可重現版本。

### 模型權重

| 來源 | 查核結果 | 實作決策 |
| --- | --- | --- |
| score-MRI `checkpoint_95.pth` | [官方 README](https://github.com/hyungjin-chung/score-MRI#installation) 與 [install.sh](https://github.com/hyungjin-chung/score-MRI/blob/main/install.sh) 連到 Dropbox。查核範圍未見獨立的 checkpoint 授權／再散布說明，且本次未下載檔案。 | 記錄為「公開下載來源、權重授權待確認」；不可僅依程式 Apache-2.0 推定權重可任意再散布。 |
| SPRECO notebook 連結的 Hugging Face priors | 確切來源為 [Guanxiong/MRI-Image-Priors](https://huggingface.co/Guanxiong/MRI-Image-Priors)。查核 [model API](https://huggingface.co/api/models/Guanxiong/MRI-Image-Priors) 的 cardData 未見 license、檔案清單未列 LICENSE；[README](https://huggingface.co/Guanxiong/MRI-Image-Priors/raw/main/README.md) 亦未提供獨立授權。對照 revision 為 `7f03fa3d022721cd27be70f0e555a2c67629d07a`。 | 標記為「可下載、權重授權未釐清」，不可推定套用 SPRECO 程式授權。 |
| 後續 magnitude-prior 工作的 Zenodo 資產 | [Zenodo 8083750](https://zenodo.org/records/8083750) 的[官方 metadata](https://zenodo.org/api/records/8083750) 明列 `cc-by-4.0`，附件為 `Diffusion.zip` 與 `PixelCNN.zip`。本次僅查 metadata，未下載壓縮檔。 | 可確認此記錄標示 CC BY 4.0；採用 diffusion 部分仍須核對相容性、內含檔案與必要署名。不能反推 Hugging Face 的另一份資產也採相同授權。 |

這修正了 backpack 對 Zenodo 模型／資料「未見清楚獨立授權」的概括：**Zenodo 8083750 有記錄層級的 CC BY 4.0 標示**，Hugging Face 與 Dropbox 則仍須各自釐清。Zenodo 的 diffusion prior 也不能未經核對就當作 2023 Bayesian MRI 各項實驗的相同 checkpoint。

### 資料

score-MRI 的訓練入口使用 fastMRI，repository 也含範例影像；程式授權不會取代這些資料的使用條件。NYU 官方 fastMRI 頁面要求申請並接受各資料集的 Data Sharing Agreement，限制於內部研究／教育，且有再散布限制；條款也明列資料及其生成影像不供病人診斷或照護使用。[fastMRI 官方資料條款](https://fastmri.med.nyu.edu/)

使用自有 MRI 時，應確認資料取得、研究使用、去識別化與分享範圍。模型訓練、variance 校準、示例影像公開與權重再散布是不同用途，不能以「程式是開源」一併推定獲准。

## 5. 開源來源安全性與具體處理

| 查核面向 | 已觀察到的事實 | 工程處理 |
| --- | --- | --- |
| 下載完整性 | score-MRI `install.sh` 直接從 Dropbox 下載 `.pth`，該腳本未驗證 checksum／signature。 | 先確認發布者與資產授權，固定來源和版本；比對可信發布者提供的 hash。自行計算 hash 只能識別後續是否改變，不能自行證明來源可信。 |
| 反序列化 | [utils.py](https://github.com/hyungjin-chung/score-MRI/blob/main/utils.py) 的 `restore_checkpoint` 呼叫 `torch.load`，沒有明確指定 `weights_only`。 | 使用相容且已修補的 PyTorch，明設受限載入；不要因舊 checkpoint 載入失敗便對未信任檔案關閉限制。必要的格式轉換需在無敏感資料、無憑證的隔離環境完成。 |
| 權重與架構不一致 | 同一函式使用 `load_state_dict(..., strict=False)`。 | 記錄並審核 missing／unexpected keys；錯誤載入可能產生看似可用、實際不可靠的 uncertainty map。 |
| 未鎖定依賴 | score-MRI 的 [requirements.txt](https://github.com/hyungjin-chung/score-MRI/blob/main/requirements.txt) 未釘選版本；安裝腳本指定 Python 3.8、CUDA toolkit 10.2，並非現代環境的完整 lockfile。 | 建立可重現且受維護的相容環境，審核依賴和原生 CUDA 擴充；升級後重新驗證 sampler 與統計輸出。 |
| SPRECO 維護負擔 | [env.yaml](https://github.com/mrirecon/spreco/blob/main/env.yaml) 含 TensorFlow 2.4.1 等舊環境設定；[setup.py](https://github.com/mrirecon/spreco/blob/main/setup.py) 多數依賴未鎖版，且 repo 已封存。 | 整理最小依賴並建立自己的鎖版與修補流程；舊環境能重現不代表安全，新版能安裝也不代表數值相容。 |
| SPRECO 的外部資產 | [官方 Colab notebook](https://github.com/mrirecon/spreco/blob/main/examples/demo_sampler_colab.ipynb) 從 Hugging Face 下載 config 與 TensorFlow checkpoint，未固定 revision；此路徑使用 TensorFlow restore，不能套用成 PyTorch `torch.load` 的相同查核結論。 | 分別固定設定與 checkpoint revision／hash，審核 notebook 安裝及下載儲存格，使用隔離環境與相容且修補過的 TensorFlow。 |
| 病患資料外流 | 不確定性統計可以在本機完成，並不需要把原始影像送到 GitHub、Dropbox 或 Hugging Face。 | 將資產下載與病例推論分開；限制研究環境出網，不在公開 notebook、log 或 Git repository 保存可識別的 MRI／metadata。 |

`weights_only=True` 能減少一般 pickle 動態執行面，但不是安全保證。[PyTorch serialization 文件](https://docs.pytorch.org/docs/2.6/notes/serialization.html#torch-load-with-weights-only-true) 說明其受限載入機制；官方 [GHSA-63cw-57p8-fm3p／CVE-2026-24747](https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p) 仍記載惡意 checkpoint 可在受影響版本觸發程式執行，列出 `<=2.9.1` 受影響、`>=2.10.0` 修補該漏洞。這是已知風險示例，不是本次對整個依賴樹完成安全驗證。

**採用判斷：** 自行實作統計層，接有明確權利與抽樣定義的本地 MRI 模型，最容易控制依賴及資料流。SPRECO／score-MRI 可作研究基礎，但現有資產仍需補齊版本、權重條款、載入流程與校準驗證；官方來源或開源授權都不能單獨證明資安與臨床可靠性。
