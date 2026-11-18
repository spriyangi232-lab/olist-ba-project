# Process Flows: Order Fulfilment AS-IS and TO-BE

| | |
|---|---|
| **Project** | Delivery Delay Root-Cause Analysis & Customer Satisfaction Improvement (Olist E-Commerce) |
| **Author** | Priyangi Singh Chouhan |
| **Version** | 1.0 |
| **Date** | 18 November 2026 |
| **Status** | Draft for stakeholder review |

All figures come from `results/metrics.json`. The diagrams are written in Mermaid; the sources are in `docs/diagrams/*.mmd` and the rendered images are `docs/diagrams/as_is.png` and `docs/diagrams/to_be.png`.

---

## 1. How to read the diagrams

- There are four lanes: **Customer**, **Platform (Olist)**, **Seller** and **Carrier**.
- Solid arrows are steps inside one lane. Dotted arrows are hand-offs between lanes.
- On the AS-IS flow, orange boxes are steps with a pain point (PAIN 1-6).
- On the TO-BE flow, blue-filled boxes carry an improvement (FIX 1-5) and blue-outlined boxes are new or changed steps.

## 2. AS-IS order fulfilment

![AS-IS order fulfilment](diagrams/as_is.png)

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 30, "rankSpacing": 45, "wrappingWidth": 340}, "themeVariables": {"fontSize": "15px"}}}%%
flowchart TB
    subgraph CUS["CUSTOMER"]
        direction LR
        C1["Places order<br/>and pays"] --> C2["Sees one estimated<br/>delivery date"] --> C3["Waits with no update<br/>if parcel is delayed<br/><b>PAIN 4: no alert before<br/>the date is missed</b>"] --> C4["Receives parcel"] --> C5["Writes review<br/><b>PAIN 5: 62.42% of late orders<br/>get a 1-2 star review</b>"]
    end
    subgraph PLA["PLATFORM (OLIST)"]
        direction LR
        P1["Approves payment"] --> P2["Sets estimate with the<br/>same logic for every route<br/><b>PAIN 1: too tight for the<br/>North-East (AL 21.46% late)</b>"] --> P3["Monthly review of<br/>complaints and ratings<br/><b>PAIN 6: no seller or route<br/>scorecard; issues found late</b>"]
    end
    subgraph SEL["SELLER"]
        direction LR
        S1["Receives order"] --> S2["Picks and packs"] --> S3["Hands parcel to carrier<br/>by shipping limit date<br/><b>PAIN 2: 8.86% miss the deadline;<br/>their late rate is 20.98%</b>"]
    end
    subgraph CAR["CARRIER"]
        direction LR
        K1["Collects parcel"] --> K2["Line-haul transit<br/>between states<br/><b>PAIN 3: late orders spend 27.89<br/>days in transit vs 8.01 on time</b>"] --> K3["Last-mile delivery"]
    end

    CUS ~~~ PLA ~~~ SEL ~~~ CAR
    C1 -.-> P1
    P2 -.-> C2
    P1 -.-> S1
    S3 -.-> K1
    K3 -.-> C4
    C5 -.-> P3

    classDef pain fill:#fde3d8,stroke:#eb6834,stroke-width:2px,color:#0b0b0b
    classDef step fill:#ffffff,stroke:#898781,color:#0b0b0b
    class C3,C5,P2,P3,S3,K2 pain
    class C1,C2,C4,P1,S1,S2,K1,K3 step
    style CUS fill:#f9f9f7,stroke:#c3c2b7
    style PLA fill:#f9f9f7,stroke:#c3c2b7
    style SEL fill:#f9f9f7,stroke:#c3c2b7
    style CAR fill:#f9f9f7,stroke:#c3c2b7
