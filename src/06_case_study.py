"""
06_case_study.py - Build docs/case_study.docx (and try docs/case_study.pdf).

Every number in the document is read from results/metrics.json or
results/tables/*.csv, so the case study always matches the analysis.
Charts come from results/charts/ and the process flows from docs/diagrams/.

Run from the project root (after 04_charts.py):   python src/06_case_study.py
"""

import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
CHARTS = ROOT / "results" / "charts"
DIAGRAMS = ROOT / "docs" / "diagrams"
OUT_DOCX = ROOT / "docs" / "case_study.docx"
OUT_PDF = ROOT / "docs" / "case_study.pdf"

m = json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))
D, A, I, C = m["data"], m["analysis"], m["impact"], m["charts"]
cons, expd = I["conservative"], I["expected"]

DARK = RGBColor(0x0B, 0x0B, 0x0B)
GREY = RGBColor(0x52, 0x51, 0x4E)
BLUE = RGBColor(0x1C, 0x5C, 0xAB)


def n(x, d=1):
    """Number with thousands separator and d decimals (d=0 for whole numbers)."""
    return f"{x:,.{d}f}"


# ---------------------------------------------------------------------------
# Document setup: margins, fonts, heading styles, page numbers
# ---------------------------------------------------------------------------
doc = Document()
for section in doc.sections:
    section.top_margin = section.bottom_margin = Cm(2.0)
    section.left_margin = section.right_margin = Cm(2.2)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.1

for level, size in [(1, 15), (2, 12)]:
    style = doc.styles[f"Heading {level}"]
    style.font.name = "Calibri"
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.color.rgb = BLUE if level == 1 else DARK
    style.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    style.paragraph_format.space_after = Pt(4)


def add_page_number_footer():
    """Footer: 'Priyangi Singh Chouhan | Olist delivery case study | Page N'."""
    p = doc.sections[0].footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Priyangi Singh Chouhan  |  Olist delivery case study  |  Page ")
    run.font.size, run.font.color.rgb = Pt(8.5), GREY
    # A PAGE field is inserted with raw Word XML (python-docx has no helper for it)
    for tag, text in [("begin", None), (None, "PAGE"), ("end", None)]:
        r = p.add_run()
        r.font.size, r.font.color.rgb = Pt(8.5), GREY
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        r._r.append(el)


add_page_number_footer()


# ---------------------------------------------------------------------------
# Small helpers so the content below reads like a document
# ---------------------------------------------------------------------------
def h1(text):
    doc.add_heading(text, level=1)


def h2(text):
    doc.add_heading(text, level=2)


def para(text, bold_lead=None, italic=False, size=None, color=None):
    """Paragraph; bold_lead is an optional bold phrase at the start."""
    p = doc.add_paragraph()
    if bold_lead:
        p.add_run(bold_lead).bold = True
    r = p.add_run(text)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    return p


def bullets(items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        if isinstance(item, tuple):          # (bold lead, rest of text)
            p.add_run(item[0]).bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)
        p.paragraph_format.space_after = Pt(2)


