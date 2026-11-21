# KPI Dictionary & Metric Reference Guide
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Version:** 1.2.0  
**Date:** 2026-11-14  

---

### Master KPI Reference Table

| Metric ID | KPI Display Name | Business Domain | Grain | Mathematical Formula | Unit | Stated Exclusion Rule & Filter Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M01** | Total Orders Placed | Sales / Volume | Order (`order_id`) | `COUNT(DISTINCT order_id)` | Orders | **None.** Includes all 99,441 orders recorded across all lifecycle statuses. |
| **M02** | Delivered Orders | Operations / Fulfillment | Order (`order_id`) | `COUNT(DISTINCT order_id)` | Orders | **Excludes non-delivered orders and delivered orders with null delivery dates.** Requires `order_status = 'delivered'` AND `order_delivered_customer_date IS NOT NULL` (excludes 2,963 non-delivered orders and 8 delivered orders with null delivery dates; scope is exactly 96,470 orders). |
| **M03** | On-Time Delivery Rate (Date-Level) | Operations / Fulfillment | Order (`order_id`) | $\frac{\text{Delivered Orders with } \text{DATE}(t_{\text{delivered}}) \le \text{DATE}(t_{\text{estimated}})}{\text{Total Delivered Orders with Delivery Date}} \times 100$ | % | **Evaluated on M02 cohort only.** Excludes non-delivered and null-delivery orders. Evaluated at calendar DATE precision (`DATE(delivered) <= DATE(estimated)`). An order delivered on the promised date is classified as on-time. |
| **M04** | Late Delivery Rate (Date-Level) | Operations / Fulfillment | Order (`order_id`) | $\frac{\text{Delivered Orders with } \text{DATE}(t_{\text{delivered}}) > \text{DATE}(t_{\text{estimated}})}{\text{Total Delivered Orders with Delivery Date}} \times 100$ | % | **Evaluated on M02 cohort only.** Excludes non-delivered and null-delivery orders. Evaluated at calendar DATE precision (`DATE(delivered) > DATE(estimated)`). |
| **M05** | Average Delivery Delay (Days) | Operations / Fulfillment | Order (`order_id`) | $\text{AVG}(\text{DATE}(t_{\text{delivered}}) - \text{DATE}(t_{\text{estimated}}))$ | Days | **Excludes on-time delivered orders, non-delivered orders, and null dates.** Evaluated strictly on late delivered orders (`DATE(delivered) > DATE(estimated)`). Stored as integer whole calendar days. |
| **M06** | Average Handling Time (Clean) | Merchant Operations | Order (`order_id`) | $\text{AVG}(t_{\text{carrier}} - t_{\text{approved}})$ | Days | **Evaluated on clean fulfillment population (`is_clean_fulfillment = TRUE`, $N = 95,082$).** Excludes non-delivered orders, null delivery/carrier/approval timestamps, and chronological anomalies ($t_{\text{carrier}} < t_{\text{approved}}$: 1,350 orders; $t_{\text{delivered}} < t_{\text{carrier}}$: 23 orders). Average: **2.85 days**. |
| **M07** | Average Transit Time (Clean) | Logistics / Carrier | Order (`order_id`) | $\text{AVG}(t_{\text{delivered}} - t_{\text{carrier}})$ | Days | **Evaluated on clean fulfillment population (`is_clean_fulfillment = TRUE`, $N = 95,082$).** Excludes non-delivered orders, null timestamps, and chronological anomalies. Average: **9.36 days**. |
| **M08** | Total Order Cycle Time (Valid Delivered) | Operations / Fulfillment | Order (`order_id`) | $\text{AVG}(t_{\text{delivered}} - t_{\text{purchase}})$ | Days | **Excludes non-delivered orders and null delivery timestamps.** Evaluated on M02 cohort ($N = 96,470$, mean **12.56 days**). Measures customer-facing elapsed time from purchase to delivery. |
| **M08b** | Fulfillment Cycle Time (Clean Scope) | Operations / Fulfillment | Order (`order_id`) | $\text{AVG}(t_{\text{delivered}} - t_{\text{purchase}})$ | Days | **Evaluated on clean fulfillment population (`is_clean_fulfillment = TRUE`, $N = 95,082$).** Mean: **12.62 days**. Note: Includes payment authorization duration ($t_{\text{approved}} - t_{\text{purchase}}$ = 0.40 days / ~9.6 hours). Operational pipeline (Handling 2.85d + Transit 9.36d) is **12.22 days**. |
| **M08c** | Handling Share of Fulfillment (%) | Merchant Operations | Order (`order_id`) | $\frac{\text{Handling Days}}{\text{Handling Days} + \text{Transit Days}} \times 100$ | % | **Evaluated against operational logistics pipeline (Handling + Transit = 12.22 days).** $\frac{2.85175}{12.21586} \times 100 =$ **23.34%**. |
| **M08d** | Transit Share of Fulfillment (%) | Carrier Logistics | Order (`order_id`) | $\frac{\text{Transit Days}}{\text{Handling Days} + \text{Transit Days}} \times 100$ | % | **Evaluated against operational logistics pipeline (Handling + Transit = 12.22 days).** $\frac{9.36411}{12.21586} \times 100 =$ **76.66%**. |
| **M09** | Delivery Estimate Variance (Days) | Operations / Planning | Order (`order_id`) | $\text{AVG}(\text{DATE}(t_{\text{estimated}}) - \text{DATE}(t_{\text{delivered}}))$ | Days | **Excludes non-delivered orders and null delivery timestamps.** Measured in integer calendar days. Positive = early arrival; Negative = late arrival. |
| **M10** | Gross Merchandise Value (GMV) | Commercial / Revenue | Order Item (`order_id`, `order_item_id`) | $\sum \text{price}$ | BRL (R$) | **Excludes shipping fees (`freight_value`) and excludes 775 orders that have no items allocated.** Total item GMV is R$ 13,591,643.70; realized delivered GMV is R$ 13,220,248.93. |
| **M11** | Total Freight Billed | Commercial / Logistics | Order Item (`order_id`, `order_item_id`) | $\sum \text{freight\_value}$ | BRL (R$) | **Excludes items with missing freight (none in raw data) and orders without items.** Evaluated at item grain. Total: R$ 2,251,909.54. |
| **M12** | Total Customer Item Spend | Commercial / Financial | Order Item (`order_id`, `order_item_id`) | $\sum (\text{price} + \text{freight\_value})$ | BRL (R$) | **Excludes orders without allocated items.** Represents total customer checkout basket on items. Reconciles exactly to Item GMV + Freight (R$ 15,843,553.24). |
| **M13** | Total Captured Payments | Commercial / Financial | Payment (`order_id`, `payment_sequential`) | $\sum \text{payment\_value}$ | BRL (R$) | **None.** Evaluated across all 103,886 payment transactions (R$ 16,008,872.12). Reconciled against M12: difference of +R$ 165,318.88 explained by 775 orders without items (R$ 162,591.95), voucher/installment rounding (R$ 2,870.39), and 1 item order without payment (-R$ 143.46). |
| **M14** | Freight-to-Price Ratio (%) | Commercial / Pricing | Order Item (`order_id`, `order_item_id`) | $\frac{\sum \text{freight\_value}}{\sum \text{price}} \times 100$ | % | **Excludes items where $\text{price} \le 0$** (none in dataset; minimum price is R$ 0.85). |
| **M15** | Average Review Score | Customer Satisfaction | Order (`order_id`) | $\text{AVG}(\text{review\_score})$ | Rating (1.00–5.00) | **Excludes 768 orders without a review.** Evaluated on deduplicated latest review per order ($N = 98,673$, mean 4.0864). |
| **M16** | Negative Review Rate (1–2 Stars)| Customer Satisfaction | Order (`order_id`) | $\frac{\text{Orders with score } \in \{1, 2\}}{\text{Total Reviewed Orders}} \times 100$ | % | **Excludes unreviewed orders.** Evaluated on deduplicated order reviews. |
| **M17** | Positive Review Rate (5 Stars)  | Customer Satisfaction | Order (`order_id`) | $\frac{\text{Orders with score } = 5}{\text{Total Reviewed Orders}} \times 100$ | % | **Excludes unreviewed orders.** Evaluated on deduplicated order reviews. |
| **M18** | Repeat Customer Rate (%) | Customer Retention | Customer Entity (`customer_unique_id`) | $\frac{\text{Distinct } \text{customer\_unique\_id with } \ge 2 \text{ orders}}{\text{Total Distinct } \text{customer\_unique\_id}} \times 100$ | % | **Excludes transactional `customer_id` scoping.** Evaluated across all 96,096 distinct `customer_unique_id` entities (2,997 repeat buyers, 3.1188%). |
| **M19** | Review Created Before Delivery Flag | Customer Satisfaction / QA | Order (`order_id`) | $\text{DATE}(t_{\text{review\_creation}}) < \text{DATE}(t_{\text{delivered}})$ | Boolean | **Excludes unreviewed orders and non-delivered orders.** Evaluated on 95,824 delivered reviewed orders. Categorizes whether review survey was completed before actual parcel delivery. |

