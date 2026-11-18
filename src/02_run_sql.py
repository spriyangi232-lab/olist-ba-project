"""
02_run_sql.py - Run every query in sql/analysis.sql and save the results.

  1. Reads sql/analysis.sql and splits it into queries using the "-- name:" lines.
  2. Runs each query against data/processed/olist.db.
  3. Saves each result to results/tables/<name>.csv and prints it.
  4. Pulls the headline numbers out of the results and stores them in
     results/metrics.json under the "analysis" key.

Run from the project root (after 01_clean.py):   python src/02_run_sql.py
"""

import json
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "processed" / "olist.db"
SQL_PATH = ROOT / "sql" / "analysis.sql"
TABLES = ROOT / "results" / "tables"
METRICS_PATH = ROOT / "results" / "metrics.json"
TABLES.mkdir(parents=True, exist_ok=True)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


# ---------------------------------------------------------------------------
# 1. Split the SQL file into named queries
# ---------------------------------------------------------------------------
def load_queries(path):
    """Return a list of (name, question, sql) tuples from the SQL file."""
    text = path.read_text(encoding="utf-8")
    # Every query block starts with a line like "-- name: q01_overall_kpis"
    blocks = re.split(r"^-- name:\s*", text, flags=re.MULTILINE)[1:]
    queries = []
    for block in blocks:
        name, body = block.split("\n", 1)
        question = re.search(r"^-- question:\s*(.+)$", body, flags=re.MULTILINE)
        queries.append((name.strip(), question.group(1).strip() if question else "", body.strip()))
    return queries


# ---------------------------------------------------------------------------
# 2-3. Run each query and save the result
# ---------------------------------------------------------------------------
results = {}
with sqlite3.connect(DB_PATH) as conn:
    for name, question, sql in load_queries(SQL_PATH):
        result = pd.read_sql_query(sql, conn)
        result.to_csv(TABLES / f"{name}.csv", index=False)
        results[name] = result
        print(f"\n=== {name} ===\n{question}")
        print(result.head(15).to_string(index=False))

print(f"\nSaved {len(results)} tables to results/tables/")


# ---------------------------------------------------------------------------
# 4. Headline numbers -> metrics.json
# ---------------------------------------------------------------------------
def row(table, column, value):
    """Return the single row of a result table where column == value."""
    return results[table].set_index(column).loc[value]

kpi = results["q01_overall_kpis"].iloc[0]
late_rev = row("q03_review_late_vs_ontime", "delivery_status", "Late")
ontime_rev = row("q03_review_late_vs_ontime", "delivery_status", "On time")
late_stage = row("q05_stage_durations", "delivery_status", "Late")
ontime_stage = row("q05_stage_durations", "delivery_status", "On time")
cause = results["q06_late_cause_split"].set_index("late_cause")
conc = results["q09_seller_concentration"].set_index("segment")
sla = results["q10_sla_breach_vs_late"].set_index("seller_sla")
repeat = results["q15_repeat_purchase"].set_index("first_order")
monthly = results["q02_monthly_trend"]
states = results["q07_customer_state_late"]
routes = results["q08_route_late"]
cats = results["q12_category_late"]
promise = results["q14_promise_by_state"]
bucket = results["q04_review_by_delay_bucket"].set_index("delay_bucket")
promise_dist = results["q13_promise_accuracy_distribution"].set_index("days_before_estimate")

# Extra days late orders spend in each stage compared with on-time orders
extra_handling = late_stage["avg_seller_handling_days"] - ontime_stage["avg_seller_handling_days"]
extra_transit = late_stage["avg_carrier_transit_days"] - ontime_stage["avg_carrier_transit_days"]

# Share of the window's late orders that were bought in Feb + Mar 2018
feb_mar = monthly[monthly["purchase_month"].isin(["2018-02", "2018-03"])]
worst_month = monthly.loc[monthly["on_time_rate_pct"].idxmin()]
best_month = monthly.loc[monthly["on_time_rate_pct"].idxmax()]

top_state = states.iloc[0]                                   # sorted by late rate
top_route_rate = routes.sort_values("late_rate_pct", ascending=False).iloc[0]
top_route_count = routes.iloc[0]                             # sorted by late count
top_cat = cats.iloc[0]
most_padded = promise.sort_values("avg_days_early", ascending=False).iloc[0]
least_padded = promise.iloc[0]                               # sorted by days early asc

