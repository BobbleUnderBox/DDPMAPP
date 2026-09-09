[xtool\_backpack.md](docs/prepare/xtool_backpack.md)(line 265) 解釋這三種統計流程分別如何在醫療 diffusion model 上運作，請做一千字以內摘要。

[第 265 行](C:/Users/fromn/OneDrive/Desktop/XDDPMAPP/docs/prepare/xtool_backpack.md:265)的三種流程，可用於 MRI、CT 等 **diffusion 影像重建**。共同背景是：模型提供影像先驗，結合病人的量測資料與成像、雜訊模型，形成後驗分布 \(p(x\mid y)\)，描述這筆量測下可能的影像。[Bayesian MRI 研究](https://onlinelibrary.wiley.com/doi/10.1002/mrm.29624)

1. **Measurement-consistency residual：重建是否符合量測？**  
   將重建影像 \(\hat{x}\) 經成像算子 \(A\) 轉回量測空間，計算殘差 \(r=y-A\hat{x}\)。MRI 比較已採集的 k-space；CT 則比較對應的投影量測。可呈現殘差圖與整體分數，並依雜訊大小判讀。單張重建即可計算；殘差大可能來自重建錯誤、雜訊或成像模型不準，殘差小也無法排除量測未捕捉到的錯誤結構。[CT diffusion 研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC11362816/)

2. **Posterior variance：哪些位置有較多重建可能性？**  
   固定同一筆量測，利用不同隨機初始化進行多次後驗抽樣，再計算各體素在不同重建結果間的變異數，形成不確定性熱圖。例如病灶邊界在多次結果中改變，該處變異就較高。這反映模型條件下的結果分散程度；即使變異很低，也可能每次都產生相同錯誤。[MRI 不確定性研究](https://onlinelibrary.wiley.com/doi/10.1002/mrm.29624)

3. **Credible interval：估計值的可信範圍多寬？**  
   使用同一批後驗樣本，取各體素數值的第 2.5 與 97.5 百分位數，形成約 95% 後驗可信區間。也可延伸為：對每張重建使用固定方法計算病灶體積，再取體積分布的區間。相較變異數，它直接提供上下界，且分位數法不必假設常態分布。95% 指模型與量測條件下的後驗機率，不代表整張影像有 95% 機率完全正確。[後驗區間計算文件](https://search.r-project.org/CRAN/refmans/rstantools/html/posterior_interval.html)

"取各體素數值的第 2.5 與 97.5 百分位數"這是指甚麼東西的數值?

指的是 **同一個空間位置，在多次重建影像中的體素強度值**，也就是該位置的影像亮度／訊號值。Annotation 1

例如固定同一位病人的 MRI 量測，讓 diffusion model 做 100 次後驗抽樣，得到 100 張重建影像：

- 選定同一個體素位置，例如座標 \((30,40,20)\)。
- 從每張影像讀出這個位置的強度，得到 **100 個數值**。
- 將它們排序，取第 2.5 與 97.5 百分位數，作為這個體素強度的約 95% 後驗可信區間。

因此，區間描述的是「**這個位置的影像強度可能落在哪個範圍**」。若想估計病灶體積的可信區間，就要先從每張重建計算體積，再對那些體積值取百分位數。