"""
07_website.py - Build index.html, the project's home page (served by GitHub Pages).

Anyone can open the live site and see the problem, the headline numbers, every
finding with its chart, the recommendations, the process maps and links to the
dashboard, case study, BRD, SQL and notebook - with nothing to install.

All numbers are read from results/metrics.json and results/tables/*.csv.

Run from the project root (after 06_case_study.py):   python src/07_website.py
"""

import html
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
OUT = ROOT / "index.html"
REPO = "https://github.com/spriyangi232-lab/olist-ba-project"
BLOB = f"{REPO}/blob/main"          # GitHub renders .md, .sql and .ipynb files nicely

m = json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))
D, A, I, C = m["data"], m["analysis"], m["impact"], m["charts"]
cons, expd = I["conservative"], I["expected"]
sp_rj = pd.read_csv(TABLES / "q08_route_late.csv").set_index("route").loc["SP -> RJ"]
low_buffer = ", ".join(pd.read_csv(TABLES / "q14_promise_by_state.csv").head(5)["customer_state"])

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
kpis = [
    (f"{A['on_time_rate_pct']:.2f}%", "On-time delivery rate", f"{A['late_orders']:,} of {A['delivered_orders']:,} orders late"),
    (f"{A['avg_delay_days_late_orders']:.2f} days", "Average delay of late orders", "after the promised date"),
    (f"{A['bad_review_multiple_late_vs_ontime']}x", "More 1-2 star reviews when late",
     f"{A['bad_review_pct_late']:.2f}% vs {A['bad_review_pct_ontime']:.2f}%"),
    (f"{cons['avoided_late_total']:,}-{expd['avoided_late_total']:,}", "Late orders avoidable",
     f"and {cons['bad_reviews_prevented']:,}-{expd['bad_reviews_prevented']:,} bad reviews prevented"),
]

findings = [
    ("Q1", "How big is the problem?", "01_monthly_on_time_rate.png",
     f"{A['on_time_rate_pct']:.2f}% of orders arrived on time, but the rate fell to {A['worst_month_on_time_pct']:.2f}% "
     f"in March 2018. Feb-Mar 2018 had {A['feb_mar_2018_share_of_orders_pct']:.2f}% of orders and "
     f"{A['feb_mar_2018_share_of_late_pct']:.2f}% of all late orders: lateness comes in peaks."),
    ("Q2", "How much does lateness hurt reviews?", "02_bad_reviews_by_delay.png",
     f"Late orders average {A['avg_score_late']} stars vs {A['avg_score_ontime']} on time. Even 1-3 days late raises "
     f"the 1-2 star share to {A['bad_review_pct_late_1_3_days']:.2f}%."),
    ("Q3", "Where does the time go?", "03_stage_durations.png",
     f"Late orders spend {A['extra_transit_days_late']:.2f} extra days in carrier transit but only "
     f"{A['extra_handling_days_late']:.2f} extra days with the seller. {A['late_share_after_handover_pct']:.2f}% of late "
     "orders had a seller who handed over on time."),
    ("Q4", "Which regions are worst?", "05_state_late_rate.png",
     f"North-East states have the highest late rates ({A['worst_state']}: {A['worst_state_late_rate_pct']:.2f}%)."),
    ("Q4", "Which routes produce the most late orders?", "06_routes_late_orders.png",
     f"Sao Paulo to Rio de Janeiro alone produced {int(sp_rj['late_pairs']):,} late orders "
     f"({sp_rj['late_rate_pct']:.2f}% late)."),
    ("Q5", "Do sellers who miss the handover deadline cause delays?", "04_sla_breach_vs_late.png",
     f"Missing the deadline raises the late rate from {A['late_rate_sla_met_pct']:.2f}% to "
     f"{A['late_rate_sla_breached_pct']:.2f}%."),
    ("Q5", "Which sellers create excess delays?", "07_worst_sellers.png",
     f"Ranking by raw late count only finds the biggest sellers (top 20% = {A['top20_sellers_share_of_volume_pct']:.2f}% "
     f"of volume). Ranked by excess late orders, {I['worst_sellers_n']} sellers create "
     f"{I['worst_sellers_excess_late']:,} more late orders than an average seller would."),
    ("Q7", "Is the delivery promise accurate?", "08_promise_accuracy.png",
     f"{A['pct_orders_arrived_7plus_days_early']:.2f}% of orders arrive 7+ days early: the promise is padded for most "
     "customers."),
    ("Q7", "Where is the promise too tight?", "09_buffer_vs_late_by_state.png",
     f"States with less buffer see more late orders (r = {C['state_buffer_vs_late_corr']}). "
     f"{A['least_padded_state']} gets {A['least_padded_state_days_early']} days of buffer and is late "
     f"{A['least_padded_state_late_rate_pct']:.2f}% of the time."),
    ("Impact", "What is fixing it worth?", "10_impact_estimate.png",
     f"Bringing the worst {I['worst_sellers_n']} sellers and 5 worst routes to the platform average avoids "
     f"{cons['avoided_late_total']:,}-{expd['avoided_late_total']:,} late orders and "
     f"{cons['bad_reviews_prevented']:,}-{expd['bad_reviews_prevented']:,} 1-2 star reviews over 20 months."),
]

