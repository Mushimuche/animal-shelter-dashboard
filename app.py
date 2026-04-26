"""
Left Behind: A Data-Driven Analysis of Long Beach Animal Shelter Outcome Patterns
Shiny for Python Dashboard  –  v2 (redesigned)
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
from pathlib import Path

# ─────────────────────────────────────────────
# DATA LOADING & CLEANING
# ─────────────────────────────────────────────

def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["Intake Date"]  = pd.to_datetime(df["Intake Date"],  errors="coerce")
    df["Outcome Date"] = pd.to_datetime(df["Outcome Date"], errors="coerce")
    df["DOB"]          = pd.to_datetime(df["DOB"],          errors="coerce")
    df = df[df["Outcome Type"].notna()].copy()
    df["age_at_intake_years"] = (df["Intake Date"] - df["DOB"]).dt.days / 365.25
    df.loc[df["age_at_intake_years"] < 0,  "age_at_intake_years"] = np.nan
    df.loc[df["age_at_intake_years"] > 30, "age_at_intake_years"] = np.nan
    bins   = [0, 0.5, 1, 3, 7, 15, 100]
    labels = ["< 6 mo", "6-12 mo", "1-3 yr", "3-7 yr", "7-15 yr", "15+ yr"]
    df["age_group"] = pd.cut(df["age_at_intake_years"], bins=bins, labels=labels)
    df["intake_year"]  = df["Intake Date"].dt.year
    df["intake_month"] = df["Intake Date"].dt.month
    df["is_adoption"]  = (df["Outcome Type"] == "ADOPTION").astype(int)
    sex_map = {
        "Spayed": "Spayed Female", "Neutered": "Neutered Male",
        "Female": "Intact Female", "Male": "Intact Male", "Unknown": "Unknown",
    }
    df["Sex Clean"] = df["Sex"].map(sex_map).fillna("Unknown")
    df["Intake Condition"] = df["Intake Condition"].str.strip()
    df = df[df["intake_year"] >= 2017]
    return df


CSV_PATH = "https://github.com/Mushimuche/animal-shelter-dashboard/raw/refs/heads/main/animal-shelter-intakes-and-outcomes.csv"
df_full  = load_and_clean(CSV_PATH)

ANIMAL_TYPES = ["All"] + sorted(df_full["Animal Type"].unique().tolist())
YEARS        = ["All"] + sorted(df_full["intake_year"].dropna().astype(int).unique().tolist(), reverse=True)
INTAKE_TYPES = ["All"] + sorted(df_full["Intake Type"].dropna().unique().tolist())

# Design tokens
ACCENT  = ["#7c6af7","#43d9ad","#f97068","#fbbf24","#60a5fa",
           "#e879f9","#34d399","#fb923c","#a78bfa","#22d3ee"]
BG_PLOT = "rgba(0,0,0,0)"
GRID    = "rgba(255,255,255,0.055)"
MUTED   = "#8896b3"
FONT    = "Avenir Next, Avenir, Nunito, Century Gothic, Trebuchet MS, sans-serif"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def compute_kpis(df):
    total     = len(df)
    adoptions = (df["Outcome Type"] == "ADOPTION").sum()
    live      = df["was_outcome_alive"].sum()
    euth      = (df["Outcome Type"] == "EUTHANASIA").sum()
    los       = df["intake_duration"].median()
    return dict(
        total     = f"{total:,}",
        adoptions = f"{int(adoptions):,}",
        live_rate = f"{live/total*100:.1f}%" if total else "-",
        euth_rate = f"{euth/total*100:.1f}%" if total else "-",
        avg_los   = f"{los:.0f} d" if not np.isnan(los) else "-",
    )


def dl(fig, title="", height=360):
    """Apply consistent dark layout."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#f0f4ff", family=FONT),
                   x=0, xanchor="left", pad=dict(l=10, t=6)),
        paper_bgcolor=BG_PLOT, plot_bgcolor=BG_PLOT,
        font=dict(color=MUTED, family=FONT, size=11),
        height=height,
        margin=dict(t=52, b=38, l=52, r=18),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="#c4caed")),
        hoverlabel=dict(bgcolor="#1a1f3a", font_size=12, font_family=FONT),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID,
                     tickfont=dict(color=MUTED, family=FONT))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID,
                     tickfont=dict(color=MUTED, family=FONT))
    return fig


