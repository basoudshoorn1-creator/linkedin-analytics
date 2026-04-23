import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io

st.set_page_config(page_title="LinkedIn Analytics Dashboard", page_icon="🧬", layout="wide")

ORANGE = "#EA5B0C"
BLUE   = "#08A4D4"
GREEN  = "#8CB63C"
GRAY   = "#888780"

DAG_NL = {"Monday":"Maandag","Tuesday":"Dinsdag","Wednesday":"Woensdag","Thursday":"Donderdag","Friday":"Vrijdag","Saturday":"Zaterdag","Sunday":"Zondag"}

CLUSTER_DEF = {
    "Park ecosysteem": {"type":"locatie","keys":["Randstad"]},
    "Overheid": {"type":"branche","keys":["Overheids","bestuur"]},
    "Internationaal": {"type":"locatie","keys":["Boston","Parijs","Zürich","Berlijn","Barcelona","London","Kopenhagen","Stockholm","München","Leuven","Gent","New York","Cambridge","Oxford","India"]},
    "Sector LSH": {"type":"branche","keys":["Biotechnologisch","Geneesmiddelen","Onderzoeksdiensten","Medische praktijken","Ziekenhuizen","medische apparatuur","diagnostisch"]},
    "Talent": {"type":"mixed","branche_keys":["onderwijs"],"seniority_keys":["Stagiair"]},
}