```

### Pain points

| ID | Step | Pain point | Evidence |
|---|---|---|---|
| PAIN 1 | Platform sets the estimate | The same logic is used for every route, so the promise is too tight for the North-East and too loose elsewhere | AL: 8.6 days buffer and 21.46% late; 78.87% of all orders arrive 7+ days early |
| PAIN 2 | Seller hands over to the carrier | Some sellers miss the shipping limit date | 8.86% of handovers are late; those orders are late 20.98% of the time vs 5.32% |
| PAIN 3 | Carrier line-haul transit | Long and uneven transit between states | Late orders spend 27.89 days in transit vs 8.01 for on-time orders |
| PAIN 4 | Customer waits | No warning before the promised date is missed | No at-risk flag exists in the current process |
| PAIN 5 | Customer writes review | A broken promise turns into a bad review | 62.42% of late orders get 1-2 stars vs 9.25% of on-time orders |
| PAIN 6 | Platform reviews performance | Only a monthly look at complaints; no seller or route view | 125 sellers create 1,061 excess late orders without being flagged |

## 3. TO-BE order fulfilment

![TO-BE order fulfilment](diagrams/to_be.png)

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 30, "rankSpacing": 45, "wrappingWidth": 340}, "themeVariables": {"fontSize": "15px"}}}%%
flowchart TB
    subgraph CUS["CUSTOMER"]
        direction LR
        C1["Places order<br/>and pays"] --> C2["Sees estimate based on<br/>route and seller history"] --> C3["Gets a message and new<br/>date if order is at risk<br/><b>FIX 4: customer told before<br/>the date passes</b>"] --> C4["Receives parcel"] --> C5["Writes review"]
    end
    subgraph PLA["PLATFORM (OLIST)"]
        direction LR
        P1["Approves payment"] --> P2["Sets estimate by route<br/>and seller track record<br/><b>FIX 1: re-set estimates for<br/>AL, MA, SE, ES, CE</b>"] --> P4["Daily monitoring dashboard<br/>flags at-risk orders"] --> P5["Weekly seller scorecard and<br/>route watchlist review<br/><b>FIX 5: sellers ranked by<br/>excess late orders</b>"]
    end
    subgraph SEL["SELLER"]
        direction LR
        S1["Receives order"] --> S2["Picks and packs"] --> S3["Gets alert 24h before<br/>shipping limit date<br/><b>FIX 2: alert and SLA<br/>follow-up for flagged sellers</b>"] --> S4["Hands parcel to<br/>carrier on time"]
    end
    subgraph CAR["CARRIER"]
        direction LR
        K1["Collects parcel"] --> K2["Line-haul transit with<br/>route-level service levels<br/><b>FIX 3: service levels and peak<br/>plan for SP to RJ, BA, CE; PR to RJ</b>"] --> K3["Last-mile delivery"]
    end

    CUS ~~~ PLA ~~~ SEL ~~~ CAR
    C1 -.-> P1
    P2 -.-> C2
    P1 -.-> S1
    S4 -.-> K1
    K2 -.-> P4
    P4 -.-> C3
    K3 -.-> C4

    classDef fix fill:#d9e8fa,stroke:#2a78d6,stroke-width:2px,color:#0b0b0b
    classDef newstep fill:#ffffff,stroke:#2a78d6,stroke-width:2px,color:#0b0b0b
    classDef step fill:#ffffff,stroke:#898781,color:#0b0b0b
    class C3,P2,P5,S3,K2 fix
    class C2,P4,S4 newstep
    class C1,C4,C5,P1,S1,S2,K1,K3 step
    style CUS fill:#f9f9f7,stroke:#c3c2b7
    style PLA fill:#f9f9f7,stroke:#c3c2b7
    style SEL fill:#f9f9f7,stroke:#c3c2b7
    style CAR fill:#f9f9f7,stroke:#c3c2b7
```

### Improvements

| ID | Change | Fixes | Owner |
|---|---|---|---|
| FIX 1 | Set the delivery estimate by route and seller track record; first re-set the five lowest-buffer states (AL, MA, SE, ES, CE) | PAIN 1 | Product Manager |
| FIX 2 | Alert sellers 24 hours before the shipping limit date and follow up with sellers who breach it often | PAIN 2 | Seller Operations Manager |
| FIX 3 | Agree route-level service levels and a peak-season capacity plan with carriers for SP to RJ, SP to BA, SP to CE and PR to RJ | PAIN 3 | Logistics Partner Manager |
| FIX 4 | Flag at-risk orders daily and send the customer a message and a new date before the promise is missed | PAIN 4, PAIN 5 | CX Lead |
| FIX 5 | Weekly seller scorecard ranked by excess late orders and a route watchlist, both in the monitoring dashboard | PAIN 6 | BI Lead, Seller Ops |

## 4. What changes for each lane

| Lane | AS-IS | TO-BE |
|---|---|---|
| Customer | Sees one fixed date and gets no update | Sees a date that fits their route; is told early if the order is at risk |
| Platform | Same estimate logic everywhere; monthly review of complaints | Route-based estimate; daily at-risk monitoring; weekly scorecard and watchlist |
| Seller | Learns about a missed deadline after the fact | Gets an alert before the deadline; is ranked fairly on excess late orders |
| Carrier | No route-level targets | Route-level service levels and a peak capacity plan |
