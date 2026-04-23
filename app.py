import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Leiden Bio Science Park · LinkedIn Analytics",
    page_icon="🧬",
    layout="wide",
)

# ── Brand colours ─────────────────────────────────────────────────────────────
ORANGE = "#EA5B0C"
BLUE   = "#08A4D4"
GREEN  = "#8CB63C"
GRAY   = "#888780"

DAG_NL = {
    "Monday": "Maandag", "Tuesday": "Dinsdag", "Wednesday": "Woensdag",
    "Thursday": "Donderdag", "Friday": "Vrijdag",
    "Saturday": "Zaterdag", "Sunday": "Zondag",
}

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetric"] { background: #f7f7f5; border-radius: 10px; padding: 1rem; }
    [data-testid="stMetricLabel"] { font-size: 12px !important; text-transform: uppercase; letter-spacing: .06em; color: #888 !important; }
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 500 !important; }
    div[data-testid="stMetricDelta"] > div { font-size: 13px !important; }
    .strategy-banner {
        background: #EA5B0C18; border-left: 4px solid #EA5B0C;
        padding: .75rem 1rem; border-radius: 0 8px 8px 0;
        font-size: 14px; margin-bottom: 1.5rem;
    }
    .section-head { font-size: 11px; font-weight: 600; text-transform: uppercase;
        letter-spacing: .08em; color: #888; margin: 1.5rem 0 .5rem; }
</style>
""", unsafe_allow_html=True)


# ── Data loader ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_xls(file_bytes: bytes):
    import io
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")

    # ── Posts sheet ──────────────────────────────────────────────────────────
    df_posts = pd.read_excel(xl, sheet_name="Alle bijdragen", header=1, skiprows=[0])
    df_posts.columns = [
        "Titel", "Link", "Soort", "Campagne", "Geplaatst_door",
        "Aangemaakt", "Campagne_start", "Campagne_eind", "Doelgroep",
        "Weergaven", "Weergaven2", "Weergaven_buiten",
        "Klikken", "CTR", "Interessant", "Commentaren",
        "Reposts", "Gevolgd", "Engagement_pct", "Type_content",
    ]
    df_posts = df_posts[df_posts["Aangemaakt"].notna()].copy()
    df_posts["Aangemaakt"]    = pd.to_datetime(df_posts["Aangemaakt"], errors="coerce")
    df_posts                  = df_posts[df_posts["Aangemaakt"].notna()]
    df_posts["Type_content"]  = df_posts["Type_content"].fillna("Tekst/Afbeelding")
    df_posts["Dag"]           = df_posts["Aangemaakt"].dt.day_name()
    df_posts["Maand"]         = df_posts["Aangemaakt"].dt.to_period("M").astype(str)
    df_posts["Titel_kort"]    = df_posts["Titel"].str.replace("\xa0", " ").str.replace("\n", " ").str.strip().str[:90]
    for col in ["Weergaven", "Klikken", "Interessant", "Commentaren", "Reposts"]:
        df_posts[col] = pd.to_numeric(df_posts[col], errors="coerce").fillna(0).astype(int)
    df_posts["Engagement_pct"] = pd.to_numeric(df_posts["Engagement_pct"], errors="coerce").fillna(0) * 100

    # ── Stats sheet ──────────────────────────────────────────────────────────
    df_stats = pd.read_excel(xl, sheet_name="Statistieken", header=1, skiprows=[0])
    df_stats.columns = [
        "Datum", "Weergaven_spontaan", "Weergaven_gesponsord", "Weergaven_totaal",
        "Unieke_weergaven", "Klikken_spontaan", "Klikken_gesponsord", "Klikken_totaal",
        "Reacties_spontaan", "Reacties_gesponsord", "Reacties_totaal",
        "Comments_spontaan", "Comments_gesponsord", "Comments_totaal",
        "Reposts_spontaan", "Reposts_gesponsord", "Reposts_totaal",
        "Engagement_spontaan", "Engagement_gesponsord", "Engagement_totaal",
    ]
    df_stats["Datum"] = pd.to_datetime(df_stats["Datum"], errors="coerce")
    df_stats = df_stats[df_stats["Datum"].notna()]

    return df_posts, df_stats


def monthly_agg(df_stats):
    df = df_stats.copy()
    df["Maand"] = df["Datum"].dt.to_period("M").astype(str)
    return df.groupby("Maand").agg(
        Weergaven=("Weergaven_totaal", "sum"),
        Klikken=("Klikken_totaal", "sum"),
        Reacties=("Reacties_totaal", "sum"),
        Reposts=("Reposts_totaal", "sum"),
    ).reset_index()


def day_agg(df_posts):
    return df_posts[df_posts["Dag"].isin(DAG_NL)].groupby("Dag").agg(
        Gem_weergaven=("Weergaven", "mean"),
        Gem_engagement=("Engagement_pct", "mean"),
        Aantal_posts=("Titel_kort", "count"),
    ).reset_index()


# ── Plotly theme helper ────────────────────────────────────────────────────────
def base_layout(**kwargs):
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Helvetica Neue, sans-serif", size=12, color="#555"),
        margin=dict(l=0, r=0, t=24, b=0),
        **kwargs,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("## Leiden Bio Science Park · LinkedIn Analytics")

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload LinkedIn export(s) (.xls) — meerdere bestanden tegelijk mag",
    type=["xls"],
    accept_multiple_files=True,
    help="Download via: LinkedIn Page → Analytics → Export (rechtsboven). Upload meerdere exports om periodes samen te voegen.",
)

if not uploaded_files:
    st.info("Upload één of meerdere LinkedIn Analytics exports om te beginnen. "
            "Je vindt de export op je LinkedIn Page onder Analytics → Export.")
    st.stop()

with st.spinner(f"Data laden ({len(uploaded_files)} bestand(en))..."):
    all_posts = []
    all_stats = []
    for f in uploaded_files:
        posts, stats = load_xls(f.read())
        all_posts.append(posts)
        all_stats.append(stats)

    df_posts = pd.concat(all_posts, ignore_index=True)
    df_posts = df_posts.drop_duplicates(subset=["Link"], keep="last")
    df_posts = df_posts.sort_values("Aangemaakt").reset_index(drop=True)

    df_stats = pd.concat(all_stats, ignore_index=True)
    df_stats = df_stats.drop_duplicates(subset=["Datum"], keep="last")
    df_stats = df_stats.sort_values("Datum").reset_index(drop=True)

if len(uploaded_files) > 1:
    st.success(f"{len(uploaded_files)} exports samengevoegd · {len(df_posts)} unieke posts · "
               f"{df_stats['Datum'].min().strftime('%b %Y')} – {df_stats['Datum'].max().strftime('%b %Y')}")

monthly = monthly_agg(df_stats)
days    = day_agg(df_posts)

# Detect strategy start month (default: 2026-04)
all_months   = sorted(df_posts["Maand"].unique())
strategy_idx = st.sidebar.selectbox(
    "Nieuwe strategie gestart vanaf",
    options=all_months,
    index=len(all_months) - 1,
    help="Posts ná deze maand worden oranje gemarkeerd.",
)

# ── Strategy banner ────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="strategy-banner">📌 Nieuwe strategie gestart vanaf <strong>{strategy_idx}</strong> '
    f'— data vóór deze maand is de baseline.</div>',
    unsafe_allow_html=True,
)

# ── KPI row ───────────────────────────────────────────────────────────────────
total_views   = int(monthly["Weergaven"].sum())
posts_new     = df_posts[df_posts["Maand"] >= strategy_idx]
posts_old     = df_posts[df_posts["Maand"] < strategy_idx]

avg_eng_new   = posts_new[posts_new["Engagement_pct"] > 0]["Engagement_pct"].mean() if len(posts_new) else 0
avg_eng_old   = posts_old[posts_old["Engagement_pct"] > 0]["Engagement_pct"].mean() if len(posts_old) else 0
delta_eng     = avg_eng_new - avg_eng_old

best_month    = monthly.loc[monthly["Weergaven"].idxmax()]
n_posts_new   = len(posts_new)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Totaal weergaven", f"{total_views:,.0f}".replace(",", "."))
c2.metric(
    "Gem. engagement (nieuw)",
    f"{avg_eng_new:.1f}%",
    delta=f"{delta_eng:+.1f}% vs baseline",
    delta_color="normal",
)
c3.metric("Beste maand", best_month["Maand"], f"{best_month['Weergaven']:,.0f} views".replace(",", "."))
c4.metric("Posts nieuwe strategie", n_posts_new)

st.markdown("---")

# ── Monthly reach chart ────────────────────────────────────────────────────────
st.markdown('<p class="section-head">Maandelijks bereik</p>', unsafe_allow_html=True)

metric_choice = st.radio(
    "Metric", ["Weergaven", "Klikken", "Reacties"],
    horizontal=True, label_visibility="collapsed",
)

bar_colors = [ORANGE if m >= strategy_idx else BLUE for m in monthly["Maand"]]
fig_month  = go.Figure(go.Bar(
    x=monthly["Maand"],
    y=monthly[metric_choice],
    marker_color=bar_colors,
    text=monthly[metric_choice].apply(lambda v: f"{v/1000:.1f}k" if v >= 1000 else str(v)),
    textposition="outside",
    textfont=dict(size=10),
))
fig_month.update_layout(
    **base_layout(height=300),
    xaxis=dict(tickangle=-45, showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="#eee", tickformat=","),
    bargap=0.35,
)
fig_month.add_annotation(
    x=0.01, y=1.06, xref="paper", yref="paper",
    text=f"<b style='color:{ORANGE}'>■</b> Nieuwe strategie &nbsp; <b style='color:{BLUE}'>■</b> Baseline",
    showarrow=False, font=dict(size=11, color="#888"), align="left",
)
st.plotly_chart(fig_month, use_container_width=True)

# ── Day-of-week split ─────────────────────────────────────────────────────────
st.markdown('<p class="section-head">Dag van de week</p>', unsafe_allow_html=True)

col_eng, col_reach = st.columns(2)

with col_eng:
    st.caption("Gemiddeld engagement %")
    eng_sorted = days.sort_values("Gem_engagement", ascending=True)
    fig_eng = go.Figure(go.Bar(
        x=eng_sorted["Gem_engagement"].round(2),
        y=eng_sorted["Dag"].map(DAG_NL),
        orientation="h",
        marker_color=ORANGE,
        text=eng_sorted["Gem_engagement"].apply(lambda v: f"{v:.2f}%"),
        textposition="outside",
    ))
    fig_eng.update_layout(**base_layout(height=220), xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False))
    st.plotly_chart(fig_eng, use_container_width=True)

with col_reach:
    st.caption("Gemiddeld bereik (views)")
    reach_sorted = days.sort_values("Gem_weergaven", ascending=True)
    fig_reach = go.Figure(go.Bar(
        x=reach_sorted["Gem_weergaven"].round(0),
        y=reach_sorted["Dag"].map(DAG_NL),
        orientation="h",
        marker_color=BLUE,
        text=reach_sorted["Gem_weergaven"].apply(lambda v: f"{int(v):,}".replace(",", ".")),
        textposition="outside",
    ))
    fig_reach.update_layout(**base_layout(height=220), xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False))
    st.plotly_chart(fig_reach, use_container_width=True)

# ── Top posts table ───────────────────────────────────────────────────────────
st.markdown('<p class="section-head">Top posts</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Meeste views", "Hoogste engagement", "Nieuwe strategie"])

def post_table(df):
    display = df[["Titel_kort", "Aangemaakt", "Dag", "Weergaven", "Klikken", "Interessant", "Engagement_pct"]].copy()
    display["Aangemaakt"]    = display["Aangemaakt"].dt.strftime("%Y-%m-%d")
    display["Dag"]           = display["Dag"].map(DAG_NL)
    display["Engagement_pct"] = display["Engagement_pct"].round(1).astype(str) + "%"
    display.columns          = ["Post", "Datum", "Dag", "Views", "Klikken", "Likes", "Engagement"]
    display["Views"]         = display["Views"].apply(lambda v: f"{v:,}".replace(",", "."))
    display["Klikken"]       = display["Klikken"].apply(lambda v: f"{v:,}".replace(",", "."))
    st.dataframe(display, use_container_width=True, hide_index=True)

with tab1:
    post_table(df_posts.sort_values("Weergaven", ascending=False).head(10))

with tab2:
    post_table(
        df_posts[df_posts["Engagement_pct"] > 0]
        .sort_values("Engagement_pct", ascending=False).head(10)
    )

with tab3:
    new_posts = df_posts[df_posts["Maand"] >= strategy_idx].sort_values("Weergaven", ascending=False)
    if len(new_posts) == 0:
        st.info("Nog geen posts in de nieuwe strategie periode.")
    else:
        post_table(new_posts.head(10))

# ── Engagement scatter ────────────────────────────────────────────────────────
st.markdown('<p class="section-head">Views vs engagement per post</p>', unsafe_allow_html=True)

scatter_df = df_posts[df_posts["Weergaven"] > 0].copy()
scatter_df["Periode"] = scatter_df["Maand"].apply(lambda m: "Nieuwe strategie" if m >= strategy_idx else "Baseline")

fig_scatter = px.scatter(
    scatter_df,
    x="Weergaven",
    y="Engagement_pct",
    color="Periode",
    color_discrete_map={"Nieuwe strategie": ORANGE, "Baseline": BLUE},
    hover_data={"Titel_kort": True, "Aangemaakt": True, "Weergaven": True, "Engagement_pct": ":.1f"},
    labels={"Weergaven": "Views", "Engagement_pct": "Engagement %"},
)
fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))
fig_scatter.update_layout(**base_layout(height=320), legend=dict(orientation="h", y=1.08))
st.plotly_chart(fig_scatter, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"Data: {df_stats['Datum'].min().strftime('%d %b %Y')} – {df_stats['Datum'].max().strftime('%d %b %Y')} · "
    f"{len(df_posts)} posts · Leiden Bio Science Park LinkedIn Analytics"
)