r = lambda x: round(float(x), 2)
metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
metrics["analysis"] = {
    # Q1 size and trend
    "delivered_orders": int(kpi["delivered_orders"]),
    "late_orders": int(kpi["late_orders"]),
    "late_rate_pct": r(kpi["late_rate_pct"]),
    "on_time_rate_pct": r(kpi["on_time_rate_pct"]),
    "avg_delay_days_late_orders": r(kpi["avg_delay_days_late_orders"]),
    "avg_review_score": r(kpi["avg_review_score"]),
    "bad_review_pct": r(kpi["bad_review_pct"]),
    "seller_sla_breach_pct": r(kpi["seller_sla_breach_pct"]),
    "worst_month": worst_month["purchase_month"],
    "worst_month_on_time_pct": r(worst_month["on_time_rate_pct"]),
    "best_month": best_month["purchase_month"],
    "best_month_on_time_pct": r(best_month["on_time_rate_pct"]),
    "feb_mar_2018_late_orders": int(feb_mar["late_orders"].sum()),
    "feb_mar_2018_share_of_late_pct": r(100 * feb_mar["late_orders"].sum() / kpi["late_orders"]),
    "feb_mar_2018_share_of_orders_pct": r(100 * feb_mar["orders"].sum() / kpi["delivered_orders"]),
    # Q2 reviews
    "avg_score_late": r(late_rev["avg_review_score"]),
    "avg_score_ontime": r(ontime_rev["avg_review_score"]),
    "bad_review_pct_late": r(late_rev["bad_review_pct"]),
    "bad_review_pct_ontime": r(ontime_rev["bad_review_pct"]),
    "bad_review_multiple_late_vs_ontime": round(late_rev["bad_review_pct"] / ontime_rev["bad_review_pct"], 1),
    "bad_review_pct_late_1_3_days": r(bucket.loc["1-3 days", "bad_review_pct"]),
    "bad_review_pct_late_15plus_days": r(bucket.loc["15+ days", "bad_review_pct"]),
    # Q3 journey stages
    "avg_handling_days_late": r(late_stage["avg_seller_handling_days"]),
    "avg_handling_days_ontime": r(ontime_stage["avg_seller_handling_days"]),
    "avg_transit_days_late": r(late_stage["avg_carrier_transit_days"]),
    "avg_transit_days_ontime": r(ontime_stage["avg_carrier_transit_days"]),
    "extra_handling_days_late": r(extra_handling),
    "extra_transit_days_late": r(extra_transit),
    "late_share_seller_breach_pct": r(cause.loc["Seller missed handover deadline", "share_of_late_orders_pct"]),
    "late_share_after_handover_pct": r(cause.loc["Seller on time, late after handover", "share_of_late_orders_pct"]),
    # Q4 geography
    "states_analysed": int(len(states)),
    "worst_state": top_state["customer_state"],
    "worst_state_late_rate_pct": r(top_state["late_rate_pct"]),
    "routes_analysed": int(len(routes)),
    "worst_route_by_rate": top_route_rate["route"],
    "worst_route_late_rate_pct": r(top_route_rate["late_rate_pct"]),
    "top_route_by_late_count": top_route_count["route"],
    "top_route_late_count": int(top_route_count["late_pairs"]),
    "top_route_late_rate_pct": r(top_route_count["late_rate_pct"]),
    # Q5 sellers
    "top10_sellers_share_of_late_pct": r(conc.loc["Top 10% of sellers", "share_of_late_orders_pct"]),
    "top10_sellers_share_of_volume_pct": r(conc.loc["Top 10% of sellers", "share_of_order_volume_pct"]),
    "top20_sellers_share_of_late_pct": r(conc.loc["Top 20% of sellers", "share_of_late_orders_pct"]),
    "top20_sellers_share_of_volume_pct": r(conc.loc["Top 20% of sellers", "share_of_order_volume_pct"]),
    "late_rate_sla_breached_pct": r(sla.loc["SLA breached", "late_rate_pct"]),
    "late_rate_sla_met_pct": r(sla.loc["SLA met", "late_rate_pct"]),
    # Q6 categories
    "categories_analysed": int(len(cats)),
    "worst_category": top_cat["main_category"],
    "worst_category_late_rate_pct": r(top_cat["late_rate_pct"]),
    # Q7 promise accuracy
    "pct_orders_arrived_7plus_days_early": r(promise_dist.loc[["3. 7-13 days early", "4. 14-20 days early",
                                                               "5. 21+ days early"], "share_pct"].sum()),
    "most_padded_state": most_padded["customer_state"],
    "most_padded_state_days_early": r(most_padded["avg_days_early"]),
    "least_padded_state": least_padded["customer_state"],
    "least_padded_state_days_early": r(least_padded["avg_days_early"]),
    "least_padded_state_late_rate_pct": r(least_padded["late_rate_pct"]),
    # Q8 repeat purchase (directional)
    "repeat_rate_all_pct": r(repeat.loc["All customers", "repeat_rate_pct"]),
    "repeat_rate_first_late_pct": r(repeat.loc["First order late", "repeat_rate_pct"]),
    "repeat_rate_first_ontime_pct": r(repeat.loc["First order on time", "repeat_rate_pct"]),
}
METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

print("\nHeadline metrics written to results/metrics.json:")
for key, value in metrics["analysis"].items():
    print(f"  {key}: {value}")
