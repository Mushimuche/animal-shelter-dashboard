"""
Left Behind: Long Beach Animal Shelter Outcome Patterns
Shiny for Python Dashboard  –  Final Layout Fixes Applied
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget

# ─────────────────────────────────────────────
# DATA (DO NOT MODIFY)
# ─────────────────────────────────────────────

def load_and_clean(path: str) -> pd.DataFrame:
    # 1. Read the parquet file instead of CSV
    df = pd.read_parquet(path)
    
    df["Intake Date"]  = pd.to_datetime(df["Intake Date"],  errors="coerce")
    df["Outcome Date"] = pd.to_datetime(df["Outcome Date"], errors="coerce")
    df["DOB"]          = pd.to_datetime(df["DOB"],          errors="coerce")
    df = df[df["Outcome Type"].notna()].copy()

    df["age_years"] = (df["Intake Date"] - df["DOB"]).dt.days / 365.25
    df.loc[df["age_years"] < 0,  "age_years"] = np.nan
    df.loc[df["age_years"] > 30, "age_years"] = np.nan

    bins   =[0, 0.25, 1, 3, 7, 15, 100]
    labels =["Neonatal\n(<3mo)", "Juvenile\n(3mo–1yr)", "Young Adult\n(1–3yr)",
              "Adult\n(3–7yr)", "Senior\n(7–15yr)", "Geriatric\n(15+yr)"]
    df["age_group"] = pd.cut(df["age_years"], bins=bins, labels=labels)

    df["intake_year"]  = df["Intake Date"].dt.year
    df["intake_month"] = df["Intake Date"].dt.month
    df["is_adoption"]  = (df["Outcome Type"] == "ADOPTION").astype(int)
    df["Intake Condition"] = df["Intake Condition"].str.strip()
    df = df[df["intake_year"] >= 2017]
    return df

# 2. Point directly to your new local Parquet file
LOCAL_PARQUET_PATH = "animal-shelter.parquet"
df_full  = load_and_clean(LOCAL_PARQUET_PATH)

ANIMAL_TYPES = ["All"] + sorted(df_full["Animal Type"].unique().tolist())
YEARS        =["All"] + sorted(df_full["intake_year"].dropna().astype(int).unique().tolist(), reverse=True)
INTAKE_TYPES = ["All"] + sorted(df_full["Intake Type"].dropna().unique().tolist())

# ─────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────

ACCENT =["#E88D67", "#81A684", "#F2C94C", "#5C6BC0", "#4DB6AC",
          "#F2994A", "#E5C07B", "#3A405A", "#E07A5F", "#8AB17D"]
BG     = "rgba(0,0,0,0)"
GRID   = "rgba(0,0,0,0.05)"
FONT   = "Nunito, Avenir Next, sans-serif"

# ─────────────────────────────────────────────
# SVG ICONS
# ─────────────────────────────────────────────

def svg_icon(path_d, color, size=24):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="{color}" style="display:block;flex-shrink:0;">'
        f'<path d="{path_d}"/></svg>'
    )

SVG_PAW = ("M4.5 9.5C3.12 9.5 2 10.62 2 12s1.12 2.5 2.5 2.5S7 13.38 7 12 "
           "5.88 9.5 4.5 9.5zm15 0c-1.38 0-2.5 1.12-2.5 2.5s1.12 2.5 2.5 "
           "2.5S22 13.38 22 12s-1.12-2.5-2.5-2.5zm-8.5-5C9.62 4.5 8.5 5.62 "
           "8.5 7S9.62 9.5 11 9.5 13.5 8.38 13.5 7 12.38 4.5 11 4.5zm4 0c-1.38 "
           "0-2.5 1.12-2.5 2.5s1.12 2.5 2.5 2.5S17.5 8.38 17.5 7 16.38 4.5 15 "
           "4.5zM12 11c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z")
SVG_HOUSE = "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"
SVG_HEART = ("M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 "
             "0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 "
             "3.78-3.4 6.86-8.55 11.54L12 21.35z")
SVG_MEDICAL = ("M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 "
               "2-2V5c0-1.1-.9-2-2-2zm-7 3c.55 0 1 .45 1 1v3h3c.55 0 1 .45 "
               "1 1s-.45 1-1 1h-3v3c0 .55-.45 1-1 1s-1-.45-1-1v-3H8c-.55 "
               "0-1-.45-1-1s.45-1 1-1h3V7c0-.55.45-1 1-1z")
SVG_CALENDAR = ("M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 "
                "2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 "
                "10h5v5H7z")
SVG_TREND = ("M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 "
             "16.99z")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800;900&family=Fredoka+One&display=swap');

:root {
  --font: 'Nunito', sans-serif;
  --font-display: 'Fredoka One', cursive;
  --bg: #FBF7EF;
  --bg-card: #FFFFFF;
  --border: #EBE5D8;
  --header-bg: #3A405A;
  --a1: #E88D67;
  --a2: #81A684;
  --a3: #F2C94C;
  --a4: #5C6BC0;
  --a5: #4DB6AC;
  --txt: #2C3539;
  --muted: #7A8B99;
}

*, *::before, *::after { box-sizing: border-box; font-family: var(--font) !important; }

body {
  margin: 0; background: var(--bg); color: var(--txt);
  overflow-x: hidden; position: relative;
}
body::before {
  content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background-image: radial-gradient(circle at 2px 2px, rgba(232,141,103,0.12) 2px, transparent 0);
  background-size: 36px 36px; pointer-events: none; z-index: 0;
}
.container-fluid, .dashboard-header, .filter-bar, .kpi-row, .charts-grid, .full-width-row {
  position: relative; z-index: 1;
}

/* ── HEADER ── */
.dashboard-header {
  padding: 28px 40px 20px; border-bottom: 3px solid var(--a1);
  background: var(--header-bg); text-align: center;
  position: relative; overflow: hidden;
}
.dashboard-header::before {
  content: ''; position: absolute; top: 0; right: 0;
  width: 220px; height: 100%;
  background: linear-gradient(135deg, transparent 40%, rgba(232,141,103,0.18) 40%);
  pointer-events: none;
}
.dashboard-header::after {
  content: ''; position: absolute; top: 0; left: 0;
  width: 220px; height: 100%;
  background: linear-gradient(225deg, transparent 40%, rgba(77,182,172,0.12) 40%);
  pointer-events: none;
}
.dashboard-header h1 {
  font-family: var(--font-display) !important;
  font-size: 2.4rem; font-weight: 400;
  margin: 0 0 8px; color: #FFFFFF;
  text-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.subtitle {
  color: rgba(255,255,255,0.75); font-size: 0.9rem;
  margin: 0; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
}
.header-badge {
  display: inline-block; background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2); border-radius: 20px;
  padding: 4px 14px; font-size: 0.78rem; color: rgba(255,255,255,0.85);
  font-weight: 700; margin-top: 10px; letter-spacing: 0.05em;
}

/* ── FILTER BAR ── */
.filter-bar {
  padding: 16px 40px;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 20px;
  background: var(--header-bg);
  border-bottom: 3px solid rgba(255,255,255,0.08);
}
.filter-bar .shiny-input-container {
  flex: 0 0 240px;
  max-width: 280px;
}
.shiny-input-container label {
  color: rgba(255,255,255,0.7) !important; font-size: .72rem !important;
  font-weight: 800 !important; text-transform: uppercase;
  letter-spacing: .08em; margin-bottom: 6px; display: block;
}
.shiny-input-container select, select.form-control {
  background: rgba(255,255,255,0.1) !important;
  border: 1.5px solid rgba(255,255,255,0.2) !important;
  border-radius: 10px !important; color: #FFFFFF !important;
  font-size: 0.95rem !important; padding: 10px 14px !important;
  width: 100%; transition: all .2s; font-weight: 600; cursor: pointer;
}
.shiny-input-container select option { background: #3A405A; color: #FFFFFF; }
.shiny-input-container select:focus {
  border-color: var(--a1) !important; outline: none;
  box-shadow: 0 0 0 3px rgba(232,141,103,0.3) !important;
}

/* ── KPI CARDS ── */
.kpi-row { display: flex; gap: 20px; padding: 28px 40px 20px; }
.kpi-card {
  flex: 1; background: var(--bg-card); border: 1.5px solid var(--border);
  border-radius: 20px; padding: 22px 16px 20px;
  transition: transform .25s cubic-bezier(.34,1.56,.64,1), box-shadow .25s;
  position: relative; overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  text-align: center; display: flex; flex-direction: column; align-items: center;
}
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0;
  height: 6px; border-radius: 20px 20px 0 0;
}
.kpi-card:nth-child(1)::before { background: var(--a5); }
.kpi-card:nth-child(2)::before { background: var(--a2); }
.kpi-card:nth-child(3)::before { background: var(--a1); }
.kpi-card:nth-child(4)::before { background: var(--a4); }
.kpi-card:nth-child(5)::before { background: var(--a3); }
.kpi-card::after {
  content: ''; position: absolute; bottom: -20px; right: -20px;
  width: 90px; height: 90px; border-radius: 50%; opacity: 0.06;
}
.kpi-card:nth-child(1)::after { background: var(--a5); }
.kpi-card:nth-child(2)::after { background: var(--a2); }
.kpi-card:nth-child(3)::after { background: var(--a1); }
.kpi-card:nth-child(4)::after { background: var(--a4); }
.kpi-card:nth-child(5)::after { background: var(--a3); }
.kpi-card:hover { transform: translateY(-6px) scale(1.01); box-shadow: 0 12px 32px rgba(0,0,0,0.1); }

.kpi-icon-wrap {
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 12px;
}
.kpi-card:nth-child(1) .kpi-icon-wrap { background: rgba(77,182,172,0.12); }
.kpi-card:nth-child(2) .kpi-icon-wrap { background: rgba(129,166,132,0.12); }
.kpi-card:nth-child(3) .kpi-icon-wrap { background: rgba(232,141,103,0.12); }
.kpi-card:nth-child(4) .kpi-icon-wrap { background: rgba(92,107,192,0.12); }
.kpi-card:nth-child(5) .kpi-icon-wrap { background: rgba(242,201,76,0.14); }

.kpi-value {
  font-size: 2rem !important; font-weight: 900 !important;
  color: var(--header-bg); letter-spacing: -.03em;
  line-height: 1; margin-bottom: 6px;
}
.kpi-label {
  font-size: .72rem !important; color: var(--muted) !important;
  font-weight: 800; text-transform: uppercase;
  letter-spacing: .06em; line-height: 1.3;
}

/* ── CHARTS GRID ── */
/* FIX: Reduced bottom padding slightly so the full width row fits naturally */
.charts-grid {
  padding: 0 40px 24px;
  display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
}

/* FIX: Added a dedicated row class OUTSIDE the grid specifically for the heatmap */
.full-width-row {
  padding: 0 40px 40px;
  display: block; 
  width: 100%;
}

.chart-card {
  background: var(--bg-card); border: 1.5px solid var(--border);
  border-radius: 20px; overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  transition: transform .25s cubic-bezier(.34,1.56,.64,1), box-shadow .25s;
  display: flex; flex-direction: column;
}
.chart-card:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.09); }

.chart-header {
  background: var(--header-bg); color: #FFFFFF;
  padding: 14px 20px; font-size: 0.95rem; font-weight: 800;
  letter-spacing: 0.03em; display: flex; align-items: center; gap: 10px;
  border-left: 5px solid var(--a1);
}

/* ── CHART BODY ── */
.chart-body {
  padding: 16px; 
  width: 100%; 
  flex: 1;
  background: var(--bg-card);
  overflow: hidden; 
}

/* Let the wrappers stretch, but don't force flex or block on them */
.chart-body > div, 
.html-widget {
  width: 100% !important;
}

/* Remove all manual margins and sizing from Plotly containers */
.js-plotly-plot, 
.plot-container {
  width: 100% !important;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #F8F3E6; }
::-webkit-scrollbar-thumb { background: #D1CBC0; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #B5AFA4; }
"""

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
        avg_los   = f"{los:.0f} d" if (not np.isnan(los)) else "-",
    )


