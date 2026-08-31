# 醫療影像分割與異常定位：可直接推論的開源模型整理

更新日期：2026-08-31

本文件延伸自[醫療影像中的 Diffusion Model 應用](./df_app_on_mechanism.md)，整理適合製作可解釋性 Demo 的開源模型。篩選範圍包含：

1. 器官、腫瘤與病灶分割。
2. 疾病異常偵測與病灶定位。

## 篩選條件

- 有可取得的程式碼。
- 有可直接執行 inference 的預訓練權重，不需要自行訓練。
- 能找到模型所使用的訓練資料或其公開資料來源。
- NVIDIA T4 16 GB 至少能以 batch 1、AMP 或 sliding window 等保守設定執行。
- 模型輸出適合呈現 mask、bounding box、機率圖、重建差異或不確定性，而不是只有無法驗證的分類結果。

## 結論

若進一步限定「必須是 Diffusion Model」，目前無法找到五款同時具備公開權重、可追溯訓練資料及 T4 可執行性的成熟模型。因此，本清單以「應用任務相符」為主要條件，不限制模型架構；其中保留 AutoDDPM，作為真正以 diffusion 進行異常偵測與病灶定位的選項。

以下五款都不需要重新訓練。訓練資料主要用於確認模型來源、挑選展示案例及驗證結果，不必為了 inference 下載完整訓練集。

## 推薦模型總覽

