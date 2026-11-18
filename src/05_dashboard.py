"""
05_dashboard.py - Build dashboard/dashboard.html, one self-contained interactive file.

The Plotly JavaScript library is embedded inside the HTML, so the file opens
offline in any browser - no internet, no server.

Sections:
  1. KPI tiles: on-time rate, avg delay of late orders, bad-review share, seller SLA breach rate
  2. Monthly on-time trend
  3. Where: customer-state late rates and the routes with the most late orders
  4. Who: sellers with the most excess late orders
  5. What: product-category late rates
  6. Impact estimate range

All numbers come from results/metrics.json and results/tables/*.csv.

Run from the project root (after 03_impact.py):   python src/05_dashboard.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
METRICS_PATH = ROOT / "results" / "metrics.json"
OUT = ROOT / "dashboard" / "dashboard.html"
OUT.parent.mkdir(exist_ok=True)

metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
D, A, I = metrics["data"], metrics["analysis"], metrics["impact"]

# Same colours as the static charts
LATE, ONTIME, GREY, INK, INK2, GRID = "#eb6834", "#2a78d6", "#c3c2b7", "#0b0b0b", "#52514e", "#e1e0d9"


def style(fig, height=360):
    """Apply one clean layout to every figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=20, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Segoe UI, system-ui, sans-serif", size=12, color=INK2),
        showlegend=False,
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GREY)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GREY)
    return fig


def to_div(fig):
    """Turn a figure into an HTML <div> (Plotly JS is added once, separately)."""
    # default_width + responsive make each chart fit (and resize with) its card
    return fig.to_html(full_html=False, include_plotlyjs=False, default_width="100%",
                       config={"displayModeBar": False, "responsive": True})


# ---------------------------------------------------------------------------
# Figure: monthly on-time trend
# ---------------------------------------------------------------------------
monthly = pd.read_csv(TABLES / "q02_monthly_trend.csv")
fig_month = go.Figure(go.Scatter(
    x=monthly["purchase_month"], y=monthly["on_time_rate_pct"], mode="lines+markers",
    line=dict(color=ONTIME, width=2), marker=dict(size=7),
    customdata=monthly[["orders", "late_orders", "bad_review_pct"]],
    hovertemplate="<b>%{x}</b><br>On-time rate: %{y:.1f}%<br>Orders: %{customdata[0]:,}"
                  "<br>Late orders: %{customdata[1]:,}<br>1-2 star reviews: %{customdata[2]:.1f}%<extra></extra>"))
fig_month.add_hline(y=A["on_time_rate_pct"], line_dash="dash", line_color=INK2, line_width=1,
                    annotation_text=f"Average {A['on_time_rate_pct']:.1f}%", annotation_position="bottom left")
fig_month.update_yaxes(title="On-time rate (%)", range=[75, 100])
style(fig_month)

# ---------------------------------------------------------------------------
# Figure: customer states
# ---------------------------------------------------------------------------
states = pd.read_csv(TABLES / "q07_customer_state_late.csv").sort_values("late_rate_pct")
fig_state = go.Figure(go.Bar(
    x=states["late_rate_pct"], y=states["customer_state"], orientation="h",
    marker_color=[LATE if v > A["late_rate_pct"] else GREY for v in states["late_rate_pct"]],
    customdata=states[["orders", "late_orders", "share_of_all_late_pct"]],
    hovertemplate="<b>%{y}</b><br>Late rate: %{x:.1f}%<br>Orders: %{customdata[0]:,}"
                  "<br>Late orders: %{customdata[1]:,}<br>Share of all late: %{customdata[2]:.1f}%<extra></extra>"))
fig_state.add_vline(x=A["late_rate_pct"], line_dash="dash", line_color=INK2, line_width=1)
fig_state.update_xaxes(title="Late rate (%)")
style(fig_state, height=520)

# ---------------------------------------------------------------------------
# Figure: routes with the most late orders
# ---------------------------------------------------------------------------
routes = pd.read_csv(TABLES / "q08_route_late.csv").head(12).iloc[::-1]
fig_route = go.Figure(go.Bar(
    x=routes["late_pairs"], y=routes["route"], orientation="h",
    marker_color=[LATE if v > A["late_rate_pct"] else GREY for v in routes["late_rate_pct"]],
    customdata=routes[["order_seller_pairs", "late_rate_pct"]],
    hovertemplate="<b>%{y}</b><br>Late orders: %{x:,}<br>Orders: %{customdata[0]:,}"
                  "<br>Late rate: %{customdata[1]:.1f}%<extra></extra>"))
