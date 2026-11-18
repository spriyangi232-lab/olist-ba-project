# Business Requirements Document: Delivery Performance Monitoring

| | |
|---|---|
| **Project** | Delivery Delay Root-Cause Analysis & Customer Satisfaction Improvement (Olist E-Commerce) |
| **Author** | Priyangi Singh Chouhan |
| **Version** | 1.0 |
| **Date** | 18 November 2026 |
| **Status** | Draft for stakeholder review |
| **Data source** | Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0), orders purchased Jan 2017 to Aug 2018 |

All figures in this document come from `results/metrics.json`, which the project scripts generate. Where I propose a target rather than report a fact, I say so.

---

## 1. Background

Olist is a Brazilian marketplace that connects small sellers to large online stores. A customer orders on the platform, the seller packs the item and hands it to a carrier, and the carrier delivers it. At checkout the platform shows the customer an estimated delivery date. After delivery the customer is asked to write a review of 1 to 5 stars.

I analysed 96,203 delivered orders purchased between January 2017 and August 2018. Of these, 6,531 (6.79%) arrived after the estimated date. Late orders receive an average review of 2.27 stars against 4.29 for on-time orders, and 62.42% of late orders get a 1-2 star review compared with 9.25% of on-time orders.

## 2. Problem statement

Late deliveries are the strongest driver of bad reviews on the platform. A late order is 6.7 times as likely to get a 1-2 star review as an on-time order. Bad reviews lower seller ratings, which reduces conversion for those sellers, and customers whose first order arrived late come back less often (1.62% repeat rate against 2.19%, a directional result because few customers buy twice).

Today the business has no single view of where delays come from. The analysis shows that:

- 72.16% of late orders had a seller who handed over the parcel on time, so most of the delay happens in carrier transit (19.88 extra days on late orders, against 2.93 extra days of seller handling).
- Lateness is concentrated in time (Feb-Mar 2018 produced 34.51% of late orders from 14.09% of volume), in place (the São Paulo to Rio de Janeiro route alone produced 1,157 late orders) and in a group of sellers (125 sellers create 1,061 more late orders than an average seller would).
- The delivery estimate is padded for most customers (78.87% of orders arrive 7 or more days early) but not enough for some North-East states (Alagoas: 21.46% late).

**Problem to solve:** the business needs a way to see delivery performance by stage, seller, route and region every week, so that each team can act on the part of the delay it controls.

## 3. Business objectives

The baselines are measured. The targets are my proposals, based on the impact estimate in the case study (conservative 5.94% to expected 5.26% late rate), and need to be agreed with the owners.

| ID | Objective (SMART) | Baseline | Proposed target | Owner |
|---|---|---|---|---|
| BO-1 | Raise the platform on-time delivery rate within 6 months of go-live, measured monthly | 93.21% | 94.5% | Head of Operations |
| BO-2 | Reduce the share of 1-2 star reviews within 6 months of go-live, measured monthly | 12.8% | 12.2% | Customer Experience Lead |
| BO-3 | Reduce the seller SLA breach rate (handover after the shipping limit date) within 6 months | 8.86% | 7.0% | Seller Operations Manager |
| BO-4 | Bring the late rate of the 5 worst routes to the platform average within 9 months | SP→RJ 14.01%, SP→BA 12.71% (see FR-07) | Platform average | Logistics Partner Manager |
| BO-5 | Launch the Delivery Performance Monitoring dashboard with weekly use by Operations, Seller Operations and Customer Experience within 60 days | No dashboard | Live, used weekly by 3 teams | BI Lead |

## 4. Scope

**In scope**

- A Delivery Performance Monitoring dashboard covering on-time rate, delay days, journey stages, seller SLA breach, routes, regions, categories and review impact.
- A weekly seller scorecard ranked by excess late orders.
- A route watchlist for carrier performance reviews.
- An estimate-accuracy view by customer state to support re-setting delivery promises.
- Data-quality checks on order timestamps.

