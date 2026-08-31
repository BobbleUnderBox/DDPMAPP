# 醫療影像分割與異常定位：T4 可推論的 Diffusion Models

更新日期：2026-08-31

## 篩選條件

- 模型必須在分割、重建或異常定位的任務推論中實際執行 diffusion／reverse diffusion；只用 Stable Diffusion VAE、只拿 diffusion 產生訓練資料，或只載入 diffusion backbone initialization 均不算。
- 用途為器官、腫瘤、病灶分割，或疾病異常偵測與病灶定位。
- 有作者或論文官方維護的公開程式碼。
- 有任務訓練完成的 checkpoint，可直接下載；若只需低門檻的學術／非營利申請或聯絡作者，也可列為備選。
- NVIDIA T4 16 GB 至少可合理預期以 batch 1、AMP、2D slice、crop 或其他保守設定推論。
- 輸出適合展示 segmentation mask、anomaly map、pseudo-healthy reconstruction、重建差異或隨機樣本間的不確定性。

## 結論

找到 **六款具有官方任務 checkpoint、可直接下載**的 diffusion models：DermoSegDiff、cDAL、CCDM、THOR、AutoDDPM 與 DiffAtlas。因此不必把「寄信申請權重」當成主清單的必要補位；需要更多候選時，AnoDDPM 可依作者指示聯絡索取。

這裡的「T4 可執行」是依官方最低顯存說明、輸入尺寸、模型設定與 sampling steps 所作的部署前判斷，不代表已在本專案的 T4 上完成 benchmark。首次部署仍應記錄 peak VRAM、單張／單 volume 延遲及 CUDA 相容性。

## 推薦模型總覽

| 模型 | 任務與輸入 | Diffusion 在推論中的角色 | 權重取得 | T4 16 GB 判斷 | 最適合展示 |
| --- | --- | --- | --- | --- | --- |
| **DermoSegDiff** | 2D dermoscopy 皮膚病灶分割 | 以影像條件逐步去噪 segmentation mask | ISIC 2018、PH2 權重直接下載 | **高**：官方要求至少 12 GB；batch 1 | 多次採樣的 mask、邊界分歧與不確定性 |
| **cDAL** | 2D 胸腔 X-ray 肺野、MoNuSeg 細胞核；3D hippocampus | 少步數 conditional diffusion 直接生成 mask | 三項任務權重皆公開於 Hugging Face | **中高**：2D 僅 2–4 steps；batch 1 應可，但官方程式需整理 | mask、不同 folds／隨機 latent 的差異 |
| **CCDM** | 2D LIDC 肺結節的多標註分割 | categorical diffusion 生成多個合理 label maps | LIDCv1 checkpoint 與 evaluation config 直接下載 | **高**：128×256、base channels 32；batch 1 | 多位醫師可能邊界、像素 agreement／entropy |
| **THOR** | 2D 腦 MRI stroke 異常與兒童腕部 X-ray 異常定位 | DDPM 產生 pseudo-healthy reconstruction，時間調和 anomaly maps | 腦 MRI 與腕部 X-ray 各有 Gaussian／Simplex 權重 | **高（顯存）／低（速度）**：128×128、batch 1、1000 steps | 原圖、重建、residual heatmap、anomaly mask |
| **AutoDDPM** | 2D T1w 腦 MRI 異常偵測與病灶定位 | diffusion 重建、mask、stitch 與 re-sample，產生 pseudo-healthy image | 官方 T1w brain checkpoint 直接下載 | **高（顯存）／低（速度）**：128×128、batch 1、1000 steps | 初始 likelihood、重建修補流程、最終 residual heatmap |
| **DiffAtlas** | 3D CT/MRI whole-heart 多結構分割 | 影像與多類 mask 共同進行 3D diffusion | 多個 MMWHS／TotalSegmentator 權重公開於 Hugging Face | **中**：64³、6 channels、batch 1 應可；300 steps 偏慢 | 五類心臟結構、3D mask、逐步去噪 |