fig_route.update_xaxes(title="Late orders")
style(fig_route, height=520)

# ---------------------------------------------------------------------------
# Figure: sellers with the most excess late orders
# ---------------------------------------------------------------------------
sellers = pd.read_csv(TABLES / "impact_seller_excess.csv").head(20).iloc[::-1]
sellers["label"] = "Seller " + sellers["seller_id"].str[:6]     # short id for display
fig_seller = go.Figure(go.Bar(
    x=sellers["excess_late"], y=sellers["label"], orientation="h", marker_color=LATE,
    customdata=sellers[["orders", "late", "late_rate"]],
    hovertemplate="<b>%{y}</b><br>Excess late orders: %{x:.0f}<br>Orders: %{customdata[0]:,}"
                  "<br>Late orders: %{customdata[1]:,}<br>Late rate: %{customdata[2]:.1%}<extra></extra>"))
fig_seller.update_xaxes(title="Excess late orders")
style(fig_seller, height=520)

# ---------------------------------------------------------------------------
# Figure: categories
# ---------------------------------------------------------------------------
cats = pd.read_csv(TABLES / "q12_category_late.csv").sort_values("late_rate_pct")
fig_cat = go.Figure(go.Bar(
    x=cats["late_rate_pct"], y=cats["main_category"], orientation="h",
    marker_color=[LATE if v > A["late_rate_pct"] else GREY for v in cats["late_rate_pct"]],
    customdata=cats[["orders", "late_orders"]],
    hovertemplate="<b>%{y}</b><br>Late rate: %{x:.1f}%<br>Orders: %{customdata[0]:,}"
                  "<br>Late orders: %{customdata[1]:,}<extra></extra>"))
fig_cat.add_vline(x=A["late_rate_pct"], line_dash="dash", line_color=INK2, line_width=1)
fig_cat.update_xaxes(title="Late rate (%)")
style(fig_cat, height=700)

# ---------------------------------------------------------------------------
# HTML page
# ---------------------------------------------------------------------------
c, e = I["conservative"], I["expected"]
kpis = [
    ("On-time rate", f"{A['on_time_rate_pct']:.1f}%", f"{A['late_orders']:,} of {A['delivered_orders']:,} orders late"),
    ("Avg delay of late orders", f"{A['avg_delay_days_late_orders']:.1f} days", "after the estimated date"),
    ("1-2 star review share", f"{A['bad_review_pct']:.1f}%",
     f"{A['bad_review_pct_late']:.1f}% when late vs {A['bad_review_pct_ontime']:.1f}% on time"),
    ("Seller SLA breach rate", f"{A['seller_sla_breach_pct']:.1f}%", "handed to carrier after the deadline"),
]
tiles = "\n".join(
    f'<div class="tile"><div class="label">{l}</div><div class="value">{v}</div><div class="note">{n}</div></div>'
    for l, v, n in kpis)

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Olist Delivery Performance</title>
<style>
  :root {{ --bg:#f9f9f7; --card:#ffffff; --ink:{INK}; --ink2:{INK2}; --muted:#898781;
          --line:rgba(11,11,11,0.10); --late:{LATE}; --ontime:{ONTIME}; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font-family:"Segoe UI", system-ui, -apple-system, sans-serif; }}
  main {{ max-width:1200px; margin:0 auto; padding:24px 16px 48px; }}
  h1 {{ font-size:24px; margin:0 0 4px; }}
  h2 {{ font-size:16px; margin:0 0 2px; }}
  .sub {{ color:var(--ink2); font-size:13px; margin:0 0 12px; }}
  .tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin:20px 0; }}
  .tile, .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; }}
  .tile .label {{ color:var(--ink2); font-size:13px; }}
  .tile .value {{ font-size:30px; font-weight:600; margin:4px 0; }}
  .tile .note {{ color:var(--muted); font-size:12px; }}
  .grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr)); gap:12px; margin-bottom:12px; }}
  .card {{ margin-bottom:12px; min-width:0; }}
  .impact {{ display:flex; flex-wrap:wrap; gap:24px; }}
  .impact div {{ min-width:200px; }}
  .impact .ilabel {{ color:var(--ink2); font-size:13px; }}
  .impact .value {{ font-size:26px; font-weight:600; }}
  footer {{ color:var(--muted); font-size:12px; margin-top:24px; line-height:1.5; }}
