-- =============================================================================
-- analysis.sql - Business questions for the Olist delivery-delay case study
-- =============================================================================
-- Database : data/processed/olist.db (built by src/01_clean.py)
-- Main tables:
--   analysis_orders        one row per delivered order in the analysis window
--   analysis_order_sellers one row per (order_id, seller_id) pair
--
-- Definitions used everywhere (see docs/data_validation_report.md):
--   Late order    : delivered date > estimated date (dates only)  -> is_late = 1
--   Delay days    : delivered date - estimated date (positive = late)
--   Bad review    : latest review score 1-2; good review: 4-5
--   SLA breach    : seller handed parcel to carrier after shipping_limit_date
--   Stage columns : only trusted where stage_valid = 1
--
-- How this file is run: src/02_run_sql.py splits the file on the "-- name:" lines,
-- runs each query and saves the result to results/tables/<name>.csv.
-- =============================================================================


-- name: q01_overall_kpis
-- question: Q1. How big is the late-delivery problem overall?
SELECT
    COUNT(*)                                             AS delivered_orders,
    SUM(is_late)                                         AS late_orders,
    ROUND(100.0 * AVG(is_late), 2)                       AS late_rate_pct,
    ROUND(100.0 * (1 - AVG(is_late)), 2)                 AS on_time_rate_pct,
    ROUND(AVG(CASE WHEN is_late = 1 THEN delay_days END), 2)  AS avg_delay_days_late_orders,
    ROUND(AVG(review_score), 2)                          AS avg_review_score,
    ROUND(100.0 * SUM(is_bad_review) / SUM(has_review), 2)    AS bad_review_pct,
    (SELECT ROUND(100.0 * AVG(sla_breach), 2)
       FROM analysis_order_sellers
      WHERE sla_breach IS NOT NULL)                      AS seller_sla_breach_pct
FROM analysis_orders;


-- name: q02_monthly_trend
-- question: Q1. What is the monthly trend in on-time rate?
SELECT
    purchase_month,
    COUNT(*)                                             AS orders,
    SUM(is_late)                                         AS late_orders,
    ROUND(100.0 * (1 - AVG(is_late)), 2)                 AS on_time_rate_pct,
    ROUND(AVG(CASE WHEN is_late = 1 THEN delay_days END), 2)  AS avg_delay_days_late_orders,
    ROUND(100.0 * SUM(is_bad_review) / SUM(has_review), 2)    AS bad_review_pct
FROM analysis_orders
GROUP BY purchase_month
ORDER BY purchase_month;


-- name: q03_review_late_vs_ontime
-- question: Q2. How strongly does lateness affect review score and bad-review share?
SELECT
    CASE WHEN is_late = 1 THEN 'Late' ELSE 'On time' END AS delivery_status,
    COUNT(*)                                             AS reviewed_orders,
    ROUND(AVG(review_score), 2)                          AS avg_review_score,
    ROUND(100.0 * AVG(is_bad_review), 2)                 AS bad_review_pct,
    ROUND(100.0 * AVG(is_good_review), 2)                AS good_review_pct
FROM analysis_orders
WHERE has_review = 1
GROUP BY delivery_status
ORDER BY delivery_status;


-- name: q04_review_by_delay_bucket
-- question: Q2. Does review score get worse the later an order is? (1-3, 4-7, 8-14, 15+ days)
SELECT
    delay_bucket,
    COUNT(*)                                             AS reviewed_orders,
    ROUND(AVG(review_score), 2)                          AS avg_review_score,
    ROUND(100.0 * AVG(is_bad_review), 2)                 AS bad_review_pct,
    ROUND(100.0 * AVG(is_good_review), 2)                AS good_review_pct
FROM analysis_orders
WHERE has_review = 1
GROUP BY delay_bucket
ORDER BY CASE delay_bucket
            WHEN 'on time'   THEN 0
            WHEN '1-3 days'  THEN 1
            WHEN '4-7 days'  THEN 2
            WHEN '8-14 days' THEN 3
            ELSE 4
         END;


-- name: q05_stage_durations
-- question: Q3. Where in the journey does time go? Average stage durations, late vs on-time
-- (only orders with valid timestamps: stage_valid = 1)
SELECT
    CASE WHEN is_late = 1 THEN 'Late' ELSE 'On time' END AS delivery_status,
    COUNT(*)                                             AS orders,
    ROUND(AVG(approval_days), 2)                         AS avg_approval_days,
    ROUND(AVG(seller_handling_days), 2)                  AS avg_seller_handling_days,
    ROUND(AVG(carrier_transit_days), 2)                  AS avg_carrier_transit_days,
    ROUND(AVG(actual_lead_days), 2)                      AS avg_actual_lead_days,
    ROUND(AVG(promised_lead_days), 2)                    AS avg_promised_lead_days