| 模型 | 主題與輸入 | 預訓練權重及訓練資料 | T4 16 GB 判斷 | 適合的可解釋性展示 |
| --- | --- | --- | --- | --- |
| **SAM-Med3D Turbo** | 互動式 3D CT/MRI 器官、腫瘤與病灶分割 | [權重](https://huggingface.co/blueyo0/SAM-Med3D)、[SA-Med3D-140K](https://huggingface.co/datasets/blueyo0/SA-Med3D-140K) | 高把握可執行；建議 batch 1、128³ crop | 正負提示點、3D mask、提示點擾動後的邊界變化 |
| **nnU-Net v1 Task001 BrainTumour** | 四模態腦部 MRI 腫瘤自動分割 | [權重](https://zenodo.org/records/4003545)、[MSD Task01](https://registry.opendata.aws/msd/) | 官方說明 inference 約需 4 GB VRAM | 三種腫瘤區域、五 folds 分歧、voxel entropy |
| **MONAI Pancreas CT DiNTS** | CT 胰臟及胰臟腫瘤分割 | [Bundle 與權重](https://huggingface.co/MONAI/pancreas_ct_dints_segmentation)、[MSD Task07](https://registry.opendata.aws/msd/) | 保守設定可執行；AMP、96³ ROI、`sw_batch_size=1` | 胰臟／腫瘤 mask、softmax、邊界不確定度與腫瘤體積 |
| **MONAI Lung Nodule CT Detection** | CT 肺結節 3D 偵測與定位 | [Bundle 與權重](https://huggingface.co/MONAI/lung_nodule_ct_detection)、[LUNA16](https://luna16.grand-challenge.org/Data/) | 保守設定可執行；AMP 與 sliding window | 三視圖 3D boxes、信心分數及 threshold slider |
| **AutoDDPM** | T1w 腦部 MRI diffusion 異常偵測 | [程式與設定](https://github.com/ci-ber/autoDDPM)、[權重](https://www.dropbox.com/scl/fi/7vem1s1ocx51duecekl06/latest_model.pt.zip?rlkey=wl5trcby4rozu4p4cgd940p53&dl=1)、[IXI](https://brain-development.org/ixi-dataset/) | 顯存可執行，但 diffusion 採樣慢；完整 volume 建議預先快取 | 原圖、pseudo-healthy 重建、residual heatmap 與 anomaly mask |

## 1. SAM-Med3D Turbo

### 用途

SAM-Med3D 是 promptable 3D 醫療影像分割模型，可處理多種 CT、MRI 解剖結構與病灶。使用者提供一個或多個正／負提示點，模型輸出對應的 3D segmentation mask。

### 公開資源

- [官方程式碼](https://github.com/uni-medical/SAM-Med3D)，Apache-2.0。
- [SAM-Med3D Turbo checkpoint](https://huggingface.co/blueyo0/SAM-Med3D/blob/main/sam_med3d_turbo.pth)，約 402 MB。
- [SA-Med3D-140K](https://huggingface.co/datasets/blueyo0/SA-Med3D-140K)，包含 21,729 個 3D 影像及 143,518 個 masks，總容量約 1.09 TB。

### T4 執行判斷

以 batch 1、128³ crop 執行時，T4 16 GB 有很高機率足夠。這不是官方 T4 benchmark；一份使用 SAM-Med3D 的[應用研究](https://www.nature.com/articles/s43856-026-01735-y)曾回報約 1.45 GB 的推論顯存用量，可作為間接參考。

### Demo 設計

- 使用者在 CT/MRI 切片上點選目標。
- 同步顯示 axial、coronal、sagittal 三視圖及 3D mask。
- 增加正提示點或負提示點，觀察 mask 如何修正。
- 對提示點加入小幅位移，顯示 segmentation stability。

### 注意事項

官方單一影像範例會從 ground truth 產生提示點。實際互動 Demo 必須改成滑鼠點擊輸入，否則會不合理地依賴答案本身。

## 2. nnU-Net v1 Task001 BrainTumour

### 用途

這是針對 Medical Segmentation Decathlon Task01 BrainTumour 訓練的自動分割模型。輸入包含 FLAIR、T1、T1-Gd/T1ce 與 T2 MRI，輸出可整理為 enhancing tumor、tumor core 及 whole tumor。

### 公開資源

- [nnU-Net v1 程式碼](https://github.com/MIC-DKFZ/nnUNet/tree/nnunetv1)，Apache-2.0。
- [官方預訓練模型封存](https://zenodo.org/records/4003545)，下載 `Task001_BrainTumour.zip`，約 1.9 GB。
- [Medical Segmentation Decathlon 公開資料](https://registry.opendata.aws/msd/)。Task01 共 750 個 4D volumes，其中 484 個為訓練案例、266 個為測試案例。
- MSD 的資料描述與授權可參考[官方資料論文](https://www.nature.com/articles/s41467-022-30695-9)。

### T4 執行判斷

[nnU-Net v1 官方說明](https://raw.githubusercontent.com/MIC-DKFZ/nnUNet/nnunetv1/readme.md)指出 inference 約需 4 GB VRAM，因此 T4 16 GB 足夠。這是五款模型中顯存依據最明確的一款。

### Demo 設計

- 顯示三種腫瘤區域的彩色 overlay 與體積。
- 不只執行最後 ensemble，也保留五個 folds 的 softmax。
- 計算 folds 間變異或 entropy，將模型不確定區域疊在腫瘤邊界上。
- 顯示 threshold 調整如何影響腫瘤體積與 connected components。

### 注意事項

這是 nnU-Net v1 的舊版模型，建議固定舊版 Python/PyTorch/nnU-Net 環境或包成獨立 container，避免直接套用 nnU-Net v2 的指令及資料結構。

## 3. MONAI Pancreas CT DiNTS Segmentation

### 用途

DiNTS 是 3D neural architecture search 產生的分割網路，用於 portal venous phase CT 的胰臟與胰臟腫瘤分割。輸出有 background、pancreas 與 pancreatic tumor 三個 channels。

### 公開資源

- [Hugging Face MONAI Bundle](https://huggingface.co/MONAI/pancreas_ct_dints_segmentation)，Apache-2.0。
- [官方 Bundle 說明](https://github.com/Project-MONAI/model-zoo/blob/dev/models/pancreas_ct_dints_segmentation/docs/README.md)。
- 權重資料夾同時包含 `model.pt` 及很小的 `search_code_18590.pt`；建議使用 MONAI Bundle downloader 下載完整 bundle，不要只抓單一 checkpoint。
- 訓練資料為 [MSD Task07 Pancreas](https://registry.opendata.aws/msd/)，約 420 個 3D CT volumes。

### T4 執行判斷

官方文件指出訓練使用至少 16 GB GPU，實際模型輸入為 96×96×96。推論沒有官方 T4 benchmark，但在下列設定下，T4 16 GB 應能執行：

- AMP/FP16。
- batch 1。
- 96³ ROI。
- `sw_batch_size=1`。
- 不在 GPU 中快取完整訓練資料。

這裡的「可執行」屬工程估計，部署前仍應用實際病例量測 peak VRAM。

### Demo 設計

- 分色顯示 pancreas 及 tumor masks。
- 顯示各 voxel 的 softmax probability。
- 以 entropy 或最大類別機率呈現邊界信心。
- 列出胰臟體積、腫瘤體積與腫瘤占比。

## 4. MONAI Lung Nodule CT Detection

### 用途

這是以 LUNA16 訓練的 3D RetinaNet 肺結節偵測模型。它不是單純分類器，而是直接輸出 3D bounding boxes、labels 與 confidence scores，因此非常適合做病灶定位 Demo。

### 公開資源

- [Hugging Face MONAI Bundle](https://huggingface.co/MONAI/lung_nodule_ct_detection)，Apache-2.0。
- [官方 Bundle 說明](https://github.com/Project-MONAI/model-zoo/blob/dev/models/lung_nodule_ct_detection/docs/README.md)。
- [LUNA16 公開資料](https://luna16.grand-challenge.org/Data/)，包含 888 個 CT scans，資料源自 LIDC-IDRI。
- [LIDC-IDRI/TCIA 資料頁](https://www.cancerimagingarchive.net/collection/lidc-idri/)。

官方 bundle 使用 LUNA16 fold 0 訓練與驗證，文件回報 mAP 0.852、mAR 0.998；這些數值不能直接視為院內或外部資料的臨床效能。

### T4 執行判斷

模型 patch 為 192×192×80，官方訓練配置使用至少 16 GB GPU。推論建議：

- AMP/FP16。
- batch 1。
- `force_sliding_window=true`。
- 先完成官方要求的 resampling，再送入模型。

上述配置對 T4 16 GB 應可行，但仍屬工程估計，不是官方 T4 benchmark。

### Demo 設計

- 在 axial、coronal、sagittal 三視圖顯示同一個 3D box。
- 用 slider 調整 confidence threshold，觀察候選結節數量。
- 列出每個候選的中心座標、box 尺寸與分數。
- 對 false positive 候選保留人工接受／排除操作，呈現 human-in-the-loop 流程。

### 注意事項

此模型偵測的是肺結節候選，不能判斷良性或惡性，也不能單獨等同於肺癌診斷。

## 5. AutoDDPM

### 用途

AutoDDPM 使用 diffusion model 重建模型認為正常的 T1w 腦部 MRI，接著比較原始影像與 pseudo-healthy 重建結果，產生異常 likelihood map、mask 及最終 residual。這一流程最貼近原始主題文件描述的「正常重建差異」異常偵測機制。

### 公開資源

- [官方程式碼](https://github.com/ci-ber/autoDDPM)，GPL-3.0。
- [官方 T1w brain checkpoint](https://www.dropbox.com/scl/fi/7vem1s1ocx51duecekl06/latest_model.pt.zip?rlkey=wl5trcby4rozu4p4cgd940p53&dl=1)，壓縮檔約 191.5 MiB。
- [IXI 正常腦部 MRI](https://brain-development.org/ixi-dataset/)，約 600 位健康受試者。
- Repository 內含 IXI、FastMRI 與 ATLAS 的資料切分與設定檔。

### T4 執行判斷

預設配置為 2D、單 channel、128×128、batch 1，模型及 activation 的顯存需求對 T4 16 GB 應可行。主要限制不是顯存，而是 diffusion 的反覆採樣：

- 單張 slice 可作現場推論。
- 完整 3D volume 可能無法即時完成。
- 展示時可預先快取完整 volume，只針對少量 slices 重新推論。

目前沒有官方 T4 benchmark，因此不能承諾實際秒數。

### Demo 設計

依序呈現：

1. 原始病人影像。
2. 初步重建與 initial residual。
3. 初步 anomaly mask。
4. mask、stitch 及 re-sample 後的 pseudo-healthy 影像。
5. 原圖與 pseudo-healthy 影像的最終差異熱圖。
6. threshold 改變時，異常區域如何增減。

### 注意事項

- 官方 checkpoint 名稱只是 `latest_model.pt`。Repository、預設 config 與 README 能將它連到 T1w/IXI 工作流程，但沒有獨立 model card 或 hash 精確聲明 checkpoint 使用的每一筆資料；其權重可稽核性弱於前三個 MONAI/nnU-Net 選項。
- README 明確提醒 domain shift 會改變正常影像的重建誤差分布，因此換醫院、掃描器或資料集時必須重新校正 anomaly threshold。

## 建議的 Demo 優先順序

### 最快完成穩定成果

1. **nnU-Net BrainTumour**：官方顯存需求明確，自動 mask 容易驗證。
2. **MONAI Lung Nodule**：原生輸出位置與 confidence，互動呈現簡單清楚。

### 最有展示效果

1. **SAM-Med3D Turbo**：使用者點選後直接產生與修正 3D mask。
2. **AutoDDPM**：完整呈現病灶如何由正常重建差異形成。

### 共用部署框架

若希望減少環境種類，可先選兩個 MONAI bundles：Pancreas CT DiNTS 與 Lung Nodule Detection。兩者可以共用 MONAI Bundle 的下載、設定及 inference 管線。

## 未列入主要五款的候選

| 候選 | 未列入原因 |
| --- | --- |
| [MedSegDiff](https://github.com/ImprintLab/MedSegDiff) | 有程式及資料處理說明，但官方 repository 沒有可直接使用的正式預訓練 checkpoint，仍需自行訓練。 |
| [Diffusion Models for Medical Anomaly Detection](https://github.com/JuliaWolleb/diffusion-anomaly) | 對應原始文件中的 Wolleb 方法，但官方 repository 只提供訓練／sampling 程式，沒有公開 `model.pt` 與 classifier checkpoint。 |
| [TotalSegmentator](https://github.com/wasserth/TotalSegmentator) | 很適合 T4 low-resolution Demo，但現行權重標示 1,559 subjects，公開資料集為 1,228 cases，無法確認完整且完全相同的訓練 corpus。 |
| [BiomedParse](https://huggingface.co/microsoft/BiomedParse) | 權重與資料需要申請，而且公開的 processed training data 只是一部分，不符合完整資料透明度要求。 |
| [Acute Stroke Detection and Segmentation](https://github.com/Chin-Fu-Liu/Acute-stroke_Detection_Segmentation) | 公開版本明確不支援 GPU，無法符合「使用 NVIDIA T4 inference」的條件。 |
| [TorchXRayVision](https://github.com/mlmed/torchxrayvision) | NIH DenseNet 有權重與資料，但輸出主要是影像級分類；Grad-CAM 只是 post-hoc saliency，不能視為已驗證的病灶定位。 |
| [PICARD](https://github.com/mazurowski-lab/picard-anomalydetection) | 有 DBT anomaly-localization checkpoint 與公開資料，但完整高解析度掃描速度慢，不適合即時 T4 Demo。 |

## 授權與使用限制

- 程式碼授權、模型權重授權及訓練資料授權是三件不同的事，應分別檢查。
- SAM-Med3D 與 AutoDDPM 的程式碼有明確開源授權，但 checkpoint 頁面沒有獨立且完整的權重授權聲明。研究或校內 Demo 通常較單純；公開再散布或商業使用前應向作者確認。
- Medical Segmentation Decathlon、LUNA16、IXI 等資料各有自己的引用與再利用條款，使用公開案例時仍須遵循原始資料授權。
- 所有模型只適合作為研究、教學或醫師判讀輔助展示，不能宣稱為臨床診斷系統。

## 研究紀錄

- [Undermind：預訓練醫療分割與異常定位模型](https://app.undermind.ai/projects/1f44d5f3-0d70-4a0c-95eb-d9b44e684093?path=/%E9%A0%90%E8%A8%93%E7%B7%B4%E9%86%AB%E7%99%82%E5%88%86%E5%89%B2%E8%88%87%E7%95%B0%E5%B8%B8%E5%AE%9A%E4%BD%8D%E6%A8%A1%E5%9E%8B)

