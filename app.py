"""
Left Behind: A Data-Driven Analysis of Long Beach Animal Shelter Outcome Patterns
Shiny for Python Dashboard
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget

# ─────────────────────────────────────────────
# DATA LOADING & CLEANING
# ─────────────────────────────────────────────

def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)

    # Parse dates
    df["Intake Date"]  = pd.to_datetime(df["Intake Date"],  errors="coerce")
    df["Outcome Date"] = pd.to_datetime(df["Outcome Date"], errors="coerce")
    df["DOB"]          = pd.to_datetime(df["DOB"],          errors="coerce")

    # Drop records still in shelter (no outcome yet)
    df = df[df["Outcome Type"].notna()].copy()

    # Age at intake (years)
    df["age_at_intake_years"] = (df["Intake Date"] - df["DOB"]).dt.days / 365.25
    # Remove impossible ages
    df.loc[df["age_at_intake_years"] < 0, "age_at_intake_years"] = np.nan
    df.loc[df["age_at_intake_years"] > 30, "age_at_intake_years"] = np.nan

    # Age bucket
    bins   = [0, 0.5, 1, 3, 7, 15, 100]
    labels = ["< 6 mo", "6–12 mo", "1–3 yr", "3–7 yr", "7–15 yr", "15+ yr"]
    df["age_group"] = pd.cut(df["age_at_intake_years"], bins=bins, labels=labels)

    # Derived columns
    df["intake_year"]  = df["Intake Date"].dt.year
    df["intake_month"] = df["Intake Date"].dt.month
    df["is_adoption"]  = (df["Outcome Type"] == "ADOPTION").astype(int)

    # Normalise Sex: keep only meaningful values
    sex_map = {
        "Spayed": "Spayed Female",
        "Neutered": "Neutered Male",
        "Female": "Intact Female",
        "Male": "Intact Male",
        "Unknown": "Unknown",
    }
    df["Sex Clean"] = df["Sex"].map(sex_map).fillna("Unknown")

    # Live-release flag already exists: was_outcome_alive
    # Simplify Intake Condition labels
    df["Intake Condition"] = df["Intake Condition"].str.strip()

    # Keep only years with meaningful data
    df = df[df["intake_year"] >= 2017]

    return df


# ── Load once at startup ──────────────────────────────────────────────────────
CSV_PATH = "https://github.com/Mushimuche/animal-shelter-dashboard/raw/refs/heads/main/animal-shelter-intakes-and-outcomes.csv"
df_full  = load_and_clean(CSV_PATH)

ANIMAL_TYPES = ["All"] + sorted(df_full["Animal Type"].unique().tolist())
YEARS        = ["All"] + sorted(df_full["intake_year"].dropna().astype(int).unique().tolist(), reverse=True)

# Colour palette (accessible)
PALETTE = px.colors.qualitative.Safe

# ─────────────────────────────────────────────
# HELPER – pre-compute KPIs
# ─────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    total          = len(df)
    adoptions      = (df["Outcome Type"] == "ADOPTION").sum()
    live_release   = df["was_outcome_alive"].sum()
    euthanasia     = (df["Outcome Type"] == "EUTHANASIA").sum()
    avg_los        = df["intake_duration"].median()
    adoption_rate  = adoptions / total * 100 if total else 0
    live_rate      = live_release / total * 100 if total else 0
    euth_rate      = euthanasia / total * 100 if total else 0
    return dict(
        total=total,
        adoptions=int(adoptions),
        adoption_rate=round(adoption_rate, 1),
        live_rate=round(live_rate, 1),
        euth_rate=round(euth_rate, 1),
        avg_los=round(avg_los, 1),
    )

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

app_ui = ui.page_fluid(

    ui.tags.head(
        ui.tags.style("""
        body { background:#0f172a; color:#e2e8f0; font-family:'Segoe UI',sans-serif; }
        .kpi-card  { background:#1e293b; border-radius:12px; padding:18px 22px;
                     border-left:4px solid #38bdf8; margin-bottom:8px; }
        .kpi-value { font-size:2rem; font-weight:700; color:#38bdf8; }
        .kpi-label { font-size:.82rem; color:#94a3b8; margin-top:2px; }
        .section-title { font-size:1.1rem; font-weight:600; color:#f1f5f9;
                          border-bottom:1px solid #334155; padding-bottom:8px;
                          margin:24px 0 14px; }
        .sidebar-panel { background:#1e293b !important; border-radius:12px;
                         padding:16px; border:1px solid #334155; }
        .main-panel    { background:#0f172a; }
        select, .shiny-input-container label { color:#cbd5e1 !important; }
        .nav-tab { color:#94a3b8 !important; }
        h1 { font-size:1.6rem; font-weight:700; color:#f8fafc; }
        p.subtitle { color:#94a3b8; font-size:.9rem; }
        .insight-box { background:#1e3a5f; border-radius:8px; padding:14px 16px;
                       border-left:3px solid #38bdf8; margin-top:10px;
                       font-size:.85rem; color:#bae6fd; line-height:1.6; }
        """)
    ),

    # ── Header ──
    ui.div(
        ui.h1("🐾 Left Behind: Long Beach Animal Shelter Outcome Patterns"),
        ui.p("A data-driven analysis of 54 k+ intake records from the City of Long Beach Open Data Portal (updated Apr 23 2026)",
             class_="subtitle"),
        style="padding:24px 24px 0;"
    ),

    # ── Filters ──
    ui.div(
        ui.layout_columns(
            ui.input_select("animal_type", "Animal Type", choices=ANIMAL_TYPES, selected="All"),
            ui.input_select("year",        "Intake Year",  choices=YEARS,        selected="All"),
            ui.input_select("intake_type", "Intake Type",
                            choices=["All"] + sorted(df_full["Intake Type"].dropna().unique().tolist()),
                            selected="All"),
            col_widths=[4, 4, 4],
        ),
        style="padding:0 24px 10px; background:#0f172a;"
    ),

    # ── KPI Row ──
    ui.div(
        ui.layout_columns(
            ui.div(ui.div(class_="kpi-value", id="kpi_total"),
                   ui.div("Total Animals Processed", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.div(class_="kpi-value", id="kpi_adoptions"),
                   ui.div("Adoptions", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.div(class_="kpi-value", id="kpi_live"),
                   ui.div("Live Release Rate", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.div(class_="kpi-value", id="kpi_euth"),
                   ui.div("Euthanasia Rate", class_="kpi-label"), class_="kpi-card"),
            ui.div(ui.div(class_="kpi-value", id="kpi_los"),
                   ui.div("Median Length of Stay (days)", class_="kpi-label"), class_="kpi-card"),
            col_widths=[2, 3, 2, 2, 3],
        ),
        style="padding:0 24px;"
    ),

    # ── Tabs ──
    ui.navset_tab(

        # ── TAB 1: Outcomes Overview ──
        ui.nav_panel("📊 Outcomes Overview",
            ui.div(
                ui.layout_columns(
                    output_widget("chart_outcome_dist"),
                    output_widget("chart_outcome_by_species"),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    output_widget("chart_trend_yearly"),
                    output_widget("chart_live_by_condition"),
                    col_widths=[6, 6],
                ),
                style="padding:16px 24px;"
            )
        ),

        # ── TAB 2: Animal Characteristics ──
        ui.nav_panel("🐕 Animal Characteristics",
            ui.div(
                ui.layout_columns(
                    output_widget("chart_age_outcome"),
                    output_widget("chart_sex_outcome"),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    output_widget("chart_los_by_type"),
                    output_widget("chart_intake_type"),
                    col_widths=[6, 6],
                ),
                style="padding:16px 24px;"
            )
        ),

        # ── TAB 3: Length of Stay ──
        ui.nav_panel("⏱️ Length of Stay",
            ui.div(
                ui.layout_columns(
                    output_widget("chart_los_outcome"),
                    output_widget("chart_los_species"),
                    col_widths=[6, 6],
                ),
                output_widget("chart_los_heatmap"),
                style="padding:16px 24px;"
            )
        ),

        # ── TAB 4: Trends ──
        ui.nav_panel("📈 Trends Over Time",
            ui.div(
                output_widget("chart_monthly_trend"),
                ui.layout_columns(
                    output_widget("chart_yearly_mix"),
                    output_widget("chart_adoption_trend"),
                    col_widths=[6, 6],
                ),
                style="padding:16px 24px;"
            )
        ),

        # ── TAB 5: Insights ──
        ui.nav_panel("💡 Insights & Recommendations",
            ui.div(
                ui.h3("Key Business Insights", style="color:#f1f5f9; margin-bottom:16px;"),
                ui.div(
                    ui.h5("🔍 Finding 1 — Intake Condition is the Strongest Predictor of Outcome",
                          style="color:#f1f5f9;"),
                    ui.p("""Animals arriving in NORMAL condition have a 95.4% live release rate,
                    while animals arriving ILL SEVERE drop to just 21.5% and INJURED SEVERE to 31.3%.
                    Early triage and medical intervention at intake is the single highest-leverage action
                    the shelter can take to improve outcomes."""),
                    class_="insight-box"
                ),
                ui.div(
                    ui.h5("🔍 Finding 2 — Length of Stay Predicts Outcome Type",
                          style="color:#f1f5f9;"),
                    ui.p("""Adopted animals spend a median of 49 days in the shelter — roughly 6× longer
                    than euthanised animals (5 days). This means euthanasia often occurs quickly, possibly
                    before adoption marketing has even begun. A mandatory minimum 7-day marketing window
                    before euthanasia decisions (for healthy animals) could materially change outcomes."""),
                    class_="insight-box"
                ),
                ui.div(
                    ui.h5("🔍 Finding 3 — Dogs Adopt Better Than Cats Despite More Cats",
                          style="color:#f1f5f9;"),
                    ui.p("""Cats are the most common intake (25,760 records) yet have a lower adoption rate (24.3%)
                    than dogs (28.8%). Cats also make up the bulk of COMMUNITY CAT and TRANSFER outcomes.
                    Targeted cat-adoption campaigns (free/reduced fee events, foster-to-adopt programs)
                    could meaningfully reduce cat inventory pressure."""),
                    class_="insight-box"
                ),
                ui.div(
                    ui.h5("🔍 Finding 4 — Spayed/Neutered Animals Have Near-Perfect Live Release Rates",
                          style="color:#f1f5f9;"),
                    ui.p("""Spayed animals achieve a 97.7% live release rate and neutered animals 95.5%,
                    versus 79.5% for intact females and 77.8% for intact males.
                    This strongly supports expanding TNR (Trap-Neuter-Return) and pre-adoption spay/neuter
                    programs as a long-term strategy for both welfare and adoption outcomes."""),
                    class_="insight-box"
                ),
                ui.div(
                    ui.h5("🔍 Finding 5 — Stray Intake Dominates; Owner Surrenders Are a Controllable Lever",
                          style="color:#f1f5f9;"),
                    ui.p("""Stray animals (38,079 records, 70%) dominate intake. Owner surrenders (4,756)
                    are the second largest controllable category. Community outreach programs that help
                    owners keep pets (veterinary assistance, training resources, temporary fostering)
                    could reduce owner-surrender numbers and free up shelter capacity."""),
                    class_="insight-box"
                ),
                ui.div(
                    ui.h5("🔍 Finding 6 — Birds, Other, and Wild Animals Drag Down Overall Live Release Rate",
                          style="color:#f1f5f9;"),
                    ui.p("""Wild animals have a 32.8% live release rate and OTHER animals 45.6%,
                    bringing down the shelter's headline metric. Separating these from companion animals
                    in reporting — and partnering with wildlife rehabilitation organisations —
                    would give a more accurate picture of companion-animal outcomes
                    and route wild animals to better-equipped handlers."""),
                    class_="insight-box"
                ),
                ui.h3("Strategic Recommendations", style="color:#f1f5f9; margin:24px 0 12px;"),
                ui.tags.ol(
                    ui.tags.li("Implement immediate medical triage scoring at intake — prioritise resources for borderline ILL/INJURED animals."),
                    ui.tags.li("Introduce a 7-day mandatory marketing hold for all healthy animals before euthanasia consideration."),
                    ui.tags.li("Launch targeted cat adoption campaigns (reduced fees, foster-to-adopt, social media spotlights)."),
                    ui.tags.li("Expand TNR programs and pre-intake spay/neuter partnerships with local vets."),
                    ui.tags.li("Create an owner-support hotline to divert owner surrenders into voluntary fostering."),
                    ui.tags.li("Partner with wildlife rehabilitation centres to re-route wild animal intakes."),
                    style="color:#cbd5e1; line-height:2.2; font-size:.9rem;"
                ),
                style="padding:20px 28px;"
            )
        ),

    ),

    style="min-height:100vh;"
)

# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────

DARK_LAYOUT = dict(
    paper_bgcolor="#1e293b",
    plot_bgcolor="#1e293b",
    font=dict(color="#cbd5e1", size=12),
    margin=dict(t=50, b=40, l=50, r=20),
    legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
)

def apply_dark(fig):
    fig.update_layout(**DARK_LAYOUT)
    fig.update_xaxes(gridcolor="#334155", zerolinecolor="#334155")
    fig.update_yaxes(gridcolor="#334155", zerolinecolor="#334155")
    return fig

# ─────────────────────────────────────────────
# SERVER
# ─────────────────────────────────────────────

def server(input, output, session):

    # ── Reactive filtered df ──────────────────────────────────────────────────
    @reactive.calc
    def df_filtered():
        d = df_full.copy()
        if input.animal_type() != "All":
            d = d[d["Animal Type"] == input.animal_type()]
        if input.year() != "All":
            d = d[d["intake_year"] == int(input.year())]
        if input.intake_type() != "All":
            d = d[d["Intake Type"] == input.intake_type()]
        return d

    # ── KPIs (rendered as text into divs) ────────────────────────────────────
    @output
    @render.ui
    def kpi_total():
        kpis = compute_kpis(df_filtered())
        return ui.div(f"{kpis['total']:,}", class_="kpi-value")

    @output
    @render.ui
    def kpi_adoptions():
        kpis = compute_kpis(df_filtered())
        return ui.div(f"{kpis['adoptions']:,}", class_="kpi-value")

    @output
    @render.ui
    def kpi_live():
        kpis = compute_kpis(df_filtered())
        return ui.div(f"{kpis['live_rate']}%", class_="kpi-value")

    @output
    @render.ui
    def kpi_euth():
        kpis = compute_kpis(df_filtered())
        return ui.div(f"{kpis['euth_rate']}%", class_="kpi-value",
                      style="color:#f87171;")

    @output
    @render.ui
    def kpi_los():
        kpis = compute_kpis(df_filtered())
        return ui.div(f"{kpis['avg_los']} d", class_="kpi-value")

    # ── Chart 1: Outcome Distribution (donut) ────────────────────────────────
    @output
    @render_widget
    def chart_outcome_dist():
        d = df_filtered()
        top = d["Outcome Type"].value_counts().head(10).reset_index()
        top.columns = ["Outcome", "Count"]
        fig = px.pie(top, names="Outcome", values="Count",
                     title="Outcome Type Distribution",
                     hole=0.45, color_discrete_sequence=PALETTE)
        fig.update_traces(textposition="outside", textinfo="label+percent")
        return apply_dark(fig)

    # ── Chart 2: Outcome by Species (stacked bar) ────────────────────────────
    @output
    @render_widget
    def chart_outcome_by_species():
        d = df_filtered()
        # Group into broad categories
        cats_of_interest = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER",
                            "RETURN TO OWNER","COMMUNITY CAT","DIED"]
        dd = d[d["Outcome Type"].isin(cats_of_interest)]
        grp = dd.groupby(["Animal Type","Outcome Type"]).size().reset_index(name="Count")
        fig = px.bar(grp, x="Animal Type", y="Count", color="Outcome Type",
                     title="Outcomes by Animal Type",
                     color_discrete_sequence=PALETTE, barmode="stack")
        return apply_dark(fig)

    # ── Chart 3: Yearly Intake Trend ─────────────────────────────────────────
    @output
    @render_widget
    def chart_trend_yearly():
        d = df_filtered()
        yr = d.groupby("intake_year").agg(
            Total=("Animal ID","count"),
            Adoptions=("is_adoption","sum"),
            Live=("was_outcome_alive","sum"),
        ).reset_index()
        yr["Adoption Rate"] = yr["Adoptions"] / yr["Total"] * 100
        yr["Live Rate"]     = yr["Live"]      / yr["Total"] * 100

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=yr["intake_year"], y=yr["Total"],
                             name="Total Intakes", marker_color="#334155"), secondary_y=False)
        fig.add_trace(go.Scatter(x=yr["intake_year"], y=yr["Live Rate"],
                                 name="Live Release %", mode="lines+markers",
                                 line=dict(color="#38bdf8", width=2)), secondary_y=True)
        fig.add_trace(go.Scatter(x=yr["intake_year"], y=yr["Adoption Rate"],
                                 name="Adoption %", mode="lines+markers",
                                 line=dict(color="#4ade80", width=2, dash="dash")), secondary_y=True)
        fig.update_layout(title="Yearly Intake Volume & Outcome Rates")
        fig.update_yaxes(title_text="Count", secondary_y=False)
        fig.update_yaxes(title_text="Rate (%)", secondary_y=True)
        return apply_dark(fig)

    # ── Chart 4: Live Release by Intake Condition ────────────────────────────
    @output
    @render_widget
    def chart_live_by_condition():
        d = df_filtered()
        grp = d.groupby("Intake Condition").agg(
            Live_Rate=("was_outcome_alive","mean"),
            Count=("Animal ID","count")
        ).reset_index().sort_values("Live_Rate")
        grp["Live_Rate_pct"] = grp["Live_Rate"] * 100

        fig = px.bar(grp, x="Live_Rate_pct", y="Intake Condition",
                     orientation="h",
                     title="Live Release Rate by Intake Condition",
                     color="Live_Rate_pct",
                     color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                     text=grp["Live_Rate_pct"].round(1).astype(str) + "%")
        fig.update_traces(textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Live Release Rate (%)", yaxis_title="")
        return apply_dark(fig)

    # ── Chart 5: Outcome by Age Group ────────────────────────────────────────
    @output
    @render_widget
    def chart_age_outcome():
        d = df_filtered().dropna(subset=["age_group"])
        grp = d.groupby(["age_group","Outcome Type"]).size().reset_index(name="Count")
        cats = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER"]
        grp  = grp[grp["Outcome Type"].isin(cats)]
        fig  = px.bar(grp, x="age_group", y="Count", color="Outcome Type",
                      title="Outcomes by Age at Intake",
                      color_discrete_sequence=PALETTE, barmode="group")
        fig.update_layout(xaxis_title="Age Group", yaxis_title="Count")
        return apply_dark(fig)

    # ── Chart 6: Live Release by Sex ─────────────────────────────────────────
    @output
    @render_widget
    def chart_sex_outcome():
        d = df_filtered()
        grp = d.groupby("Sex Clean").agg(
            Live_Rate=("was_outcome_alive","mean"),
            Count=("Animal ID","count")
        ).reset_index()
        grp["Live_Rate_pct"] = grp["Live_Rate"] * 100
        fig = px.bar(grp, x="Sex Clean", y="Live_Rate_pct",
                     title="Live Release Rate by Sex / Neuter Status",
                     color="Live_Rate_pct",
                     color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
                     text=grp["Live_Rate_pct"].round(1).astype(str) + "%")
        fig.update_traces(textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="", yaxis_title="Live Release Rate (%)")
        return apply_dark(fig)

    # ── Chart 7: LOS by Intake Type ──────────────────────────────────────────
    @output
    @render_widget
    def chart_los_by_type():
        d = df_filtered().dropna(subset=["intake_duration"])
        d = d[d["intake_duration"] <= 365]
        grp = d.groupby("Intake Type")["intake_duration"].median().reset_index()
        grp.columns = ["Intake Type","Median LOS"]
        grp = grp.sort_values("Median LOS", ascending=False)
        fig = px.bar(grp, x="Median LOS", y="Intake Type",
                     orientation="h",
                     title="Median Length of Stay by Intake Type",
                     color="Median LOS",
                     color_continuous_scale="Blues",
                     text=grp["Median LOS"].round(1))
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Median Days", yaxis_title="")
        return apply_dark(fig)

    # ── Chart 8: Intake Type Breakdown ───────────────────────────────────────
    @output
    @render_widget
    def chart_intake_type():
        d = df_filtered()
        grp = d["Intake Type"].value_counts().reset_index()
        grp.columns = ["Intake Type","Count"]
        fig = px.bar(grp, x="Count", y="Intake Type",
                     orientation="h",
                     title="Intake Volume by Intake Type",
                     color="Count",
                     color_continuous_scale="Teal",
                     text="Count")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Number of Animals", yaxis_title="")
        return apply_dark(fig)

    # ── Chart 9: LOS by Outcome Type (box) ───────────────────────────────────
    @output
    @render_widget
    def chart_los_outcome():
        d = df_filtered().dropna(subset=["intake_duration"])
        d = d[d["intake_duration"] <= 200]
        cats = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER","DIED"]
        d = d[d["Outcome Type"].isin(cats)]
        fig = px.box(d, x="Outcome Type", y="intake_duration",
                     title="Length of Stay Distribution by Outcome Type",
                     color="Outcome Type",
                     color_discrete_sequence=PALETTE,
                     points=False)
        fig.update_layout(xaxis_title="", yaxis_title="Days in Shelter",
                          showlegend=False)
        return apply_dark(fig)

    # ── Chart 10: LOS by Species (violin) ────────────────────────────────────
    @output
    @render_widget
    def chart_los_species():
        d = df_filtered().dropna(subset=["intake_duration"])
        d = d[d["intake_duration"] <= 200]
        main_species = ["CAT","DOG","BIRD","RABBIT","GUINEA PIG"]
        d = d[d["Animal Type"].isin(main_species)]
        fig = px.violin(d, x="Animal Type", y="intake_duration",
                        title="Length of Stay by Species",
                        color="Animal Type",
                        color_discrete_sequence=PALETTE,
                        box=True, points=False)
        fig.update_layout(xaxis_title="", yaxis_title="Days in Shelter",
                          showlegend=False)
        return apply_dark(fig)

    # ── Chart 11: LOS Heatmap (month × species) ──────────────────────────────
    @output
    @render_widget
    def chart_los_heatmap():
        d = df_filtered().dropna(subset=["intake_duration","intake_month"])
        main_species = ["CAT","DOG","BIRD","RABBIT"]
        d = d[d["Animal Type"].isin(main_species)]
        piv = d.groupby(["intake_month","Animal Type"])["intake_duration"].median().reset_index()
        piv_wide = piv.pivot(index="Animal Type", columns="intake_month", values="intake_duration")
        piv_wide.columns = ["Jan","Feb","Mar","Apr","May","Jun",
                             "Jul","Aug","Sep","Oct","Nov","Dec"][:len(piv_wide.columns)]
        fig = px.imshow(piv_wide, title="Median Length of Stay: Species × Month of Intake",
                        color_continuous_scale="YlOrRd",
                        text_auto=".0f", aspect="auto")
        fig.update_layout(xaxis_title="Month of Intake", yaxis_title="")
        return apply_dark(fig)

    # ── Chart 12: Monthly trend (line) ───────────────────────────────────────
    @output
    @render_widget
    def chart_monthly_trend():
        d = df_filtered()
        d["ym"] = d["Intake Date"].dt.to_period("M").astype(str)
        grp = d.groupby("ym").agg(
            Total=("Animal ID","count"),
            Adoptions=("is_adoption","sum"),
        ).reset_index()
        grp["Adoption Rate"] = grp["Adoptions"] / grp["Total"] * 100

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=grp["ym"], y=grp["Total"],
                                 name="Monthly Intakes", fill="tozeroy",
                                 line=dict(color="#334155"),
                                 fillcolor="rgba(51,65,85,0.5)"), secondary_y=False)
        fig.add_trace(go.Scatter(x=grp["ym"], y=grp["Adoption Rate"],
                                 name="Adoption Rate %", mode="lines",
                                 line=dict(color="#4ade80", width=1.5)), secondary_y=True)
        fig.update_layout(title="Monthly Intake Volume & Adoption Rate Over Time")
        fig.update_yaxes(title_text="Monthly Intakes", secondary_y=False)
        fig.update_yaxes(title_text="Adoption Rate (%)", secondary_y=True)
        return apply_dark(fig)

    # ── Chart 13: Yearly outcome mix (100% stacked) ──────────────────────────
    @output
    @render_widget
    def chart_yearly_mix():
        d = df_filtered()
        cats = ["ADOPTION","EUTHANASIA","RESCUE","TRANSFER","RETURN TO OWNER","OTHER"]
        def remap(x):
            return x if x in cats[:-1] else "OTHER"
        d["Outcome Cat"] = d["Outcome Type"].apply(remap)
        grp = d.groupby(["intake_year","Outcome Cat"]).size().reset_index(name="Count")
        totals = grp.groupby("intake_year")["Count"].transform("sum")
        grp["Pct"] = grp["Count"] / totals * 100
        fig = px.bar(grp, x="intake_year", y="Pct", color="Outcome Cat",
                     title="Outcome Mix by Year (% of annual intakes)",
                     color_discrete_sequence=PALETTE, barmode="stack")
        fig.update_layout(xaxis_title="Year", yaxis_title="% of Animals",
                          yaxis_range=[0,100])
        return apply_dark(fig)

    # ── Chart 14: Adoption rate by species over time ──────────────────────────
    @output
    @render_widget
    def chart_adoption_trend():
        d = df_filtered()
        main_species = ["CAT","DOG","RABBIT"]
        d = d[d["Animal Type"].isin(main_species)]
        grp = d.groupby(["intake_year","Animal Type"]).agg(
            Adoption_Rate=("is_adoption","mean")
        ).reset_index()
        grp["Adoption_Rate"] *= 100
        fig = px.line(grp, x="intake_year", y="Adoption_Rate", color="Animal Type",
                      title="Adoption Rate Over Time by Species",
                      markers=True, color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="Year", yaxis_title="Adoption Rate (%)")
        return apply_dark(fig)


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
from shinywidgets import output_widget, render_widget   # already imported above

app = App(app_ui, server)