FROM analysis_orders
WHERE stage_valid = 1
GROUP BY delivery_status
ORDER BY delivery_status;


-- name: q06_late_cause_split
-- question: Q3. Is the delay mainly seller handling or carrier transit?
-- Each late order is put in one group: did any seller in the order miss its
-- handover deadline (SLA breach), or did the seller hand over on time and the
-- parcel still arrived late?
WITH order_sla AS (
    SELECT order_id, MAX(sla_breach) AS any_sla_breach
    FROM analysis_order_sellers
    GROUP BY order_id
)
SELECT
    CASE WHEN s.any_sla_breach = 1
         THEN 'Seller missed handover deadline'
         ELSE 'Seller on time, late after handover'
    END                                                  AS late_cause,
    COUNT(*)                                             AS late_orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)   AS share_of_late_orders_pct,
    ROUND(AVG(a.seller_handling_days), 2)                AS avg_seller_handling_days,
    ROUND(AVG(a.carrier_transit_days), 2)                AS avg_carrier_transit_days,
    ROUND(AVG(a.delay_days), 2)                          AS avg_delay_days
FROM analysis_orders a
JOIN order_sla s ON s.order_id = a.order_id
WHERE a.is_late = 1
  AND a.stage_valid = 1
GROUP BY late_cause
ORDER BY late_orders DESC;


-- name: q07_customer_state_late
-- question: Q4. Which customer states have the highest late rates (min 300 orders)?
SELECT
    customer_state,
    COUNT(*)                                             AS orders,
    SUM(is_late)                                         AS late_orders,
    ROUND(100.0 * AVG(is_late), 2)                       AS late_rate_pct,
    ROUND(100.0 * SUM(is_late) / (SELECT SUM(is_late) FROM analysis_orders), 2)
                                                         AS share_of_all_late_pct,
    ROUND(AVG(CASE WHEN is_late = 1 THEN delay_days END), 2)  AS avg_delay_days_late_orders
FROM analysis_orders
GROUP BY customer_state
HAVING COUNT(*) >= 300
ORDER BY late_rate_pct DESC;


-- name: q08_route_late
-- question: Q4. Which seller-to-customer routes have the highest late rates and the most late orders (min 300 order-seller pairs)?
SELECT
    route,
    COUNT(*)                                             AS order_seller_pairs,
    SUM(is_late)                                         AS late_pairs,
    ROUND(100.0 * AVG(is_late), 2)                       AS late_rate_pct,
    RANK() OVER (ORDER BY AVG(is_late) DESC)             AS rank_by_late_rate,
    RANK() OVER (ORDER BY SUM(is_late) DESC)             AS rank_by_late_count
FROM analysis_order_sellers
GROUP BY route
HAVING COUNT(*) >= 300
ORDER BY late_pairs DESC;


-- name: q09_seller_concentration
-- question: Q5. What share of late orders comes from the top 10% / 20% of sellers (ranked by number of late orders)?
WITH seller_late AS (
    SELECT seller_id,
           COUNT(*)     AS pairs,
           SUM(is_late) AS late_pairs
    FROM analysis_order_sellers
    GROUP BY seller_id
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY late_pairs DESC, pairs DESC) AS seller_rank,
           COUNT(*)        OVER ()                                  AS n_sellers,
           SUM(late_pairs) OVER ()                                  AS total_late,
           SUM(pairs)      OVER ()                                  AS total_pairs
    FROM seller_late
),
segments AS (
    SELECT 'Top 10% of sellers' AS segment, 1 AS sort_order, 0.10 AS cutoff
    UNION ALL SELECT 'Top 20% of sellers', 2, 0.20
    UNION ALL SELECT 'All sellers',        3, 1.00
)
SELECT
    g.segment,
    COUNT(*)                                             AS sellers,
    SUM(r.late_pairs)                                    AS late_orders,
    ROUND(100.0 * SUM(r.late_pairs) / MAX(r.total_late), 2)   AS share_of_late_orders_pct,
    ROUND(100.0 * SUM(r.pairs) / MAX(r.total_pairs), 2)       AS share_of_order_volume_pct,
    ROUND(100.0 * SUM(r.late_pairs) / SUM(r.pairs), 2)        AS late_rate_pct
FROM segments g
JOIN ranked r ON r.seller_rank <= g.cutoff * r.n_sellers
GROUP BY g.segment, g.sort_order
ORDER BY g.sort_order;


-- name: q10_sla_breach_vs_late
-- question: Q5. How does a seller SLA breach relate to lateness and reviews?
SELECT
    CASE WHEN sla_breach = 1 THEN 'SLA breached' ELSE 'SLA met' END AS seller_sla,
    COUNT(*)                                             AS order_seller_pairs,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)   AS share_of_pairs_pct,
    ROUND(100.0 * AVG(is_late), 2)                       AS late_rate_pct,
    ROUND(100.0 * AVG(is_bad_review), 2)                 AS bad_review_pct_all_pairs