**Out of scope**

- Changing carrier contracts or pricing (this project gives the evidence; the commercial negotiation is separate).
- Building a new delivery-date prediction model. The requirement is for rule-based estimate adjustment by state and route.
- Real-time parcel tracking integration with carriers.
- Canceled and undelivered orders (2,963 orders), which need a separate fulfilment-failure study.
- Customer compensation policy design (I recommend it, but the policy belongs to Customer Experience and Finance).

## 5. Stakeholders

| Stakeholder | Role in this project | Main interest | What they need from the solution |
|---|---|---|---|
| Head of Operations | Sponsor | Lower late rate and cost of delays | Platform KPIs and trend, impact of actions |
| Customer Experience (CX) Lead | Key user | Fewer bad reviews and complaints | Link between delay and review score, at-risk orders |
| Seller Operations Manager | Key user | Seller performance and seller retention | Seller scorecard, SLA breach list |
| Logistics Partner Manager | Key user | Carrier performance on each route | Route watchlist, transit times |
| Product Manager, Checkout & Delivery Promise | Contributor | Accurate delivery estimate shown to customers | Estimate accuracy by state and route |
| BI / Data Engineering Lead | Builder | Reliable data pipeline and definitions | Clear requirements and KPI definitions |
| Category Managers | Informed | Category growth | Category late rates (low priority, category is not a main driver) |
| Finance | Informed | Cost of compensation and carrier penalties | Impact estimate and assumptions |
| Sellers (external) | Affected | Fair ratings, clear rules | Their own scorecard and deadlines |
| Carriers (external) | Affected | Clear service levels | Route-level performance data |
| Customers (external) | Affected | Parcel arrives when promised | Accurate estimate, early warning of delay |

### 5.1 Power-interest grid

| | **Low interest** | **High interest** |
|---|---|---|
| **High power** | **Keep satisfied:** Finance, Carriers | **Manage closely:** Head of Operations, Logistics Partner Manager, Seller Operations Manager |
| **Low power** | **Monitor:** Category Managers, Customers | **Keep informed:** CX Lead, Product Manager, BI Lead, Sellers |

How I would engage each group:

- **Manage closely:** fortnightly review of findings and progress; they sign off the requirements.
- **Keep satisfied:** short monthly summary; Finance reviews the impact assumptions before targets are agreed.
- **Keep informed:** weekly working sessions with CX, Product and BI during the build; sellers get a notice before scorecards go live.
- **Monitor:** release notes and the dashboard link.

### 5.2 RACI

R = Responsible, A = Accountable, C = Consulted, I = Informed.

| Activity | Head of Ops | Business Analyst (me) | BI Lead | Seller Ops | Logistics Partner Mgr | CX Lead | Product Mgr |
|---|---|---|---|---|---|---|---|
| Define problem and KPIs | A | R | C | C | C | C | C |
| Data analysis and root cause | I | R/A | C | I | I | I | I |
| Write and sign off requirements (this BRD) | A | R | C | C | C | C | C |
| Build data pipeline and dashboard | I | C | R/A | I | I | I | I |
| User acceptance testing | A | R | C | R | R | R | C |
| Seller scorecard and SLA follow-up | I | C | I | R/A | I | I | I |
| Route reviews with carriers | I | C | I | I | R/A | I | I |
| Re-set delivery estimates by state/route | C | C | C | I | C | I | R/A |
| Track benefits after go-live | A | R | C | I | I | C | I |

## 6. Functional requirements

Priority uses MoSCoW: M = Must, S = Should, C = Could.