recommendations = [
    ("Seller scorecard and handover alerts", "Weekly ranking by excess late orders; alert 24 hours before the shipping limit date.", "Quick win"),
    ("Re-set delivery estimates", f"Add buffer for the lowest-buffer states ({low_buffer}); trim it where it is excessive.", "Quick win"),
    ("Route service levels with carriers", "Targets and monthly reviews for SP to RJ, SP to BA, SP to CE and PR to RJ.", "Major project"),
    ("Peak-season capacity plan", "Agree carrier capacity six weeks before Black Friday and other known peaks.", "Major project"),
    ("Proactive customer messages", "Tell customers about an at-risk order before the promised date passes.", "Plan next"),
]

docs = [
    ("Interactive dashboard", "KPI tiles, trend, states, routes, sellers, categories", "dashboard/dashboard.html", "Open"),
    ("Case study (PDF, 12 pages)", "Full write-up with charts, recommendations and roadmap", "docs/case_study.pdf", "Read"),
    ("Business Requirements Document", "Objectives, stakeholders, RACI, FR-01 to FR-16, KPIs", f"{BLOB}/docs/BRD.md", "Read"),
    ("Process flows", "AS-IS and TO-BE swimlanes with pain points and fixes", f"{BLOB}/docs/process_flows.md", "Read"),
    ("SQL analysis", "15 queries, each labelled with its business question", f"{BLOB}/sql/analysis.sql", "View"),
    ("Notebook walkthrough", "Question, query, result, chart and insight", f"{BLOB}/notebooks/analysis.ipynb", "View"),
    ("Data validation report", "Row counts, exclusions and data-quality issues", f"{BLOB}/docs/data_validation_report.md", "Read"),
    ("Power BI guide", "Data model, DAX measures and layout to rebuild the dashboard", f"{BLOB}/docs/powerbi_guide.md", "Read"),
]

e = html.escape

kpi_html = "\n".join(
    f'<div class="kpi"><div class="kpi-value">{e(v)}</div><div class="kpi-label">{e(l)}</div>'
    f'<div class="kpi-note">{e(n)}</div></div>' for v, l, n in kpis)

finding_html = "\n".join(
    f'''<article class="finding">
      <div class="finding-text"><span class="tag">{e(tag)}</span><h3>{e(q)}</h3><p>{e(text)}</p></div>
      <a href="results/charts/{img}" class="finding-img"><img src="results/charts/{img}" alt="{e(q)}" loading="lazy"></a>
    </article>''' for tag, q, img, text in findings)

rec_html = "\n".join(
    f'<li><div><strong>{e(t)}</strong><span>{e(d)}</span></div><em>{e(p)}</em></li>' for t, d, p in recommendations)

doc_html = "\n".join(
    f'<a class="doc" href="{e(href)}"><div><strong>{e(t)}</strong><span>{e(d)}</span></div><b>{e(act)} &rarr;</b></a>'
    for t, d, href, act in docs)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Olist Delivery Delay Case Study</title>
