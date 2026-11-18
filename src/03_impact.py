"""
03_impact.py - Impact scenario: how many late orders and 1-2 star reviews could be avoided?

Scenario question
-----------------
"If the worst 20% of sellers and the worst routes reached the platform-average
late rate, how many late orders would be avoided, and how many 1-2 star reviews
would be prevented?"

Assumptions (written out so they can be challenged)
---------------------------------------------------
A1. Unit of analysis is the (order_id, seller_id) pair, the same as the seller SQL queries.
A2. Platform-average late rate = all late pairs / all pairs in the analysis window.
A3. "Worst sellers" are ranked by EXCESS late orders, not raw late count:
        excess = actual late orders - (seller's orders x platform late rate)
    Raw late count mostly picks the biggest sellers (they have the most orders, so
    the most late orders even at an average late rate). Excess picks sellers who are
    both large AND worse than average. Only sellers with >= 30 orders are ranked,
    so one bad week at a tiny seller doesn't count as a pattern.
A4. "Worst routes" = the 5 routes (>= 300 pairs) with the most excess late orders
    AFTER the seller fix, so the same late order is never counted twice.
A5. Order of fixes: sellers first, then routes. A fixed seller's late rate becomes
    the platform average; then each worst route's remaining late rate is scaled
    down to the platform average.
A6. Two scenarios:
        Conservative = each lever closes 50% of the gap to the platform average
        Expected     = each lever closes 100% of the gap (the scenario as asked)
A7. Reviews: an avoided late order becomes an on-time order. Prevented 1-2 star
    reviews = avoided late orders x review coverage of late orders
              x (bad-review rate of late orders - bad-review rate of on-time orders),
    using the observed rates from sql query q03.
A8. Totals cover the 20-month window (Jan 2017 - Aug 2018). A per-year figure
    is the window total x 12 / 20.
A9. This is a what-if estimate, not a forecast. It assumes the gap can be closed
    and that customers react to an avoided delay the same way they react to
    on-time orders today.

Run from the project root (after 02_run_sql.py):   python src/03_impact.py
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "processed" / "olist.db"
TABLES = ROOT / "results" / "tables"
METRICS_PATH = ROOT / "results" / "metrics.json"

MIN_SELLER_ORDERS = 30      # A3
WORST_SELLER_SHARE = 0.20   # worst 20% of ranked sellers
MIN_ROUTE_PAIRS = 300       # A4
N_WORST_ROUTES = 5          # A4
GAP_CLOSED = {"conservative": 0.5, "expected": 1.0}   # A6

# ---------------------------------------------------------------------------
# Load pairs and the observed review rates
# ---------------------------------------------------------------------------
with sqlite3.connect(DB_PATH) as conn:
    pairs = pd.read_sql_query(
        "SELECT order_id, seller_id, route, is_late FROM analysis_order_sellers", conn)
    review_cov = pd.read_sql_query(
        "SELECT AVG(has_review) AS cov FROM analysis_orders WHERE is_late = 1", conn)["cov"].iloc[0]

rev = pd.read_csv(TABLES / "q03_review_late_vs_ontime.csv").set_index("delivery_status")
bad_rate_late = rev.loc["Late", "bad_review_pct"] / 100
bad_rate_ontime = rev.loc["On time", "bad_review_pct"] / 100

platform_rate = pairs["is_late"].mean()                                # A2
baseline_late = pairs["is_late"].sum()
window_months = json.loads(METRICS_PATH.read_text(encoding="utf-8"))["data"]["window_months"]

# ---------------------------------------------------------------------------
# Rank sellers by excess late orders (A3)
# ---------------------------------------------------------------------------
sellers = pairs.groupby("seller_id").agg(orders=("is_late", "size"), late=("is_late", "sum")).reset_index()
sellers["expected_late"] = sellers["orders"] * platform_rate
sellers["excess_late"] = sellers["late"] - sellers["expected_late"]
sellers["late_rate"] = sellers["late"] / sellers["orders"]

eligible = sellers[sellers["orders"] >= MIN_SELLER_ORDERS].sort_values("excess_late", ascending=False)
n_worst = int(round(WORST_SELLER_SHARE * len(eligible)))
worst_sellers = eligible.head(n_worst)
# Only sellers who really are above average can be "brought down" to it
worst_sellers = worst_sellers[worst_sellers["excess_late"] > 0]
worst_ids = set(worst_sellers["seller_id"])

# For comparison: the same exercise ranking by raw late-order count
by_count = eligible.sort_values("late", ascending=False).head(n_worst)
avoided_if_ranked_by_count = by_count["excess_late"].clip(lower=0).sum()


def run_scenario(gap_closed):
    """Return avoided late orders from sellers and from routes for one scenario."""
    p = pairs.copy()
    # Start from what actually happened: 1 = late, 0 = on time
    p["adj_late"] = p["is_late"].astype(float)

    # Lever 1 - sellers (A5): move each worst seller's late rate towards the platform rate
    seller_rate = p.groupby("seller_id")["is_late"].transform("mean")
    is_worst = p["seller_id"].isin(worst_ids)
    target = seller_rate - gap_closed * (seller_rate - platform_rate)
    p.loc[is_worst, "adj_late"] = target[is_worst]
    avoided_sellers = baseline_late - p["adj_late"].sum()

    # Lever 2 - routes (A4, A5): measured after the seller fix
    routes = p.groupby("route").agg(pairs=("adj_late", "size"), late=("adj_late", "sum")).reset_index()
    routes = routes[routes["pairs"] >= MIN_ROUTE_PAIRS]
    routes["excess_late"] = routes["late"] - routes["pairs"] * platform_rate
    worst_routes = routes[routes["excess_late"] > 0].nlargest(N_WORST_ROUTES, "excess_late")

    before_routes = p["adj_late"].sum()
    for _, r in worst_routes.iterrows():
        in_route = p["route"] == r["route"]
        route_rate = r["late"] / r["pairs"]
        new_rate = route_rate - gap_closed * (route_rate - platform_rate)
        p.loc[in_route, "adj_late"] *= new_rate / route_rate   # scale every pair on the route
    avoided_routes = before_routes - p["adj_late"].sum()

    avoided_total = avoided_sellers + avoided_routes
    bad_reviews_prevented = avoided_total * review_cov * (bad_rate_late - bad_rate_ontime)
    new_late_rate = p["adj_late"].sum() / len(p)
    return {
        "avoided_late_sellers": round(avoided_sellers),
        "avoided_late_routes": round(avoided_routes),
        "avoided_late_total": round(avoided_total),
        "avoided_late_pct_of_all_late": float(round(100 * avoided_total / baseline_late, 1)),
        "bad_reviews_prevented": round(bad_reviews_prevented),
        "avoided_late_per_year": round(avoided_total * 12 / window_months),
        "bad_reviews_prevented_per_year": round(bad_reviews_prevented * 12 / window_months),
        "late_rate_after_pct": float(round(100 * new_late_rate, 2)),
        "worst_routes": worst_routes["route"].tolist(),
    }


results = {name: run_scenario(g) for name, g in GAP_CLOSED.items()}

# ---------------------------------------------------------------------------
# Print and save
# ---------------------------------------------------------------------------
print(f"Platform late rate (pairs): {platform_rate:.2%}  |  late pairs: {baseline_late:,}")
print(f"Eligible sellers (>= {MIN_SELLER_ORDERS} orders): {len(eligible):,}; worst 20% = {n_worst}; "
      f"of those above average: {len(worst_ids)}")
print(f"Worst sellers: {worst_sellers['orders'].sum():,} orders "
      f"({worst_sellers['orders'].sum() / len(pairs):.1%} of volume), late rate "
      f"{worst_sellers['late'].sum() / worst_sellers['orders'].sum():.2%}, "
      f"excess late orders {worst_sellers['excess_late'].sum():.0f}")
print(f"For comparison, ranking by raw late count would avoid {avoided_if_ranked_by_count:.0f} late orders")
print(f"Review coverage of late orders {review_cov:.1%}; bad-review rate late {bad_rate_late:.1%} "
      f"vs on time {bad_rate_ontime:.1%}")
for name, res in results.items():
    print(f"\n{name.upper()}: {res}")

eligible.to_csv(TABLES / "impact_seller_excess.csv", index=False)
pd.DataFrame(results).T.drop(columns="worst_routes").to_csv(TABLES / "impact_scenarios.csv")

metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
metrics["impact"] = {
    "platform_late_rate_pairs_pct": round(100 * platform_rate, 2),
    "eligible_sellers": int(len(eligible)),
    "worst_sellers_n": int(len(worst_ids)),
    "worst_sellers_share_of_volume_pct": round(100 * worst_sellers["orders"].sum() / len(pairs), 1),
    "worst_sellers_late_rate_pct": round(100 * worst_sellers["late"].sum() / worst_sellers["orders"].sum(), 2),
    "worst_sellers_excess_late": round(worst_sellers["excess_late"].sum()),
    "worst_sellers_late": int(worst_sellers["late"].sum()),
    # Late rate of every other seller (including small sellers) for comparison
    "other_sellers_late_rate_pct": round(100 * (baseline_late - worst_sellers["late"].sum())
                                         / (len(pairs) - worst_sellers["orders"].sum()), 2),
    "avoided_if_ranked_by_late_count": round(avoided_if_ranked_by_count),
    "worst_routes": results["expected"]["worst_routes"],
    "review_coverage_late_pct": round(100 * review_cov, 1),
    "bad_rate_late_pct": round(100 * bad_rate_late, 2),
    "bad_rate_ontime_pct": round(100 * bad_rate_ontime, 2),
    "conservative": {k: v for k, v in results["conservative"].items() if k != "worst_routes"},
    "expected": {k: v for k, v in results["expected"].items() if k != "worst_routes"},
}
METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
print("\nImpact numbers written to results/metrics.json")
