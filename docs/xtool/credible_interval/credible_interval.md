# Credible interval：後驗可信區間

> 查核日期：2026-09-07。依 [xtool_backpack.md](./xtool_backpack.md) 的 posterior uncertainty／Bayesian MRI 情境整理，對應 [xtool_list.md](./xtool_list.md) 的 credible interval 項目。本文區分數學方法、抽樣後端、統計工具、權重與資料；安全性為公開來源及指定程式的靜態初篩，未安裝或執行外部 repository、下載權重或進行漏洞掃描。

## 1. 對 diffusion model 的可解釋性目的

**回答：「在這筆量測與目前模型假設下，這個像素或 ROI 指標有哪些合理數值範圍？」**

Credible interval 將同一量測的 posterior samples 轉成有機率意義的上下界。相較只顯示 posterior variance 的大小，區間可呈現不對稱性，例如病灶 ROI 平均訊號的下界、上界與中位數，以及是否跨過預先定義的研究門檻。它屬於輸出不確定性的解釋，不提供神經網路內部特徵的因果歸因。

MRI 情境可用 diffusion／score model 表示影像先驗，再結合量測模型產生條件式重建。Chung 與 Ye 的 score-MRI 以 score prior、SDE 更新與 data consistency 交替重建，並討論生成式抽樣的不確定性用途；這提供樣本來源，但不自動證明某個 sampler 的名目 95% 區間已校準。[score-MRI 論文](https://arxiv.org/abs/2110.05243)

建議呈現三種結果：

- **Pixel／voxel-wise 區間：** 下界圖 $L$、中位數圖、上界圖 $U$ 與寬度圖 $W=U-L$，指出哪些位置仍容許較大的訊號差異。
- **ROI／任務指標區間：** 固定 ROI 的平均訊號、組織體積或其他明確定義的 scalar；比逐像素區間更容易連結研究問題。
- **代表性完整樣本：** 與區間圖並列，保留解剖結構的聯合變動；把各像素下界或上界拼成的影像不一定是任何一張合理重建。

窄區間只代表目前條件分布集中；若先驗偏差或 sampler 漏掉其他模式，所有樣本可能一致地出錯。應與 [measurement-consistency residual](./xtool_measurement_consistency_residual.md) 及 [posterior variance](./xtool_posterior_variance.md) 一起閱讀。

## 2. 方法與機率意義

### 2.1 先定義要抽樣的 posterior

令 $x$ 為未知影像、$y$ 為已觀測量測、$A$ 為 forward operator、$\theta$ 為固定的 diffusion model 參數：

$$
y=Ax+\varepsilon,\qquad
p_\theta(x\mid y,A)\propto p(y\mid x,A)\,p_\theta(x).
$$

MRI 常見 $A=MFS$：$S$ 為 coil sensitivity，$F$ 為 Fourier transform，$M$ 為 sampling mask。Likelihood 還需描述量測雜訊；固定校正值與固定模型權重時，區間不會自動涵蓋它們本身的不確定性。

重建樣本記為 $x^{(1)},\ldots,x^{(K)}$，必須來自**同一個 $y$、operator、likelihood 與 sampler 設定**。實際 diffusion 後端通常產生近似分布 $q_{\theta,\mathrm{sampler}}(x\mid y,A)$；未驗證其 posterior 忠實度前，報告應註明「近似後驗區間」或「重建樣本經驗區間」，不能只因換 seed 就宣稱有效 Bayesian posterior。

對像素強度 $z=x_i$ 或 ROI 指標 $z=g(x)$，連續分布下理想的 $100(1-\alpha)\%$ 可信集合滿足下式；離散指標可能只能得到至少指定機率質量的集合：

$$
P_\theta\{z\in C_\alpha(y)\mid y,A\}=1-\alpha.
$$

此處的機率是條件於量測與模型的 posterior 機率。頻率學派 confidence interval 則以重複取得資料時區間涵蓋固定真值的長期比例定義；兩者不能只因數字同為 95% 就互換名稱。[Stan 的 posterior interval 說明](https://mc-stan.org/learn-stan/case-studies/tutorial_rstanarm.html)

### 2.2 等尾可信區間：建議先做的版本

令 $Q_p(z\mid y)$ 為 posterior 的第 $p$ 分位數：

$$
C^{\mathrm{ETI}}_\alpha(z)
=\left[Q_{\alpha/2}(z\mid y),\;Q_{1-\alpha/2}(z\mid y)\right].
$$

95% 等尾區間使用 2.5% 與 97.5% 分位數；以樣本分位數估計，不必假設 Gaussian。實作要固定量化變數、抽樣軸、分位數算法與軟體版本；例如 `numpy.quantile(samples, [0.025, 0.975], axis=0, method="linear")`。預設 `axis=None` 會把影像與樣本攤平，不能用來產生逐像素區間。[NumPy quantile 官方文件](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html)

### 2.3 HPD／HDI：適合補充偏態或多峰分析

Highest posterior density（HPD）集合可定義為：

$$
C^{\mathrm{HPD}}_\alpha=\{z:p(z\mid y)\geq c_\alpha\},
\qquad\int_{C^{\mathrm{HPD}}_\alpha}p(z\mid y)\,dz=1-\alpha.
$$

對連續、單峰的一維分布，常以最短且含指定機率質量的 highest density interval（HDI）估計。ArviZ 0.22.0 的預設 `_hdi` 先排序，再選取指定樣本跨度下最窄的窗口；它是樣本算法，並非直接計算高維影像的聯合 posterior 密度。[ArviZ 0.22.0 實作](https://github.com/arviz-devs/arviz/blob/v0.22.0/arviz/stats/stats.py)

- 多峰 posterior 的 HPD 可能由數段不相連區間組成。強制只輸出一段 HDI 可能跨過低密度谷，掩蓋互斥的重建解。
- ArviZ 的 `multimodal=True` 可嘗試回傳多段區間；結果仍受密度估計、樣本數與 `max_modes` 影響，並不保證找到所有模式。
- MRI phase 是 circular variable；直接對接近 $-\pi$ 與 $\pi$ 的樣本做普通分位數會出錯。需圓形統計或先明確選擇 magnitude；ArviZ 0.22.0 提供 `circular=True`，但不可與其 multimodal 模式同用。[ArviZ hdi API](https://python.arviz.org/en/v0.22.0/api/generated/arviz.hdi.html)

### 2.4 ROI 區間必須先逐樣本計算指標

固定 ROI $R$ 的平均訊號，先算：

$$
z^{(s)}=g(x^{(s)})=\frac{1}{|R|}\sum_{i\in R}x_i^{(s)},
\qquad C^{\mathrm{ETI}}_\alpha(g)=
[\widehat Q_{\alpha/2}(z^{(1:K)}),\widehat Q_{1-\alpha/2}(z^{(1:K)})].
$$

此設計保留每張樣本內像素間的相關性。**先算逐像素上下界再取 ROI 平均，通常不等於 ROI 平均的可信區間。** 非線性的體積、最大值或病灶對比也應先逐樣本計算 $g$，再取區間；這是 posterior transformation 的推導。

若 $g$ 使用固定 segmentation model，結果只傳遞重建樣本的變動，不包含該 segmentation model 自身的不確定性。類別編號沒有自然數值順序，不能對 label 0、1、2 直接取分位數後解讀為疾病區間；可改為體積等有意義的 scalar 或各類別機率。

## 3. 最低必要輸入與實作流程

| 階段 | 必要資訊 | 視情況增加 |
| --- | --- | --- |
| 已有 posterior samples，只做區間 | 同一案例的完整最終樣本、樣本軸、影像座標／尺度、抽樣來源與設定、區間機率及 ETI／HDI 選擇 | ROI mask、scalar 函數、樣本權重或有效樣本數診斷 |
| 從 diffusion model 產生樣本 | $y$、可執行的 $A$、雜訊模型、相容 checkpoint、訓練前處理、sampler／步數／guidance／seed／抽樣次數 | MRI mask、coil maps、相位與線圈合成策略、校正誤差的建模 |
| 驗證區間 | 獨立測試案例及可信的 reference、相同的量化變數與座標 | 依病灶、加速率、掃描器分層的 coverage；模型內模擬用 SBC |

Ground truth 不參與一般個案區間計算；只在評估 error、實際 coverage 或校準時需要。如果輸入是帶權重的 importance samples，不能忽略權重做一般分位數；NumPy 的 weighted quantile 有算法與版本限制，應另設分支。[NumPy weighted quantile](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html)

建議接線流程：

1. 固定病例、量測、mask、校正與模型參數，明確記錄 posterior 假設。MRI 複數樣本先選定要統計 magnitude、實部／虛部或圓形 phase。
2. 重複啟動完整重建軌跡，變更初始噪聲與需要的隨機流；保留每次的最終數值樣本與獨立檔名。不要把一條 diffusion 軌跡的中間 timestep 當成同一 posterior 的多筆樣本。
3. 使用共同座標與共同反正規化；不要逐樣本獨立 min–max normalization、取整或只保留 PNG，以免抹去或製造區間寬度。
4. 沿樣本軸計算 ETI；針對 ROI 的 scalar 分布檢查偏態、多峰與尾部分位數穩定度，必要時另外計算 HDI。
5. 輸出區間圖、ROI 表、代表樣本、樣本數與抽樣設定；進行抽樣預算敏感度及獨立 reference 的 coverage 驗證。

### 3.1 最小統計示意

以下是需自行接到 posterior 後端的統計片段，**不產生或驗證 posterior samples**。輸入為已採共同尺度的實數樣本 `samples[K, H, W]` 或 `samples[K, D, H, W]`；`roi` 是對齊影像的固定 boolean mask。

```python
import numpy as np

def credible_summary(samples, roi, alpha=0.05):
    x = np.asarray(samples)
    r = np.asarray(roi)
    if x.ndim < 3 or x.shape[0] < 2:
        raise ValueError("需要 [sample, spatial...] 與至少兩個樣本")
    if x.dtype.kind not in "fiu" or not np.isfinite(x).all():
        raise ValueError("樣本必須是有限實數；複數需先定義量化變數")
    if r.dtype.kind != "b" or r.shape != x.shape[1:] or not r.any():
        raise ValueError("ROI 必須是同空間形狀、非空的 boolean mask")
    if not 0 < alpha < 1:
        raise ValueError("alpha 必須介於 0 與 1")
    levels = [alpha / 2, 0.5, 1 - alpha / 2]
    lower, median, upper = np.quantile(
        x, levels, axis=0, method="linear"
    )
    roi_draws = x[:, r].mean(axis=1, dtype=np.float64)
    roi_interval = np.quantile(roi_draws, levels, method="linear")
    return lower, median, upper, upper - lower, roi_interval
```

「至少兩個樣本」只是防止輸入退化的檢查，遠不足以證明 95% 尾部分位數可靠。若採 ArviZ 0.22.0，可對一維 `roi_draws` 呼叫 `az.hdi(roi_draws, hdi_prob=0.95)`；影像應明確建立 `chain`／`draw`／空間維度，避免將高度誤認成抽樣軸。此處引用版本化 API，並非建議忽略後續修補或宣稱 0.22.0 是最新版。[ArviZ hdi 文件](https://python.arviz.org/en/v0.22.0/api/generated/arviz.hdi.html)

## 4. 實作限制與驗證要求

| 限制 | 對解釋的影響與處理 |
| --- | --- |
| Posterior approximation／先驗錯置 | 偏離資料域、guidance 過強、hard data projection、有限去噪步數都可能改變抽樣分布；先驗或 likelihood 不準時，窄區間仍可一致地偏離真值。需保留假設並做資料域內外驗證。 |
| 有限樣本與尾部不穩 | 95% 區間的兩端落在尾部；例如 40 個獨立樣本，每側 2.5% 尾部的期望樣本數只有 1。此為算術示例，不是建議抽樣門檻。比較不同抽樣預算的端點變化，並報告 quantile MCSE／tail ESS 等診斷。 |
| 相關性／模式未探索 | 有 MCMC 鏈時需檢查 chain mixing、ESS、$\hat R$；對多次 diffusion restart，應檢查重複 seed、共享噪聲與結果多樣性。不要直接把非平穩的 diffusion timestep 序列套入 MCMC 診斷並據此宣稱收斂。 |
| Gaussian 區間可能失真 | $\bar x_i\pm1.96s_i$ 只適合近似 Gaussian 的邊際 posterior；magnitude 的非負性、偏態或多峰時優先使用分位數或適當 HPD 集合。 |
| 把 MCSE 當成影像區間 | $s_i/\sqrt{K_{\mathrm{eff}}}$ 是 posterior mean 估計的 Monte Carlo 誤差尺度，不是未知像素本身的 posterior spread。增加樣本會改善區間端點精度，不應讓原本的 posterior 寬度按此比例消失。 |
| Pointwise 不等於 simultaneous | 每個像素各有 95% posterior mass，不代表整張影像同時落在上下界內的機率是 95%。全圖 simultaneous credible band 要另外設計聯合事件與閾值；不能把所有 pointwise 區間直接改名。 |
| 空間／下游統計 | 模式間病灶位移可能使像素區間很寬，也可能使中位數圖模糊；ROI 若由有偏的重建先選定，結果也會受此選擇影響。需標明 ROI 定義，必要時分析完整結構樣本。 |
| 計算與儲存 | 需支付多次完整重建成本；exact quantile 需保留或重新讀取各位置的全部樣本。可沿空間分塊，但不能把不同樣本分批算出的分位數直接平均。近似 streaming quantile 需另外量化誤差。 |

上述 MCSE、ESS 與尾部分位數要求可參考 [Stan posterior analysis](https://mc-stan.org/docs/2_38/reference-manual/analysis.html) 及 [posterior 套件的 quantile ESS 文件](https://mc-stan.org/posterior/reference/ess_quantile.html)。這些診斷處理抽樣誤差，不能單獨證明學到的影像 prior 正確。

**名目 95% 不等於實際 coverage 95%。** 對獨立 reference $x^\star_n$，可以報告指定 ROI 指標的 empirical coverage：

$$
\widehat{\mathrm{coverage}}=\frac1N\sum_{n=1}^N
\mathbf 1\{g(x_n^\star)\in[L_n,U_n]\}.
$$

應同時報告區間寬度，並依病灶、掃描器、加速率等分層。大量背景像素的平均 coverage 不能取代病灶區域結果；同一病患的像素與切片不是獨立病患，coverage 估計誤差宜以病患為單位處理。若從指定 prior／likelihood 模擬資料做 SBC，檢查的是該模型內的 posterior sampling 正確性，仍需真實資料驗證模型適切性。[Stan SBC 官方文件](https://mc-stan.org/docs/stan-users-guide/simulation-based-calibration.html)

**Conformal prediction 是另一個校準流程。** 它可以使用模型區間或分數，加上獨立校準資料，在交換性等條件下取得 marginal coverage 保證；把結果稱為 conformal prediction interval 時，應說明校準資料與保證的事件。對單一病例的條件 posterior credible interval 取分位數，本身並未完成 conformal calibration，也不取得相同保證。[Angelopoulos 與 Bates 的 conformal 教程，第 1、2.4 節](https://arxiv.org/html/2107.07511v6)

## 5. 開源來源與可直接使用的範圍

| 元件 | 官方來源與程式授權 | 已提供什麼／仍需自行實作什麼 |
| --- | --- | --- |
| score-MRI：MRI 抽樣後端 | [作者 repository](https://github.com/hyungjin-chung/score-MRI)、[根目錄 LICENSE](https://github.com/hyungjin-chung/score-MRI/blob/main/LICENSE)：Apache-2.0 | 提供 score-based MRI 重建與多種 inference 腳本。需自行接出固定量測的多次最終樣本、seed 管理、ETI／HDI、ROI 與校準報告；不能視為已有完整 credible interval 介面。 |
| NumPy：ETI 統計層 | [quantile 實作](https://github.com/numpy/numpy/blob/main/numpy/lib/_function_base_impl.py)、[LICENSE](https://github.com/numpy/numpy/blob/main/LICENSE.txt)：BSD-3-Clause | 可直接沿指定軸計算分位數；不理解 MRI、diffusion、posterior 或 coverage。上述統計片段屬這一層。 |
| ArviZ：HDI 與抽樣診斷 | [0.22.0 hdi／_hdi 實作](https://github.com/arviz-devs/arviz/blob/v0.22.0/arviz/stats/stats.py)、[該版本 LICENSE](https://github.com/arviz-devs/arviz/blob/v0.22.0/LICENSE)：Apache-2.0 | 可對已存在的樣本做 HDI；需處理樣本維度與統計目標。其 HDI、ESS 等工具不會把任意生成 ensemble 轉成有效 posterior。 |

score-MRI 的 [`sampling.get_pc_fouriercs_fast`](https://github.com/hyungjin-chung/score-MRI/blob/main/sampling.py) 包含隨機抽樣與 Fourier data-fidelity 步驟；[`inference_real.py`](https://github.com/hyungjin-chung/score-MRI/blob/main/inference_real.py) 呼叫一次 sampler，並以病例檔名保存一張 `.npy` 重建。直接重跑可能覆寫結果，也可能在 retrospective 模式重新建立 mask；整合時應固定原始量測並自行保存完整 ensemble。

程式根目錄授權也不代表每個內嵌上游檔案都只有同一條款：score-MRI 的 [`fastmri_utils.py`](https://github.com/hyungjin-chung/score-MRI/blob/main/fastmri_utils.py) 明寫 Facebook MIT notice。再散布應保留個別來源的版權、授權與變更聲明。

**權重與資料分開判斷：** score-MRI README／安裝腳本連到 Dropbox `.pth`；本次查閱這些來源未找到該下載權重明確的獨立授權說明，不能推定一併取得 Apache-2.0 再散布權。[官方 README](https://github.com/hyungjin-chung/score-MRI)、[install.sh](https://github.com/hyungjin-chung/score-MRI/blob/main/install.sh)

fastMRI 資料另受 NYU Data Sharing Agreement 約束，包括內部研究／教育用途、存取與再散布限制，且明定不得用於診斷或病患照護。這些資料條款不由 NumPy、ArviZ 或重建程式的開源授權取代。[fastMRI 官方資料條款](https://fastmri.med.nyu.edu/)

## 6. 開源來源的安全性

| 查核面向 | 有依據的發現 | 採用前的具體處理 |
| --- | --- | --- |
| 權重取得 | score-MRI [`install.sh`](https://github.com/hyungjin-chung/score-MRI/blob/main/install.sh) 直接以 `wget` 下載 Dropbox `.pth`，該腳本沒有 checksum 驗證。 | 先確認權重來源與授權，取得可信發布者的 hash／簽章並比對；自行算 hash 可記錄後續一致性，不能單獨證明來源可信。 |
| Checkpoint 反序列化 | [`utils.restore_checkpoint`](https://github.com/hyungjin-chung/score-MRI/blob/main/utils.py) 呼叫 `torch.load`，未明設 `weights_only`。實際預設依 PyTorch 版本不同；官方說明 2.6 起預設改為 `True`，仍存在安全限制。[PyTorch serialization](https://docs.pytorch.org/docs/main/notes/serialization.html) | 使用受維護且已修補的版本、明確設定受限載入，僅載入可信資產。若不相容，先審核格式；不要為了讓權重可讀而對未知來源關閉限制。 |
| 已知 PyTorch 弱點 | [CVE-2026-24747／GHSA-63cw-57p8-fm3p](https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p) 指出惡意 checkpoint 即使用 `weights_only=True` 也可能導致程式執行；公告列受影響版 `<=2.9.1`，此漏洞修補版 `>=2.10.0`。 | 針對實際環境版本檢查公告；該修補下限只表示修正這一漏洞，不是所有後續漏洞均不存在。此處沒有證據指稱 score-MRI 提供的權重本身惡意。 |
| 依賴與重現 | score-MRI [`requirements.txt`](https://github.com/hyungjin-chung/score-MRI/blob/main/requirements.txt) 列出未鎖版本的套件；安裝腳本使用 Python 3.8／CUDA 10.2 設定。 | 先完成相容性移植與依賴盤點，再鎖定通過測試且已修補的環境；不要把原始舊環境設定當成安全建議。 |
| 樣本檔案解析 | NumPy [`load`](https://numpy.org/doc/stable/reference/generated/numpy.load.html) 對 pickle 有明確警告；數值分位數無需 object pickle。 | 讀 `.npy` 時明設 `allow_pickle=False`，限制 dtype、維度、檔案大小、樣本數及可用記憶體；同時避免過大陣列造成資源耗盡。 |
| 統計層暴露面 | NumPy 指出不應直接讓不可信使用者任意執行 NumPy／Python，亦建議對複雜外來資料使用隔離。[NumPy security](https://numpy.org/doc/stable/reference/security.html) | 用固定 API 接受數值樣本；不要接受任意 Python 的 ROI 函數字串或 notebook 上傳後直接執行。ArviZ 使用記憶體內樣本即可，不必執行與區間無關的下載範例。 |
| 醫療資料與結果保存 | 區間圖、完整樣本及 ROI 仍可能保留病患影像資訊；fastMRI 條款要求資料安全與保密。[官方 DUA](https://fastmri.med.nyu.edu/) | 在受控儲存處理，限制檔案權限與結果匯出；分享示範時改用有權公開的合成資料。 |

**採用判斷：** 先以已有合法來源的 posterior samples 接 NumPy ETI，是本項最少依賴的落地方式；需要偏態／多峰分析時再接 ArviZ。score-MRI 可作為研究後端，但需完成權重、依賴與抽樣有效性的查核。授權明確、程式可讀、區間算得出來與臨床上可靠，是需要分別驗證的四件事。

