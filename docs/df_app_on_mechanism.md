# Diffusion Model application

## 器官、腫瘤與病灶分割

醫學影像分割的目標，是在 MRI、CT、超音波或眼底影像中標出特定區域，例如腫瘤邊界、器官或結節。

在這類任務中，diffusion model 通常不是生成完整醫學影像，而是逐步生成或修正 segmentation mask。相較於只輸出單一結果的傳統分割網路，diffusion model 還能多次取樣，產生數個可能的分割結果，藉此呈現模型的不確定性。

MedSegDiff 已經被測試於：

眼底影像的視杯分割。
MRI 的腦腫瘤分割。
超音波影像的甲狀腺結節分割。

資料來源：

Wu, J. et al. (2024). MedSegDiff: Medical Image Segmentation with Diffusion Probabilistic Model. Medical Imaging with Deep Learning, PMLR 227, 1623–1639.
Wolleb, J. et al. (2022). Diffusion Models for Implicit Image Segmentation Ensembles. Medical Imaging with Deep Learning, PMLR 172, 1336–1348.

## 疾病異常偵測與病灶定位

Diffusion model 可以先學習「正常影像」的分布，再將病人的影像重建成模型認為正常的版本。原始影像與正常重建影像之間的差異，就可能對應腫瘤、病灶或其他異常區域。

基本流程可以理解為：

使用正常影像訓練 diffusion model。
將待測影像加入適量雜訊。
模型重建正常外觀。
比較原始影像與重建影像。
產生異常位置圖。

Wolleb 等人的研究使用 diffusion model 在 BRATS2020 腦部 MRI 上進行弱監督異常偵測與腦腫瘤定位，只需要影像層級標籤，不必完全依賴像素級病灶標註。

資料來源：

Wolleb, J. et al. (2022). Diffusion Models for Medical Anomaly Detection. Medical Image Computing and Computer Assisted Intervention—MICCAI 2022, 35–45.
論文預印本：arXiv:2203.04306

這類方法比較適合作為異常篩檢或醫師判讀輔助，不能單獨等同於臨床診斷。