## 1. DermoSegDiff

### 用途與 diffusion 證據

DermoSegDiff 是針對 dermoscopic image 設計的 diffusion segmentation model。輸入皮膚影像後，模型從 noisy mask 反覆去噪，得到 lesion segmentation；這不是把 diffusion 當作資料增強，而是實際以 reverse diffusion 產生任務輸出。

### 官方資源與權重

- [官方程式碼](https://github.com/xmindflow/DermoSegDiff)，MIT。
- [論文](https://arxiv.org/abs/2308.02959)。
- [ISIC 2018：DermoSegDiff-A 權重](https://uniregensburg-my.sharepoint.com/:f:/g/personal/say26747_ads_uni-regensburg_de/EhsfBqr1Z-lCr6KaOkRM3EgBIVTv8ew2rEvMWpFFOPOi1w?e=ifo9jF)。
- [PH2：DermoSegDiff-B 權重](https://uniregensburg-my.sharepoint.com/:f:/g/personal/say26747_ads_uni-regensburg_de/EoCkyNc5yeRFtD-KTFbF0gcB8lbjMLY6t1D7tMYq7yTkfw?e=tfGHee)。
- 官方測試入口為 `python src/testing.py -c <config>`；載入任意 checkpoint 時，要在 config 將 `testing.model_weigths.overload` 設為 `true` 並填入路徑。原始欄位確實拼成 `weigths`。

### T4 與 Demo 判斷

官方 README 明確要求 12 GB 以上 GPU；T4 有 16 GB，並可把 batch 降為 1。預設 250 個 diffusion steps，加上多次 ensemble 會使現場推論變慢，Demo 可先只取一個樣本，再以背景工作補齊多樣本。

最有價值的畫面是原圖、單次 lesion mask、五次採樣平均 mask，以及邊界 disagreement／entropy。這能直接解釋 diffusion 的隨機性，而不是只顯示單一硬 mask。

## 2. cDAL

### 用途與 diffusion 證據

cDAL 以 conditional diffusion、time-dependent discriminator、spatial attention 及 random latent embedding 生成醫療 segmentation mask。官方提供三組任務權重：MoNuSeg 細胞核、胸腔 X-ray 肺野，以及 3D hippocampus。

### 官方資源與權重

- [官方程式碼](https://github.com/Hejrati/cDAL)。
- [論文](https://arxiv.org/abs/2502.06997)。
- [Hugging Face checkpoint repository](https://huggingface.co/Hejrati/cDAL/tree/main)：包含 `monu.pth`、三個 lung folds 與三個 hippocampus folds。
- 程式碼衍生自 NVIDIA Denoising Diffusion GAN，使用 **NVIDIA Source Code License-NC**，僅限非商業研究或評估；這符合本專案目前接受的非營利用途，但不適合直接商用。

### T4 與 Demo 判斷

2D MoNuSeg 與 lung 設定只有 4／2 個 sampling timesteps，且 checkpoint 約 35–167 MB，因此 batch 1 在 T4 上很有希望。3D hippocampus 也只有 2 steps，但仍應先實測 peak VRAM。

官方研究碼不是即插即用套件：sampling script 有硬編碼資料路徑，並預設 DDP/NCCL；參數檔命名與讀取邏輯也需要整理。部署前應改為單卡 inference entry point。Demo 可呈現原圖、mask，以及三 folds 或不同 latent samples 的 disagreement。

## 3. CCDM

### 用途與 diffusion 證據

CCDM（Conditional Categorical Diffusion Model）對離散 segmentation labels 做 categorical diffusion。官方 LIDC 模型會對同一張 CT slice 生成多個肺結節 masks，用來表示多位標註者之間本來就存在的 aleatoric uncertainty。

### 官方資源與權重

- [官方程式碼](https://github.com/LarsDoorenbos/ccdm-stochastic-segmentation)，MIT。
- [ICCV 2023 論文](https://arxiv.org/abs/2303.08888)。
- [LIDCv1 checkpoint 與 evaluation 參數](https://drive.google.com/drive/folders/1pcXOZpQlSLJOOhId6yZa_3vYS-L0nA4S)。
- 官方推論入口為 `python ddpm_eval.py params_eval.yml`。

### T4 與 Demo 判斷

官方 evaluation config 使用 128×256、base channels 32、batch 2、250 timesteps；將 batch 改成 1，T4 16 GB 應有充足顯存。舊版環境指定 Python 3.10 與 Torch 1.7.0，實際部署宜固定 container，或先驗證升級 PyTorch 後的相容性。

這款最適合做「同一影像有多個合理答案」的可解釋 Demo：顯示 8 個採樣 masks、majority mask、像素 agreement map，以及結節邊界 entropy。

## 4. THOR

### 用途與 diffusion 證據

THOR（Temporal Harmonization for Optimal Restoration）在 DDPM denoising 過程中以時間序列 anomaly maps 做 implicit guidance，將病灶影像恢復為 pseudo-healthy 影像，再由輸入與重建差異定位異常。官方流程涵蓋腦 MRI stroke 與兒童腕部 X-ray 的骨折、異物、骨異常等項目。

### 官方資源與權重

- [官方程式碼](https://github.com/ci-ber/THOR_DDPM)。
- [論文](https://arxiv.org/abs/2403.08464)。
- 腦 MRI：[Gaussian checkpoint](https://www.dropbox.com/scl/fi/55cl3821vw1jp3jim2da2/brain_Gaussian.pt?dl=1&rlkey=pz99o0x3g6vi3siwtvfpb0oyo)、[Simplex checkpoint](https://www.dropbox.com/scl/fi/d8olm81iynd4lbsjt0fgm/brain_Simplex.pt?dl=1&rlkey=onmyjogb3ej7uibs7r4poy4w8)。
- 腕部 X-ray：[Gaussian checkpoint](https://www.dropbox.com/scl/fi/dd0zzzjcimmw3egcfvhvu/wxr_Gaussian.pt?dl=1&rlkey=iovq4hx9zcmlogszhg19d9ou2)、[Simplex checkpoint](https://www.dropbox.com/scl/fi/0aeiawcih2io4imdo169f/wxr_Simplex.pt?dl=1&rlkey=grn8t62nsn0ojo6rc378gemvt)。
- 執行入口為 `python core/Main.py --config_path ./projects/thor/configs/brain/thor.yaml`，並需把 config 的 task 改成 test、填入 weights。

### T4 與 Demo 判斷

官方 brain／wrist config 均為 2D 128×128、downstream batch 1，模型 channels 為 128/256/256；T4 顯存應足夠。預設 1000 inference steps 才是主要瓶頸，因此現場展示宜只重跑單張 slice，完整病例則預先快取。

需要注意兩個工程問題：repository 未附明確 LICENSE；另有一個檔名尾端帶空白，會讓 Windows checkout 失敗。Linux／WSL 可作為較穩定的部署環境，對外再散布程式或權重前應先向作者確認條款。

## 5. AutoDDPM

### 用途與 diffusion 證據

AutoDDPM（Automatic Denoising Diffusion Probabilistic Model）先以 diffusion reconstruction 取得初始 anomaly likelihood，再自動建立疑似異常 mask，將正常組織與待修補區域 stitch 後重新加噪、取樣，產生保留正常結構的 pseudo-healthy image。最後由原始影像與重建影像的差異定位病灶，因此 reverse diffusion 是任務推論的核心，不只是資料增強或 backbone initialization。

### 官方資源與權重

- [官方程式碼](https://github.com/ci-ber/autoDDPM)，GPL-3.0。
- [論文](https://arxiv.org/abs/2305.19643)。
- [官方 T1w brain checkpoint](https://www.dropbox.com/scl/fi/7vem1s1ocx51duecekl06/latest_model.pt.zip?rlkey=wl5trcby4rozu4p4cgd940p53&dl=1)，壓縮檔約 191.5 MiB。
- [IXI 正常腦部 MRI](https://brain-development.org/ixi-dataset/)；官方 repository 也列出 FastMRI 與 ATLAS，並在 `data/$DATASET/splits` 提供對應切分檔。
- 執行入口為 `python core/Main.py --config_path ./projects/autoddpm/autoddpm.yaml`；把 checkpoint 放入 config 指定位置即可跳過 training。

官方 README 將公開權重描述為可用於 mid-axial T1w brain scans，預設 config 與資料切分則指向 IXI-T1 工作流程。不過 checkpoint 檔名只有泛稱的 `latest_model.pt`，沒有獨立 model card 或 hash 精確聲明該檔使用的每一筆訓練資料；其權重可稽核性比 DermoSegDiff、CCDM 等模型弱。

### T4 與 Demo 判斷

官方預設為 2D、單 channel、128×128，模型約 18.5M parameters，downstream inference 可設 batch 1；T4 16 GB 的顯存應足夠。主要限制是 DDPM 的多步採樣而非 VRAM，完整 volume 不適合現場全部重算。建議預先快取完整病例，只讓使用者對選定 slice 重跑 reconstruction。

最適合依序呈現原始影像、初始 reconstruction／likelihood map、threshold 後的 anomaly mask、stitch 與 re-sample 結果、pseudo-healthy image，以及最終 residual heatmap。threshold 對結果影響很大；官方 README 也提醒不同醫院、掃描器或資料分布必須重新校正 threshold。

## 6. DiffAtlas

### 用途與 diffusion 證據

DiffAtlas 是 3D joint image-and-label diffusion model。它在每個 denoising step 以 noisy image 引導 noisy multi-class masks，最後輸出 whole-heart segmentation，並可在 CT 與 MRI 間做跨模態 atlas transfer。

### 官方資源與權重

- [官方程式碼](https://github.com/HINTLab/DiffAtlas)，Apache-2.0。
- [論文](https://arxiv.org/abs/2503.06748)。
- [Hugging Face 預訓練權重](https://huggingface.co/YuheLiuu/DiffAtlas_Pretrained_model)：提供 MMWHS CT、MMWHS MRI 及 TotalSegmentator 不同訓練／測試設定的 `.pt`。
- 官方 repository 另附各 checkpoint 的 testing scripts。

### T4 與 Demo 判斷

官方 testing scripts 使用 64×64×64、6 channels、3D U-Net、batch 1 與 300 timesteps。依輸入尺寸判斷，T4 16 GB 應可執行單一 crop，但這是六款中最需要實機驗證的一款；若 OOM，需嘗試 autocast／FP16，且先確認模型的 normalization layers 在 half precision 下穩定。

Demo 可用五種顏色顯示心臟結構，並以 axial／coronal／sagittal 與 3D surface 同步呈現。300-step 3D sampling 不適合每次互動重跑，應預先快取完整結果，只對少量 crop 展示 denoising 過程。

## 建議實作順序

1. **DermoSegDiff**：官方直接給出 12 GB 最低需求，2D 輸入與皮膚病灶 overlay 最容易先做成穩定 Demo。
2. **CCDM**：模型小、MIT、公開 LIDC checkpoint，且多重 masks 能直接呈現不確定性。
3. **cDAL lung**：只有 2 個 sampling steps，理論上最快，但要先清理硬編碼與 DDP。
4. **THOR brain**：病灶差異圖最符合 diffusion anomaly localization 主題，但 1000 steps 需要快取。
5. **AutoDDPM**：mask、stitch、re-sample 到 pseudo-healthy image 的流程最完整，但 checkpoint provenance 較弱且 1000 steps 需要快取。
6. **DiffAtlas**：3D 多結構展示效果佳，卻是顯存、延遲與前處理風險最高者。

## 申請型與次要備選

| 候選 | 權重狀態 | 未列入主要五款的原因 |
| --- | --- | --- |
| [AnoDDPM](https://github.com/Julian-Wyatt/AnoDDPM) | README 指示直接聯絡作者索取 checkpoint；程式為 MIT | 申請方式簡單，但官方沒有公開資格、處理時間或必然核准條件，因此列為申請型備選。它與 AutoDDPM 是不同模型。 |
| [LDSeg](https://github.com/FahimZaman/LDSeg) | 2D GlaS 與 3D knee checkpoints 直接包含在 repository | 15-step DDIM、模型小且適合 T4，但 repository 沒有 LICENSE；若作者補充研究使用許可，可升為主候選。 |
| [BerDiff](https://github.com/takimailto/BerDiff) | 官方 Google Drive 有 LIDC checkpoint | 程式明列 Linux 舊環境，repository 沒有 LICENSE，且推論文件不如 CCDM 完整。 |

## 已排除的常見候選

| 候選 | 排除原因 |
| --- | --- |
| [MedSegDiff](https://github.com/ImprintLab/MedSegDiff)／MedSegDiff-V2 | 官方 repository 沒有正式、任務訓練完成的 checkpoint，仍需自行訓練。 |
| [SDSeg](https://github.com/lin-tianyu/Stable-Diffusion-Seg) | 公開的是 Stable Diffusion autoencoder／conditioning／LSUN 初始化權重，不是醫療分割任務 checkpoint。 |
| [SegDT](https://github.com/Bekhouche/SegDT) | repository 幾乎只有 README，尚無足以直接推論的完整程式與權重。 |
| [GMS](https://github.com/King-HAW/GMS) | 有任務 checkpoint，但推論核心是 frozen SD VAE 加 latent mapping CNN，沒有執行 reverse diffusion；不符合新增必要條件。 |
| [LeFusion](https://github.com/HINTLab/LeFusion)／Siamese-Diffusion | diffusion 用來生成合成病灶與 masks 供其他模型訓練，不是直接分割病人輸入的任務推論模型。 |
| [BTD](https://github.com/freddiemg/btd--unsupervised-detection-of-medical-deepfakes) | 有 diffusion 權重與 anomaly map，但目標是偵測被竄改／生成的醫療影像，不是疾病異常定位。 |
| [IterMask3D](https://github.com/ZiyunLiang/IterMask3D) | 有完整 3D inference 程式，但 repository 未提供 pretrained checkpoint。 |

## 授權與使用限制

- 「程式碼可讀」、「程式碼有開源授權」及「checkpoint 可再散布」是三件不同的事。主清單只保證官方有下載入口，不代表權重允許商用或重新發布。
- DermoSegDiff 與 CCDM 程式為 MIT；DiffAtlas 為 Apache-2.0；AutoDDPM 為 GPL-3.0；cDAL 明確限制非商業研究／評估；THOR 未附明確程式授權。
- 即使本專案是非營利研究，公開部署前仍應保存下載頁、LICENSE、checkpoint hash 與取得日期；若模型頁沒有獨立權重條款，應向作者確認。
- 所有模型只適合研究、教學或臨床決策支援原型，不能宣稱已通過醫療器材驗證，也不能把示範結果當成診斷。

## 研究紀錄

- [Undermind：Diffusion-only 醫療分割與異常定位模型](https://app.undermind.ai/projects/1f44d5f3-0d70-4a0c-95eb-d9b44e684093?path=/Diffusion-only%20%E9%86%AB%E7%99%82%E5%88%86%E5%89%B2%E8%88%87%E7%95%B0%E5%B8%B8%E5%AE%9A%E4%BD%8D%E6%A8%A1%E5%9E%8B)
- Hugging Face 上的 cDAL 與 DiffAtlas repository 已逐一核對檔名與任務 checkpoint；checkpoint 是否適用商業用途仍以各作者條款為準。
