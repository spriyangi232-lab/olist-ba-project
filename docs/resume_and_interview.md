# Resume Bullets and Interview Preparation

| | |
|---|---|
| **Project** | Delivery Delay Root-Cause Analysis & Customer Satisfaction Improvement (Olist E-Commerce) |
| **Author** | Priyangi Singh Chouhan |
| **Version** | 1.0 |
| **Date** | 18 November 2026 |
| **Status** | Personal preparation notes |

Every number here comes from `results/metrics.json`. If I re-run the analysis, I re-check this file with `src/07_check_numbers.py`.

---

## 1. Resume bullets

**Delivery Delay Root-Cause Analysis | Olist E-Commerce (public dataset) | SQL, Python, Power BI, BRD**

- Analysed 96,203 marketplace orders with 15 SQL queries (CTEs, window functions) and Python to find why 6.79% of deliveries were late; showed late orders were 6.7× as likely to get a 1-2 star review and that 72.16% of late orders had a seller who shipped on time, putting most of the delay in carrier transit.
- Wrote a BRD (16 functional requirements, RACI, power-interest grid, SMART objectives) and AS-IS / TO-BE swimlane process maps; identified 125 sellers creating 1,061 excess late orders and recommended a seller scorecard, route service levels and re-set delivery estimates.
- Estimated that fixing the worst sellers and 5 worst routes would avoid 752-1,413 late orders and 391-734 bad reviews, and built an offline Plotly dashboard and Power BI guide to track on-time rate, delay days, bad-review share and seller SLA breach.

Shorter version for a one-page resume (pick one):

- Diagnosed why 6.79% of 96,203 e-commerce orders arrived late using SQL and Python; wrote a BRD and process maps and recommended actions estimated to avoid 752-1,413 late orders and 391-734 bad reviews, tracked in a KPI dashboard.

## 2. "Tell me about this project" (about 60 seconds)

> I picked a problem every marketplace has: late deliveries leading to bad reviews. I used Olist's public data, about 96,000 delivered orders from Brazil.
>
> I started like a BA would: I defined the problem, the stakeholders and what "late" means, which is delivered after the date promised at checkout. Then I used SQL to answer eight business questions.
>
> Three things stood out. First, 6.79% of orders were late, and a late order was 6.7 times as likely to get a one- or two-star review. Second, most of the delay was in carrier transit, not with sellers: 72% of late orders had a seller who shipped on time. Third, the problem was concentrated in two peak months, in routes like São Paulo to Rio, and in about 125 sellers.
>
> I turned that into a BRD with requirements for a monitoring dashboard, AS-IS and TO-BE process maps, and five prioritised recommendations. My estimate is that fixing the worst sellers and routes would avoid 752 to 1,413 late orders and 391 to 734 bad reviews over the period. I also built the dashboard and a guide to rebuild it in Power BI.

## 3. Likely interview questions with my answers

### Q1. Why did you choose this problem?

Delivery is where e-commerce promises are kept or broken, and it shows up directly in reviews and repeat purchases. It also involves several parties (customer, platform, seller, carrier), which makes it a good BA problem: the answer is not just a number, it is who should change what. Olist's data has timestamps for each stage, so I could trace where the time goes.

### Q2. How did you define "late", and why that way?

An order is late when the date it was delivered is after the estimated delivery date shown at checkout. I compare dates, not timestamps, because the estimated date has no time part. If I compared timestamps, an order delivered at 3 pm on the promised day would count as late, which is not how a customer sees it. I also limited the analysis to delivered orders with a delivery date, and to months with at least 500 orders, which keeps January 2017 to August 2018.

### Q3. Why these KPIs?

Each KPI maps to one owner and one part of the process, so nobody gets a number they cannot act on:

- **On-time rate** is the outcome the business cares about (Head of Operations).
- **Average delay days** of late orders shows how bad a late order is, and reviews get much worse after a week (Logistics).
- **1-2 star review share** is the customer impact (Customer Experience).
- **Seller SLA breach rate** is the part the seller controls (Seller Operations).

I added **excess late orders** for the seller and route scorecards because raw late counts just point at the biggest sellers.

### Q4. Why rank sellers by "excess late orders" instead of late-order count?

When I ranked sellers by late-order count, the top 20% produced 87.42% of late orders, which looks like a strong finding. But they also handled 78.65% of all orders, and their late rate was close to average. They were simply the biggest sellers. Excess late orders = actual late orders minus what the platform late rate would predict for that seller's volume. It finds sellers who are both large and worse than average, which is fairer to sellers and more useful to Seller Operations.

### Q5. What data limitations did you face?

- The data is from 2017-2018, so I would re-run it on recent data before setting targets.
- There are no carrier names, so I used seller-state to customer-state routes as a proxy for carrier performance.
- 1,384 orders (1.44%) had impossible timestamps, mostly a carrier handover recorded before payment approval. I flagged them and left them out of the stage analysis only.
- There is no cost data, so my impact estimate is in orders and reviews, not money.
- Only 2.15% of customers buy twice, so the repeat-purchase result is directional.

### Q6. How did you estimate the impact, and how confident are you?

