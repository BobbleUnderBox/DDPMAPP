CCDM（Conditional Categorical Diffusion Model，條件式類別擴散模型）的核心想法，是學習「給定一張影像，哪些分割結果可能成立，以及它們出現的機率」。以肺結節為例，模糊邊界可能讓不同醫師畫出大小不同、但都合理的輪廓。模型透過反覆採樣，產生一組符合影像內容的分割，表達影像與標註本身的**偶然不確定性**。例如，某段邊界可能多數標註者都同意，另一段卻有明顯分歧；保留這些差異，可以呈現單張遮罩難以表達的資訊。[原論文](https://arxiv.org/abs/2303.08888)

輸入方面，文件所列的 LIDC 版本使用以肺結節為中心、經前處理的單通道二維 CT 切片。**實際尺寸為 128×128**；筆記中的 128×256 設定並未套用於 LIDC 資料流程。推論時使用者提供影像，系統自行建立隨機標籤圖。每次去噪，網路同時接收原始影像、目前的含噪標籤圖與時間步。訓練另需醫師標註，官方流程每次從同張影像的四份標註中隨機選取一份。[資料處理程式](https://github.com/LarsDoorenbos/ccdm-stochastic-segmentation/blob/main/datasets/lidc.py)、[資料載入流程](https://github.com/LarsDoorenbos/ccdm-stochastic-segmentation/blob/main/ddpm/trainer.py)

輸出是與輸入空間對齊的逐像素類別圖；肺結節任務包含背景與結節兩類。一次完整採樣得到一張遮罩，重跑可得到不同輪廓。將多張結果疊合，可以另外計算多數決遮罩、像素被判為結節的比例，以及熵或一致性圖。這些統計圖是由採樣結果衍生的展示，能將結節範圍與邊界分歧一起呈現。[專案中的展示構想](C:/Users/fromn/OneDrive/Desktop/XDDPMAPP/docs/model/model_backpack.md)

內部的正向擴散會逐步破壞真實分割：每個像素依預定機率保留原類別，或從所有類別中均勻抽取新標籤。隨步數增加，原有輪廓逐漸消失，最後接近均勻隨機的類別圖。整條鏈的狀態都維持離散標籤，因此可以直接描述背景、結節等沒有大小順序的類別。CT 影像則保留作為條件，協助逆向過程找回符合影像內容的結構。[擴散實作](https://github.com/LarsDoorenbos/ccdm-stochastic-segmentation/blob/main/ddpm/models/diffusion_denoising.py)

去噪網路採用帶有自注意力的 U-Net。含噪標籤以獨熱編碼表示，與影像通道合併輸入；時間步經編碼後也進入網路，告知目前的擾動程度。編碼器、解碼器與跳接整合局部邊界及較大範圍的空間資訊，使相鄰像素能形成連貫輪廓。網路每一步預測的是各像素在**「乾淨分割」中屬於各類別的機率**。[網路實作](https://github.com/LarsDoorenbos/ccdm-stochastic-segmentation/blob/main/ddpm/models/unet_openai/unet.py)

逆向擴散再把上述機率與目前標籤、已知的正向轉移規則結合，計算前一時間步的類別分布，並抽樣得到較乾淨的標籤圖。模型反覆執行此程序，原論文設定為 250 步，最後一步選取機率最大的類別形成遮罩。不同的起始雜訊與途中抽樣會帶來不同答案；影像條件和學到的空間關係則約束答案的合理性。[採樣實作](https://github.com/LarsDoorenbos/ccdm-stochastic-segmentation/blob/main/ddpm/models/diffusion_denoising.py)、[官方設定](https://github.com/LarsDoorenbos/ccdm-stochastic-segmentation/blob/main/params.yml)

訓練時，模型隨機抽取時間步，將選定標註擾動到相應程度，再學習還原。目標以變分下界為基礎，透過重建項與分布間的 KL 散度，讓學得的逆向轉移接近由真實標註推導的轉移。多位醫師的不同答案因而成為可學習的資料分布，目標是保留輪廓差異及其出現頻率。[論文方法](https://arxiv.org/html/2303.08888v5#S3)

在本專案中，CCDM 最適合用於肺結節分割與不確定性展示：並排呈現原圖、多次遮罩、共識區及分歧邊界，協助理解哪些區域較穩定、哪些需要人工複核。展示時應保留個別採樣，因為平均圖可能掩蓋不同輪廓的形狀。實作上的主要代價是多步去噪加上重複採樣所需的時間；分歧圖表達的是模型學到的標註變異，解讀時仍須與分割準確度分開評估。