FROM analysis_order_sellers
WHERE sla_breach IS NOT NULL
GROUP BY seller_sla
ORDER BY seller_sla;


-- name: q11_seller_breach_band
-- question: Q5. Do sellers who breach SLA more often have higher late rates?
-- (sellers with at least 30 orders, grouped by their own SLA breach rate)
WITH seller_stats AS (
    SELECT seller_id,
           COUNT(*)        AS pairs,
           AVG(sla_breach) AS breach_rate,
           AVG(is_late)    AS late_rate
    FROM analysis_order_sellers
    WHERE sla_breach IS NOT NULL
    GROUP BY seller_id
    HAVING COUNT(*) >= 30
)
SELECT
    CASE WHEN breach_rate = 0     THEN '1. 0%'
         WHEN breach_rate <= 0.05 THEN '2. 0-5%'
         WHEN breach_rate <= 0.15 THEN '3. 5-15%'
         ELSE                          '4. over 15%'
    END                                                  AS seller_breach_band,
    COUNT(*)                                             AS sellers,
    SUM(pairs)                                           AS order_seller_pairs,
    ROUND(100.0 * SUM(late_rate * pairs) / SUM(pairs), 2) AS late_rate_pct
FROM seller_stats
GROUP BY seller_breach_band
ORDER BY seller_breach_band;


-- name: q12_category_late
-- question: Q6. Which product categories have the highest late rates (min 300 orders)?
-- Category = category of the most expensive item in the order.
SELECT
    main_category,
    COUNT(*)                                             AS orders,
    SUM(is_late)                                         AS late_orders,
    ROUND(100.0 * AVG(is_late), 2)                       AS late_rate_pct,
    ROUND(AVG(freight_value), 2)                         AS avg_freight_brl
FROM analysis_orders
GROUP BY main_category
HAVING COUNT(*) >= 300
ORDER BY late_rate_pct DESC;


-- name: q13_promise_accuracy_distribution
-- question: Q7. How accurate is the delivery promise? Distribution of (estimated - actual) days.
SELECT
    CASE WHEN -delay_days < 0   THEN '1. Late (after estimate)'
         WHEN -delay_days <= 6  THEN '2. 0-6 days early'
         WHEN -delay_days <= 13 THEN '3. 7-13 days early'
         WHEN -delay_days <= 20 THEN '4. 14-20 days early'
         ELSE                        '5. 21+ days early'
    END                                                  AS days_before_estimate,
    COUNT(*)                                             AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)   AS share_pct
FROM analysis_orders
GROUP BY days_before_estimate
ORDER BY days_before_estimate;


-- name: q14_promise_by_state
-- question: Q7. Is Olist over-promising in some states and padding too much in others?
-- days_early = estimated date - delivered date (positive = arrived before the promise)
SELECT
    customer_state,
    COUNT(*)                                             AS orders,
    ROUND(AVG(promised_lead_days), 1)                    AS avg_promised_days,
    ROUND(AVG(actual_lead_days), 1)                      AS avg_actual_days,
    ROUND(AVG(-delay_days), 1)                           AS avg_days_early,
    ROUND(100.0 * AVG(is_late), 2)                       AS late_rate_pct
FROM analysis_orders
GROUP BY customer_state
HAVING COUNT(*) >= 300
ORDER BY avg_days_early;


-- name: q15_repeat_purchase
-- question: Q8. Do customers whose first order was late come back less often?
-- Repeat = the same customer_unique_id has another delivered order on a later date.
-- Directional only: very few Olist customers ever buy twice.
WITH ranked AS (
    SELECT customer_unique_id,
           is_late,
           date(order_purchase_timestamp) AS purchase_date,
           ROW_NUMBER() OVER (PARTITION BY customer_unique_id
                              ORDER BY order_purchase_timestamp, order_id) AS order_seq,
           MAX(date(order_purchase_timestamp)) OVER (PARTITION BY customer_unique_id) AS last_purchase_date
    FROM analysis_orders
),
first_orders AS (
    SELECT customer_unique_id,
           is_late AS first_order_late,
           CASE WHEN last_purchase_date > purchase_date THEN 1 ELSE 0 END AS is_repeat
    FROM ranked
    WHERE order_seq = 1
)
SELECT
    CASE WHEN first_order_late = 1 THEN 'First order late' ELSE 'First order on time' END AS first_order,
    COUNT(*)                                             AS customers,
    SUM(is_repeat)                                       AS repeat_customers,
    ROUND(100.0 * AVG(is_repeat), 2)                     AS repeat_rate_pct
FROM first_orders
GROUP BY first_order
UNION ALL
SELECT 'All customers', COUNT(*), SUM(is_repeat), ROUND(100.0 * AVG(is_repeat), 2)
FROM first_orders;