I took the worst 125 sellers and the 5 worst routes and asked: if their late rate came down to the platform average, how many late orders would disappear? I fixed sellers first and then routes so no order is counted twice. Each avoided late order then has the on-time bad-review rate instead of the late one, which gives the reviews prevented. I show a range: conservative (closing half the gap) gives 752 late orders and 391 bad reviews; expected (closing the full gap) gives 1,413 and 734. It is a what-if estimate, not a forecast, and I would validate it with a pilot.

### Q7. How would you validate your recommendations with stakeholders?

1. Walk Seller Operations and Logistics through the evidence for their area and ask what I am missing. For example, the carrier team may know about a strike or a hub closure behind the Feb-Mar 2018 spike.
2. Pilot before rollout. Send handover alerts to half of the flagged sellers and compare their breach rate with the other half after 4 to 6 weeks. Do the same with an A/B test for the new delivery estimates in the low-buffer states.
3. Agree targets with each owner using the BRD, then track them on the dashboard and review the benefits at 90 days.

### Q8. Which stakeholder would push back most, and how would you handle it?

Sellers and Seller Operations, because a scorecard can feel like blame when most delay is in carrier transit. I would show seller handover and carrier transit separately, rank on excess late orders rather than raw counts, give sellers a warning before the deadline rather than only a score afterwards, and let them see their own data first.

### Q9. What would you do with more time?

- Get carrier names and cost data, so I could compare carriers on the same route and put a money value on each late order.
- Look into the Feb-Mar 2018 spike with the operations team to find the cause.
- Build a simple rule-based at-risk flag (transit already longer than the route's usual time) and test how early it catches late orders.
- Re-run everything on recent data and automate the refresh.

### Q10. How does this apply to an Indian company like Flipkart, Meesho or Amazon India?

The structure is the same: many small sellers, long and uneven routes (metro hubs to Tier 2/3 towns and the North-East, like São Paulo to Brazil's North-East), and big sale peaks such as Big Billion Days and the Great Indian Festival. I would run the same analysis by pincode cluster instead of state, use the excess-late-order scorecard for sellers, and agree a capacity plan with logistics partners before each sale. For India I would add return-to-origin (RTO) rate and failed-delivery attempts, because cash-on-delivery orders behave differently.

### Q11. SQL: walk me through one of your queries.

This is the seller concentration query (`q09_seller_concentration` in `sql/analysis.sql`), simplified:

```sql
WITH seller_late AS (                      -- one row per seller
    SELECT seller_id,
           COUNT(*)     AS pairs,          -- orders handled
           SUM(is_late) AS late_pairs      -- late orders
    FROM analysis_order_sellers
    GROUP BY seller_id
),
ranked AS (                                -- rank sellers, add platform totals
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY late_pairs DESC, pairs DESC) AS seller_rank,
           COUNT(*)        OVER () AS n_sellers,
           SUM(late_pairs) OVER () AS total_late
    FROM seller_late
)
SELECT COUNT(*)                                          AS sellers,
       ROUND(100.0 * SUM(late_pairs) / MAX(total_late), 2) AS share_of_late_orders_pct
FROM ranked
WHERE seller_rank <= 0.20 * n_sellers;     -- top 20% of sellers
```

- The first CTE aggregates to one row per seller.
- In the second, `ROW_NUMBER()` ranks sellers by late orders. `COUNT(*) OVER ()` and `SUM(...) OVER ()` with an empty window put the platform totals on every row, so I can divide without a second query.
- The final filter keeps the top 20%. I use `100.0` rather than `100` so SQLite does decimal division, not integer division.
- The answer was 87.42% of late orders, and the same query showed those sellers had 78.65% of the volume. That is what made me change the ranking (Q4).

Follow-up they may ask: **WHERE vs HAVING.** `WHERE` filters rows before grouping; `HAVING` filters groups after aggregation. In the state query I use `HAVING COUNT(*) >= 300` because the 300-order threshold applies to each state's total, which only exists after `GROUP BY`.

### Q12. What did you learn, or what would you do differently?

The first ranking can mislead. My first seller result looked like a classic 80/20 story, and it would have pointed Seller Operations at the biggest, mostly average sellers. Checking the denominator (share of volume, not just share of late orders) changed the recommendation. I also learned to write definitions down before analysing. Deciding that "late" compares dates, and that each order keeps its latest review, made every later number consistent and easy to explain.

## 4. Numbers to remember

| Number | What it is |
|---|---|
| 96,203 | Delivered orders analysed (Jan 2017 - Aug 2018) |
| 6.79% | Late rate (93.21% on time) |
| 10.62 days | Average delay of late orders |
| 6.7× | Bad-review likelihood, late vs on time (62.42% vs 9.25%) |
| 72.16% | Late orders where the seller handed over on time |
| 19.88 days | Extra carrier transit time on late orders |
| 34.51% | Share of late orders from Feb-Mar 2018 (14.09% of volume) |
| 1,157 | Late orders on São Paulo → Rio de Janeiro |
| 125 / 1,061 | Worst sellers / their excess late orders |
| 752-1,413 | Late orders avoidable (conservative-expected) |
| 391-734 | 1-2 star reviews preventable |
