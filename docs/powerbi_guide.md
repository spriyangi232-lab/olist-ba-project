# Power BI Guide: Rebuilding the Delivery Performance Dashboard

| | |
|---|---|
| **Project** | Delivery Delay Root-Cause Analysis & Customer Satisfaction Improvement (Olist E-Commerce) |
| **Author** | Priyangi Singh Chouhan |
| **Version** | 1.0 |
| **Date** | 18 November 2026 |
| **Status** | Build guide |

This guide lists the steps I follow to rebuild `dashboard/dashboard.html` in Power BI Desktop. The check values in section 5 come from `results/metrics.json`; if the Power BI numbers match them, the model is correct.

---

## 1. Before you start

1. Run the Python scripts once so the data files exist:
   ```bash
   python src/01_clean.py
   ```
   ```bash
   python src/03_impact.py
   ```
   (`03_impact.py` needs `02_run_sql.py` to have run first.)
2. Files to import:

| File | Rows | One row per | Used for |
|---|---:|---|---|
| `data/processed/analysis_orders.csv` | 96,203 | Delivered order | Order KPIs, trend, states, categories, reviews, stages |
| `data/processed/analysis_order_sellers.csv` | 97,541 | Order-seller pair | SLA breach, routes, seller scorecard |
| `results/tables/impact_seller_excess.csv` | 625 | Seller with 30+ orders | Excess late orders ranking (optional, can also be built in DAX) |

## 2. Import and clean (Power Query)

1. **Home > Get data > Text/CSV**, select `analysis_orders.csv`, click **Transform Data**.
2. Set column types:
   - Date/Time: `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`. The files store dates as `YYYY-MM-DD HH:MM:SS`. If Power BI shows errors, use **Change Type > Using Locale > Date/Time, English (United States)**.
   - Whole number: `is_late`, `has_review`, `is_bad_review`, `is_good_review`, `stage_valid`, `is_multi_seller`, `n_items`, `n_sellers`, `delay_days`, `review_score`.
   - Decimal number: `approval_days`, `seller_handling_days`, `carrier_transit_days`, `promised_lead_days`, `actual_lead_days`, `order_value`, `freight_value`.
   - Text: everything else.
3. Add a date-only column for the date table: **Add Column > Custom Column**, name `purchase_date`, formula `DateTime.Date([order_purchase_timestamp])`, type Date.
4. Repeat steps 1-2 for `analysis_order_sellers.csv`. `sla_breach` is Whole number and is blank for 1 pair with no carrier date; leave the blank as is.
5. Import `impact_seller_excess.csv` if you want the ready-made ranking. Types: `orders`, `late` Whole number; `expected_late`, `excess_late`, `late_rate` Decimal number.
6. **Close & Apply**.

## 3. Data model

Create a date table: **Modeling > New table**:

```DAX
Dates =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2017, 1, 1 ), DATE ( 2018, 8, 31 ) ),
    "Month", FORMAT ( [Date], "YYYY-MM" ),
    "Month Start", DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 )
)
```

Mark it as a date table (**Table tools > Mark as date table**, column `Date`).

Relationships (**Model view**, drag and drop):

| From (many) | To (one) | Cardinality | Filter direction |
|---|---|---|---|
| `analysis_orders[purchase_date]` | `Dates[Date]` | Many to one | Single |
| `analysis_order_sellers[order_id]` | `analysis_orders[order_id]` | Many to one | Single |
| `impact_seller_excess[seller_id]` | none | Leave unrelated (it is a ready-made summary) | - |

Note: with single direction, a filter on an order column (month, customer state, category) flows to the seller pairs. A filter on a pair column (seller, route, seller state) does **not** flow back to the order table. That is why the seller and route visuals in section 6 use measures from the pairs table only.

## 4. DAX measures

Create a measure table to keep things tidy: **Home > Enter data**, name it `_Measures`, load an empty table, then add each measure below to it (**New measure**). Set the format shown in brackets.

### Order measures

```DAX
Delivered Orders = COUNTROWS ( analysis_orders )                                  -- (Whole number)

Late Orders = SUM ( analysis_orders[is_late] )                                    -- (Whole number)

Late Rate % = DIVIDE ( [Late Orders], [Delivered Orders] )                        -- (Percentage, 2 dp)

On-Time Rate % = 1 - [Late Rate %]                                                -- (Percentage, 2 dp)

Avg Delay Days (Late) =
CALCULATE ( AVERAGE ( analysis_orders[delay_days] ), analysis_orders[is_late] = 1 )   -- (Decimal, 2 dp)

Reviewed Orders = SUM ( analysis_orders[has_review] )

Avg Review Score = AVERAGE ( analysis_orders[review_score] )                       -- blanks are ignored

Bad Review % = DIVIDE ( SUM ( analysis_orders[is_bad_review] ), [Reviewed Orders] )   -- (Percentage, 2 dp)

Bad Review % (Late) = CALCULATE ( [Bad Review %], analysis_orders[is_late] = 1 )

Bad Review % (On Time) = CALCULATE ( [Bad Review %], analysis_orders[is_late] = 0 )

Bad Review Multiple = DIVIDE ( [Bad Review % (Late)], [Bad Review % (On Time)] )      -- (Decimal, 1 dp)
```

### Journey-stage measures (valid timestamps only)

