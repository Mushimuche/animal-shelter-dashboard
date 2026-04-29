"""
Left Behind: Long Beach Animal Shelter Outcome Patterns
Shiny for Python Dashboard  –  v3 (6 charts only)
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────

def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["Intake Date"]  = pd.to_datetime(df["Intake Date"],  errors="coerce")
    df["Outcome Date"] = pd.to_datetime(df["Outcome Date"], errors="coerce")
    df["DOB"]          = pd.to_datetime(df["DOB"],          errors="coerce")
    df = df[df["Outcome Type"].notna()].copy()

    # Age at intake
    df["age_years"] = (df["Intake Date"] - df["DOB"]).dt.days / 365.25
    df.loc[df["age_years"] < 0,  "age_years"] = np.nan
    df.loc[df["age_years"] > 30, "age_years"] = np.nan

    # Age group
    bins   = [0, 0.25, 1, 3, 7, 15, 100]
    labels = ["Neonatal\n(<3mo)", "Juvenile\n(3mo–1yr)", "Young Adult\n(1–3yr)",
              "Adult\n(3–7yr)", "Senior\n(7–15yr)", "Geriatric\n(15+yr)"]
    df["age_group"] = pd.cut(df["age_years"], bins=bins, labels=labels)

    df["intake_year"] = df["Intake Date"].dt.year
    df["is_adoption"] = (df["Outcome Type"] == "ADOPTION").astype(int)
    df["Intake Condition"] = df["Intake Condition"].str.strip()
    df = df[df["intake_year"] >= 2017]
    return df


CSV_PATH = "https://github.com/Mushimuche/animal-shelter-dashboard/raw/refs/heads/main/animal-shelter-intakes-and-outcomes.csv"
df_full  = load_and_clean(CSV_PATH)

ANIMAL_TYPES = ["All"] + sorted(df_full["Animal Type"].unique().tolist())
YEARS        = ["All"] + sorted(df_full["intake_year"].dropna().astype(int).unique().tolist(), reverse=True)
INTAKE_TYPES = ["All"] + sorted(df_full["Intake Type"].dropna().unique().tolist())

# ─────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────

ACCENT = ["#7c6af7","#43d9ad","#f97068","#fbbf24","#60a5fa",
          "#e879f9","#34d399","#fb923c","#a78bfa","#22d3ee"]
BG     = "rgba(0,0,0,0)"
GRID   = "rgba(255,255,255,0.055)"
MUTED  = "#8896b3"
FONT   = "Avenir Next,Avenir,Nunito,Century Gothic,Trebuchet MS,sans-serif"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');

:root {
  --font:'Avenir Next','Avenir','Nunito','Century Gothic','Trebuchet MS',sans-serif;
  --bg:#06091a; --bg-card:rgba(255,255,255,0.045); --border:rgba(255,255,255,0.08);
  --a1:#7c6af7; --a2:#43d9ad; --a3:#f97068; --a4:#fbbf24; --a5:#60a5fa;
  --txt:#f0f4ff; --muted:#8896b3;
}
*,*::before,*::after{box-sizing:border-box;font-family:var(--font)!important;}
body{
  margin:0;background:var(--bg);color:var(--txt);overflow-x:hidden;position:relative;
  background-image:
    linear-gradient(rgba(255,255,255,0.018) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,0.018) 1px,transparent 1px);
  background-size:44px 44px;
}
body::before{
  content:'';position:fixed;border-radius:50%;width:750px;height:750px;
  background:radial-gradient(circle,rgba(124,106,247,0.35) 0%,transparent 65%);
  top:-220px;left:-220px;filter:blur(90px);
  animation:orb1 20s ease-in-out infinite alternate;pointer-events:none;z-index:0;
}
body::after{
  content:'';position:fixed;border-radius:50%;width:650px;height:650px;
  background:radial-gradient(circle,rgba(67,217,173,0.25) 0%,transparent 65%);
  bottom:-180px;right:-180px;filter:blur(90px);
  animation:orb2 25s ease-in-out infinite alternate;pointer-events:none;z-index:0;
}
.orb3{
  position:fixed;border-radius:50%;width:450px;height:450px;
  background:radial-gradient(circle,rgba(249,112,104,0.18) 0%,transparent 65%);
  top:42%;left:48%;transform:translate(-50%,-50%);filter:blur(100px);
  animation:orb3 30s ease-in-out infinite alternate;pointer-events:none;z-index:0;
}
@keyframes orb1{
  0%{transform:translate(0,0) scale(1);}
  50%{transform:translate(130px,90px) scale(1.18);}
  100%{transform:translate(60px,170px) scale(0.92);}
}
@keyframes orb2{
  0%{transform:translate(0,0) scale(1);}
  50%{transform:translate(-110px,-70px) scale(1.22);}
  100%{transform:translate(-50px,-140px) scale(0.88);}
}
@keyframes orb3{
  0%{transform:translate(-50%,-50%) scale(1);}
  100%{transform:translate(-44%,-58%) scale(1.35);}
}
.container-fluid,nav,.tab-content,.dashboard-header,
.filter-bar,.kpi-row,.chart-card{position:relative;z-index:1;}

/* Header */
.dashboard-header{
  padding:30px 32px 14px;border-bottom:1px solid var(--border);
  background:rgba(6,9,26,0.6);backdrop-filter:blur(14px);
}
.dashboard-header h1{
  font-size:1.75rem;font-weight:800;letter-spacing:-0.025em;margin:0 0 4px;
  background:linear-gradient(130deg,#f0f4ff 0%,var(--a1) 55%,var(--a2) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.subtitle{color:var(--muted);font-size:.83rem;margin:0;}

/* Filters */
.filter-bar{
  padding:14px 32px;gap:16px;display:flex;
  background:rgba(6,9,26,0.4);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--border);
}
.shiny-input-container{flex:1;}
.shiny-input-container label{
  color:var(--muted)!important;font-size:.72rem!important;font-weight:700!important;
  text-transform:uppercase;letter-spacing:.09em;margin-bottom:5px;display:block;
}
.shiny-input-container select,select.form-control{
  background:rgba(255,255,255,0.055)!important;border:1px solid var(--border)!important;
  border-radius:9px!important;color:var(--txt)!important;font-size:.87rem!important;
  padding:8px 12px!important;width:100%;transition:border-color .2s,box-shadow .2s;
}
.shiny-input-container select:focus{
  border-color:var(--a1)!important;outline:none;
  box-shadow:0 0 0 3px rgba(124,106,247,.22)!important;
}
select option{background:#0f172a;color:var(--txt);}

/* KPIs */
.kpi-row{display:flex;gap:14px;padding:20px 32px;}
.kpi-card{
  flex:1;background:var(--bg-card);border:1px solid var(--border);
  border-radius:16px;padding:20px 22px;backdrop-filter:blur(10px);
  transition:background .3s,transform .2s,box-shadow .2s;
  position:relative;overflow:hidden;
}
.kpi-card::before{
  content:'';position:absolute;top:0;left:0;right:0;
  height:2px;border-radius:16px 16px 0 0;
}
.kpi-card:nth-child(1)::before{background:var(--a5);}
.kpi-card:nth-child(2)::before{background:var(--a2);}
.kpi-card:nth-child(3)::before{background:var(--a1);}
.kpi-card:nth-child(4)::before{background:var(--a3);}
.kpi-card:nth-child(5)::before{background:var(--a4);}
.kpi-card:hover{background:rgba(255,255,255,.07);transform:translateY(-3px);
                box-shadow:0 8px 32px rgba(0,0,0,.35);}
.kpi-icon{font-size:1.3rem;margin-bottom:8px;display:block;}
.kpi-value{font-size:2rem!important;font-weight:800!important;
           letter-spacing:-.025em;line-height:1;margin-bottom:5px;}
.kpi-card:nth-child(1) .kpi-value{color:var(--a5)!important;}
.kpi-card:nth-child(2) .kpi-value{color:var(--a2)!important;}
.kpi-card:nth-child(3) .kpi-value{color:var(--a1)!important;}
.kpi-card:nth-child(4) .kpi-value{color:var(--a3)!important;}
.kpi-card:nth-child(5) .kpi-value{color:var(--a4)!important;}
.kpi-label{font-size:.73rem!important;color:var(--muted)!important;
           font-weight:600;text-transform:uppercase;letter-spacing:.07em;}

/* Charts */
.charts-grid{padding:22px 32px;display:grid;
             grid-template-columns:1fr 1fr;gap:16px;}
.chart-card{
  background:var(--bg-card);border:1px solid var(--border);
  border-radius:16px;padding:6px;backdrop-filter:blur(10px);
  transition:background .3s;
}
.chart-card:hover{background:rgba(255,255,255,.065);}
.chart-card-full{grid-column:1 / -1;}

::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.13);border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,.22);}
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


def dl(fig, title="", height=370):
    fig.update_layout(
        title=dict(text=title, font=dict(size=13,color="#f0f4ff",family=FONT),
                   x=0, xanchor="left", pad=dict(l=10,t=6)),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=MUTED,family=FONT,size=11),
        height=height,
        margin=dict(t=52,b=38,l=52,r=18),
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=10,color="#c4caed")),
        hoverlabel=dict(bgcolor="#1a1f3a",font_size=12,font_family=FONT),
    )
    fig.update_xaxes(gridcolor=GRID,zerolinecolor=GRID,
                     tickfont=dict(color=MUTED,family=FONT))
    fig.update_yaxes(gridcolor=GRID,zerolinecolor=GRID,
                     tickfont=dict(color=MUTED,family=FONT))
    return fig

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap"),
        ui.tags.style(CSS),
    ),

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
            ui.input_select("animal_type","Animal Type", choices=ANIMAL_TYPES, selected="All"),
            ui.input_select("year",       "Intake Year",  choices=YEARS,        selected="All"),
            ui.input_select("intake_type","Intake Type",  choices=INTAKE_TYPES, selected="All"),
            col_widths=[4,4,4],
        ),
        class_="filter-bar"
    ),

    # KPIs
    ui.div(
        ui.div(
            ui.div(ui.tags.span("🐾",class_="kpi-icon"), ui.output_ui("kpi_total"),
                   ui.div("Total Animals Processed",class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("🏠",class_="kpi-icon"), ui.output_ui("kpi_adoptions"),
                   ui.div("Adoptions",class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("💚",class_="kpi-icon"), ui.output_ui("kpi_live"),
                   ui.div("Live Release Rate",class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("⚠️",class_="kpi-icon"), ui.output_ui("kpi_euth"),
                   ui.div("Euthanasia Rate",class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.tags.span("📅",class_="kpi-icon"), ui.output_ui("kpi_los"),
                   ui.div("Median Length of Stay",class_="kpi-label"), class_="kpi-card"),
            class_="kpi-row"
        )
    ),

    # 6 Charts — 2-column grid, chart 4 spans full width
    ui.div(
        # Row 1
        ui.div(output_widget("chart_1_outcome_dist"),  class_="chart-card"),
        ui.div(output_widget("chart_2_live_by_species"),class_="chart-card"),
        # Row 2
        ui.div(output_widget("chart_3_adoption_condition"),class_="chart-card"),
        ui.div(output_widget("chart_5_los_outcome"),   class_="chart-card"),
        # Row 3 — chart 4 (heatmap) full width, chart 6 half
        ui.div(output_widget("chart_4_intake_outcome_heatmap"), class_="chart-card chart-card-full"),
        ui.div(output_widget("chart_6_adoption_age"), class_="chart-card"),
        ui.div(style=""),   # empty cell to balance grid
        class_="charts-grid"
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

    # KPIs
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

    # ── CHART 1: Outcome Type Distribution (donut) ───────────────────────────
    @output
    @render_widget
    def chart_1_outcome_dist():
        top = dff()["Outcome Type"].value_counts().reset_index()
        top.columns = ["Outcome","Count"]
        top["Pct"] = (top["Count"] / top["Count"].sum() * 100).round(1)
        fig = px.pie(top, names="Outcome", values="Count", hole=0.48,
                     color_discrete_sequence=ACCENT,
                     custom_data=["Pct"])
        fig.update_traces(
            textposition="outside", textinfo="label+percent",
            textfont=dict(size=10, family=FONT),
            marker=dict(line=dict(color="rgba(6,9,26,0.8)", width=2)),
            hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>Share: %{customdata[0]:.1f}%<extra></extra>"
        )
        return dl(fig, "Chart 1 — Outcome Type Distribution")

    # ── CHART 2: Live Release Rate by Animal Type ────────────────────────────
    @output
    @render_widget
    def chart_2_live_by_species():
        d   = dff()
        grp = d.groupby("Animal Type").agg(
            Live_Rate=("was_outcome_alive","mean"),
            Count=("Animal ID","count")
        ).reset_index().sort_values("Live_Rate", ascending=False)
        grp["Live_Pct"] = (grp["Live_Rate"] * 100).round(1)
        # Only show species with meaningful sample size
        grp = grp[grp["Count"] >= 30]
        fig = px.bar(grp, x="Animal Type", y="Live_Pct",
                     color="Live_Pct",
                     color_continuous_scale=[[0,"#f97068"],[0.45,"#fbbf24"],[1,"#43d9ad"]],
                     text=grp["Live_Pct"].astype(str) + "%",
                     custom_data=["Count"])
        fig.update_traces(
            textposition="outside",
            textfont=dict(size=11, family=FONT),
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Live Release Rate: %{y:.1f}%<br>n = %{customdata[0]:,}<extra></extra>"
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="", yaxis_title="Live Release Rate (%)",
                          yaxis_range=[0, 110])
        return dl(fig, "Chart 2 — Live Release Rate by Animal Type")

    # ── CHART 3: Adoption Rate by Intake Condition ───────────────────────────
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
            name="Adoption Rate",
            marker_color="#7c6af7", marker_line_width=0,
            text=grp["Adoption_Pct"].astype(str)+"%",
            textposition="outside",
            textfont=dict(size=10, family=FONT),
            hovertemplate="<b>%{x}</b><br>Adoption Rate: %{y:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=grp["Intake Condition"], y=grp["Live_Pct"],
            name="Live Release Rate",
            marker_color="#43d9ad", marker_line_width=0,
            text=grp["Live_Pct"].astype(str)+"%",
            textposition="outside",
            textfont=dict(size=10, family=FONT),
            hovertemplate="<b>%{x}</b><br>Live Release Rate: %{y:.1f}%<extra></extra>"
        ))
        fig.update_layout(barmode="group", xaxis_title="",
                          yaxis_title="Rate (%)", yaxis_range=[0,120])
        return dl(fig, "Chart 3 — Adoption & Live Release Rate by Intake Condition")

    # ── CHART 4: Intake Type vs Outcome Type (Heatmap) ──────────────────────
    @output
    @render_widget
    def chart_4_intake_outcome_heatmap():
        d    = dff()
        keep_out = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER",
                    "COMMUNITY CAT","DIED"]
        d = d[d["Outcome Type"].isin(keep_out)]
        pivot = d.groupby(["Intake Type","Outcome Type"]).size().reset_index(name="Count")
        wide  = pivot.pivot(index="Intake Type", columns="Outcome Type", values="Count").fillna(0)
        # Normalize each row to % so intake types with very different volumes are comparable
        wide_pct = wide.div(wide.sum(axis=1), axis=0) * 100

        fig = px.imshow(
            wide_pct.round(1),
            color_continuous_scale=[[0,"#06091a"],[0.3,"#7c6af7"],[0.7,"#43d9ad"],[1,"#fbbf24"]],
            text_auto=".1f",
            aspect="auto",
            labels=dict(color="% of Row")
        )
        fig.update_traces(
            textfont=dict(size=10, family=FONT),
            hovertemplate="Intake: <b>%{y}</b><br>Outcome: <b>%{x}</b><br>%{z:.1f}% of intakes<extra></extra>"
        )
        fig.update_coloraxes(
            colorbar=dict(title="% of Row", tickfont=dict(color=MUTED, family=FONT),
                          title_font=dict(color=MUTED, family=FONT))
        )
        fig.update_layout(xaxis_title="Outcome Type", yaxis_title="Intake Type")
        return dl(fig, "Chart 4 — Intake Type vs. Outcome Type (% of each intake category)", height=340)

    # ── CHART 5: Length of Stay by Outcome Type (box) ───────────────────────
    @output
    @render_widget
    def chart_5_los_outcome():
        d    = dff().dropna(subset=["intake_duration"])
        d    = d[d["intake_duration"] <= 200]
        cats = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER","DIED"]
        d    = d[d["Outcome Type"].isin(cats)]
        # Sort by median LOS
        order = d.groupby("Outcome Type")["intake_duration"].median().sort_values().index.tolist()
        d["Outcome Type"] = pd.Categorical(d["Outcome Type"], categories=order, ordered=True)
        d = d.sort_values("Outcome Type")

        fig = px.box(d, x="Outcome Type", y="intake_duration",
                     color="Outcome Type",
                     color_discrete_sequence=ACCENT,
                     points=False,
                     category_orders={"Outcome Type": order})
        fig.update_traces(
            line_width=1.5,
            hovertemplate="<b>%{x}</b><br>Median: %{median:.0f} d<extra></extra>"
        )
        fig.update_layout(xaxis_title="", yaxis_title="Days in Shelter",
                          showlegend=False)
        return dl(fig, "Chart 5 — Length of Stay Distribution by Outcome Type")

    # ── CHART 6: Adoption Rate by Age Group ─────────────────────────────────
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
                     color_continuous_scale=[[0,"#f97068"],[0.4,"#fbbf24"],[1,"#43d9ad"]],
                     text=grp["Adoption_Pct"].astype(str)+"%",
                     custom_data=["Count"])
        fig.update_traces(
            textposition="outside",
            textfont=dict(size=11, family=FONT),
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Adoption Rate: %{y:.1f}%<br>n = %{customdata[0]:,}<extra></extra>"
        )
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Age Group at Intake", yaxis_title="Adoption Rate (%)",
                          yaxis_range=[0, grp["Adoption_Pct"].max() * 1.2])

        # Note about missing DOB
        fig.add_annotation(
            text="Note: ~12% of records excluded due to missing DOB",
            xref="paper", yref="paper", x=1, y=-0.18,
            showarrow=False, font=dict(size=9, color=MUTED, family=FONT),
            xanchor="right"
        )
        return dl(fig, "Chart 6 — Adoption Rate by Age Group at Intake")


app = App(app_ui, server)