| ID | Requirement | Priority | Source finding |
|---|---|---|---|
| FR-01 | The system shall load delivered orders daily and classify each order as late when the delivered date is after the estimated date (dates compared without time). | M | KPI definition |
| FR-02 | The dashboard shall show four KPI tiles: on-time rate, average delay days of late orders, 1-2 star review share, seller SLA breach rate, each with the change against the previous period. | M | Section 2 |
| FR-03 | The dashboard shall show the monthly and weekly on-time rate trend, with a reference line for the period average. | M | Feb-Mar 2018 spike |
| FR-04 | Users shall be able to filter all views by purchase period, customer state, seller state, route, seller and product category. | M | - |
| FR-05 | The dashboard shall split each order's lead time into approval, seller handling and carrier transit, and compare late with on-time orders. | M | Transit is the main delay |
| FR-06 | The system shall produce a weekly seller scorecard listing, for every seller with at least 30 orders in the period: orders, late orders, late rate, SLA breach rate and excess late orders (late orders minus orders × platform late rate), sorted by excess late orders. | M | 125 sellers, 1,061 excess late orders |
| FR-07 | The system shall produce a route watchlist (seller state → customer state, minimum 300 orders) with late orders, late rate and excess late orders, highlighting routes above the platform rate. | M | SP→RJ 1,157 late orders |
| FR-08 | The system shall flag every order-seller pair where the parcel was handed to the carrier after the shipping limit date (SLA breach). | M | Breach late rate 20.98% vs 5.32% |
| FR-09 | The system shall send an alert to the seller and Seller Operations 24 hours before the shipping limit date when the order has not been handed over. | S | SLA breach |
| FR-10 | The dashboard shall show estimate accuracy by customer state: average promised days, actual days, days delivered early and late rate. | M | AL: 8.6 days buffer, 21.46% late |
| FR-11 | The dashboard shall show 1-2 star review share by delay band (on time, 1-3, 4-7, 8-14, 15+ days late). | S | 32.14% bad reviews even at 1-3 days late |
| FR-12 | The system shall flag orders at risk of being late (not yet delivered and carrier transit already longer than the route's 90th percentile) so CX can contact the customer. | S | Proactive communication |
| FR-13 | The system shall publish a data-quality report with each refresh: missing timestamps, carrier date before approval, carrier date before purchase, and number of orders excluded from stage analysis. | M | 1,384 orders with timestamp issues |
| FR-14 | Users shall be able to export any table view to CSV. | S | - |
| FR-15 | The dashboard shall show late rate by product category (minimum 300 orders). | C | Category not a main driver |
| FR-16 | An external seller shall see only their own scorecard and orders. | S | - |

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Data shall refresh daily by 08:00 local time. |
| NFR-02 | Each dashboard page shall load in under 5 seconds for 12 months of data. |
| NFR-03 | KPI values shall reconcile with a direct SQL count within ±0.1 percentage points. |
| NFR-04 | Access shall be role-based; seller-level data is visible only to internal teams and to the seller concerned. |
| NFR-05 | Customer personal data (names, addresses) shall not be stored in the dashboard data model. Customers are identified by ID and state only. |
| NFR-06 | Every KPI shall have a written definition available from the dashboard (tooltip or glossary page). |
| NFR-07 | The dashboard shall be readable on a laptop screen and usable on a tablet. |
| NFR-08 | The pipeline shall log each run, row counts loaded and rows excluded, and keep logs for 90 days. |
| NFR-09 | The data model shall handle at least 3 times the current order volume without redesign. |

## 8. Assumptions

- A1. `order_estimated_delivery_date` is the date shown to the customer at checkout.
- A2. `order_delivered_carrier_date` is the date the carrier collected the parcel. 1,350 orders show this before payment approval, which suggests the field is sometimes entered incorrectly.
- A3. `shipping_limit_date` in the order items is the seller's handover deadline.
- A4. The latest review per order reflects the customer's final view of the order.
- A5. Patterns from Jan 2017 to Aug 2018 still apply to current operations. This needs to be checked against recent data before targets are fixed.

## 9. Constraints

- C1. The data does not include carrier names, so carrier-level performance can only be inferred through routes.
- C2. The data has no cost information (shipping cost to Olist, compensation paid), so the impact estimate is in orders and reviews, not money.
- C3. Only 2.15% of customers buy again, which limits any conclusion about repeat purchase.
- C4. The analysis covers delivered orders only.

## 10. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Sellers see the scorecard as unfair because some delays are caused by carriers | Medium | High | Show SLA breach and carrier transit separately; rank on excess late orders, not raw counts |
| R-02 | Carrier date field is unreliable for some orders | Medium | Medium | FR-13 data-quality report; exclude impossible rows from stage analysis |
| R-03 | Lengthening estimates in some states lowers conversion at checkout | Medium | High | Product Manager runs an A/B test before full rollout |
| R-04 | Peak periods (Black Friday, Feb-Mar) overwhelm carriers again | High | High | Capacity plan agreed with carriers 6 weeks before known peaks |
| R-05 | Dashboard built but not used | Medium | Medium | Named owner per view; weekly operations review uses the dashboard as its agenda |
| R-06 | Historical data (2017-2018) does not reflect current operations | Medium | Medium | Re-run the analysis on the latest 12 months before fixing targets (A5) |

## 11. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | For the Jan 2017 - Aug 2018 test data, the dashboard shows on-time rate 93.21%, average delay of late orders 10.62 days, 1-2 star review share 12.8% and seller SLA breach rate 8.86%. |
| AC-02 | Filtering to customer state AL shows a late rate of 21.46%. |
| AC-03 | The seller scorecard lists 625 sellers with 30 or more orders, and the top 125 by excess late orders add up to 1,061 excess late orders. |
| AC-04 | The route watchlist shows SP → RJ with 1,157 late orders and a 14.01% late rate. |
| AC-05 | The data-quality report shows 1,384 orders excluded from stage analysis. |
| AC-06 | Each KPI tile has a definition matching section 12. |
| AC-07 | Seller Operations, Logistics and CX each confirm in UAT that they can answer their top three weekly questions from the dashboard without help. |

## 12. KPI definitions

| KPI | Definition | Formula | Baseline | Owner | Frequency |
|---|---|---|---|---|---|
| On-time rate | Share of delivered orders that arrived on or before the estimated date | 1 − late orders ÷ delivered orders | 93.21% | Head of Operations | Weekly |
| Late rate | Share of delivered orders delivered after the estimated date | late orders ÷ delivered orders | 6.79% | Head of Operations | Weekly |
| Average delay days (late orders) | Average days between estimated and delivered date for late orders | AVG(delivered date − estimated date) where late | 10.62 days | Logistics Partner Manager | Weekly |
| 1-2 star review share | Share of reviewed orders whose latest review is 1 or 2 stars | bad reviews ÷ reviewed orders | 12.8% | CX Lead | Weekly |
| Seller SLA breach rate | Share of order-seller pairs handed to the carrier after the shipping limit date | breaches ÷ pairs with a carrier date | 8.86% | Seller Operations Manager | Weekly |
| Excess late orders (seller or route) | Late orders above what the platform late rate would predict | late orders − orders × platform late rate | 1,061 for the worst 125 sellers | Seller Ops / Logistics | Weekly |
| Seller handling days | Days from payment approval to carrier handover | carrier date − approval date | 2.62 on-time / 5.55 late | Seller Operations Manager | Monthly |
| Carrier transit days | Days from carrier handover to delivery | delivered date − carrier date | 8.01 on-time / 27.89 late | Logistics Partner Manager | Monthly |
| Estimate buffer | Average days an order arrives before its estimated date | AVG(estimated date − delivered date) | 8.6 (AL) to 14.3 (MT) by state | Product Manager | Monthly |

**Definitions used throughout:** analysis population = orders with status "delivered" and a delivery date, purchased in a month with at least 500 orders (Jan 2017 to Aug 2018); late = delivered date after estimated date, comparing dates only; bad review = latest review score 1-2.