```DAX
Avg Seller Handling Days =
CALCULATE ( AVERAGE ( analysis_orders[seller_handling_days] ), analysis_orders[stage_valid] = 1 )

Avg Carrier Transit Days =
CALCULATE ( AVERAGE ( analysis_orders[carrier_transit_days] ), analysis_orders[stage_valid] = 1 )

Avg Approval Days =
CALCULATE ( AVERAGE ( analysis_orders[approval_days] ), analysis_orders[stage_valid] = 1 )

Avg Days Early = AVERAGE ( analysis_orders[delay_days] ) * -1                      -- buffer in the estimate
```

### Seller and route measures (order-seller pairs)

```DAX
Pairs = COUNTROWS ( analysis_order_sellers )

Late Pairs = SUM ( analysis_order_sellers[is_late] )

Pair Late Rate % = DIVIDE ( [Late Pairs], [Pairs] )

SLA Breach % =
DIVIDE (
    SUM ( analysis_order_sellers[sla_breach] ),
    COUNT ( analysis_order_sellers[sla_breach] )          -- COUNT skips the blank row
)

Platform Pair Late Rate % =
CALCULATE ( [Pair Late Rate %], ALL ( analysis_order_sellers ) )

Excess Late Orders = [Late Pairs] - [Pairs] * [Platform Pair Late Rate %]          -- (Decimal, 0 dp)
```

`Platform Pair Late Rate %` uses `ALL`, so it ignores slicers. If you want "platform" to mean "the selected period", change `ALL ( analysis_order_sellers )` to `ALLEXCEPT ( analysis_order_sellers, analysis_order_sellers[purchase_month] )`. The Python analysis uses the whole window.

## 5. Check values

With no slicers applied, the measures must show:

| Measure | Expected value |
|---|---|
| Delivered Orders | 96,203 |
| Late Orders | 6,531 |
| On-Time Rate % | 93.21% |
| Avg Delay Days (Late) | 10.62 |
| Bad Review % | 12.80% |
| Bad Review % (Late) / (On Time) | 62.42% / 9.25% |
| SLA Breach % | 8.86% |
| Avg Carrier Transit Days, filtered to is_late = 1 / 0 | 27.89 / 8.01 |
| Pair Late Rate % (platform) | 6.71% |
| Late rate, customer state AL | 21.46% |
| Late pairs, route SP -> RJ | 1,157 |

If a value is off, check the column types first (a text `is_late` column gives wrong sums).

## 6. Report layout

One page, 16:9, white background. Colours: late / problem `#EB6834` (orange), on time / baseline `#2A78D6` (blue), context `#C3C2B7` (grey).

| Area | Visual | Fields |
|---|---|---|
| Top row | 4 **Card** visuals | `On-Time Rate %`, `Avg Delay Days (Late)`, `Bad Review %`, `SLA Breach %` |
| Top right | **Slicers** (dropdown) | `Dates[Month]`, `analysis_orders[customer_state]`, `analysis_orders[main_category]` |
| Row 2, full width | **Line chart** | X: `Dates[Month Start]` (Month level), Y: `On-Time Rate %`. Add a constant line at 0.9321 (Analytics pane) labelled "Average" |
| Row 3, left | **Clustered bar chart** | Y: `analysis_orders[customer_state]`, X: `Late Rate %`. Visual-level filter: `Delivered Orders` ≥ 300. Sort by `Late Rate %` descending. Conditional formatting > Data colors > Rules: orange if value > 0.0679, else grey |
| Row 3, right | **Clustered bar chart** | Y: `analysis_order_sellers[route]`, X: `Late Pairs`. Filter: Top N = 12 by `Late Pairs`. Tooltips: `Pair Late Rate %`, `Pairs` |
| Row 4, left | **Clustered bar chart** | Y: `analysis_order_sellers[seller_id]`, X: `Excess Late Orders`. Filters: `Pairs` ≥ 30 and Top N = 20 by `Excess Late Orders`. Tooltips: `Pairs`, `Late Pairs`, `Pair Late Rate %` |
| Row 4, right | **Clustered bar chart** | Y: `analysis_orders[main_category]`, X: `Late Rate %`. Filter: `Delivered Orders` ≥ 300. Same orange/grey rule as states |
| Row 5, left | **Clustered column chart** | X: `analysis_orders[delay_bucket]`, Y: `Bad Review %`. Sort the axis: on time, 1-3, 4-7, 8-14, 15+ days (add a sort column in Power Query if needed) |
| Row 5, right | **Clustered bar chart** | Y: stage names, X: `Avg Approval Days`, `Avg Seller Handling Days`, `Avg Carrier Transit Days`; Legend: `analysis_orders[is_late]` |

Tip for the stage chart: put the three stage measures in **X-axis** and `is_late` in **Legend**, then rename the legend items to "On time" and "Late" in the Format pane.

## 7. Finishing

1. Add a text box under the title: "Late = delivered after the estimated date. Data: Olist public dataset (Kaggle, CC BY-NC-SA 4.0), Jan 2017 - Aug 2018."
2. Add a **Glossary** page with the KPI definitions table from `docs/BRD.md` section 12.
3. Save as `dashboard/olist_delivery.pbix` and export a screenshot for the README (**File > Export > Export to PDF** or a screen capture).
