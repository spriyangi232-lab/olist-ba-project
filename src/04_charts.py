"""
04_charts.py - Build the 10 report charts (results/charts/*.png).

Rules followed:
  - One business question per chart.
  - The title states the insight; every number in a title is read from
    results/metrics.json or results/tables/*.csv (nothing typed by hand).
  - One colour scheme everywhere: orange = late / problem, blue = on time / baseline,
    grey = context.
  - Sized 8 x 4.5 inches at 200 dpi so they stay readable on an A4 page.

Run from the project root (after 03_impact.py):   python src/04_charts.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")            # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
CHARTS = ROOT / "results" / "charts"
METRICS_PATH = ROOT / "results" / "metrics.json"
CHARTS.mkdir(parents=True, exist_ok=True)

metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
A = metrics["analysis"]
I = metrics["impact"]

# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------
LATE = "#eb6834"      # orange - late orders / problem areas
ONTIME = "#2a78d6"    # blue - on-time orders / baseline
GREY = "#c3c2b7"      # context bars
INK = "#0b0b0b"       # main text
INK2 = "#52514e"      # secondary text
MUTED = "#898781"     # axis labels
GRID = "#e1e0d9"      # gridlines

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": GREY,
    "axes.labelcolor": INK2,
    "axes.titlesize": 13,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def new_chart(title, subtitle, figsize=(8, 4.5)):
    """Create a figure with an insight title and a grey subtitle, left aligned."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.suptitle(title, x=0.02, y=0.98, ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.text(0.02, 0.90, subtitle, ha="left", fontsize=9.5, color=INK2)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def save(fig, name):
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(CHARTS / name, dpi=200)
    plt.close(fig)
    print("saved", name)


def fmt(x, d=1):
    """Format a number with d decimals."""
    return f"{x:.{d}f}"


# ---------------------------------------------------------------------------
# Chart 1 - Q1 monthly on-time trend
# ---------------------------------------------------------------------------
monthly = pd.read_csv(TABLES / "q02_monthly_trend.csv")
fig, ax = new_chart(
    f"On-time delivery fell to {fmt(A['worst_month_on_time_pct'])}% in March 2018",
    f"Feb-Mar 2018 had {fmt(A['feb_mar_2018_share_of_orders_pct'])}% of orders but "
    f"{fmt(A['feb_mar_2018_share_of_late_pct'])}% of all late orders. On-time rate by purchase month.")
x = range(len(monthly))
ax.plot(x, monthly["on_time_rate_pct"], color=ONTIME, linewidth=2, marker="o", markersize=4)
worst = monthly["on_time_rate_pct"].idxmin()
ax.plot(worst, monthly.loc[worst, "on_time_rate_pct"], "o", color=LATE, markersize=8)
ax.annotate(f"{monthly.loc[worst, 'purchase_month']}: {fmt(monthly.loc[worst, 'on_time_rate_pct'])}%",
            (worst, monthly.loc[worst, "on_time_rate_pct"]), xytext=(-110, -5),
            textcoords="offset points", color=INK, fontsize=9)
ax.axhline(A["on_time_rate_pct"], color=MUTED, linewidth=1, linestyle="--")
ax.text(0, A["on_time_rate_pct"] - 1.6, f"Average {fmt(A['on_time_rate_pct'])}%", color=INK2, fontsize=8.5)
ax.set_xticks(list(x)[::2])
ax.set_xticklabels(monthly["purchase_month"][::2], rotation=45, ha="right")
ax.set_ylabel("On-time rate (%)")
ax.set_ylim(75, 100)
save(fig, "01_monthly_on_time_rate.png")

# ---------------------------------------------------------------------------
# Chart 2 - Q2 bad-review share by how late
# ---------------------------------------------------------------------------
bucket = pd.read_csv(TABLES / "q04_review_by_delay_bucket.csv")
fig, ax = new_chart(
    f"Late orders are {A['bad_review_multiple_late_vs_ontime']}x more likely to get a 1-2 star review",
    f"Share of reviews scoring 1-2 stars. Late: {fmt(A['bad_review_pct_late'])}% vs on time: "
    f"{fmt(A['bad_review_pct_ontime'])}%. Even 1-3 days late gives {fmt(A['bad_review_pct_late_1_3_days'])}% "
    f"bad reviews.")
labels = ["On time"] + [f"{b} late" for b in bucket["delay_bucket"][1:]]
colors = [ONTIME] + [LATE] * (len(bucket) - 1)
bars = ax.bar(labels, bucket["bad_review_pct"], color=colors, width=0.55)
for bar, v in zip(bars, bucket["bad_review_pct"]):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5, f"{fmt(v)}%", ha="center", color=INK, fontsize=9)
ax.set_ylabel("1-2 star reviews (%)")
ax.set_ylim(0, 100)
save(fig, "02_bad_reviews_by_delay.png")

# ---------------------------------------------------------------------------
# Chart 3 - Q3 where the time goes
# ---------------------------------------------------------------------------
stages = pd.read_csv(TABLES / "q05_stage_durations.csv").set_index("delivery_status")
stage_cols = {"avg_approval_days": "Payment approval",
              "avg_seller_handling_days": "Seller handling",
              "avg_carrier_transit_days": "Carrier transit"}