def shade(cell, hex_fill):
    """Background colour for a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def table(header, rows, widths=None):
    """Simple grid table with a shaded header row."""
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(h))
        run.bold, run.font.size = True, Pt(9)
        shade(cell, "DCE8F7")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            cells[i].paragraphs[0].add_run(str(v)).font.size = Pt(9)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def chart(file_name, folder=CHARTS, width=13.5):
    path = folder / file_name
    if path.exists():
        doc.add_picture(str(path), width=Cm(width))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        para(f"[Image missing: {file_name}]", italic=True, color=GREY)


def so_what(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4)
    lead = p.add_run("So what: ")
    lead.bold, lead.font.color.rgb = True, BLUE
    p.add_run(text)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ---------------------------------------------------------------------------
# Data needed for tables
# ---------------------------------------------------------------------------
states = pd.read_csv(TABLES / "q07_customer_state_late.csv")
routes = pd.read_csv(TABLES / "q08_route_late.csv")
cats = pd.read_csv(TABLES / "q12_category_late.csv")
repeat = pd.read_csv(TABLES / "q15_repeat_purchase.csv")
bands = pd.read_csv(TABLES / "q11_seller_breach_band.csv")
rj = states.set_index("customer_state").loc["RJ"]
sp_rj = routes.set_index("route").loc["SP -> RJ"]
low_buffer = pd.read_csv(TABLES / "q14_promise_by_state.csv").head(5)
low_buffer_states = ", ".join(low_buffer["customer_state"])

# ===========================================================================
# Title block
# ===========================================================================
t = doc.add_paragraph()
r = t.add_run("Delivery Delay Root-Cause Analysis &\nCustomer Satisfaction Improvement")
r.bold, r.font.size, r.font.color.rgb = True, Pt(20), DARK
para("Olist E-Commerce (Brazil) | Business Analyst case study", size=12, color=GREY)
para("Priyangi Singh Chouhan  |  Version 1.0  |  18 November 2026", size=10, color=GREY)

# ===========================================================================
# 1. Executive summary
# ===========================================================================
h1("1. Executive summary")
para(f"I analysed {n(D['analysis_orders'], 0)} delivered orders from Olist, a Brazilian marketplace, "
     f"purchased between {D['window_start']} and {D['window_end']}, to find where delivery delays come "
     "from and what the business should fix first. Three numbers summarise the result:")
table(["Headline", "Number", "Meaning"], [
    ["Late delivery rate", f"{A['late_rate_pct']}%",
     f"{n(A['late_orders'], 0)} orders arrived after the promised date, on average "
     f"{A['avg_delay_days_late_orders']} days late"],
    ["1-2 star reviews when late", f"{A['bad_review_pct_late']}% vs {A['bad_review_pct_ontime']}%",
     f"A late order is {A['bad_review_multiple_late_vs_ontime']} times as likely to get a bad review"],
    ["Late orders avoidable", f"{n(cons['avoided_late_total'], 0)} to {n(expd['avoided_late_total'], 0)}",
     f"If the worst {I['worst_sellers_n']} sellers and 5 worst routes reached the platform average "
     f"({cons['avoided_late_pct_of_all_late']}% to {expd['avoided_late_pct_of_all_late']}% of late orders)"],
], widths=[4, 3.5, 9])
para(f"Most delay happens after the seller hands over the parcel: {A['late_share_after_handover_pct']}% of late "
     f"orders had a seller who met the handover deadline, and late orders spend {A['extra_transit_days_late']} "
     "extra days in carrier transit. Delays are concentrated in two peak periods, in routes out of São Paulo to "
     f"Rio de Janeiro and the North-East, and in {I['worst_sellers_n']} sellers. I recommend a weekly seller "
     "scorecard and handover alerts, route service levels with carriers, re-set delivery estimates for the "
     "states with the least buffer, and a peak-season capacity plan, tracked through a Delivery Performance "
     "Monitoring dashboard.")

# ===========================================================================
# 2. Problem and context
# ===========================================================================
h1("2. Problem and context")
para("Olist connects small Brazilian sellers to large online stores. The customer orders on the platform, "
     "the seller packs the item and hands it to a carrier, and the carrier delivers it. At checkout the "
     "customer sees an estimated delivery date, and after delivery they are asked for a 1 to 5 star review.")
para("Reviews matter to every party. A bad review lowers the seller's rating and future sales, raises "
     "customer service cost, and makes the customer less likely to buy again. The business question I set "
     "out to answer was:")
para("Late deliveries drive bad reviews. Where do delays come from, and what should the business fix first?",
     italic=True)

# ===========================================================================
# 3. Stakeholders
# ===========================================================================
h1("3. Stakeholders")
para("The full stakeholder analysis, power-interest grid and RACI are in the BRD (docs/BRD.md). "
     "The main groups are:")
table(["Stakeholder", "Interest", "What they need from this work"], [
    ["Head of Operations (sponsor)", "Lower late rate", "Platform KPIs, trend, impact of actions"],
    ["Seller Operations Manager", "Seller performance", "Seller scorecard and SLA breach list"],
    ["Logistics Partner Manager", "Carrier performance", "Route watchlist and transit times"],
    ["Customer Experience Lead", "Fewer bad reviews", "Delay vs review link, at-risk orders"],
    ["Product Manager, Delivery Promise", "Accurate estimates", "Estimate accuracy by state"],
    ["BI Lead", "Reliable pipeline", "Clear KPI definitions and requirements"],
], widths=[5, 4, 7.5])

# ===========================================================================
# 4. Approach and data
# ===========================================================================
h1("4. Approach and data")
bullets([
    ("Data: ", "Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0): orders, items, "
               "reviews, customers, sellers, products and payments. The geolocation file was not needed."),
    ("Cleaning (Python, pandas): ", "parsed dates, translated categories, kept the latest review per order, "
                                    "flagged timestamp errors and built an order-level table in SQLite."),
    ("Analysis (SQL): ", "15 queries, each answering one business question, run by a Python script that "
                         "saves every result to CSV."),
    ("Impact estimate (Python): ", "a what-if scenario with written assumptions and a conservative / "
                                   "expected range."),
    ("Outputs: ", "10 charts, an offline interactive dashboard, a BRD, AS-IS / TO-BE process flows and a "
                  "Power BI rebuild guide."),
])
para("From the 99,441 orders in the dataset I removed:")
table(["Step", "Orders removed", "Orders left"], [
    ["All orders", "-", n(D["total_orders"], 0)],
    ["Status not 'delivered'", n(D["excluded_not_delivered"], 0), n(D["orders_after_status_filter"], 0)],
    ["Delivered but no delivery date", n(D["excluded_delivered_no_date"], 0), n(D["orders_after_date_filter"], 0)],
    ["Purchased in a month with under 500 orders", n(D["excluded_outside_window"], 0),
     n(D["analysis_orders"], 0)],
], widths=[8, 4, 4])
para(f"A further {n(D['stage_invalid_orders'], 0)} orders ({D['stage_invalid_pct']}%) have impossible "
     "timestamps, mostly a carrier handover recorded before payment approval. They stay in the late-rate and "
     "review analysis but are left out of the journey-stage comparison.")

# ===========================================================================
# 5. Definitions
# ===========================================================================
h1("5. Definitions")
table(["Term", "Definition"], [
    ["Analysis population", f"Delivered orders with a delivery date, purchased {D['window_start']} to "
                            f"{D['window_end']} (months with 500+ orders)"],
    ["Late order", "Delivered date after estimated date, comparing dates only (the estimate has no time)"],
    ["Delay days", "Delivered date minus estimated date; positive means late"],
    ["Bad / good review", "Latest review score 1-2 / 4-5 (orders with several reviews keep the latest)"],
    ["Approval time", "Payment approved minus purchase"],
    ["Seller handling time", "Handed to carrier minus payment approved"],
    ["Carrier transit time", "Delivered to customer minus handed to carrier"],
    ["Promised lead time", "Estimated delivery date minus purchase"],
    ["Seller SLA breach", "Parcel handed to carrier after the item's shipping limit date"],
    ["Route", "Seller state to customer state, e.g. SP -> RJ"],
    ["Excess late orders", "Late orders minus (orders x platform late rate); how many more late orders a "
                           "seller or route has than an average one of the same size"],
], widths=[4.5, 12])
para(f"Seller and route analysis uses (order, seller) pairs. Only {D['multi_seller_pct']}% of orders have more "
     "than one seller, so this choice has little effect.", size=9.5, color=GREY)

# ===========================================================================
# 6. Findings
# ===========================================================================
page_break()
h1("6. Findings")

h2("Q1. How big is the problem, and how has it changed?")
chart("01_monthly_on_time_rate.png")
para(f"{A['on_time_rate_pct']}% of orders arrived on time. The rate was steady at around 95-97% for most months "
     f"but fell to {A['worst_month_on_time_pct']}% in {A['worst_month']}. February and March 2018 together had "
     f"{A['feb_mar_2018_share_of_orders_pct']}% of orders but {A['feb_mar_2018_share_of_late_pct']}% of all late "
     "orders. November 2017, the Black Friday month, shows a smaller dip.")
so_what("Lateness is not a constant background problem. A large part comes from short periods when the network "
        "is overloaded, so a peak-season capacity plan targets a third of late orders.")

h2("Q2. How much does lateness hurt reviews?")
chart("02_bad_reviews_by_delay.png")
para(f"Late orders average {A['avg_score_late']} stars against {A['avg_score_ontime']} for on-time orders. "
     f"Even 1-3 days late raises the 1-2 star share to {A['bad_review_pct_late_1_3_days']}%, and beyond a week "
     f"it is close to 80% ({A['bad_review_pct_late_15plus_days']}% at 15+ days).")
so_what("Customers react to the broken promise itself, not only to long waits. Preventing small delays, or "
        "warning the customer before the date passes, is worth the effort.")

h2("Q3. Where in the journey does the time go?")
chart("03_stage_durations.png")
para(f"Late orders spend {A['avg_transit_days_late']} days in carrier transit against "
     f"{A['avg_transit_days_ontime']} for on-time orders, {A['extra_transit_days_late']} extra days. Seller "
     f"handling adds only {A['extra_handling_days_late']} extra days. {A['late_share_after_handover_pct']}% of "
     "late orders had a seller who handed over before the deadline; the other "
     f"{A['late_share_seller_breach_pct']}% had at least one seller who missed it.")
so_what("The carrier leg is the main source of delay, so carrier and route management has the most potential. "
        "Sellers still matter for about a quarter of late orders.")

h2("Q4. Which regions and routes are worst?")
chart("05_state_late_rate.png", width=11.5)
para(f"North-East states have the highest late rates: {A['worst_state']} {A['worst_state_late_rate_pct']}%, "
     f"followed by MA and SE. In absolute terms Rio de Janeiro matters most: its {rj['late_rate_pct']}% late rate "
     f"on a large volume produces {rj['share_of_all_late_pct']}% of all late orders.")
chart("06_routes_late_orders.png")
para(f"The São Paulo to Rio de Janeiro route produced {n(sp_rj['late_pairs'], 0)} late orders at a "
     f"{sp_rj['late_rate_pct']}% late rate. São Paulo to São Paulo has more late orders "
     f"({n(A['top_route_late_count'], 0)}) but only because of its volume; its late rate "
     f"({A['top_route_late_rate_pct']}%) is below average.")
so_what("A short list of routes, led by SP -> RJ, deserves a dedicated conversation with carriers. The North-East "
        "needs both better carrier coverage and more realistic delivery promises.")

h2("Q5. Are delays concentrated in a few sellers?")
chart("04_sla_breach_vs_late.png", width=12)
para(f"When a seller misses the handover deadline, the order is late {A['late_rate_sla_breached_pct']}% of the "
     f"time, against {A['late_rate_sla_met_pct']}% when the deadline is met. Sellers who miss more than 15% of "
     f"deadlines run a {bands.iloc[-1]['late_rate_pct']}% late rate.")
para(f"Ranking sellers simply by number of late orders is misleading: the top 20% by late count produce "
     f"{A['top20_sellers_share_of_late_pct']}% of late orders, but they also handle "
     f"{A['top20_sellers_share_of_volume_pct']}% of all orders, so they are mostly just the biggest sellers. "
     "I ranked sellers instead by excess late orders (late orders above what the platform rate would predict "
     "for their volume), counting sellers with at least 30 orders.")
chart("07_worst_sellers.png", width=12)
so_what(f"{I['worst_sellers_n']} sellers, handling {I['worst_sellers_share_of_volume_pct']}% of orders, create "
        f"{n(I['worst_sellers_excess_late'], 0)} excess late orders. A scorecard built on this measure is fair "
        "to large sellers and points Seller Operations at the right accounts.")

h2("Q6. Do some product categories have more delays?")
top_cats = cats.head(5)
table(["Category (300+ orders)", "Orders", "Late rate"],
      [[r.main_category, n(r.orders, 0), f"{r.late_rate_pct}%"] for r in top_cats.itertuples()],
      widths=[7, 3, 3])
para(f"Of {A['categories_analysed']} categories with 300+ orders, most sit between 5% and 8%. Only "
     f"{A['worst_category']} stands out at {A['worst_category_late_rate_pct']}%, on a small volume.")
so_what("Category is not a main driver of lateness, so I do not recommend category-specific actions.")

h2("Q7. Is the delivery promise set correctly?")
chart("08_promise_accuracy.png")
para(f"{A['pct_orders_arrived_7plus_days_early']}% of orders arrive a week or more before the estimated date. "
     "The estimate is padded for most customers, yet still missed for others.")
chart("09_buffer_vs_late_by_state.png", width=12.5)
para(f"States with less buffer have more late orders (correlation r = {C['state_buffer_vs_late_corr']}). "
     f"{A['least_padded_state']} gets {A['least_padded_state_days_early']} days of buffer on average and is late "
     f"{A['least_padded_state_late_rate_pct']}% of the time, while {A['most_padded_state']} gets "
     f"{A['most_padded_state_days_early']} days.")
so_what(f"The promise is too tight for {low_buffer_states} and too loose elsewhere. Adding a few days for the "
        "tightest states and trimming padding where it is excessive would cut late orders without making the "
        "average promise longer.")

h2("Q8. Do customers come back after a late first order?")
table(["First order", "Customers", "Bought again", "Repeat rate"],
      [[r.first_order, n(r.customers, 0), n(r.repeat_customers, 0), f"{r.repeat_rate_pct}%"]
       for r in repeat.itertuples()], widths=[5, 3, 3, 3])
para(f"Customers whose first order was late came back {A['repeat_rate_first_late_pct']}% of the time against "
     f"{A['repeat_rate_first_ontime_pct']}% after an on-time first order.")
so_what(f"The direction is as expected, but only {A['repeat_rate_all_pct']}% of customers ever buy again, so this "
        "is directional evidence only. The review impact (Q2) is the stronger argument.")

# ===========================================================================
# 7. Root-cause summary
# ===========================================================================
h1("7. Root-cause summary")
table(["Root cause", "Evidence", "Owner"], [
    ["Carrier transit delays on long routes",
     f"{A['extra_transit_days_late']} extra transit days on late orders; SP -> RJ "
     f"{n(sp_rj['late_pairs'], 0)} late orders", "Logistics Partner Manager"],
    ["Network overload in peak periods",
     f"Feb-Mar 2018: {A['feb_mar_2018_share_of_late_pct']}% of late orders from "
     f"{A['feb_mar_2018_share_of_orders_pct']}% of volume", "Head of Operations"],
    ["Delivery promise not matched to the route",
     f"{A['least_padded_state']}: {A['least_padded_state_days_early']} days buffer, "
     f"{A['least_padded_state_late_rate_pct']}% late; r = {C['state_buffer_vs_late_corr']}", "Product Manager"],
    ["A group of sellers who hand over late",
     f"SLA breach late rate {A['late_rate_sla_breached_pct']}% vs {A['late_rate_sla_met_pct']}%; "
     f"{I['worst_sellers_n']} sellers, {n(I['worst_sellers_excess_late'], 0)} excess late orders",
     "Seller Operations Manager"],
    ["No monitoring or early warning", "Problems seen only through reviews after delivery", "BI Lead / CX Lead"],
], widths=[4.5, 8, 4])

# ===========================================================================
# 8. Recommendations
# ===========================================================================
h1("8. Prioritised recommendations")
para("I scored each recommendation on impact (share of late orders it addresses) and effort (cost, systems "
     "and partners involved).")
table(["#", "Recommendation", "Impact", "Effort", "Priority"], [
    ["1", "Weekly seller scorecard ranked by excess late orders, plus handover alerts 24 hours before the "
          "shipping limit date", "High", "Low", "Quick win"],
    ["2", f"Re-set delivery estimates for the lowest-buffer states ({low_buffer_states}) and trim padding "
          "where it is excessive", "Medium", "Low", "Quick win"],
    ["3", "Route-level service levels and monthly reviews with carriers for the 5 worst routes",
     "High", "Medium", "Major project"],
    ["4", "Peak-season capacity plan with carriers six weeks before Black Friday and other known peaks",
     "High", "Medium", "Major project"],
    ["5", "Proactive message and new date to customers whose order is at risk of being late",
     "Medium", "Medium", "Plan next"],
    ["6", f"Fix carrier handover date capture ({n(D['carrier_before_approval_orders'], 0)} orders "
          "recorded before approval)",
     "Low (enables the rest)", "Low", "Do alongside"],
    ["7", "Category-specific delivery actions", "Low", "Medium", "Not recommended"],
], widths=[0.8, 9, 2.2, 1.8, 2.7])

# ===========================================================================
# 9. Impact estimate
# ===========================================================================
h1("9. Impact estimate")
chart("10_impact_estimate.png", width=12.5)
table(["", "Conservative", "Expected"], [
    ["Share of gap to platform average closed", "50%", "100%"],
    ["Late orders avoided: sellers", n(cons["avoided_late_sellers"], 0), n(expd["avoided_late_sellers"], 0)],
    ["Late orders avoided: routes", n(cons["avoided_late_routes"], 0), n(expd["avoided_late_routes"], 0)],
    ["Late orders avoided: total", n(cons["avoided_late_total"], 0), n(expd["avoided_late_total"], 0)],
    ["Share of all late orders", f"{cons['avoided_late_pct_of_all_late']}%",
     f"{expd['avoided_late_pct_of_all_late']}%"],
    ["1-2 star reviews prevented", n(cons["bad_reviews_prevented"], 0), n(expd["bad_reviews_prevented"], 0)],
    ["Per year (x 12/20)", f"{n(cons['avoided_late_per_year'], 0)} late / "
                           f"{n(cons['bad_reviews_prevented_per_year'], 0)} reviews",
     f"{n(expd['avoided_late_per_year'], 0)} late / {n(expd['bad_reviews_prevented_per_year'], 0)} reviews"],
    ["Late rate after (order-seller pairs)", f"{cons['late_rate_after_pct']}%", f"{expd['late_rate_after_pct']}%"],
], widths=[7, 4.5, 4.5])
para("Assumptions:", bold_lead=None)
bullets([
    f"Platform average late rate = {I['platform_late_rate_pairs_pct']}% across order-seller pairs.",
    f"Worst sellers = top 20% of the {I['eligible_sellers']} sellers with 30+ orders, ranked by excess late "
    f"orders ({I['worst_sellers_n']} sellers). Ranking by raw late count would avoid "
    f"{n(I['avoided_if_ranked_by_late_count'], 0)} late orders instead of {n(expd['avoided_late_sellers'], 0)}.",
    "Worst routes = the 5 routes (300+ orders) with the most excess late orders after the seller fix, so no late "
    "order is counted twice.",
    f"Each avoided late order becomes on time; prevented bad reviews = avoided late orders x review coverage "
    f"({I['review_coverage_late_pct']}%) x the difference in bad-review rate ({I['bad_rate_late_pct']}% late vs "
    f"{I['bad_rate_ontime_pct']}% on time).",
    "This is a what-if estimate, not a forecast. It does not model the peak-season plan or the estimate "
    "re-set, so the full programme could do more.",
])

# ===========================================================================
# 10. Roadmap
# ===========================================================================
h1("10. Implementation roadmap")
table(["Phase", "Actions", "Output"], [
    ["Days 1-30", "Agree KPI definitions and targets with owners; launch the seller scorecard as a weekly "
                  "spreadsheet; start handover reminder emails for flagged sellers; fix carrier date capture",
     "Signed-off BRD; first scorecard; baseline report"],
    ["Days 31-60", "Build the Delivery Performance Monitoring dashboard; share route data with carriers and "
                   "agree service levels for the 5 worst routes; design the estimate change for low-buffer "
                   "states", "Dashboard live; carrier review pack; A/B test plan"],
    ["Days 61-90", "Run the estimate A/B test; agree the peak-season capacity plan; start at-risk customer "
                   "messages; first benefits review against baseline",
     "Test results; peak plan; 90-day benefits report"],
], widths=[2.5, 9.5, 4.5])

# ===========================================================================
# 11. KPIs
# ===========================================================================
h1("11. KPIs to monitor")
table(["KPI", "Baseline", "Owner", "Frequency"], [
    ["On-time rate", f"{A['on_time_rate_pct']}%", "Head of Operations", "Weekly"],
    ["Average delay of late orders", f"{A['avg_delay_days_late_orders']} days", "Logistics Partner Manager", "Weekly"],
    ["1-2 star review share", f"{A['bad_review_pct']}%", "CX Lead", "Weekly"],
    ["Seller SLA breach rate", f"{A['seller_sla_breach_pct']}%", "Seller Operations Manager", "Weekly"],
    ["Excess late orders, worst sellers", n(I["worst_sellers_excess_late"], 0), "Seller Operations Manager", "Weekly"],
    ["Late rate, SP -> RJ", f"{sp_rj['late_rate_pct']}%", "Logistics Partner Manager", "Weekly"],
    [f"Late rate, {A['least_padded_state']}", f"{A['least_padded_state_late_rate_pct']}%", "Product Manager", "Monthly"],
], widths=[6, 3, 5, 2.5])

# ===========================================================================
# 12. Limitations
# ===========================================================================
h1("12. Limitations")
bullets([
    "The data covers 2017-2018. Patterns should be re-checked on recent data before targets are fixed.",
    "Carrier names are not in the data, so carrier performance is inferred from routes.",
    f"{n(D['stage_invalid_orders'], 0)} orders have impossible timestamps and are excluded from stage analysis.",
    "There is no cost data, so the impact is in orders and reviews, not money.",
    f"Repeat purchase is rare ({A['repeat_rate_all_pct']}%), so the repeat finding is directional.",
    "The analysis shows association, not proof of cause. The A/B test and the 90-day review are how I would "
    "confirm the effect of each action.",
    "Only delivered orders are covered; cancellations need a separate study.",
])

# ===========================================================================
# 13. Indian marketplaces
# ===========================================================================
h1("13. How this applies to Indian marketplaces")
para("The same problem and the same method carry over to Flipkart, Meesho and Amazon India:")
bullets([
    ("Small sellers: ", "Meesho in particular depends on small sellers who ship themselves, which is close to "
                        "Olist's model. A scorecard on excess late orders is fairer than raw counts when seller "
                        "size varies widely."),
    ("Long and uneven routes: ", "deliveries from metro seller hubs to Tier 2/3 towns and the North-East "
                                 "behave like Olist's São Paulo to North-East routes; route-level service levels "
                                 "and route-specific delivery promises apply directly."),
    ("Sale peaks: ", "festive sales such as Big Billion Days and the Great Indian Festival create the same "
                     "overload I saw in Brazil, so a capacity plan agreed with carriers before the sale is "
                     "essential."),
    ("Delivery promise by pincode: ", "Indian platforms already show dates by pincode; the buffer analysis by "
                                      "state can be run by pincode cluster to find where the promise is too "
                                      "tight."),
    ("Extra Indian metrics: ", "for cash-on-delivery orders I would add return-to-origin (RTO) rate and "
                               "failed-delivery attempts as KPIs next to on-time rate."),
])

# ===========================================================================
# Appendix: process flows
# ===========================================================================
page_break()
h1("Appendix: AS-IS and TO-BE process flows")
para("Four swimlanes: Customer, Platform, Seller, Carrier. Orange boxes are pain points on the current process; "
     "blue boxes are the improvements. Full-size versions and Mermaid sources are in docs/process_flows.md.",
     size=9.5, color=GREY)
# Put the two flows side by side in a borderless 2-column table so they share one page
flows = doc.add_table(rows=2, cols=2)
flows.alignment = WD_TABLE_ALIGNMENT.CENTER
for col, (label, image) in enumerate([("AS-IS", "as_is.png"), ("TO-BE", "to_be.png")]):
    head = flows.rows[0].cells[col].paragraphs[0]
    head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    head.add_run(label).bold = True
    pic = flows.rows[1].cells[col].paragraphs[0]
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic.add_run().add_picture(str(DIAGRAMS / image), width=Cm(8.2))

doc.save(OUT_DOCX)
print(f"Saved {OUT_DOCX.relative_to(ROOT)}")

# ---------------------------------------------------------------------------
# PDF: docx2pdf drives Microsoft Word, so it only works where Word is installed
# ---------------------------------------------------------------------------
if OUT_PDF.exists():
    OUT_PDF.unlink()          # remove the old PDF so we can tell whether this run made a new one
try:
    from docx2pdf import convert
    convert(str(OUT_DOCX), str(OUT_PDF))
except Exception as err:
    # docx2pdf sometimes raises an error while closing Word even though the PDF was written
    print(f"docx2pdf reported: {err}")

if OUT_PDF.exists():
    print(f"Saved {OUT_PDF.relative_to(ROOT)}")
else:
    print("PDF not created. Open case_study.docx in Word/WPS and export as PDF.")