<meta name="description" content="Business Analyst case study by Priyangi Singh Chouhan: why {A['late_rate_pct']}% of Olist orders arrive late and what to fix first.">
<style>
  :root {{ --bg:#f9f9f7; --card:#ffffff; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --line:rgba(11,11,11,.10);
          --blue:#2a78d6; --blue-dark:#1c5cab; --orange:#eb6834; --wash:#eef4fc; }}
  * {{ box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI",system-ui,-apple-system,sans-serif; line-height:1.55; }}
  a {{ color:var(--blue-dark); }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:0 16px; }}
  h1, .lead, .byline {{ overflow-wrap:anywhere; }}
  body {{ overflow-x:hidden; }}
  header.hero {{ background:var(--card); border-bottom:1px solid var(--line); padding:48px 0 36px; }}
  .eyebrow {{ color:var(--blue-dark); font-weight:600; font-size:14px; letter-spacing:.04em; text-transform:uppercase; }}
  h1 {{ font-size:clamp(28px,4.5vw,42px); line-height:1.15; margin:8px 0 12px; }}
  .lead {{ font-size:18px; color:var(--ink2); max-width:760px; margin:0 0 20px; }}
  .byline {{ color:var(--muted); font-size:14px; }}
  .btns {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:22px; }}
  .btn {{ display:inline-block; padding:10px 18px; border-radius:8px; font-weight:600; text-decoration:none; border:1px solid var(--blue); }}
  .btn.primary {{ background:var(--blue); color:#fff; }}
  .btn.ghost {{ color:var(--blue-dark); background:#fff; }}
  nav.toc {{ position:sticky; top:0; z-index:5; background:rgba(249,249,247,.95); backdrop-filter:blur(6px); border-bottom:1px solid var(--line); }}
  nav.toc .wrap {{ display:flex; gap:18px; overflow-x:auto; padding-top:10px; padding-bottom:10px; font-size:14px; white-space:nowrap; }}
  nav.toc a {{ text-decoration:none; color:var(--ink2); }}
  section {{ padding:40px 0 8px; }}
  h2 {{ font-size:26px; margin:0 0 6px; }}
  .sub {{ color:var(--ink2); margin:0 0 20px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr)); gap:12px; }}
  .kpi {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px; }}
  .kpi-value {{ font-size:30px; font-weight:700; }}
  .kpi-label {{ font-weight:600; margin-top:2px; }}
  .kpi-note {{ color:var(--muted); font-size:13px; }}
  .problem {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:12px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px; }}
  .card h3 {{ margin:0 0 6px; font-size:17px; }}
  .card p {{ margin:0; color:var(--ink2); }}
  .finding {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.5fr); gap:20px; align-items:center;
             background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px; margin-bottom:14px; }}
  .finding h3 {{ margin:6px 0; font-size:19px; }}
  .finding p {{ margin:0; color:var(--ink2); }}
  .finding-img img {{ width:100%; height:auto; display:block; border-radius:6px; }}
  .tag {{ display:inline-block; background:var(--wash); color:var(--blue-dark); font-size:12px; font-weight:700; padding:2px 8px; border-radius:99px; }}
  ol.recs {{ list-style:none; padding:0; margin:0; counter-reset:r; display:grid; gap:10px; }}
  ol.recs li {{ counter-increment:r; display:flex; gap:14px; align-items:center; justify-content:space-between;
               background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 18px; }}
  ol.recs li::before {{ content:counter(r); font-weight:700; color:#fff; background:var(--blue); border-radius:50%;
                        min-width:28px; height:28px; display:grid; place-items:center; }}
  ol.recs li div {{ flex:1; }}
  ol.recs strong, .doc strong {{ display:block; }}
  ol.recs span, .doc span {{ color:var(--ink2); font-size:14px; }}
  ol.recs em {{ font-style:normal; font-size:12px; font-weight:700; color:var(--blue-dark); background:var(--wash);
               padding:3px 10px; border-radius:99px; white-space:nowrap; }}
  .flows {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr)); gap:12px; }}
  .flows figure {{ margin:0; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; }}
  .flows img {{ width:100%; height:auto; }}
  .flows figcaption {{ font-weight:600; margin-bottom:8px; }}
  .docs {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr)); gap:10px; }}
  .doc {{ display:flex; gap:12px; align-items:center; justify-content:space-between; text-decoration:none; color:var(--ink);
         background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 18px; }}
  .doc:hover {{ border-color:var(--blue); }}
  .doc b {{ color:var(--blue-dark); white-space:nowrap; font-size:14px; }}
  .steps {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr)); gap:10px; counter-reset:s; }}
  .step {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; }}
  .step b {{ display:block; }}
  .step span {{ color:var(--ink2); font-size:14px; }}
  .tools {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
  .tools span {{ background:var(--card); border:1px solid var(--line); border-radius:99px; padding:4px 12px; font-size:13px; }}
  footer {{ margin-top:40px; padding:24px 0 40px; border-top:1px solid var(--line); color:var(--muted); font-size:13px; }}
  @media (max-width:760px) {{
    .finding {{ grid-template-columns:1fr; }}
    ol.recs li {{ flex-wrap:wrap; }}
    header.hero {{ padding-top:32px; }}
  }}
</style>
</head>
<body>
<header class="hero">
  <div class="wrap">
    <div class="eyebrow">Business Analyst case study</div>
    <h1>Delivery Delay Root-Cause Analysis &amp; Customer Satisfaction Improvement</h1>
    <p class="lead">Late deliveries drive bad reviews. Using {D['analysis_orders']:,} delivered orders from Olist, a Brazilian
    marketplace, I found where the delays come from and what the business should fix first.</p>
    <div class="byline">Priyangi Singh Chouhan &middot; SQL &middot; Python &middot; BRD &middot; Process mapping &middot; Dashboard</div>
    <div class="btns">
      <a class="btn primary" href="dashboard/dashboard.html">Open the dashboard</a>
      <a class="btn ghost" href="docs/case_study.pdf">Read the case study</a>
      <a class="btn ghost" href="{REPO}">View the code</a>
    </div>
  </div>
</header>

<nav class="toc"><div class="wrap">
  <a href="#results">Results</a><a href="#problem">Problem</a><a href="#findings">Findings</a>
  <a href="#recommendations">Recommendations</a><a href="#process">Process maps</a>
  <a href="#approach">Approach</a><a href="#documents">Documents</a>
</div></nav>

<main class="wrap">
  <section id="results">
    <h2>Headline results</h2>
    <p class="sub">Orders purchased {D['window_start']} to {D['window_end']}. Late = delivered after the date promised at checkout.</p>
    <div class="kpis">{kpi_html}</div>
  </section>

  <section id="problem">
    <h2>The business problem</h2>
    <p class="sub">Where do delays come from, and what should the business fix first?</p>
    <div class="problem">
      <div class="card"><h3>Why it matters</h3><p>A bad review lowers the seller's rating and future sales, adds customer-service
      cost and makes the customer less likely to return. Late orders get a 1-2 star review {A['bad_review_pct_late']:.2f}% of the time.</p></div>
      <div class="card"><h3>Who is involved</h3><p>Four parties touch every order: customer, platform, seller and carrier. Each controls a
      different part of the delay, so each needs its own measure and owner.</p></div>
      <div class="card"><h3>What I delivered</h3><p>A BRD, AS-IS / TO-BE process maps, 15 SQL analyses, an impact estimate,
      10 charts, an interactive dashboard and a 12-page case study.</p></div>
    </div>
  </section>

  <section id="findings">
    <h2>Findings</h2>
    <p class="sub">One business question per chart. Click a chart to enlarge it.</p>
    {finding_html}
  </section>

  <section id="recommendations">
    <h2>Prioritised recommendations</h2>
    <p class="sub">Ranked by impact and effort. Full roadmap (30/60/90 days) in the case study.</p>
    <ol class="recs">{rec_html}</ol>
  </section>

  <section id="process">
    <h2>Process maps</h2>
    <p class="sub">Order fulfilment across customer, platform, seller and carrier. Orange = pain point, blue = improvement.</p>
    <div class="flows">
      <figure><figcaption>AS-IS</figcaption><a href="docs/diagrams/as_is.png"><img src="docs/diagrams/as_is.png" alt="AS-IS order fulfilment flow" loading="lazy"></a></figure>
      <figure><figcaption>TO-BE</figcaption><a href="docs/diagrams/to_be.png"><img src="docs/diagrams/to_be.png" alt="TO-BE order fulfilment flow" loading="lazy"></a></figure>
    </div>
  </section>

  <section id="approach">
    <h2>Approach</h2>
    <p class="sub">From business problem to measurable recommendation.</p>
    <div class="steps">
      <div class="step"><b>1. Define</b><span>Problem, stakeholders, SMART objectives, requirements</span></div>
      <div class="step"><b>2. Map</b><span>AS-IS and TO-BE swimlanes with pain points</span></div>
      <div class="step"><b>3. Clean</b><span>{D['analysis_orders']:,} orders, written definitions, data-quality flags</span></div>
      <div class="step"><b>4. Analyse</b><span>15 SQL queries, one per business question</span></div>
      <div class="step"><b>5. Estimate</b><span>Impact range with written assumptions</span></div>
      <div class="step"><b>6. Communicate</b><span>Dashboard, case study, KPI definitions</span></div>
    </div>
    <div class="tools"><span>SQL (SQLite, CTEs, window functions)</span><span>Python (pandas)</span><span>matplotlib</span>
      <span>Plotly</span><span>python-docx</span><span>Mermaid</span><span>Power BI</span><span>Jupyter</span></div>
  </section>

  <section id="documents">
    <h2>Documents and code</h2>
    <p class="sub">Everything opens in the browser.</p>
    <div class="docs">{doc_html}</div>
  </section>
</main>

<footer><div class="wrap">
  Built by Priyangi Singh Chouhan. Data: Brazilian E-Commerce Public Dataset by Olist
  (<a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">Kaggle</a>,
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>). Non-commercial portfolio project, not affiliated with Olist.
  Every number on this page is generated from <a href="{BLOB}/results/metrics.json">results/metrics.json</a>.
</div></footer>
</body>
</html>
"""
OUT.write_text(page, encoding="utf-8")
print(f"Saved {OUT.relative_to(ROOT)}")