def dl(fig, height=380):
    fig.update_layout(
        autosize=True,
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color="#3A405A", family=FONT, size=13),
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            font=dict(size=12, color="#3A405A"),
            bordercolor="#E8E3D5", borderwidth=1
        ),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family=FONT,
                        bordercolor="#E8E3D5", font_color="#3A405A"),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color="#7A8B99", family=FONT))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color="#7A8B99", family=FONT))
    return fig

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800;900&family=Fredoka+One&display=swap"
        ),
        ui.tags.style(CSS),
        # ---> PASTE THIS NEW SCRIPT HERE <---
        ui.tags.script("""
            // The Nuclear Plotly Resizer
            function forcePlotlyResize() {
                // Find every Plotly chart on the page
                document.querySelectorAll('.js-plotly-plot').forEach(function(el) {
                    // Get the exact pixel width of the card it lives inside
                    let parentWidth = el.parentElement.clientWidth;
                    
                    // If Plotly is loaded and the card actually has a width, force Plotly to match it
                    if (parentWidth > 100 && window.Plotly) {
                        Plotly.relayout(el, {width: parentWidth});
                    }
                });
            }

            // The data takes a few seconds to load. 
            // This runs our forced resize every 500 milliseconds for the first 5 seconds.
            let attempts = 0;
            let forceResize = setInterval(function() {
                forcePlotlyResize();
                attempts++;
                if (attempts > 10) clearInterval(forceResize);
            }, 500);

            // Also keep it snappy if the user manually resizes their browser window
            window.addEventListener('resize', forcePlotlyResize);
        """),
        # ------------------------------------
    ),

    # ── HEADER ────────────────────────────────
    ui.div(
        ui.h1(
            ui.HTML('<span style="font-size:1.8rem;margin:0 10px;">🐾</span>'),
            "Left Behind",
            ui.HTML('<span style="font-size:1.8rem;margin:0 10px;">🐾</span>'),
        ),
        ui.p("Long Beach Animal Shelter · Outcome Patterns Dashboard", class_="subtitle"),
        ui.div("54,000+ intake records  ·  City of Long Beach Open Data Portal", class_="header-badge"),
        class_="dashboard-header"
    ),

    # ── FILTERS ───────────────────────────────
    ui.div(
        ui.input_select("animal_type", "Species Category", choices=ANIMAL_TYPES, selected="All"),
        ui.input_select("year",        "Intake Year",      choices=YEARS,        selected="All"),
        ui.input_select("intake_type", "Intake Origin",    choices=INTAKE_TYPES, selected="All"),
        class_="filter-bar"
    ),

    # ── KPI ROW ───────────────────────────────
    ui.div(
        ui.div(
            ui.div(
                ui.HTML(f'<div class="kpi-icon-wrap">{svg_icon(SVG_PAW, "#4DB6AC")}</div>'),
                ui.output_ui("kpi_total"),
                ui.div("Total Animals Processed", class_="kpi-label"),
                class_="kpi-card"
            ),
            ui.div(
                ui.HTML(f'<div class="kpi-icon-wrap">{svg_icon(SVG_HOUSE, "#81A684")}</div>'),
                ui.output_ui("kpi_adoptions"),
                ui.div("Adoptions", class_="kpi-label"),
                class_="kpi-card"
            ),
            ui.div(
                ui.HTML(f'<div class="kpi-icon-wrap">{svg_icon(SVG_HEART, "#E88D67")}</div>'),
                ui.output_ui("kpi_live"),
                ui.div("Live Release Rate", class_="kpi-label"),
                class_="kpi-card"
            ),
            ui.div(
                ui.HTML(f'<div class="kpi-icon-wrap">{svg_icon(SVG_MEDICAL, "#5C6BC0")}</div>'),
                ui.output_ui("kpi_euth"),
                ui.div("Euthanasia Rate", class_="kpi-label"),
                class_="kpi-card"
            ),
            ui.div(
                ui.HTML(f'<div class="kpi-icon-wrap">{svg_icon(SVG_CALENDAR, "#C9A020")}</div>'),
                ui.output_ui("kpi_los"),
                ui.div("Median Length of Stay", class_="kpi-label"),
                class_="kpi-card"
            ),
            class_="kpi-row"
        )
    ),

    # ── CHARTS GRID (2-Column Cards Only) ─────
    ui.div(
        # Row 1
        ui.div(
            ui.div(
                ui.HTML('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.88-11.71L10 14.17l-1.88-1.88a.996.996 0 1 0-1.41 1.41l2.59 2.59c.39.39 1.02.39 1.41 0L17.3 9.7a.996.996 0 0 0 0-1.41c-.39-.39-1.03-.39-1.42 0z"/></svg>'),
                " Chart 1 — Outcome Type Distribution",
                class_="chart-header"
            ),
            ui.div(output_widget("chart_1_outcome_dist", width="100%", height="430px"), class_="chart-body"),
            class_="chart-card"
        ),
        ui.div(
            ui.div(
                ui.HTML(f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><path d="{SVG_TREND}"/></svg>'),
                " Chart 7 — Seasonal Intake vs. Live Release Rate",
                class_="chart-header"
            ),
            ui.div(output_widget("chart_7_seasonal", width="100%", height="430px"), class_="chart-body"),
            class_="chart-card"
        ),

        # Row 2
        ui.div(
            ui.div(
                ui.HTML('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z"/></svg>'),
                " Chart 2 — Live Release Rate by Species",
                class_="chart-header"
            ),
            ui.div(output_widget("chart_2_live_by_species", width="100%", height="380px"), class_="chart-body"),
            class_="chart-card"
        ),
        ui.div(
            ui.div(
                ui.HTML('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><path d="M22 21H2V3h2v16h2v-9h4v9h2V6h4v15h2v-5h4v5z"/></svg>'),
                " Chart 3 — Adoption & Live Release by Condition",
                class_="chart-header"
            ),
            ui.div(output_widget("chart_3_adoption_condition", width="100%", height="380px"), class_="chart-body"),
            class_="chart-card"
        ),

        # Row 3
        ui.div(
            ui.div(
                ui.HTML('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z"/></svg>'),
                " Chart 5 — Length of Stay Distribution by Outcome",
                class_="chart-header"
            ),
            ui.div(output_widget("chart_5_los_outcome", width="100%", height="380px"), class_="chart-body"),
            class_="chart-card"
        ),
        ui.div(
            ui.div(
                ui.HTML('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 17.52 22 22 12S17.52 2 11.99 2zm4.24 16L12 15.45 7.77 18l1.12-4.81-3.73-3.23 4.92-.42L12 5l1.92 4.53 4.92.42-3.73 3.23L16.23 18z"/></svg>'),
                " Chart 6 — Adoption Rate by Age Group",
                class_="chart-header"
            ),
            ui.div(output_widget("chart_6_adoption_age", width="100%", height="380px"), class_="chart-body"),
            class_="chart-card"
        ),

        class_="charts-grid"
    ),

    # ── FULL WIDTH ROW (Heatmap - Placed OUTSIDE the Grid) ──────────
    # FIX: By placing this outside the CSS Grid, Plotly is no longer victims of
    # grid initialization race conditions. It will load 100% wide on the very first try.
    ui.div(
        ui.div(
            ui.div(
                ui.HTML('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><path d="M20 2H4c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 2h2v2h-2V4zm0 4h2v2h-2V8zm-4-4h2v2H8V4zm0 4h2v2H8V8zm-4 0h2v2H4V8zm0-4h2v2H4V4zm0 12H4v-2h2v2zm4 0H8v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm0-4h-2v-2h2v2zm0-4h-2V8h2v2z"/></svg>'),
                " Chart 4 — Intake Type vs. Outcome Type",
                class_="chart-header"
            ),
            ui.div(output_widget("chart_4_intake_outcome_heatmap", width="100%", height="620px"), class_="chart-body"),
            class_="chart-card"
        ),
        class_="full-width-row"
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

    # ── KPIs ──────────────────────────────────
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

    # ── CHART 1: Outcome Type Distribution (Donut) ────────────────────────────
    @output
    @render_widget
    def chart_1_outcome_dist():
        top = dff()["Outcome Type"].value_counts().reset_index()
        top.columns = ["Outcome", "Count"]

        if len(top) > 10:
            other_count = top.iloc[9:]["Count"].sum()
            top = top.iloc[:9].copy()
            top.loc[len(top)] =["Other", other_count]

        top["Pct"] = (top["Count"] / top["Count"].sum() * 100).round(1)
        total_count = int(top["Count"].sum())

        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=top["Outcome"],
            values=top["Count"],
            hole=0.52,
            domain=dict(x=[0.05, 0.58], y=[0.02, 0.98]),
            marker=dict(
                colors=ACCENT[:len(top)],
                line=dict(color="#FFFFFF", width=2.5)
            ),
            textposition="inside",
            textinfo="percent",
            textfont=dict(size=12, family=FONT, color="#FFFFFF"),
            insidetextorientation="horizontal",
            customdata=top[["Pct"]].values,
            hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>Share: %{customdata[0]:.1f}%<extra></extra>",
        ))

        cx = (0.05 + 0.58) / 2
        fig.add_annotation(
            text="Total",
            x=cx, y=0.56,
            xanchor="center", yanchor="middle",
            font=dict(size=12, color="#7A8B99", family=FONT),
            showarrow=False,
        )
        fig.add_annotation(
            text=f"<b>{total_count:,}</b>",
            x=cx, y=0.44,
            xanchor="center", yanchor="middle",
            font=dict(size=18, color="#3A405A", family=FONT),
            showarrow=False,
        )

        fig.update_layout(
            autosize=True,
            height=430,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(
                orientation="v",
                yanchor="middle", y=0.5,
                xanchor="left",  x=0.62,
                font=dict(size=13, color="#3A405A", family=FONT),
                bgcolor="rgba(255,255,255,0.0)",
                borderwidth=0,
                itemsizing="constant",
                traceorder="normal",
            ),
            hoverlabel=dict(
                bgcolor="#FFFFFF", font_size=13, font_family=FONT,
                bordercolor="#E8E3D5", font_color="#3A405A"
            ),
        )
        return fig

    # ── CHART 2: Live Release Rate by Animal Type ─────────────────────────────
    @output
    @render_widget
    def chart_2_live_by_species():
        d   = dff()
        grp = d.groupby("Animal Type").agg(
            Live_Rate=("was_outcome_alive","mean"),
            Count=("Animal ID","count")
        ).reset_index().sort_values("Live_Rate", ascending=False)
        grp["Live_Pct"] = (grp["Live_Rate"] * 100).round(1)
        grp = grp[grp["Count"] >= 30]

        fig = px.bar(grp, x="Animal Type", y="Live_Pct",
                     color="Live_Pct",
                     color_continuous_scale=[[0,"#E88D67"],[0.5,"#F2C94C"],[1,"#81A684"]],
                     text=grp["Live_Pct"].astype(str) + "%",
                     custom_data=["Count"])
        fig.update_traces(
            textposition="outside",
            textfont=dict(size=13, family=FONT, color="#3A405A"),
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Live Release Rate: %{y:.1f}%<br>n = %{customdata[0]:,}<extra></extra>"
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="", yaxis_title="Live Release Rate (%)", yaxis_range=[0, 115])
        return dl(fig, height=380)

    # ── CHART 3: Adoption Rate by Intake Condition ────────────────────────────
    @output
    @render_widget
    def chart_3_adoption_condition():
        d   = dff()
        grp = d.groupby("Intake Condition").agg(
            Adoption_Rate=("is_adoption","mean"),
            Live_Rate=("was_outcome_alive","mean"),
            Count=("Animal ID","count")
        ).reset_index().sort_values("Adoption_Rate", ascending=False)
        grp = grp[grp["Count"] >= 20]
        grp["Adoption_Pct"] = (grp["Adoption_Rate"] * 100).round(1)
        grp["Live_Pct"]     = (grp["Live_Rate"]     * 100).round(1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=grp["Intake Condition"], y=grp["Adoption_Pct"],
            name="Adoption Rate", marker_color="#E88D67", marker_line_width=0,
            text=grp["Adoption_Pct"].astype(str)+"%", textposition="outside",
            textfont=dict(size=12, family=FONT, color="#3A405A"),
            hovertemplate="<b>%{x}</b><br>Adoption Rate: %{y:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=grp["Intake Condition"], y=grp["Live_Pct"],
            name="Live Release Rate", marker_color="#81A684", marker_line_width=0,
            text=grp["Live_Pct"].astype(str)+"%", textposition="outside",
            textfont=dict(size=12, family=FONT, color="#3A405A"),
            hovertemplate="<b>%{x}</b><br>Live Release Rate: %{y:.1f}%<extra></extra>"
        ))
        fig.update_layout(
            barmode="group", xaxis_title="", yaxis_title="Rate (%)", yaxis_range=[0,120],
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return dl(fig, height=380)

    # ── CHART 4: Intake Type vs Outcome Type (Heatmap) ───────────────────────
    @output
    @render_widget
    def chart_4_intake_outcome_heatmap():
        d    = dff()
        keep_out =["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER",
                    "COMMUNITY CAT","DIED"]
        d = d[d["Outcome Type"].isin(keep_out)]
        pivot = d.groupby(["Intake Type","Outcome Type"]).size().reset_index(name="Count")
        wide  = pivot.pivot(index="Intake Type", columns="Outcome Type", values="Count").fillna(0)
        wide_pct = wide.div(wide.sum(axis=1), axis=0) * 100

        z_vals   = wide_pct.round(1).values
        x_labels = wide_pct.columns.tolist()
        y_labels  = wide_pct.index.tolist()

        HEATMAP_SCALE = [
            [0.00, "#FBF7EF"],[0.40, "#E88D67"],[1.00, "#3A405A"],   
        ]

        threshold = 40
        text_colors = [["#FFFFFF" if v >= threshold else "#3A405A" for v in row]
            for row in z_vals
        ]

        fig = go.Figure(go.Heatmap(
            z=z_vals,
            x=x_labels,
            y=y_labels,
            colorscale=HEATMAP_SCALE,
            hovertemplate="Intake: <b>%{y}</b><br>Outcome: <b>%{x}</b><br>%{z:.1f}% of intakes<extra></extra>",
            colorbar=dict(
                title=dict(text="% of Row", font=dict(color="#3A405A", family=FONT, size=11)),
                tickfont=dict(color="#3A405A", family=FONT, size=10),
                thickness=14,
                len=0.80,
                x=1.01,
                xpad=4,
                outlinewidth=0,
            ),
            zmin=0,
            zmax=100,
            texttemplate="",
        ))

        flat_x, flat_y, flat_text, flat_colors = [], [], [],[]
        for ri, yl in enumerate(y_labels):
            for ci, xl in enumerate(x_labels):
                flat_x.append(xl)
                flat_y.append(yl)
                flat_text.append(f"{z_vals[ri][ci]:.1f}")
                flat_colors.append(text_colors[ri][ci])

        fig.add_trace(go.Scatter(
            x=flat_x, y=flat_y,
            mode="text",
            text=flat_text,
            textfont=dict(size=12, family=FONT, color=flat_colors),
            hoverinfo="skip",
            showlegend=False,
        ))

        fig.update_layout(
            autosize=True,
            height=620,                          
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#3A405A", family=FONT, size=12),
            xaxis_title="Outcome Category",
            yaxis_title="Intake Origin",
            margin=dict(t=30, b=80, l=40, r=80),
            xaxis=dict(
                automargin=True,
                tickangle=-30,
                tickfont=dict(color="#7A8B99", family=FONT, size=11),
                title_font=dict(color="#7A8B99", family=FONT),
                gridcolor=GRID, zerolinecolor=GRID, side="bottom",
            ),
            yaxis=dict(
                automargin=True,
                tickfont=dict(color="#7A8B99", family=FONT, size=11),
                title_font=dict(color="#7A8B99", family=FONT),
                gridcolor=GRID, zerolinecolor=GRID,
            ),
            hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family=FONT,
                            bordercolor="#E8E3D5", font_color="#3A405A"),
        )
        return fig

    # ── CHART 5: Length of Stay by Outcome Type (Box) ────────────────────────
    @output
    @render_widget
    def chart_5_los_outcome():
        d    = dff().dropna(subset=["intake_duration"])
        d    = d[d["intake_duration"] <= 200]
        cats =["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER","DIED"]
        d    = d[d["Outcome Type"].isin(cats)]

        order = d.groupby("Outcome Type")["intake_duration"].median().sort_values().index.tolist()
        d["Outcome Type"] = pd.Categorical(d["Outcome Type"], categories=order, ordered=True)
        d = d.sort_values("Outcome Type")

        fig = px.box(d, x="Outcome Type", y="intake_duration",
                     color="Outcome Type",
                     color_discrete_sequence=ACCENT,
                     points=False,
                     category_orders={"Outcome Type": order})
        fig.update_traces(
            line_width=1.8,
            hovertemplate="<b>%{x}</b><br>Median: %{median:.0f} days<extra></extra>"
        )
        fig.update_layout(xaxis_title="", yaxis_title="Days in Shelter", showlegend=False)
        return dl(fig, height=380)

    # ── CHART 6: Adoption Rate by Age Group ──────────────────────────────────
    @output
    @render_widget
    def chart_6_adoption_age():
        d   = dff().dropna(subset=["age_group"])
        grp = d.groupby("age_group", observed=True).agg(
            Adoption_Rate=("is_adoption","mean"),
            Count=("Animal ID","count")
        ).reset_index()
        grp["Adoption_Pct"] = (grp["Adoption_Rate"] * 100).round(1)
        grp = grp[grp["Count"] >= 10]

        fig = px.bar(grp, x="age_group", y="Adoption_Pct",
                     color="Adoption_Pct",
                     color_continuous_scale=[[0,"#E88D67"],[0.5,"#F2C94C"],[1,"#81A684"]],
                     text=grp["Adoption_Pct"].astype(str)+"%",
                     custom_data=["Count"])
        fig.update_traces(
            textposition="outside",
            textfont=dict(size=12, family=FONT, color="#3A405A"),
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Adoption Rate: %{y:.1f}%<br>n = %{customdata[0]:,}<extra></extra>"
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(
            xaxis_title="Age Group at Intake",
            yaxis_title="Adoption Rate (%)",
            yaxis_range=[0, grp["Adoption_Pct"].max() * 1.25]
        )
        fig.add_annotation(
            text="Note: ~12% of records excluded due to missing DOB",
            xref="paper", yref="paper", x=1, y=-0.22,
            showarrow=False, font=dict(size=11, color="#7A8B99", family=FONT),
            xanchor="right"
        )
        return dl(fig, height=380)

    # ── CHART 7: Seasonal Intake Volume vs. Live Release Rate ─────────────────
    @output
    @render_widget
    def chart_7_seasonal():
        d = dff()

        MONTH_NAMES =["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]

        monthly = d.groupby("intake_month").agg(
            Intake_Count=("Animal ID","count"),
            Live_Rate=("was_outcome_alive","mean"),
        ).reset_index()
        monthly = monthly.sort_values("intake_month")
        monthly["Month"]    = monthly["intake_month"].apply(lambda m: MONTH_NAMES[m-1])
        monthly["Live_Pct"] = (monthly["Live_Rate"] * 100).round(1)

        fig = go.Figure()

        # Bars — intake volume (left y-axis)
        fig.add_trace(go.Bar(
            x=monthly["Month"],
            y=monthly["Intake_Count"],
            name="Intake Volume",
            marker_color="#E88D67",
            marker_line_width=0,
            opacity=0.85,
            yaxis="y1",
            hovertemplate="<b>%{x}</b><br>Intakes: %{y:,}<extra></extra>",
        ))

        # Line — live release rate (right y-axis)
        fig.add_trace(go.Scatter(
            x=monthly["Month"],
            y=monthly["Live_Pct"],
            name="Live Release Rate",
            mode="lines+markers",
            line=dict(color="#81A684", width=3),
            marker=dict(size=8, color="#81A684",
                        line=dict(color="#FFFFFF", width=2)),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Live Release Rate: %{y:.1f}%<extra></extra>",
        ))

        y1_max = monthly["Intake_Count"].max() * 1.30 if len(monthly) else 100
        y2_min = max(0, monthly["Live_Pct"].min() - 5) if len(monthly) else 0
        y2_max = min(100, monthly["Live_Pct"].max() + 5) if len(monthly) else 100

        fig.update_layout(
            autosize=True,
            height=430,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#3A405A", family=FONT, size=12),
            margin=dict(t=20, b=40, l=40, r=40),
            yaxis=dict(
                automargin=True,
                title="Monthly Intake Count",
                title_font=dict(color="#E88D67", family=FONT, size=11),
                tickfont=dict(color="#E88D67", family=FONT, size=10),
                range=[0, y1_max],
                gridcolor=GRID, zerolinecolor=GRID,
                showgrid=True,
            ),
            yaxis2=dict(
                automargin=True,
                title="Live Release Rate (%)",
                title_font=dict(color="#81A684", family=FONT, size=11),
                tickfont=dict(color="#81A684", family=FONT, size=10),
                range=[y2_min, y2_max],
                overlaying="y",
                side="right",
                showgrid=False,
                ticksuffix="%",
            ),
            xaxis=dict(
                automargin=True,
                title="",
                tickfont=dict(color="#7A8B99", family=FONT, size=11),
                gridcolor=GRID, zerolinecolor=GRID,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="center", x=0.5,
                bgcolor="rgba(255,255,255,0.85)",
                font=dict(size=12, color="#3A405A"),
                bordercolor="#E8E3D5", borderwidth=1,
            ),
            hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family=FONT,
                            bordercolor="#E8E3D5", font_color="#3A405A"),
            bargap=0.25,
        )
        return fig


app = App(app_ui, server)

#version 5