def card(widget):
    return ui.div(widget, class_="chart-card")

# ─────────────────────────────────────────────
# INLINE CSS  (avoids needing static file serve)
# ─────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');

:root {
  --font: 'Avenir Next','Avenir','Nunito','Century Gothic','Trebuchet MS',sans-serif;
  --bg:        #06091a;
  --bg-card:   rgba(255,255,255,0.045);
  --border:    rgba(255,255,255,0.08);
  --a1: #7c6af7; --a2: #43d9ad; --a3: #f97068;
  --a4: #fbbf24; --a5: #60a5fa;
  --txt: #f0f4ff;  --muted: #8896b3;
}

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; font-family: var(--font) !important; }
body {
  margin:0; background: var(--bg); color: var(--txt);
  background-image:
    linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,0.018) 1px,transparent 1px);
  background-size: 44px 44px;
  overflow-x: hidden;
  position: relative;
}

/* ── Animated orbs ── */
body::before {
  content:''; position:fixed; border-radius:50%;
  width:750px; height:750px;
  background: radial-gradient(circle, rgba(124,106,247,0.35) 0%, transparent 65%);
  top:-220px; left:-220px; filter:blur(90px); opacity:1;
  animation: orb1 20s ease-in-out infinite alternate; pointer-events:none; z-index:0;
}
body::after {
  content:''; position:fixed; border-radius:50%;
  width:650px; height:650px;
  background: radial-gradient(circle, rgba(67,217,173,0.25) 0%, transparent 65%);
  bottom:-180px; right:-180px; filter:blur(90px); opacity:1;
  animation: orb2 25s ease-in-out infinite alternate; pointer-events:none; z-index:0;
}
.orb3 {
  position:fixed; border-radius:50%;
  width:450px; height:450px;
  background: radial-gradient(circle, rgba(249,112,104,0.2) 0%, transparent 65%);
  top:42%; left:48%; transform:translate(-50%,-50%);
  filter:blur(100px); opacity:1;
  animation: orb3 30s ease-in-out infinite alternate; pointer-events:none; z-index:0;
}

@keyframes orb1 {
  0%   { transform: translate(0,0) scale(1); }
  50%  { transform: translate(130px,90px) scale(1.18); }
  100% { transform: translate(60px,170px) scale(0.92); }
}
@keyframes orb2 {
  0%   { transform: translate(0,0) scale(1); }
  50%  { transform: translate(-110px,-70px) scale(1.22); }
  100% { transform: translate(-50px,-140px) scale(0.88); }
}
@keyframes orb3 {
  0%   { transform: translate(-50%,-50%) scale(1); }
  100% { transform: translate(-44%,-58%) scale(1.35); }
}

/* ── Layout layers above orbs ── */
.container-fluid, nav, .tab-content, .dashboard-header,
.filter-bar, .kpi-row, .chart-card, .insight-box { position:relative; z-index:1; }