st.markdown("""<style>
[data-testid="stMetric"]{background:#f7f7f5;border-radius:10px;padding:1rem}
[data-testid="stMetricLabel"]{font-size:12px!important;text-transform:uppercase;letter-spacing:.06em;color:#888!important}
[data-testid="stMetricValue"]{font-size:26px!important;font-weight:500!important}
.strategy-banner{background:#EA5B0C18;border-left:4px solid #EA5B0C;padding:.75rem 1rem;border-radius:0 8px 8px 0;font-size:14px;margin-bottom:1.5rem}
.section-head{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#888;margin:1.5rem 0 .5rem}
</style>""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_content(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    df_posts = pd.read_excel(xl, sheet_name="Alle bijdragen", header=1, skiprows=[0])
    df_posts.columns = ["Titel","Link","Soort","Campagne","Geplaatst_door","Aangemaakt","Campagne_start","Campagne_eind","Doelgroep","Weergaven","Weergaven2","Weergaven_buiten","Klikken","CTR","Interessant","Commentaren","Reposts","Gevolgd","Engagement_pct","Type_content"]
    df_posts = df_posts[df_posts["Aangemaakt"].notna()].copy()
    df_posts["Aangemaakt"] = pd.to_datetime(df_posts["Aangemaakt"], errors="coerce")
    df_posts = df_posts[df_posts["Aangemaakt"].notna()]
    df_posts["Type_content"] = df_posts["Type_content"].fillna("Tekst/Afbeelding")
    df_posts["Dag"] = df_posts["Aangemaakt"].dt.day_name()
    df_posts["Maand"] = df_posts["Aangemaakt"].dt.to_period("M").astype(str)
    df_posts["Titel_kort"] = df_posts["Titel"].str.replace("\xa0"," ").str.replace("\n"," ").str.strip().str[:90]
    for col in ["Weergaven","Klikken","Interessant","Commentaren","Reposts"]:
        df_posts[col] = pd.to_numeric(df_posts[col], errors="coerce").fillna(0).astype(int)
    df_posts["Engagement_pct"] = pd.to_numeric(df_posts["Engagement_pct"], errors="coerce").fillna(0)*100
    df_posts["CTR"] = pd.to_numeric(df_posts["CTR"], errors="coerce").fillna(0)*100
    df_stats = pd.read_excel(xl, sheet_name="Statistieken", header=1, skiprows=[0])
    df_stats.columns = ["Datum","Weergaven_spontaan","Weergaven_gesponsord","Weergaven_totaal","Unieke_weergaven","Klikken_spontaan","Klikken_gesponsord","Klikken_totaal","Reacties_spontaan","Reacties_gesponsord","Reacties_totaal","Comments_spontaan","Comments_gesponsord","Comments_totaal","Reposts_spontaan","Reposts_gesponsord","Reposts_totaal","Engagement_spontaan","Engagement_gesponsord","Engagement_totaal"]
    df_stats["Datum"] = pd.to_datetime(df_stats["Datum"], errors="coerce")
    df_stats = df_stats[df_stats["Datum"].notna()]
    return df_posts, df_stats

@st.cache_data(show_spinner=False)
def load_followers(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    df_growth = pd.read_excel(xl, sheet_name="Nieuwe volgers")
    df_growth["Datum"] = pd.to_datetime(df_growth["Datum"])
    sheets = {s: pd.read_excel(xl, sheet_name=s) for s in ["Locatie","Functie","Senioriteitsniveau","Branche","Bedrijfsgrootte"]}
    return df_growth, sheets

@st.cache_data(show_spinner=False)
def load_visitors(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    df_visits = pd.read_excel(xl, sheet_name="Statistieken over bezoekers")
    df_visits["Datum"] = pd.to_datetime(df_visits["Datum"])
    sheets = {s: pd.read_excel(xl, sheet_name=s) for s in ["Locatie","Functie","Senioriteitsniveau","Branche","Bedrijfsgrootte"]}
    return df_visits, sheets

@st.cache_data(show_spinner=False)
def load_competitors(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
    df = pd.read_excel(xl, sheet_name="COMPETITORS", header=1)
    df.columns = ["Pagina","Nieuwe_volgers","Bijdragen","Commentaren","Commentaren_per_dag","Reacties"]
    return df[df["Pagina"].notna()]

def base_layout(**kw):
    return dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(family="Helvetica Neue,sans-serif",size=12,color="#555"),margin=dict(l=0,r=0,t=24,b=0),**kw)

def horiz_bar(df, x_col, y_col, color, height=220, pct=False):
    fmt = lambda v: f"{v:.1f}%" if pct else f"{int(v):,}".replace(",",".")
    fig = go.Figure(go.Bar(x=df[x_col],y=df[y_col],orientation="h",marker_color=color,text=df[x_col].apply(fmt),textposition="outside"))
    fig.update_layout(**base_layout(height=height),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
    return fig

def post_table(df):
    d = df[["Titel_kort","Aangemaakt","Dag","Weergaven","Klikken","Interessant","Engagement_pct"]].copy()
    d["Aangemaakt"] = d["Aangemaakt"].dt.strftime("%Y-%m-%d")
    d["Dag"] = d["Dag"].map(DAG_NL)
    d["Engagement_pct"] = d["Engagement_pct"].round(1).astype(str)+"%"
    d.columns = ["Post","Datum","Dag","Views","Klikken","Likes","Engagement"]
    d["Views"] = d["Views"].apply(lambda v: f"{v:,}".replace(",","."))
    d["Klikken"] = d["Klikken"].apply(lambda v: f"{v:,}".replace(",","."))
    st.dataframe(d, use_container_width=True, hide_index=True)

def cluster_score(fol_sheets, name):
    c = CLUSTER_DEF[name]
    total = 0
    if c["type"]=="locatie":
        df=fol_sheets["Locatie"]; col=df.columns[1]
        for k in c["keys"]: total+=int(df[df[df.columns[0]].str.contains(k,na=False,case=False)][col].sum())
    elif c["type"]=="branche":
        df=fol_sheets["Branche"]; col=df.columns[1]
        for k in c["keys"]: total+=int(df[df[df.columns[0]].str.contains(k,na=False,case=False)][col].sum())
    elif c["type"]=="mixed":
        df_b=fol_sheets["Branche"]; col_b=df_b.columns[1]
        for k in c.get("branche_keys",[]): total+=int(df_b[df_b[df_b.columns[0]].str.contains(k,na=False,case=False)][col_b].sum())
        df_s=fol_sheets["Senioriteitsniveau"]; col_s=df_s.columns[1]
        for k in c.get("seniority_keys",[]): total+=int(df_s[df_s[df_s.columns[0]].str.contains(k,na=False,case=False)][col_s].sum())
    return total

# ═══════════════ MAIN ═══════════════
st.markdown("## LinkedIn Analytics Dashboard")
st.sidebar.markdown("### Data uploads")
content_files = st.sidebar.file_uploader("Content export(s)", type=["xls"], accept_multiple_files=True)
followers_file = st.sidebar.file_uploader("Volgers export", type=["xls"])
visitors_file = st.sidebar.file_uploader("Bezoekers export", type=["xls"])
competitor_file = st.sidebar.file_uploader("Concurrenten export", type=["xlsx"])

if not content_files:
    st.info("Upload minimaal de **Content export** via de sidebar. Volgers, Bezoekers en Concurrenten zijn optioneel.")
    st.stop()

with st.spinner("Data laden..."):
    all_posts,all_stats=[],[]
    for f in content_files:
        p,s=load_content(f.read()); all_posts.append(p); all_stats.append(s)
    df_posts=pd.concat(all_posts,ignore_index=True).drop_duplicates(subset=["Link"],keep="last").sort_values("Aangemaakt").reset_index(drop=True)
    df_stats=pd.concat(all_stats,ignore_index=True).drop_duplicates(subset=["Datum"],keep="last").sort_values("Datum").reset_index(drop=True)

all_months=sorted(df_posts["Maand"].unique())
strategy_idx=st.sidebar.selectbox("Nieuwe strategie vanaf",options=all_months,index=len(all_months)-1)

fol_growth=fol_sheets=vis_data=vis_sheets=df_comp=None
if followers_file: fol_growth,fol_sheets=load_followers(followers_file.read())
if visitors_file: vis_data,vis_sheets=load_visitors(visitors_file.read())
if competitor_file: df_comp=load_competitors(competitor_file.read())

df_stats_m=df_stats.copy(); df_stats_m["Maand"]=df_stats_m["Datum"].dt.to_period("M").astype(str)
monthly=df_stats_m.groupby("Maand").agg(Weergaven=("Weergaven_totaal","sum"),Klikken=("Klikken_totaal","sum"),Reacties=("Reacties_totaal","sum"),Reposts=("Reposts_totaal","sum")).reset_index()
days=df_posts[df_posts["Dag"].isin(DAG_NL)].groupby("Dag").agg(Gem_weergaven=("Weergaven","mean"),Gem_engagement=("Engagement_pct","mean"),Aantal_posts=("Titel_kort","count")).reset_index()
posts_new=df_posts[df_posts["Maand"]>=strategy_idx]; posts_old=df_posts[df_posts["Maand"]<strategy_idx]
# Only posts with actual views, use median to avoid outlier distortion
avg_new=posts_new[posts_new["Weergaven"]>0]["Engagement_pct"].median() if len(posts_new[posts_new["Weergaven"]>0]) else 0
avg_old=posts_old[posts_old["Weergaven"]>0]["Engagement_pct"].median() if len(posts_old[posts_old["Weergaven"]>0]) else 0

# Period subtitle
periode_van = df_stats["Datum"].min().strftime("%d %b %Y")
periode_tot = df_stats["Datum"].max().strftime("%d %b %Y")
n_exports = len(content_files)
st.caption(f"📅 Periode: {periode_van} – {periode_tot} · {n_exports} export(s) · {len(df_posts)} posts")

st.markdown(f'<div class="strategy-banner">📌 Nieuwe strategie gestart vanaf <strong>{strategy_idx}</strong> — data vóór deze maand is de baseline.</div>',unsafe_allow_html=True)
periode_van = df_stats["Datum"].min().strftime("%b %Y")
periode_tot = df_stats["Datum"].max().strftime("%b %Y")
c1,c2,c3,c4=st.columns(4)
c1.metric(f"Weergaven ({periode_van} – {periode_tot})",f"{int(monthly['Weergaven'].sum()):,}".replace(",","."))
c2.metric("Beste maand",monthly.loc[monthly['Weergaven'].idxmax(),'Maand'],f"{int(monthly['Weergaven'].max()):,} views".replace(",","."))
c3.metric(f"Posts ({periode_van} – {periode_tot})",len(df_posts))
with c4:
    eng_arrow = "+" if avg_new >= avg_old else "-"
    eng_delta = abs(avg_new - avg_old)
    st.markdown(f'<div style="background:#EA5B0C;border-radius:10px;padding:1rem;"><div style="font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:rgba(255,255,255,0.75);margin-bottom:4px;">Gem. engagement nieuwe strategie</div><div style="font-size:26px;font-weight:500;color:white;">{avg_new:.1f}%</div><div style="font-size:13px;color:rgba(255,255,255,0.85);margin-top:2px;">{eng_arrow}{eng_delta:.1f}% vs baseline</div></div>', unsafe_allow_html=True)
st.markdown("---")

tab_names=["📊 Content"]
if fol_growth is not None: tab_names.append("👥 Volgers")
if vis_data is not None: tab_names.append("👁 Bezoekers")
if fol_sheets is not None: tab_names.append("🎯 Strategie clusters")
if df_comp is not None: tab_names.append("🏆 Concurrenten")
tab_objs=st.tabs(tab_names)
tm={n:o for n,o in zip(tab_names,tab_objs)}

# ── CONTENT TAB ──
with tm["📊 Content"]:
    st.markdown('<p class="section-head">Maandelijks bereik</p>',unsafe_allow_html=True)
    mc=st.radio("Metric",["Weergaven","Klikken","Reacties"],horizontal=True,label_visibility="collapsed")
    bar_colors=[ORANGE if m>=strategy_idx else BLUE for m in monthly["Maand"]]
    fig_m=go.Figure(go.Bar(x=monthly["Maand"],y=monthly[mc],marker_color=bar_colors,text=monthly[mc].apply(lambda v:f"{v/1000:.1f}k" if v>=1000 else str(v)),textposition="outside",textfont=dict(size=10)))
    fig_m.update_layout(**base_layout(height=300),xaxis=dict(tickangle=-45,showgrid=False),yaxis=dict(showgrid=True,gridcolor="#eee"),bargap=0.35)
    fig_m.add_annotation(x=0.01,y=1.06,xref="paper",yref="paper",text=f"<b style='color:{ORANGE}'>■</b> Nieuwe strategie &nbsp; <b style='color:{BLUE}'>■</b> Baseline",showarrow=False,font=dict(size=11,color="#888"),align="left")
    st.plotly_chart(fig_m,use_container_width=True)

    col_e,col_r=st.columns(2)
    with col_e:
        st.markdown('<p class="section-head">Engagement per dag</p>',unsafe_allow_html=True)
        es=days.sort_values("Gem_engagement",ascending=True)
        st.plotly_chart(horiz_bar(es.assign(D=es["Dag"].map(DAG_NL)),"Gem_engagement","D",ORANGE,pct=True),use_container_width=True)
    with col_r:
        st.markdown('<p class="section-head">Bereik per dag</p>',unsafe_allow_html=True)
        rs=days.sort_values("Gem_weergaven",ascending=True)
        st.plotly_chart(horiz_bar(rs.assign(D=rs["Dag"].map(DAG_NL)),"Gem_weergaven","D",BLUE),use_container_width=True)

    st.markdown('<p class="section-head">Per auteur</p>',unsafe_allow_html=True)
    aut=df_posts.groupby("Geplaatst_door").agg(Posts=("Titel_kort","count"),Gem_views=("Weergaven","mean"),Gem_eng=("Engagement_pct","mean"),Totaal=("Weergaven","sum")).round(1).sort_values("Totaal",ascending=False).reset_index()
    aut["Gem_views"]=aut["Gem_views"].apply(lambda v:f"{int(v):,}".replace(",","."))
    aut["Totaal"]=aut["Totaal"].apply(lambda v:f"{int(v):,}".replace(",","."))
    aut["Gem_eng"]=aut["Gem_eng"].apply(lambda v:f"{v:.1f}%")
    aut.columns=["Auteur","Posts","Gem. views","Gem. engagement","Totaal views"]
    st.dataframe(aut,use_container_width=True,hide_index=True)

    st.markdown('<p class="section-head">Top posts</p>',unsafe_allow_html=True)
    t1,t2,t3=st.tabs(["Meeste views","Hoogste engagement","Nieuwe strategie"])
    with t1: post_table(df_posts.sort_values("Weergaven",ascending=False).head(10))
    with t2: post_table(df_posts[df_posts["Engagement_pct"]>0].sort_values("Engagement_pct",ascending=False).head(10))
    with t3:
        np_=df_posts[df_posts["Maand"]>=strategy_idx].sort_values("Weergaven",ascending=False)
        post_table(np_.head(10)) if len(np_) else st.info("Nog geen posts in nieuwe strategie periode.")

    st.markdown('<p class="section-head">Views vs engagement</p>',unsafe_allow_html=True)
    sc=df_posts[df_posts["Weergaven"]>0].copy()
    sc["Periode"]=sc["Maand"].apply(lambda m:"Nieuwe strategie" if m>=strategy_idx else "Baseline")
    fig_sc=px.scatter(sc,x="Weergaven",y="Engagement_pct",color="Periode",color_discrete_map={"Nieuwe strategie":ORANGE,"Baseline":BLUE},hover_data={"Titel_kort":True,"Aangemaakt":True,"Engagement_pct":":.1f"},labels={"Weergaven":"Views","Engagement_pct":"Engagement %"})
    fig_sc.update_traces(marker=dict(size=8,opacity=0.7))
    fig_sc.update_layout(**base_layout(height=320),legend=dict(orientation="h",y=1.08))
    st.plotly_chart(fig_sc,use_container_width=True)

# ── VOLGERS TAB ──
if "👥 Volgers" in tm:
    with tm["👥 Volgers"]:
        fol_growth["Cumulatief"]=fol_growth["Totaal aantal volgers"].cumsum()
        total_new=int(fol_growth["Totaal aantal volgers"].sum())
        c1,c2,c3=st.columns(3)
        c1.metric("Nieuwe volgers (periode)",f"{total_new:,}".replace(",","."))
        c2.metric("Gem. per dag",f"{fol_growth['Totaal aantal volgers'].mean():.1f}")
        c3.metric("Piek dag",fol_growth.loc[fol_growth["Totaal aantal volgers"].idxmax(),"Datum"].strftime("%d %b %Y"),f"{int(fol_growth['Totaal aantal volgers'].max())} volgers")
        st.markdown('<p class="section-head">Groei over tijd</p>',unsafe_allow_html=True)
        fig_f=go.Figure()
        fig_f.add_trace(go.Scatter(x=fol_growth["Datum"],y=fol_growth["Cumulatief"],fill="tozeroy",line=dict(color=ORANGE,width=2),fillcolor="rgba(234,91,12,0.13)",name="Cumulatief"))
        fig_f.add_trace(go.Bar(x=fol_growth["Datum"],y=fol_growth["Totaal aantal volgers"],marker_color=BLUE,opacity=0.5,name="Per dag",yaxis="y2"))
        fig_f.update_layout(**base_layout(height=300),yaxis=dict(showgrid=True,gridcolor="#eee"),yaxis2=dict(overlaying="y",side="right",showgrid=False),legend=dict(orientation="h",y=1.08))
        st.plotly_chart(fig_f,use_container_width=True)
        d1,d2=st.columns(2)
        with d1:
            st.caption("Branche (top 10)")
            df_b=fol_sheets["Branche"].head(10).sort_values(fol_sheets["Branche"].columns[1],ascending=True)
            st.plotly_chart(horiz_bar(df_b,df_b.columns[1],df_b.columns[0],ORANGE,height=300),use_container_width=True)
        with d2:
            st.caption("Functie (top 10)")
            df_fn=fol_sheets["Functie"].head(10).sort_values(fol_sheets["Functie"].columns[1],ascending=True)
            st.plotly_chart(horiz_bar(df_fn,df_fn.columns[1],df_fn.columns[0],BLUE,height=300),use_container_width=True)
        d3,d4=st.columns(2)
        with d3:
            st.caption("Senioriteitsniveau")
            df_sn=fol_sheets["Senioriteitsniveau"].sort_values(fol_sheets["Senioriteitsniveau"].columns[1],ascending=True)
            st.plotly_chart(horiz_bar(df_sn,df_sn.columns[1],df_sn.columns[0],GREEN,height=250),use_container_width=True)
        with d4:
            st.caption("Top locaties")
            df_lo=fol_sheets["Locatie"].head(10).sort_values(fol_sheets["Locatie"].columns[1],ascending=True)
            st.plotly_chart(horiz_bar(df_lo,df_lo.columns[1],df_lo.columns[0],GRAY,height=250),use_container_width=True)

# ── BEZOEKERS TAB ──
if "👁 Bezoekers" in tm:
    with tm["👁 Bezoekers"]:
        vcols=[c for c in vis_data.columns if "totaal" in c.lower() and "uniek" not in c.lower() and "pagina" not in c.lower()]
        ucols=[c for c in vis_data.columns if "unieke bezoekers" in c.lower() and "totaal" in c.lower()]
        tc=vcols[0] if vcols else vis_data.columns[1]
        uc=ucols[0] if ucols else vis_data.columns[2]
        c1,c2=st.columns(2)
        c1.metric("Totaal paginaweergaven",f"{int(vis_data[tc].sum()):,}".replace(",","."))
        c2.metric("Unieke bezoekers",f"{int(vis_data[uc].sum()):,}".replace(",","."))
        st.markdown('<p class="section-head">Bezoekers over tijd</p>',unsafe_allow_html=True)
        fig_v=go.Figure()
        fig_v.add_trace(go.Scatter(x=vis_data["Datum"],y=vis_data[tc],line=dict(color=BLUE,width=2),name="Paginaweergaven"))
        fig_v.add_trace(go.Scatter(x=vis_data["Datum"],y=vis_data[uc],line=dict(color=ORANGE,width=2,dash="dot"),name="Unieke bezoekers"))
        fig_v.update_layout(**base_layout(height=280),legend=dict(orientation="h",y=1.08))
        st.plotly_chart(fig_v,use_container_width=True)
        v1,v2=st.columns(2)
        with v1:
            st.caption("Functie")
            df_vf=vis_sheets["Functie"].sort_values(vis_sheets["Functie"].columns[1],ascending=True)
            st.plotly_chart(horiz_bar(df_vf,df_vf.columns[1],df_vf.columns[0],ORANGE,height=280),use_container_width=True)
        with v2:
            st.caption("Senioriteitsniveau")
            df_vs=vis_sheets["Senioriteitsniveau"].sort_values(vis_sheets["Senioriteitsniveau"].columns[1],ascending=True)
            st.plotly_chart(horiz_bar(df_vs,df_vs.columns[1],df_vs.columns[0],BLUE,height=280),use_container_width=True)

# ── STRATEGIE CLUSTERS TAB ──
if "🎯 Strategie clusters" in tm:
    with tm["🎯 Strategie clusters"]:
        cnames=list(CLUSTER_DEF.keys())
        ccols=[ORANGE,BLUE,GREEN,"#8B5CF6","#F59E0B"]



        # Current values
        cvals=[cluster_score(fol_sheets,c) for c in cnames]
        target_pct = 5.0

        st.markdown(f"Volgers per strategiecluster · nulmeting **{fol_growth['Datum'].max().strftime('%b %Y')}** · Doel: **+5% groei per jaar**")

        # KPI cards with target indicator
        cols=st.columns(len(cnames))
        for i,(n,v) in enumerate(zip(cnames,cvals)):
            target = int(v * (1 + target_pct/100))
            cols[i].metric(n, f"{v:,}".replace(",","."), help=f"Doel over 1 jaar: {target:,}".replace(",","."))

        st.markdown('<p class="section-head">Huidige clustergrootte · nulmeting april 2026</p>',unsafe_allow_html=True)
        st.caption("Upload volgend jaar een nieuwe volgers-export naast deze om groei per cluster te zien.")

        fig_cl=go.Figure(go.Bar(
            x=cnames, y=cvals, marker_color=ccols,
            text=[f"{v:,}".replace(",",".") for v in cvals],
            textposition="outside",
            customdata=[int(v*1.05) for v in cvals],
            hovertemplate="<b>%{x}</b><br>Huidig: %{y:,}<br>Doel (+5%): %{customdata:,}<extra></extra>",
        ))
        # Add target line per cluster as scatter
        fig_cl.add_trace(go.Scatter(
            x=cnames, y=[int(v*1.05) for v in cvals],
            mode="markers", marker=dict(symbol="line-ew", size=20, color="rgba(0,0,0,0.3)", line=dict(width=2, color="rgba(0,0,0,0.3)")),
            name="Doel (+5%)", hovertemplate="Doel: %{y:,}<extra></extra>",
        ))
        fig_cl.update_layout(**base_layout(height=320),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True,gridcolor="#eee"),
            bargap=0.4,
            legend=dict(orientation="h",y=1.08))
        st.plotly_chart(fig_cl,use_container_width=True)
        st.markdown('<p class="section-head">Internationale spreiding</p>',unsafe_allow_html=True)
        intl_cities=["Boston","Parijs","Zürich","Berlijn","Barcelona","London","Kopenhagen","Stockholm","München","Leuven","Gent","New York","Cambridge","Oxford","India"]
        df_loc=fol_sheets["Locatie"]
        rows=[{"Stad":city,"Volgers":int(df_loc[df_loc[df_loc.columns[0]].str.contains(city,na=False,case=False)][df_loc.columns[1]].sum())} for city in intl_cities]
        rows=[r for r in rows if r["Volgers"]>0]
        if rows:
            df_i=pd.DataFrame(rows).sort_values("Volgers",ascending=True)
            fig_i=go.Figure(go.Bar(x=df_i["Volgers"],y=df_i["Stad"],orientation="h",marker_color=GREEN,text=df_i["Volgers"],textposition="outside"))
            fig_i.update_layout(**base_layout(height=max(200,len(df_i)*32)),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
            st.plotly_chart(fig_i,use_container_width=True)
        st.markdown('<p class="section-head">LSH sector breakdown</p>',unsafe_allow_html=True)
        df_br=fol_sheets["Branche"]
        lsh_keys=["Biotechnologisch","Geneesmiddelen","Onderzoeksdiensten","Medische praktijken","Ziekenhuizen","medische apparatuur","diagnostisch"]
        lsh_rows=[]
        for k in lsh_keys:
            for _,row in df_br[df_br[df_br.columns[0]].str.contains(k,na=False,case=False)].iterrows():
                lsh_rows.append({"Branche":row.iloc[0][:45],"Volgers":int(row.iloc[1])})
        if lsh_rows:
            df_lsh=pd.DataFrame(lsh_rows).sort_values("Volgers",ascending=True)
            fig_lsh=go.Figure(go.Bar(x=df_lsh["Volgers"],y=df_lsh["Branche"],orientation="h",marker_color=BLUE,text=df_lsh["Volgers"],textposition="outside"))
            fig_lsh.update_layout(**base_layout(height=max(200,len(df_lsh)*32)),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
            st.plotly_chart(fig_lsh,use_container_width=True)

# ── CONCURRENTEN TAB ──
if "🏆 Concurrenten" in tm:
    with tm["🏆 Concurrenten"]:
        st.markdown('<p class="section-head">Benchmark vs concurrenten</p>',unsafe_allow_html=True)
        for metric,label in [("Nieuwe_volgers","Nieuwe volgers"),("Bijdragen","Posts"),("Reacties","Reacties")]:
            ds=df_comp.sort_values(metric,ascending=True)
            cc=[ORANGE if "Leiden" in str(p) else BLUE for p in ds["Pagina"]]
            fig=go.Figure(go.Bar(x=ds[metric],y=ds["Pagina"],orientation="h",marker_color=cc,text=ds[metric],textposition="outside"))
            fig.update_layout(**base_layout(height=200),title=dict(text=label,font=dict(size=13)),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
            st.plotly_chart(fig,use_container_width=True)
        st.caption("Oranje = Leiden Bio Science Park")

st.markdown("---")
st.caption(f"Content: {df_stats['Datum'].min().strftime('%d %b %Y')} – {df_stats['Datum'].max().strftime('%d %b %Y')} · {len(df_posts)} posts · LinkedIn Analytics Dashboard")