---

### Detailed Grain & Stated Exclusion Rules

1. **Revenue Grain vs Delivery Grain:**
   - **Revenue metrics (M10, M11, M12, M14):** Evaluated strictly at the `order_items` grain (`order_id, order_item_id`). Joining payments or reviews directly to items causes fan-out multiplication and is prohibited.
   - **Delivery metrics (M02, M03, M04, M05, M06, M07, M08, M09):** Evaluated strictly at the `orders` grain (`order_id`) in `fact_order_delivery`.

2. **Calendar Date vs Exact Timestamp Truncation:**
   - **M03 / M04 / M05 / M09:** Evaluated using calendar dates (`DATE(delivered_date)` vs `DATE(estimated_date)`). Because `order_estimated_delivery_date` has midnight timestamps (`00:00:00`), raw timestamp comparisons misclassify afternoon deliveries on the promised day as late.

3. **Fulfillment Lead Time Quality Filter (H3 Scope):**
   - **M06 / M07:** Chronological sequence violations ($t_{\text{carrier}} < t_{\text{approved}}$: 1,350 orders; $t_{\text{delivered}} < t_{\text{carrier}}$: 23 orders) are retained in the database with explicit boolean flags (`has_negative_handling = TRUE`, `has_negative_transit = TRUE`, `is_anomalous_sequence = TRUE`) to ensure non-destructive auditability, but are excluded from clean duration models.

4. **Review Entity Resolution:**
   - **M15 / M16 / M17 / M19:** Deduplicated to exactly 1 review per order using the latest `review_answer_timestamp` (tie-breaker: latest `review_creation_date`, max `review_id`). Missing reviews are excluded from satisfaction averages without dropping the underlying orders.

5. **Clean Fulfillment Population Scope (`is_clean_fulfillment`):**
   - Clean fulfillment metrics (M06, M07, M08b, M08c, M08d) require: delivered status, non-null customer delivery date, non-null carrier pickup date, non-null payment approval date, handling days $\ge 0$, and transit days $\ge 0$ ($N = 95,082$).
   - Explicit boolean column `is_clean_fulfillment` prevents DAX `BLANK() >= 0` null-coercion from admitting 15 orders that lack carrier pickup dates into the clean population.
   - Decomposition: Total cycle time on clean orders (12.62 days) includes payment authorization (0.40 days / ~9.6 hours); operational fulfillment shares (Handling 23.34%, Transit 76.66%) evaluate against the 12.22-day operational pipeline (Handling 2.85d + Transit 9.36d).