fig, ax = new_chart(
    f"Late orders spend {fmt(A['extra_transit_days_late'])} extra days in carrier transit",
    f"vs only {fmt(A['extra_handling_days_late'])} extra days with the seller. Average days per stage "
    f"(orders with valid timestamps).")
ax.grid(axis="y", visible=False)
ax.grid(axis="x", color=GRID, linewidth=0.8)
y = range(len(stage_cols))
h = 0.36
ax.barh([i + h / 2 for i in y], stages.loc["On time", list(stage_cols)], height=h, color=ONTIME, label="On time")
ax.barh([i - h / 2 for i in y], stages.loc["Late", list(stage_cols)], height=h, color=LATE, label="Late")
for i, col in enumerate(stage_cols):
    for status, offset in [("On time", h / 2), ("Late", -h / 2)]:
        v = stages.loc[status, col]
        ax.text(v + 0.3, i + offset, fmt(v), va="center", fontsize=9, color=INK)
ax.set_yticks(list(y))
ax.set_yticklabels(stage_cols.values())
ax.invert_yaxis()
ax.set_xlabel("Average days")
ax.legend(frameon=False, loc="lower right")
save(fig, "03_stage_durations.png")

# ---------------------------------------------------------------------------
# Chart 4 - Q5 seller SLA breach vs late rate
# ---------------------------------------------------------------------------
sla = pd.read_csv(TABLES / "q10_sla_breach_vs_late.csv").set_index("seller_sla")
fig, ax = new_chart(
    f"Missing the handover deadline raises the late rate from {fmt(A['late_rate_sla_met_pct'])}% "
    f"to {fmt(A['late_rate_sla_breached_pct'])}%",
    f"Seller SLA breached on {fmt(A['seller_sla_breach_pct'])}% of order-seller pairs. "
    f"But {fmt(A['late_share_after_handover_pct'], 0)}% of late orders had a seller who met the deadline.",
    figsize=(8, 4.2))
order = ["SLA met", "SLA breached"]
bars = ax.bar(order, sla.loc[order, "late_rate_pct"], color=[ONTIME, LATE], width=0.4)
for bar, v in zip(bars, sla.loc[order, "late_rate_pct"]):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.5, f"{fmt(v)}%", ha="center", color=INK)
ax.set_ylabel("Late rate (%)")
ax.set_ylim(0, 25)
save(fig, "04_sla_breach_vs_late.png")

# ---------------------------------------------------------------------------
# Chart 5 - Q4 customer states
# ---------------------------------------------------------------------------
states = pd.read_csv(TABLES / "q07_customer_state_late.csv").sort_values("late_rate_pct")
rj = states.set_index("customer_state").loc["RJ"]
fig, ax = new_chart(
    f"North-East states have the highest late rates; {A['worst_state']} reaches "
    f"{fmt(A['worst_state_late_rate_pct'])}%",
    f"Customer states with 300+ orders. RJ is late {fmt(rj['late_rate_pct'])}% of the time but produces "
    f"{fmt(rj['share_of_all_late_pct'])}% of all late orders.", figsize=(8, 6))
ax.grid(axis="y", visible=False)
ax.grid(axis="x", color=GRID, linewidth=0.8)
colors = [LATE if v > A["late_rate_pct"] else GREY for v in states["late_rate_pct"]]
ax.barh(states["customer_state"], states["late_rate_pct"], color=colors, height=0.6)
ax.axvline(A["late_rate_pct"], color=INK2, linewidth=1, linestyle="--")
ax.text(A["late_rate_pct"] + 0.2, 0, f"Platform {fmt(A['late_rate_pct'])}%", color=INK2, fontsize=8.5)
ax.set_xlabel("Late rate (%)")
save(fig, "05_state_late_rate.png")

# ---------------------------------------------------------------------------
# Chart 6 - Q4 routes with the most late orders
# ---------------------------------------------------------------------------
routes = pd.read_csv(TABLES / "q08_route_late.csv").head(10).iloc[::-1]
sp_rj = routes.set_index("route").loc["SP -> RJ"]
fig, ax = new_chart(
    f"Sao Paulo to Rio alone produced {int(sp_rj['late_pairs']):,} late orders",
    f"Top 10 seller-to-customer routes by late orders (labels show the route's late rate; "
    f"platform average {fmt(A['late_rate_pct'])}%).", figsize=(8, 5))
ax.grid(axis="y", visible=False)
ax.grid(axis="x", color=GRID, linewidth=0.8)
colors = [LATE if v > A["late_rate_pct"] else GREY for v in routes["late_rate_pct"]]
ax.barh(routes["route"], routes["late_pairs"], color=colors, height=0.6)
for i, (n, r) in enumerate(zip(routes["late_pairs"], routes["late_rate_pct"])):
    ax.text(n + 15, i, f"{n:,}  ({fmt(r)}% late)", va="center", fontsize=8.5, color=INK)
