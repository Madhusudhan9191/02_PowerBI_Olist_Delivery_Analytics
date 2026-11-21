# DAX Measure Verification & Reconciliation Test Table
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Purpose:** Quality assurance verification matrix reconciling Power BI Desktop DAX measures against independent PostgreSQL 16 and Python/Pandas warehouse totals.

> **Verification Rigor & Exact Tolerances:**
> - **Expected Control Values:** Programmatically evaluated in Python directly from warehouse CSVs and SQL analytical query outputs (`q01`–`q12`). Zero hardcoded numbers.
> - **Observed Values:** Directly extracted from Power BI Desktop DAX Query View export (`Power BI Desktop DAX Query View Export (dax_all_63_export.csv)`).
> - **Strict Tolerances:** Integer counts require **exact match (tolerance = 0)**. Financial values require $\le R\$ 0.005$ (half-cent). Rates require $\le 0.01\%$ ($1 \times 10^{-4}$). Delivery days, satisfaction scores, and percentage-point gaps require $\le 0.01$.

---

### Master Reconciliation Matrix (63 of 63 Measures)

| # | Measure Name | Display Folder | Expected Benchmark Value | Sample Size / Scope ($N$) | Observed Value in Power BI | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | `[Total Orders]` | `01_Volume_and_Spend` | **99,441** | All orders in dataset | 99441.0 | [x] PASS |
| **02** | `[Delivered Orders]` | `01_Volume_and_Spend` | **96,478** | order_status = 'delivered' | 96478.0 | [x] PASS |
| **03** | `[Valid Delivered Orders]` | `01_Volume_and_Spend` | **96,470** | Delivered with non-null delivery date | 96470.0 | [x] PASS |
| **04** | `[Gross Item Revenue]` | `01_Volume_and_Spend` | **R$ 13,591,643.70** | SUM(price) across 112,650 items | 13591643.699999858 | [x] PASS |
| **05** | `[Total Freight Billed]` | `01_Volume_and_Spend` | **R$ 2,251,909.54** | SUM(freight_value) across 112,650 items | 2251909.54 | [x] PASS |
| **06** | `[Total Customer Spend]` | `01_Volume_and_Spend` | **R$ 15,843,553.24** | SUM(price + freight_value) | 15843553.24000002 | [x] PASS |
| **07** | `[Captured Payment Value]` | `01_Volume_and_Spend` | **R$ 16,008,872.12** | SUM(payment_value) across 103,886 payments | 16008872.12 | [x] PASS |
| **08** | `[Total Unique Customers]` | `01_Volume_and_Spend` | **96,096** | DISTINCTCOUNT(customer_unique_id) on fact table | 96096.0 | [x] PASS |
| **09** | `[Total Active Sellers]` | `01_Volume_and_Spend` | **3,095** | All merchants in catalog | 3095.0 | [x] PASS |
| **10** | `[On-Time Orders]` | `02_Delivery_SLA` | **89,936** | Delivered on/before estimated date | 89936.0 | [x] PASS |
| **11** | `[Late Orders]` | `02_Delivery_SLA` | **6,534** | Delivered after estimated date | 6534.0 | [x] PASS |
| **12** | `[On-Time Delivery Rate %]` | `02_Delivery_SLA` | **93.23%** | 89,936 / 96,470 valid delivered | 0.9322690992018244 | [x] PASS |
| **13** | `[Late Delivery Rate %]` | `02_Delivery_SLA` | **6.77%** | 6,534 / 96,470 valid delivered | 0.0677309007981755 | [x] PASS |
| **14** | `[Average Delay Days (Late Orders)]` | `02_Delivery_SLA` | **10.62 days** | N = 6,534 late orders | 10.620140801958984 | [x] PASS |
| **15** | `[Average Promised Lead Time Days]` | `02_Delivery_SLA` | **24.37 days** | N = 96,470 valid delivered orders | 24.37273763864414 | [x] PASS |
| **16** | `[Average Actual Cycle Days]` | `02_Delivery_SLA` | **12.56 days** | N = 96,470 valid delivered orders | 12.558217440655117 | [x] PASS |
| **17** | `[ETA Safety Buffer Days]` | `02_Delivery_SLA` | **11.81 days** | Promised lead time minus actual cycle | 11.814520197989022 | [x] PASS |
| **18** | `[Total Reviewed Orders]` | `03_Review_Satisfaction` | **98,673** | Deduplicated latest review per order | 98673.0 | [x] PASS |
| **19** | `[Delivered Reviewed Orders]` | `03_Review_Satisfaction` | **95,824** | Delivered orders with reviews | 95824.0 | [x] PASS |
| **20** | `[Average Review Score]` | `03_Review_Satisfaction` | **4.0864** | All 98,673 reviewed orders | 4.086386346822333 | [x] PASS |
| **21** | `[Average Review Score (Delivered)]` | `03_Review_Satisfaction` | **4.1559** | N = 95,824 delivered reviewed orders | 4.155879529136751 | [x] PASS |
| **22** | `[Average Review Score (On-Time)]` | `03_Review_Satisfaction` | **4.2904** | N = 89,443 on-time reviewed orders | 4.290386055923885 | [x] PASS |
| **23** | `[Average Review Score (Late)]` | `03_Review_Satisfaction` | **2.2705** | N = 6,381 late reviewed orders | 2.270490518727472 | [x] PASS |
| **24** | `[Review Score Gap (Late vs On-Time)]` | `03_Review_Satisfaction` | **-2.02 points** | Late avg minus On-time avg | -2.0198955371964127 | [x] PASS |
| **25** | `[Negative Reviews Count (1-2 Star)]` | `03_Review_Satisfaction` | **12,272** | Delivered 1–2 star reviews | 12272.0 | [x] PASS |
| **26** | `[Negative Review Share %]` | `03_Review_Satisfaction` | **12.81%** | 12,272 / 95,824 delivered reviews | 0.128068124895642 | [x] PASS |
| **27** | `[Negative Review Share % (Late)]` | `03_Review_Satisfaction` | **62.42%** | Late cohort negative share | 0.6241968343519825 | [x] PASS |
| **28** | `[Negative Review Share % (On-Time)]` | `03_Review_Satisfaction` | **9.27%** | On-time cohort negative share | 0.0926735462808716 | [x] PASS |
| **29** | `[5-Star Reviews Count]` | `03_Review_Satisfaction` | **56,748** | Delivered 5-star reviews | 56748.0 | [x] PASS |
| **30** | `[5-Star Review Share % (Late)]` | `03_Review_Satisfaction` | **16.53%** | Late cohort 5-star share | 0.1653345870553204 | [x] PASS |
| **31** | `[5-Star Review Share % (On-Time)]` | `03_Review_Satisfaction` | **62.27%** | On-time cohort 5-star share | 0.6226647138400992 | [x] PASS |
| **32** | `[Pre-Delivery Late Reviews Count]` | `03_Review_Satisfaction` | **4,751** | Reviews submitted before parcel delivery | 4751.0 | [x] PASS |
| **33** | `[Pre-Delivery Late Review Share %]` | `03_Review_Satisfaction` | **74.46%** | 4,751 / 6,381 late reviews | 0.74455414511832 | [x] PASS |
| **34** | `[Avg Review Score (Pre-Delivery Late)]` | `03_Review_Satisfaction` | **1.8396** | N = 4,751 pre-delivery late reviews | 1.8396127131130289 | [x] PASS |
| **35** | `[Avg Review Score (Post-Delivery Late)]` | `03_Review_Satisfaction` | **3.5264** | N = 1,630 post-delivery late reviews | 3.52638036809816 | [x] PASS |
| **36** | `[Clean Fulfillment Orders]` | `04_Fulfillment_Bottlenecks` | **95,082** | is_clean_fulfillment = TRUE (handling >= 0 & transit >= 0) | 95082.0 | [x] PASS |
| **37** | `[Average Handling Days]` | `04_Fulfillment_Bottlenecks` | **2.85 days** | N = 95,082 clean orders (approval to carrier) | 2.851748588586693 | [x] PASS |
| **38** | `[Average Transit Days]` | `04_Fulfillment_Bottlenecks` | **9.36 days** | N = 95,082 clean orders (carrier to delivery) | 9.364111536358092 | [x] PASS |
| **39** | `[Average Fulfillment Cycle Days]` | `04_Fulfillment_Bottlenecks` | **12.62 days** | N = 95,082 clean orders (purchase to delivery) | 12.61796385120213 | [x] PASS |
| **40** | `[Handling Share of Fulfillment %]` | `04_Fulfillment_Bottlenecks` | **23.34%** | 2.85d / (2.85d + 9.36d) | 0.2334486196220104 | [x] PASS |
| **41** | `[Transit Share of Fulfillment %]` | `04_Fulfillment_Bottlenecks` | **76.66%** | 9.36d / (2.85d + 9.36d) | 0.7665513803779895 | [x] PASS |
| **42** | `[Interstate Orders Count]` | `04_Fulfillment_Bottlenecks` | **61,022** | Clean delivered orders across states | 61022.0 | [x] PASS |
| **43** | `[Intrastate Orders Count]` | `04_Fulfillment_Bottlenecks` | **34,060** | Clean delivered orders within state | 34060.0 | [x] PASS |
| **44** | `[Interstate On-Time Rate %]` | `04_Fulfillment_Bottlenecks` | **91.89%** | N = 61,022 interstate clean orders | 0.9188653272590214 | [x] PASS |
| **45** | `[Intrastate On-Time Rate %]` | `04_Fulfillment_Bottlenecks` | **95.43%** | N = 34,060 intrastate clean orders | 0.9542571931884908 | [x] PASS |
| **46** | `[Mix-Adjusted Performance Gap pp (RJ)]` | `05_Regional_and_Seller` | **-5.40 pp** | Actual vs Expected distance-adjusted rate | -5.39985610490803 | [x] PASS |
| **47** | `[Mix-Adjusted Performance Gap pp (SP)]` | `05_Regional_and_Seller` | **+1.07 pp** | Actual vs Expected distance-adjusted rate | 1.0723860945481056 | [x] PASS |
| **48** | `[Mix-Adjusted Performance Gap pp (AL)]` | `05_Regional_and_Seller` | **-11.68 pp** | Actual vs Expected distance-adjusted rate | -11.67588489923146 | [x] PASS |
| **49** | `[Late Dispatch Rate % (Tier 1)]` | `05_Regional_and_Seller` | **8.07%** | Sellers with 500+ orders | 0.0806900389538119 | [x] PASS |
| **50** | `[Late Dispatch Rate % (Tier 2)]` | `05_Regional_and_Seller` | **9.31%** | Sellers with 100–499 orders | 0.0931094806652915 | [x] PASS |
| **51** | `[Late Dispatch Rate % (Tier 3)]` | `05_Regional_and_Seller` | **9.86%** | Sellers with 30–99 orders | 0.0986332753989571 | [x] PASS |
| **52** | `[Late Dispatch Rate % (Tier 4)]` | `05_Regional_and_Seller` | **11.07%** | Sellers with <30 orders | 0.1107101215923602 | [x] PASS |
| **53** | `[Total Repeat Customers]` | `07_Retention_and_Cohort` | **2,997** | Distinct customers with >= 2 orders | 2997.0 | [x] PASS |
| **54** | `[Repeat Customer Rate %]` | `07_Retention_and_Cohort` | **3.12%** | 2,997 / 96,096 total customers | 0.0311875624375624 | [x] PASS |
| **55** | `[Delivered Repeat Rate % (On-Time)]` | `07_Retention_and_Cohort` | **3.04%** | On-time first order repeat rate | 0.0303580665555491 | [x] PASS |
| **56** | `[Delivered Repeat Rate % (Late)]` | `07_Retention_and_Cohort` | **2.52%** | Late first order repeat rate | 0.025177025963808 | [x] PASS |
| **57** | `[Delivered Repeat Rate Gap pp]` | `07_Retention_and_Cohort` | **-0.52 pp** | Late repeat rate minus On-time repeat rate | -0.5181040591741144 | [x] PASS |
| **58** | `[Mature Repeat Rate % (On-Time)]` | `07_Retention_and_Cohort` | **5.13%** | Mature cohort on-time repeat rate | 0.0512509599450305 | [x] PASS |
| **59** | `[Mature Repeat Rate % (Late)]` | `07_Retention_and_Cohort` | **3.78%** | Mature cohort late repeat rate | 0.0377562028047464 | [x] PASS |
| **60** | `[Mature Repeat Rate Gap pp]` | `07_Retention_and_Cohort` | **-1.35 pp** | Mature cohort late minus on-time gap | -1.3494757140284024 | [x] PASS |
| **61** | `[Mature Delivered Repeat Rate % (On-Time)]` | `07_Retention_and_Cohort` | **4.89%** | Mature delivered on-time repeat rate | 0.0489066731336647 | [x] PASS |
| **62** | `[Mature Delivered Repeat Rate % (Late)]` | `07_Retention_and_Cohort` | **3.56%** | Mature delivered late repeat rate | 0.0355987055016181 | [x] PASS |
| **63** | `[Mature Delivered Repeat Rate Gap pp]` | `07_Retention_and_Cohort` | **-1.33 pp** | Mature delivered late minus on-time gap | -1.3307967632046642 | [x] PASS |