/* ── Header ── */
.dashboard-header {
  padding: 30px 32px 14px;
  border-bottom: 1px solid var(--border);
  background: rgba(6,9,26,0.55);
  backdrop-filter: blur(14px);
}
.dashboard-header h1 {
  font-size:1.75rem; font-weight:800; letter-spacing:-0.025em; margin:0 0 4px;
  background: linear-gradient(130deg, #f0f4ff 0%, var(--a1) 55%, var(--a2) 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.dashboard-header .subtitle { color:var(--muted); font-size:.83rem; margin:0; }

/* ── Filters ── */
.filter-bar {
  padding: 14px 32px; gap:16px; display:flex;
  background: rgba(6,9,26,0.4); backdrop-filter:blur(8px);
  border-bottom: 1px solid var(--border);
}
.shiny-input-container { flex:1; }
.shiny-input-container label {
  color:var(--muted) !important; font-size:.72rem !important;
  font-weight:700 !important; text-transform:uppercase;
  letter-spacing:.09em; margin-bottom:5px; display:block;
}
.shiny-input-container select, select.form-control {
  background: rgba(255,255,255,0.055) !important;
  border: 1px solid var(--border) !important; border-radius:9px !important;
  color:var(--txt) !important; font-size:.87rem !important;
  padding: 8px 12px !important; width:100%;
  transition: border-color .2s, box-shadow .2s;
}
.shiny-input-container select:focus {
  border-color:var(--a1) !important; outline:none;
  box-shadow: 0 0 0 3px rgba(124,106,247,.22) !important;
}
select option { background:#0f172a; color:var(--txt); }

/* ── KPI row ── */
.kpi-row { display:flex; gap:14px; padding:20px 32px; }
.kpi-card {
  flex:1; background:var(--bg-card); border:1px solid var(--border);
  border-radius:16px; padding:20px 22px;
  backdrop-filter:blur(10px);
  transition: background .3s, transform .2s, box-shadow .2s;
  position:relative; overflow:hidden;
}
.kpi-card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px; border-radius:16px 16px 0 0;
}
.kpi-card:nth-child(1)::before { background:var(--a5); }
.kpi-card:nth-child(2)::before { background:var(--a2); }
.kpi-card:nth-child(3)::before { background:var(--a1); }
.kpi-card:nth-child(4)::before { background:var(--a3); }
.kpi-card:nth-child(5)::before { background:var(--a4); }
.kpi-card:hover { background:rgba(255,255,255,.07); transform:translateY(-3px);
                  box-shadow:0 8px 32px rgba(0,0,0,.35); }
.kpi-icon  { font-size:1.3rem; margin-bottom:8px; display:block; }
.kpi-value { font-size:2rem !important; font-weight:800 !important;
             letter-spacing:-.025em; line-height:1; margin-bottom:5px; }
.kpi-card:nth-child(1) .kpi-value { color:var(--a5) !important; }
.kpi-card:nth-child(2) .kpi-value { color:var(--a2) !important; }
.kpi-card:nth-child(3) .kpi-value { color:var(--a1) !important; }
.kpi-card:nth-child(4) .kpi-value { color:var(--a3) !important; }
.kpi-card:nth-child(5) .kpi-value { color:var(--a4) !important; }
.kpi-label { font-size:.73rem !important; color:var(--muted) !important;
             font-weight:600; text-transform:uppercase; letter-spacing:.07em; }

/* ── Nav tabs ── */
.nav-tabs {
  border-bottom:1px solid var(--border) !important;
  padding:0 32px; background:rgba(6,9,26,.5); backdrop-filter:blur(8px); gap:2px;
}
.nav-tabs .nav-link {
  color:var(--muted) !important; font-weight:600; font-size:.84rem;
  border:none !important; border-radius:0 !important;
  padding:11px 17px !important; border-bottom:2px solid transparent !important;
  transition:color .2s, border-color .2s;
}
.nav-tabs .nav-link:hover { color:var(--txt) !important;
                             border-bottom-color:var(--border) !important;
                             background:transparent !important; }
.nav-tabs .nav-link.active { color:var(--txt) !important;
                              background:transparent !important;
                              border-bottom:2px solid var(--a1) !important; }

/* ── Tab content & charts ── */
.tab-content { padding:22px 32px; }
.chart-card {
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:16px; padding:6px;
  backdrop-filter:blur(10px); margin-bottom:16px;
  transition:background .3s;
}
.chart-card:hover { background:rgba(255,255,255,.065); }

/* ── Insights ── */
.insight-box {
  background:rgba(124,106,247,.07) !important;
  border:1px solid rgba(124,106,247,.18) !important;
  border-left:3px solid var(--a1) !important;
  border-radius:12px !important; padding:18px 20px !important;
  margin-top:14px !important; font-size:.88rem !important;
  color:#c4caed !important; line-height:1.75 !important;
  transition:background .2s;
}
.insight-box:hover { background:rgba(124,106,247,.12) !important; }
.insight-box h5 { color:var(--txt) !important; font-weight:700 !important;
                  font-size:.93rem !important; margin-bottom:7px !important; }

ol li { color:#a0aec0; line-height:2.2; font-size:.9rem; }
h3 { font-weight:800 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(255,255,255,.13); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:rgba(255,255,255,.22); }
"""

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

app_ui = ui.page_fluid(

    ui.tags.head(
        ui.tags.link(rel="stylesheet",
                     href="https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap"),
        ui.tags.style(CSS),
    ),

    # Floating orb 3 (can't do 3 pseudo-elements, use a real div)
    ui.div(class_="orb3"),

    # Header
    ui.div(
        ui.h1("🐾 Left Behind: Long Beach Animal Shelter Outcome Patterns"),
        ui.p("A data-driven analysis of 54 k+ intake records  ·  City of Long Beach Open Data Portal  ·  Updated Apr 23 2026",
             class_="subtitle"),
        class_="dashboard-header"
    ),

    # Filters
    ui.div(
        ui.layout_columns(
            ui.input_select("animal_type", "Animal Type", choices=ANIMAL_TYPES, selected="All"),
            ui.input_select("year",        "Intake Year",  choices=YEARS,        selected="All"),
            ui.input_select("intake_type", "Intake Type",  choices=INTAKE_TYPES, selected="All"),
            col_widths=[4, 4, 4],
        ),
        class_="filter-bar"
    ),

    # KPI row
    ui.div(
        ui.div(
            ui.div(ui.tags.span("🐾", class_="kpi-icon"),
                   ui.output_ui("kpi_total"),
                   ui.div("Total Animals Processed", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("🏠", class_="kpi-icon"),
                   ui.output_ui("kpi_adoptions"),
                   ui.div("Adoptions", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("💚", class_="kpi-icon"),
                   ui.output_ui("kpi_live"),
                   ui.div("Live Release Rate", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("⚠️", class_="kpi-icon"),
                   ui.output_ui("kpi_euth"),
                   ui.div("Euthanasia Rate", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("📅", class_="kpi-icon"),
                   ui.output_ui("kpi_los"),
                   ui.div("Median Length of Stay", class_="kpi-label"), class_="kpi-card"),
            class_="kpi-row"
        )
    ),

    # Tabs
    ui.navset_tab(

        ui.nav_panel("📊  Outcomes Overview",
            ui.layout_columns(card(output_widget("chart_outcome_dist")),
                               card(output_widget("chart_outcome_by_species")),
                               col_widths=[5,7]),
            ui.layout_columns(card(output_widget("chart_trend_yearly")),
                               card(output_widget("chart_live_by_condition")),
                               col_widths=[6,6]),
        ),

        ui.nav_panel("🐕  Animal Characteristics",
            ui.layout_columns(card(output_widget("chart_age_outcome")),
                               card(output_widget("chart_sex_outcome")),
                               col_widths=[6,6]),
            ui.layout_columns(card(output_widget("chart_intake_type")),
                               card(output_widget("chart_los_by_type")),
                               col_widths=[6,6]),
        ),

        ui.nav_panel("⏱️  Length of Stay",
            ui.layout_columns(card(output_widget("chart_los_outcome")),
                               card(output_widget("chart_los_species")),
                               col_widths=[6,6]),
            card(output_widget("chart_los_heatmap")),
        ),

        ui.nav_panel("📈  Trends Over Time",
            card(output_widget("chart_monthly_trend")),
            ui.layout_columns(card(output_widget("chart_yearly_mix")),
                               card(output_widget("chart_adoption_trend")),
                               col_widths=[6,6]),
        ),

        ui.nav_panel("💡  Insights & Recommendations",
            ui.h3("Key Findings", style="color:#f0f4ff; margin:0 0 4px;"),
            ui.p("Based on 54,100+ resolved shelter records · Long Beach Animal Care Services",
                 style="color:#8896b3; font-size:.83rem; margin-bottom:0;"),
            ui.div(ui.h5("🔬 Finding 1 — Intake Condition is the Strongest Predictor of Outcome"),
                   ui.p("Animals arriving NORMAL have a 95.4% live release rate. ILL SEVERE drops to 21.5% and INJURED SEVERE to 31.3%. Early triage and medical intervention at intake is the single highest-leverage action the shelter can take."),
                   class_="insight-box"),
            ui.div(ui.h5("⏳ Finding 2 — Length of Stay Predicts Outcome Type"),
                   ui.p("Adopted animals spend a median of 49 days in the shelter — roughly 6x longer than euthanised animals (5 days). Euthanasia often occurs before adoption marketing even begins. A mandatory 7-day marketing window for healthy animals could materially change outcomes."),
                   class_="insight-box"),
            ui.div(ui.h5("🐱 Finding 3 — Dogs Adopt Better Than Cats Despite More Cats"),
                   ui.p("Cats are the most common intake (25,760 records) yet have a lower adoption rate (24.3%) than dogs (28.8%). Targeted cat-adoption campaigns — reduced fees, foster-to-adopt, social spotlights — could reduce cat inventory pressure significantly."),
                   class_="insight-box"),
            ui.div(ui.h5("✂️ Finding 4 — Spayed/Neutered Animals Have Near-Perfect Live Release Rates"),
                   ui.p("Spayed animals achieve a 97.7% live release rate; neutered 95.5%. Intact females sit at 79.5% and intact males 77.8%. This strongly supports expanding TNR programs and pre-adoption spay/neuter partnerships."),
                   class_="insight-box"),
            ui.div(ui.h5("🚶 Finding 5 — Stray Intake Dominates; Owner Surrenders Are Controllable"),
                   ui.p("Stray animals (38,079 records, 70%) dominate intake. Owner surrenders (4,756) are the second-largest controllable category. Community outreach — vet assistance, training resources, temporary fostering — could reduce owner-surrender numbers."),
                   class_="insight-box"),
            ui.div(ui.h5("🦅 Finding 6 — Wild & Other Animals Drag Down the Headline Live Release Rate"),
                   ui.p("Wild animals have a 32.8% live release rate; OTHER animals 45.6%. Partnering with wildlife rehabilitation organisations and reporting companion vs. wild animals separately would give a more accurate and actionable performance picture."),
                   class_="insight-box"),
            ui.h3("Strategic Recommendations", style="color:#f0f4ff; margin:28px 0 10px;"),
            ui.tags.ol(
                ui.tags.li("Implement medical triage scoring at intake — prioritise borderline ILL/INJURED animals."),
                ui.tags.li("Introduce a 7-day mandatory marketing hold before euthanasia for healthy animals."),
                ui.tags.li("Launch targeted cat adoption campaigns (reduced fees, foster-to-adopt, social media)."),
                ui.tags.li("Expand TNR and pre-intake spay/neuter partnerships with local veterinarians."),
                ui.tags.li("Create an owner-support hotline to divert surrenders into voluntary fostering."),
                ui.tags.li("Partner with wildlife rehabilitation centres to route wild animal intakes appropriately."),
            ),
        ),

    ),
)

# ─────────────────────────────────────────────
# SERVER
# ─────────────────────────────────────────────

def server(input, output, session):

    @reactive.calc
    def dff():
        d = df_full.copy()
        if input.animal_type() != "All":
            d = d[d["Animal Type"] == input.animal_type()]
        if input.year() != "All":
            d = d[d["intake_year"] == int(input.year())]
        if input.intake_type() != "All":
            d = d[d["Intake Type"] == input.intake_type()]
        return d

    # ── KPIs ──────────────────────────────────────────────────────────────────
    @output
    @render.ui
    def kpi_total():
        return ui.div(compute_kpis(dff())["total"], class_="kpi-value")

    @output
    @render.ui
    def kpi_adoptions():
        return ui.div(compute_kpis(dff())["adoptions"], class_="kpi-value")

    @output
    @render.ui
    def kpi_live():
        return ui.div(compute_kpis(dff())["live_rate"], class_="kpi-value")

    @output
    @render.ui
    def kpi_euth():
        return ui.div(compute_kpis(dff())["euth_rate"], class_="kpi-value")

    @output
    @render.ui
    def kpi_los():
        return ui.div(compute_kpis(dff())["avg_los"], class_="kpi-value")

    # ── Charts ────────────────────────────────────────────────────────────────

    @output
    @render_widget
    def chart_outcome_dist():
        top = dff()["Outcome Type"].value_counts().head(10).reset_index()
        top.columns = ["Outcome","Count"]
        fig = px.pie(top, names="Outcome", values="Count", hole=0.48,
                     color_discrete_sequence=ACCENT)
        fig.update_traces(textposition="outside", textinfo="label+percent",
                          textfont=dict(size=10, family=FONT),
                          marker=dict(line=dict(color="rgba(6,9,26,0.8)", width=2)))
        return dl(fig, "Outcome Type Distribution")

    @output
    @render_widget
    def chart_outcome_by_species():
        d    = dff()
        cats = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER","COMMUNITY CAT","DIED"]
        grp  = d[d["Outcome Type"].isin(cats)].groupby(
            ["Animal Type","Outcome Type"]).size().reset_index(name="Count")
        fig  = px.bar(grp, x="Animal Type", y="Count", color="Outcome Type",
                      color_discrete_sequence=ACCENT, barmode="stack")
        fig.update_traces(marker_line_width=0)
        return dl(fig, "Outcomes by Animal Type")

    @output
    @render_widget
    def chart_trend_yearly():
        d  = dff()
        yr = d.groupby("intake_year").agg(
            Total=("Animal ID","count"),
            Adoptions=("is_adoption","sum"),
            Live=("was_outcome_alive","sum"),
        ).reset_index()
        yr["Adoption %"] = yr["Adoptions"] / yr["Total"] * 100
        yr["Live %"]     = yr["Live"]      / yr["Total"] * 100
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=yr["intake_year"], y=yr["Total"], name="Total Intakes",
                             marker_color="rgba(96,165,250,0.22)", marker_line_width=0), secondary_y=False)
        fig.add_trace(go.Scatter(x=yr["intake_year"], y=yr["Live %"], name="Live Release %",
                                 mode="lines+markers", line=dict(color="#43d9ad",width=2.5),
                                 marker=dict(size=6)), secondary_y=True)
        fig.add_trace(go.Scatter(x=yr["intake_year"], y=yr["Adoption %"], name="Adoption %",
                                 mode="lines+markers", line=dict(color="#7c6af7",width=2.5,dash="dot"),
                                 marker=dict(size=6)), secondary_y=True)
        fig.update_yaxes(title_text="Count",    secondary_y=False, title_font=dict(color=MUTED,family=FONT))
        fig.update_yaxes(title_text="Rate (%)", secondary_y=True,  title_font=dict(color=MUTED,family=FONT))
        return dl(fig, "Yearly Intake Volume & Outcome Rates")

    @output
    @render_widget
    def chart_live_by_condition():
        grp = dff().groupby("Intake Condition").agg(
            LR=("was_outcome_alive","mean"), N=("Animal ID","count")
        ).reset_index().sort_values("LR")
        grp["pct"] = grp["LR"] * 100
        fig = px.bar(grp, x="pct", y="Intake Condition", orientation="h",
                     color="pct",
                     color_continuous_scale=[[0,"#f97068"],[0.5,"#fbbf24"],[1,"#43d9ad"]],
                     text=grp["pct"].round(1).astype(str)+"%")
        fig.update_traces(textposition="outside", textfont=dict(size=10,family=FONT), marker_line_width=0)
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Live Release Rate (%)", yaxis_title="")
        return dl(fig, "Live Release Rate by Intake Condition")

    @output
    @render_widget
    def chart_age_outcome():
        d   = dff().dropna(subset=["age_group"])
        cats = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER"]
        grp  = d[d["Outcome Type"].isin(cats)].groupby(
            ["age_group","Outcome Type"]).size().reset_index(name="Count")
        fig  = px.bar(grp, x="age_group", y="Count", color="Outcome Type",
                      color_discrete_sequence=ACCENT, barmode="group")
        fig.update_traces(marker_line_width=0)
        fig.update_layout(xaxis_title="Age at Intake", yaxis_title="Count")
        return dl(fig, "Outcomes by Age Group")

    @output
    @render_widget
    def chart_sex_outcome():
        grp = dff().groupby("Sex Clean").agg(
            LR=("was_outcome_alive","mean"), N=("Animal ID","count")
        ).reset_index().sort_values("LR", ascending=False)
        grp["pct"] = grp["LR"] * 100
        fig = px.bar(grp, x="Sex Clean", y="pct", color="Sex Clean",
                     color_discrete_sequence=ACCENT,
                     text=grp["pct"].round(1).astype(str)+"%")
        fig.update_traces(textposition="outside", textfont=dict(size=11,family=FONT), marker_line_width=0)
        fig.update_layout(xaxis_title="", yaxis_title="Live Release Rate (%)", showlegend=False)
        return dl(fig, "Live Release Rate by Sex / Neuter Status")

    @output
    @render_widget
    def chart_intake_type():
        grp = dff()["Intake Type"].value_counts().reset_index()
        grp.columns = ["Intake Type","Count"]
        fig = px.bar(grp, x="Count", y="Intake Type", orientation="h",
                     color="Count", color_continuous_scale=[[0,"#0f172a"],[1,"#60a5fa"]],
                     text="Count")
        fig.update_traces(textposition="outside", textfont=dict(size=10,family=FONT), marker_line_width=0)
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Number of Animals", yaxis_title="")
        return dl(fig, "Intake Volume by Intake Type")

    @output
    @render_widget
    def chart_los_by_type():
        d   = dff().dropna(subset=["intake_duration"])
        d   = d[d["intake_duration"] <= 365]
        grp = d.groupby("Intake Type")["intake_duration"].median().reset_index()
        grp.columns = ["Intake Type","Median LOS"]
        grp = grp.sort_values("Median LOS", ascending=False)
        fig = px.bar(grp, x="Median LOS", y="Intake Type", orientation="h",
                     color="Median LOS", color_continuous_scale=[[0,"#0f172a"],[1,"#7c6af7"]],
                     text=grp["Median LOS"].round(1))
        fig.update_traces(textposition="outside", textfont=dict(size=10,family=FONT), marker_line_width=0)
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Median Days in Shelter", yaxis_title="")
        return dl(fig, "Median Length of Stay by Intake Type")

    @output
    @render_widget
    def chart_los_outcome():
        d    = dff().dropna(subset=["intake_duration"])
        d    = d[d["intake_duration"] <= 200]
        cats = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER","DIED"]
        d    = d[d["Outcome Type"].isin(cats)]
        fig  = px.box(d, x="Outcome Type", y="intake_duration",
                      color="Outcome Type", color_discrete_sequence=ACCENT, points=False)
        fig.update_traces(line_width=1.5)
        fig.update_layout(xaxis_title="", yaxis_title="Days in Shelter", showlegend=False)
        return dl(fig, "Length of Stay Distribution by Outcome")

    @output
    @render_widget
    def chart_los_species():
        d   = dff().dropna(subset=["intake_duration"])
        d   = d[d["intake_duration"] <= 200]
        spp = ["CAT","DOG","BIRD","RABBIT","GUINEA PIG"]
        d   = d[d["Animal Type"].isin(spp)]
        fig = px.violin(d, x="Animal Type", y="intake_duration",
                        color="Animal Type", color_discrete_sequence=ACCENT, box=True, points=False)
        fig.update_layout(xaxis_title="", yaxis_title="Days in Shelter", showlegend=False)
        return dl(fig, "Length of Stay Distribution by Species")

    @output
    @render_widget
    def chart_los_heatmap():
        d   = dff().dropna(subset=["intake_duration","intake_month"])
        spp = ["CAT","DOG","BIRD","RABBIT"]
        d   = d[d["Animal Type"].isin(spp)]
        piv = d.groupby(["intake_month","Animal Type"])["intake_duration"].median().reset_index()
        wide = piv.pivot(index="Animal Type", columns="intake_month", values="intake_duration")
        mnames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        wide.columns = [mnames[c-1] for c in wide.columns]
        fig = px.imshow(wide,
                        color_continuous_scale=[[0,"#06091a"],[0.5,"#7c6af7"],[1,"#43d9ad"]],
                        text_auto=".0f", aspect="auto")
        fig.update_traces(textfont=dict(size=11, family=FONT))
        fig.update_coloraxes(colorbar=dict(tickfont=dict(color=MUTED,family=FONT)))
        fig.update_layout(xaxis_title="Month of Intake", yaxis_title="")
        return dl(fig, "Median Length of Stay: Species x Month of Intake", height=280)

    @output
    @render_widget
    def chart_monthly_trend():
        d    = dff()
        d    = d.copy()
        d["ym"] = d["Intake Date"].dt.to_period("M").astype(str)
        grp  = d.groupby("ym").agg(
            Total=("Animal ID","count"), Adoptions=("is_adoption","sum")
        ).reset_index()
        grp["Adoption %"] = grp["Adoptions"] / grp["Total"] * 100
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=grp["ym"], y=grp["Total"], name="Monthly Intakes",
                                 fill="tozeroy", line=dict(color="#60a5fa",width=0),
                                 fillcolor="rgba(96,165,250,0.10)"), secondary_y=False)
        fig.add_trace(go.Scatter(x=grp["ym"], y=grp["Total"], name="",
                                 showlegend=False, line=dict(color="#60a5fa",width=1.5)), secondary_y=False)
        fig.add_trace(go.Scatter(x=grp["ym"], y=grp["Adoption %"], name="Adoption Rate %",
                                 mode="lines", line=dict(color="#43d9ad",width=2)), secondary_y=True)
        fig.update_yaxes(title_text="Monthly Intakes",  secondary_y=False, title_font=dict(color=MUTED,family=FONT))
        fig.update_yaxes(title_text="Adoption Rate (%)",secondary_y=True,  title_font=dict(color=MUTED,family=FONT))
        return dl(fig, "Monthly Intake Volume & Adoption Rate", height=340)

    @output
    @render_widget
    def chart_yearly_mix():
        d    = dff()
        keep = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER"]
        d    = d.copy()
        d["OC"] = d["Outcome Type"].apply(lambda x: x if x in keep else "OTHER")
        grp  = d.groupby(["intake_year","OC"]).size().reset_index(name="Count")
        tots = grp.groupby("intake_year")["Count"].transform("sum")
        grp["Pct"] = grp["Count"] / tots * 100
        fig  = px.bar(grp, x="intake_year", y="Pct", color="OC",
                      color_discrete_sequence=ACCENT, barmode="stack")
        fig.update_traces(marker_line_width=0)
        fig.update_layout(xaxis_title="Year", yaxis_title="% of Animals",
                          yaxis_range=[0,100])
        return dl(fig, "Outcome Mix by Year (% of annual intakes)")

    @output
    @render_widget
    def chart_adoption_trend():
        d   = dff()
        spp = ["CAT","DOG","RABBIT"]
        d   = d[d["Animal Type"].isin(spp)]
        grp = d.groupby(["intake_year","Animal Type"]).agg(AR=("is_adoption","mean")).reset_index()
        grp["AR"] *= 100
        fig = px.line(grp, x="intake_year", y="AR", color="Animal Type",
                      color_discrete_sequence=ACCENT, markers=True)
        fig.update_traces(line_width=2.5, marker_size=7)
        fig.update_layout(xaxis_title="Year", yaxis_title="Adoption Rate (%)")
        return dl(fig, "Adoption Rate Over Time by Species")


app = App(app_ui, server)