ax.set_xlabel("Late orders")
ax.set_xlim(0, routes["late_pairs"].max() * 1.3)
save(fig, "06_routes_late_orders.png")

# ---------------------------------------------------------------------------
# Chart 7 - Q5 the sellers that drive excess delays
# ---------------------------------------------------------------------------
fig, ax = new_chart(
    f"{I['worst_sellers_n']} sellers create {I['worst_sellers_excess_late']:,} more late orders "
    f"than an average seller would",
    f"They handle {fmt(I['worst_sellers_share_of_volume_pct'])}% of orders. Ranked by excess late orders "
    f"(actual minus expected at the platform rate), sellers with 30+ orders.", figsize=(8, 4.2))
groups = [f"Worst {I['worst_sellers_n']} sellers", "All other sellers"]
vals = [I["worst_sellers_late_rate_pct"], I["other_sellers_late_rate_pct"]]
bars = ax.bar(groups, vals, color=[LATE, GREY], width=0.4)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.2, f"{fmt(v)}%", ha="center", color=INK)
ax.set_ylabel("Late rate (%)")
ax.set_ylim(0, 14)
save(fig, "07_worst_sellers.png")

# ---------------------------------------------------------------------------
# Chart 8 - Q7 promise accuracy
# ---------------------------------------------------------------------------
dist = pd.read_csv(TABLES / "q13_promise_accuracy_distribution.csv")
dist["label"] = dist["days_before_estimate"].str[3:]       # drop the "1. " sort prefix
fig, ax = new_chart(
    f"{fmt(A['pct_orders_arrived_7plus_days_early'])}% of orders arrive 7+ days before the promised date",
    "Days between the estimated delivery date and the actual delivery. The promise is padded for most "
    "customers, yet still missed for some.")
colors = [LATE] + [ONTIME] * (len(dist) - 1)
bars = ax.bar(dist["label"], dist["share_pct"], color=colors, width=0.55)
for bar, v in zip(bars, dist["share_pct"]):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.7, f"{fmt(v)}%", ha="center", color=INK, fontsize=9)
ax.set_ylabel("Share of orders (%)")
save(fig, "08_promise_accuracy.png")

# ---------------------------------------------------------------------------
# Chart 9 - Q7 buffer in the promise vs late rate, by state
# ---------------------------------------------------------------------------
promise = pd.read_csv(TABLES / "q14_promise_by_state.csv")
corr = promise["avg_days_early"].corr(promise["late_rate_pct"])
fig, ax = new_chart(
    "States that get less buffer in the delivery estimate see more late orders",
    f"Each dot is a customer state (300+ orders). Correlation r = {corr:.2f}. "
    f"{A['least_padded_state']}: {fmt(A['least_padded_state_days_early'])} days buffer, "
    f"{fmt(A['least_padded_state_late_rate_pct'])}% late.", figsize=(8, 5))
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.scatter(promise["avg_days_early"], promise["late_rate_pct"], s=40, color=ONTIME,
           edgecolor="white", linewidth=1.5, zorder=3)
for _, r in promise.iterrows():
    ax.annotate(r["customer_state"], (r["avg_days_early"], r["late_rate_pct"]), xytext=(4, 3),
                textcoords="offset points", fontsize=8, color=INK2)
ax.set_xlabel("Average days delivered before the estimate (buffer)")
ax.set_ylabel("Late rate (%)")
save(fig, "09_buffer_vs_late_by_state.png")

# ---------------------------------------------------------------------------
# Chart 10 - impact estimate range
# ---------------------------------------------------------------------------
c, e = I["conservative"], I["expected"]
fig, ax = new_chart(
    f"Fixing the worst sellers and routes could avoid {c['avoided_late_total']:,}-"
    f"{e['avoided_late_total']:,} late orders",
    f"and prevent {c['bad_reviews_prevented']:,}-{e['bad_reviews_prevented']:,} 1-2 star reviews over the "
    f"20-month window (about {c['bad_reviews_prevented_per_year']:,}-{e['bad_reviews_prevented_per_year']:,} "
    f"a year). Conservative = 50% of the gap closed.")
measures = ["Late orders avoided", "1-2 star reviews prevented"]
cons = [c["avoided_late_total"], c["bad_reviews_prevented"]]
expd = [e["avoided_late_total"], e["bad_reviews_prevented"]]
xs = range(len(measures))
w = 0.3
b1 = ax.bar([i - w / 2 for i in xs], cons, width=w, color=GREY, label="Conservative")
b2 = ax.bar([i + w / 2 for i in xs], expd, width=w, color=ONTIME, label="Expected")
for bars in (b1, b2):
    for bar in bars:
        v = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, v + 20, f"{int(v):,}", ha="center", color=INK, fontsize=9)
ax.set_xticks(list(xs))
ax.set_xticklabels(measures)
ax.set_ylabel("Orders / reviews (20 months)")
ax.legend(frameon=False)
save(fig, "10_impact_estimate.png")

# Keep the correlation used in chart 9 with the other numbers
metrics.setdefault("charts", {})["state_buffer_vs_late_corr"] = round(float(corr), 2)
METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