</style>
<script>{get_plotlyjs()}</script>
</head>
<body>
<main>
  <h1>Delivery Performance Monitoring - Olist</h1>
  <p class="sub">{D['analysis_orders']:,} delivered orders, purchased {D['window_start']} to {D['window_end']}.
  Late = delivered after the estimated date. Hover any chart for details.</p>

  <section class="tiles">{tiles}</section>

  <div class="card">
    <h2>On-time rate fell to {A['worst_month_on_time_pct']:.1f}% in {A['worst_month']}</h2>
    <p class="sub">Feb-Mar 2018 had {A['feb_mar_2018_share_of_orders_pct']:.1f}% of orders but
    {A['feb_mar_2018_share_of_late_pct']:.1f}% of all late orders.</p>
    {to_div(fig_month)}
  </div>

  <div class="grid2">
    <div class="card">
      <h2>Late rate by customer state</h2>
      <p class="sub">States with 300+ orders. Orange = above the {A['late_rate_pct']:.1f}% platform rate.</p>
      {to_div(fig_state)}
    </div>
    <div class="card">
      <h2>Routes with the most late orders</h2>
      <p class="sub">Seller state to customer state, top 12. Orange = route late rate above platform.</p>
      {to_div(fig_route)}
    </div>
  </div>

  <div class="grid2">
    <div class="card">
      <h2>Sellers creating the most excess late orders</h2>
      <p class="sub">The worst {I['worst_sellers_n']} sellers ({I['worst_sellers_share_of_volume_pct']:.1f}% of orders)
      run a {I['worst_sellers_late_rate_pct']:.1f}% late rate and create {I['worst_sellers_excess_late']:,}
      excess late orders. Top 20 shown.</p>
      {to_div(fig_seller)}
    </div>
    <div class="card">
      <h2>Late rate by product category</h2>
      <p class="sub">Categories with 300+ orders. Most sit close to the platform rate, so category is not a main driver.</p>
      {to_div(fig_cat)}
    </div>
  </div>

  <div class="card">
    <h2>Impact estimate: worst sellers and routes brought to the platform average</h2>
    <p class="sub">Over the 20-month window. Conservative = 50% of the gap closed; expected = 100%.</p>
    <div class="impact">
      <div><div class="ilabel">Late orders avoided</div>
        <div class="value">{c['avoided_late_total']:,} - {e['avoided_late_total']:,}</div>
        <div class="sub">{c['avoided_late_pct_of_all_late']}% - {e['avoided_late_pct_of_all_late']}% of all late orders</div></div>
      <div><div class="ilabel">1-2 star reviews prevented</div>
        <div class="value">{c['bad_reviews_prevented']:,} - {e['bad_reviews_prevented']:,}</div>
        <div class="sub">about {c['bad_reviews_prevented_per_year']:,} - {e['bad_reviews_prevented_per_year']:,} a year</div></div>
      <div><div class="ilabel">Late rate after the fix</div>
        <div class="value">{c['late_rate_after_pct']:.2f}% - {e['late_rate_after_pct']:.2f}%</div>
        <div class="sub">from {I['platform_late_rate_pairs_pct']:.2f}% today (order-seller pairs)</div></div>
    </div>
  </div>

  <footer>Data: Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0).
  Built by Priyangi Singh Chouhan. Numbers generated by src/01-05 scripts; see results/metrics.json.</footer>
</main>
<script>
  // Re-fit every chart to its card once the page layout is final
  window.addEventListener("load", function () {{
    document.querySelectorAll(".js-plotly-plot").forEach(function (p) {{ Plotly.Plots.resize(p); }});
  }});
</script>
</body>
</html>
"""
OUT.write_text(html, encoding="utf-8")
print(f"Saved {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB)")
