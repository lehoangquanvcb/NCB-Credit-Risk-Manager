
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from modules.risk_calculations import (
    compute_risk_appetite, status, hhi, ews_score, policy_breaches, stress_ecl,
    apply_policy_rule_engine, generate_credit_memo, build_board_report_text, collateral_haircut_analysis, icaap_lite, recovery_plan_assessment, simulate_credit_strategy, build_risk_committee_pack
)

st.set_page_config(page_title="NCB Credit Risk Manager Platform", page_icon="🏦", layout="wide")
AUTHOR="Le Hoang Quan"
DATA=Path("data")

@st.cache_data
def load_csv(name, **kwargs):
    return pd.read_csv(DATA/name, **kwargs)

loan=load_csv("loan_portfolio.csv")
risk_app=load_csv("risk_appetite.csv")
limits=load_csv("limits.csv")
watchlist=load_csv("watchlist.csv")
actions=load_csv("management_actions.csv")
macro=load_csv("macro_scenarios.csv")
policy_rules=load_csv("policy_rule_engine.csv")
external_alerts=load_csv("external_alerts.csv")
model_gov=load_csv("model_governance.csv")
board_template=load_csv("board_pack_template.csv")
haircuts=load_csv("collateral_haircuts.csv")
strategy_scenarios=load_csv("strategy_scenarios.csv")
recovery_triggers=load_csv("recovery_triggers.csv")
risk_committee_template=load_csv("risk_committee_pack.csv")
icaap_assumptions=load_csv("icaap_assumptions.csv")
migration=pd.read_csv(DATA/"migration_matrix.csv", index_col=0)

loan["ews_score"]=loan.apply(ews_score,axis=1)
loan["policy_result"]=loan.apply(policy_breaches,axis=1)
loan["risk_bucket"]=pd.cut(loan["ews_score"],[-1,30,60,100],labels=["Low","Medium","High"])

# Optional external alert enhancement
loan = loan.merge(external_alerts[["customer_id","external_alert_score"]], on="customer_id", how="left")
loan["external_alert_score"] = loan["external_alert_score"].fillna(0)
loan["combined_ews_score"] = np.clip(loan["ews_score"]*0.75 + loan["external_alert_score"]*0.25, 0, 100).round(1)

def pct(x): return f"{x*100:.2f}%"
def money(x): return f"{x:,.1f} bn VND"
def kpi_row(items):
    cols=st.columns(len(items))
    for c,(label,value,delta) in zip(cols,items):
        c.metric(label,value,delta)

def style_plotly(fig, height=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f7f9fc", size=12),
        margin=dict(l=25, r=20, t=55, b=35),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.12)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.12)")
    if height:
        fig.update_layout(height=height)
    return fig


def metric_card(title, value, subtitle="", icon="●", color="#3d7cff", delta=None):
    delta_html = f'<div class="kpi-delta">↗ {delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-head">
                <div class="kpi-icon" style="background:{color};">{icon}</div>
                <div class="kpi-title">{title}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtitle}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def section_title(number, title):
    st.markdown(
        f'<div class="section-title"><span class="section-number">{number}</span>{title}</div>',
        unsafe_allow_html=True
    )



st.markdown("""
<style>
    :root {
        --ncb-bg: #090e14;
        --ncb-panel: #111821;
        --ncb-panel-2: #161f2b;
        --ncb-border: rgba(255,255,255,0.075);
        --ncb-text: #f7f9fc;
        --ncb-muted: #a5afbf;
        --ncb-red: #ff4b4b;
        --ncb-blue: #3d7cff;
        --ncb-green: #22c55e;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 20% 5%, rgba(47,65,91,.35), transparent 30%),
            linear-gradient(120deg, #090e14 0%, #0b1118 55%, #070b10 100%) !important;
        color: var(--ncb-text);
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 1.4rem;
        padding-right: 1.4rem;
        max-width: 100%;
    }

    header[data-testid="stHeader"], footer {visibility: hidden;}
    [data-testid="stToolbar"] {display:none;}

    [data-testid="stSidebar"] {
        min-width: 330px;
        max-width: 330px;
        background: linear-gradient(180deg, #141a24 0%, #0b1118 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .ncb-sidebar-title {
        display:flex;
        align-items:center;
        gap:14px;
        margin: 0 0 24px 0;
        padding: 8px 4px 20px 4px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        font-size: 22px;
        font-weight: 850;
        line-height:1.12;
        color:#fff;
    }
    .ncb-sidebar-title .logo {font-size: 38px;}

    .ncb-sidebar-section {
        font-size: 12px;
        color:#a8b3c5;
        font-weight:800;
        margin: 18px 0 8px 2px;
        text-transform: uppercase;
        letter-spacing: .04em;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 12px 12px !important;
        margin: 4px 0 !important;
        border-radius: 10px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: #edf2f7 !important;
        transition: all .15s ease;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.06) !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
        display:none !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(255,75,75,.82), rgba(170,43,43,.55)) !important;
        border: 1px solid rgba(255,112,112,.45) !important;
        box-shadow: 0 12px 28px rgba(255,75,75,.16);
    }

    div[data-baseweb="select"] > div {
        background: #080d13 !important;
        border-color: rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
    }

    .topbar {
        display:flex;
        justify-content:flex-end;
        align-items:center;
        gap:12px;
        margin: 2px 0 18px 0;
        color:#f7f9fc;
        font-size: 13px;
    }

    .topbar-badge {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 10px 14px;
    }

    .kpi-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        min-height: 150px;
        padding: 20px 20px 18px 20px;
        box-shadow: 0 16px 42px rgba(0,0,0,.22);
    }
    .kpi-head {display:flex; align-items:center; gap:12px; margin-bottom:16px;}
    .kpi-icon {
        width:38px; height:38px; border-radius:50%;
        display:flex; align-items:center; justify-content:center;
        font-size:18px; color:white; font-weight:700;
    }
    .kpi-title {font-size:15px; font-weight:650; color:#f3f5f8;}
    .kpi-value {font-size:32px; font-weight:850; color:#fff; line-height:1.05;}
    .kpi-sub {font-size:19px; color:#f3f5f8; margin-top:6px;}
    .kpi-delta {
        display:inline-block;
        margin-top:12px;
        padding:4px 9px;
        border-radius: 999px;
        font-size:12px;
        font-weight:800;
        color:#75f0a0;
        background: rgba(34,197,94,.18);
    }

    .section-title {
        display:flex;
        align-items:center;
        gap:14px;
        margin: 28px 0 16px 0;
        font-size:28px;
        font-weight:850;
        color:#fff;
    }
    .section-number {
        background: linear-gradient(135deg, #62a5ff, #2764e8);
        padding:4px 12px;
        border-radius:7px;
        font-size:23px;
        box-shadow:0 8px 18px rgba(59,130,246,.35);
    }

    .chart-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.047), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 16px 42px rgba(0,0,0,.20);
        min-height: 315px;
    }

    .alert-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.047), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 18px 20px 8px 20px;
        margin-top: 16px;
    }

    .alert-title {
        font-size:23px;
        font-weight:850;
        color:#fff;
        margin-bottom:12px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 16px 18px;
    }

    h1, h2, h3 {color:#fff;}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown(
    """
    <div class="ncb-sidebar-title">
        <div class="logo">🏦</div>
        <div>NCB Credit Risk<br>Manager Platform</div>
    </div>
    """,
    unsafe_allow_html=True,
)

menu_options = [
    "1  Executive Dashboard",
    "2  Portfolio Overview",
    "3  Risk Appetite",
    "4  Concentration",
    "5  Policy Rule Engine",
    "6  Limit Monitoring",
    "7  Single Customer View",
    "8  Memo Generator",
    "9  EWS & External Alerts",
    "10 IFRS9 & Stress",
    "11 Migration",
    "12 Basel Capital",
    "13 Watchlist & Actions",
    "14 Board Pack Export",
    "15 Model Governance",
    "16 NCB Interview Mode",
    "17 ICAAP Lite",
    "18 Recovery Plan",
    "19 Credit Strategy Simulator",
    "20 Collateral Haircut",
    "21 Risk Committee Pack",
]

st.sidebar.markdown('<div class="ncb-sidebar-section">Navigation</div>', unsafe_allow_html=True)
selected_tab = st.sidebar.radio(
    "Navigation",
    menu_options,
    index=0,
    label_visibility="collapsed",
)

st.sidebar.markdown('<div class="ncb-sidebar-section">⚙️ Settings</div>', unsafe_allow_html=True)
scenario=st.sidebar.selectbox("Stress scenario", macro["scenario"].tolist(), index=0)
selected_industry=st.sidebar.multiselect("Industry filter", sorted(loan["industry"].unique()))
selected_stage=st.sidebar.multiselect("IFRS9 Stage filter", sorted(loan["stage"].unique()))
filtered=loan.copy()
if selected_industry:
    filtered=filtered[filtered["industry"].isin(selected_industry)]
if selected_stage:
    filtered=filtered[filtered["stage"].isin(selected_stage)]
sc=macro[macro["scenario"].eq(scenario)].iloc[0]
filtered["stressed_ecl_bn_vnd"]=stress_ecl(filtered, sc["pd_multiplier"], sc["lgd_multiplier"])

total=filtered["ead_bn_vnd"].sum()
ecl=filtered["ecl_bn_vnd"].sum()
stressed=filtered["stressed_ecl_bn_vnd"].sum()
weighted_pd=(filtered["pd_12m"]*filtered["ead_bn_vnd"]).sum()/total if total else 0
stage23=filtered[filtered["stage"].isin(["Stage 2","Stage 3"])] ["ead_bn_vnd"].sum()/total if total else 0
npl=filtered[filtered["stage"].eq("Stage 3")]["ead_bn_vnd"].sum()/total if total else 0
policy_table = apply_policy_rule_engine(filtered, policy_rules)
high_ews_count = int((filtered["combined_ews_score"]>=60).sum())
top_industry = filtered.groupby("industry")["ead_bn_vnd"].sum().sort_values(ascending=False).index[0] if len(filtered) else "N/A"

board_report_quick = build_board_report_text(total, ecl, stressed, scenario, weighted_pd, npl, stage23, hhi(filtered), top_industry, len(policy_table), high_ews_count)

top_left, top_right = st.columns([5, 2])
with top_left:
    st.markdown("")
with top_right:
    st.markdown('<div class="topbar"><span>🗓️ Data as of: 31/05/2026</span></div>', unsafe_allow_html=True)
    st.download_button("⬇️ Export Board Pack", board_report_quick, file_name="NCB_Board_Risk_Pack.txt", use_container_width=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    metric_card("Total exposure", f"{total:,.1f}", "bn VND", "≋", "#3d7cff")
with k2:
    metric_card("Base ECL", f"{ecl:,.1f}", "bn VND", "▦", "#7c3aed")
with k3:
    metric_card("Stressed ECL", f"{stressed:,.1f}", "bn VND", "⚠", "#ef4444", f"+{stressed-ecl:,.1f} bn VND")
with k4:
    metric_card("Weighted PD", f"{weighted_pd*100:.2f}%", "", "♙", "#f59e0b")
with k5:
    metric_card("NPL / Stage 3", f"{npl*100:.2f}%", "", "◔", "#22a6b3")
with k6:
    metric_card("Policy breaches", f"{len(policy_table)}", "", "🛡", "#43a047")


if selected_tab == menu_options[0]:
    section_title("1", "Executive Risk Dashboard")

    ecl_compare = pd.DataFrame({
        "Metric": ["Base ECL", "Stressed ECL"],
        "ECL": [ecl, stressed],
        "Color": ["Base", "Stress"]
    })

    months = ["12/2024", "01/2025", "02/2025", "03/2025", "04/2025", "05/2026"]
    current_npl = npl * 100
    npl_values = [
        max(current_npl - 2.3, 0),
        max(current_npl - 1.6, 0),
        max(current_npl - 1.1, 0),
        max(current_npl - 0.5, 0),
        current_npl,
        current_npl
    ]
    npl_trend = pd.DataFrame({"Month": months, "NPL / Stage 3": npl_values})

    by_ind = filtered.groupby("industry", as_index=False).agg(exposure=("ead_bn_vnd", "sum"))
    by_ind["pct"] = by_ind["exposure"] / by_ind["exposure"].sum() if by_ind["exposure"].sum() else 0

    c1, c2, c3 = st.columns([1.05, 1.2, 1.25])

    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig_ecl = px.bar(
            ecl_compare,
            x="Metric",
            y="ECL",
            text="ECL",
            title="ECL Overview (bn VND)",
            color="Color",
            color_discrete_map={"Base": "#3d7cff", "Stress": "#ff4b4b"},
        )
        fig_ecl.update_traces(texttemplate="%{text:.1f}", textposition="outside", marker_line_width=0)
        fig_ecl.update_layout(showlegend=False)
        st.plotly_chart(style_plotly(fig_ecl, height=300), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig_npl = px.line(
            npl_trend,
            x="Month",
            y="NPL / Stage 3",
            text="NPL / Stage 3",
            markers=True,
            title="NPL / Stage 3 Trend (%)",
        )
        fig_npl.update_traces(line=dict(color="#ff4b4b", width=3), marker=dict(size=9, color="#ff4b4b"), texttemplate="%{text:.1f}%", textposition="top center")
        fig_npl.update_yaxes(ticksuffix="%", range=[0, max(25, max(npl_values) + 3)])
        st.plotly_chart(style_plotly(fig_npl, height=300), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig_donut = go.Figure(data=[
            go.Pie(
                labels=by_ind["industry"],
                values=by_ind["exposure"],
                hole=0.48,
                textinfo="percent",
                hovertemplate="%{label}<br>%{value:,.1f} bn VND<br>%{percent}<extra></extra>",
                marker=dict(colors=["#3d7cff", "#ff4b4b", "#f7b955", "#4cc9a7", "#7b6fe6", "#78909c"])
            )
        ])
        fig_donut.update_layout(
            title="Exposure by Industry (bn VND)",
            annotations=[dict(text=f"{total:,.1f}<br>bn VND", x=0.5, y=0.5, font_size=17, showarrow=False, font_color="#ffffff")],
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
        )
        st.plotly_chart(style_plotly(fig_donut, height=300), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="alert-card"><div class="alert-title">🔔 Top Alerts</div>', unsafe_allow_html=True)

    real_estate_ratio = filtered.loc[filtered["industry"].eq("Real Estate"), "ead_bn_vnd"].sum() / total if total else 0
    alerts = pd.DataFrame([
        {
            "Alert": "Policy Breach: Single Borrower Limit",
            "Category": "Policy Breach",
            "Level": "High" if len(policy_table) else "Low",
            "Description": f"{len(policy_table)} policy exception(s) detected in selected portfolio",
            "Date": "31/05/2026",
        },
        {
            "Alert": "High Stage 2 Migration",
            "Category": "EWS",
            "Level": "Medium",
            "Description": f"Stage 2 + Stage 3 exposure equals {stage23:.1%} of selected portfolio",
            "Date": "31/05/2026",
        },
        {
            "Alert": "Collateral Revaluation Needed",
            "Category": "Collateral",
            "Level": "Medium",
            "Description": "Review facilities with high LTV or outdated collateral values",
            "Date": "31/05/2026",
        },
        {
            "Alert": "Industry Concentration Alert",
            "Category": "Concentration",
            "Level": "Low" if real_estate_ratio <= 0.25 else "Medium",
            "Description": f"Real Estate exposure: {real_estate_ratio:.1%} of selected portfolio",
            "Date": "31/05/2026",
        },
    ])

    def level_badge(v):
        color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#16a34a"}.get(v, "#64748b")
        return f"background-color: {color}; color: white; border-radius: 6px; text-align: center; font-weight: 700;"

    st.dataframe(alerts.style.applymap(level_badge, subset=["Level"]), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif selected_tab == menu_options[1]:
    st.subheader("2️⃣ Portfolio Quality")
    by_ind=filtered.groupby("industry",as_index=False).agg(exposure=("ead_bn_vnd","sum"),ecl=("ecl_bn_vnd","sum"),avg_pd=("pd_12m","mean"),avg_ews=("combined_ews_score","mean"))
    st.plotly_chart(px.bar(by_ind.sort_values("exposure",ascending=False),x="industry",y="exposure",title="Exposure by Industry"),use_container_width=True)
    st.dataframe(by_ind,use_container_width=True)

elif selected_tab == menu_options[2]:
    st.subheader("3️⃣ Risk Appetite Monitoring")
    actuals=compute_risk_appetite(filtered)
    rows=[]
    for _,r in risk_app.iterrows():
        a=actuals.get(r["metric"],np.nan)
        rows.append({"Metric":r["metric"],"Actual":a,"Limit":r["limit"],"Direction":r["direction"],"Status":status(a,r["limit"],r["direction"])})
    ra=pd.DataFrame(rows)
    st.dataframe(ra.style.format({"Actual":"{:.2%}","Limit":"{:.2%}"}),use_container_width=True)
    st.plotly_chart(px.bar(ra,x="Metric",y="Actual",color="Status",title="Risk Appetite Actuals"),use_container_width=True)

elif selected_tab == menu_options[3]:
    st.subheader("4️⃣ Concentration Risk")
    st.metric("Industry HHI",f"{hhi(filtered):.3f}")
    top=filtered.groupby(["group_id","industry"],as_index=False).agg(exposure=("ead_bn_vnd","sum")).sort_values("exposure",ascending=False).head(20)
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(top,x="group_id",y="exposure",color="industry",title="Top 20 Group Borrowers"),use_container_width=True)
    c2.plotly_chart(px.treemap(filtered,path=["industry","group_id"],values="ead_bn_vnd",title="Concentration Treemap"),use_container_width=True)
    st.dataframe(top,use_container_width=True)

elif selected_tab == menu_options[4]:
    st.subheader("5️⃣ Credit Policy Rule Engine")
    st.markdown("Rule engine giải thích khoản vay vi phạm điều khoản nào, mức độ nghiêm trọng và hành động quản lý đề xuất.")
    st.dataframe(policy_rules,use_container_width=True)
    st.markdown("### Breach details")
    st.dataframe(policy_table,use_container_width=True,height=430)
    if not policy_table.empty:
        st.plotly_chart(px.histogram(policy_table,x="severity",color="rule_name",title="Policy Breaches by Severity"),use_container_width=True)

elif selected_tab == menu_options[5]:
    st.subheader("6️⃣ Limit Monitoring")
    total_exp=filtered["ead_bn_vnd"].sum()
    lim_rows=[]
    for _,r in limits.iterrows():
        lt=r["limit_type"]
        if lt=="Single borrower": actual=filtered.groupby("customer_id")["ead_bn_vnd"].sum().max()/total_exp
        elif lt=="Group borrower": actual=filtered.groupby("group_id")["ead_bn_vnd"].sum().max()/total_exp
        elif lt in ["Real Estate","Construction","Manufacturing"]: actual=filtered.loc[filtered["industry"].eq(lt),"ead_bn_vnd"].sum()/total_exp
        elif lt=="Unsecured lending": actual=filtered.loc[filtered["collateral_type"].eq("Unsecured"),"ead_bn_vnd"].sum()/total_exp
        elif lt=="Stage 2 exposure": actual=filtered.loc[filtered["stage"].eq("Stage 2"),"ead_bn_vnd"].sum()/total_exp
        else: actual=0
        lim_rows.append({"Limit type":lt,"Actual":actual,"Limit":r["limit_pct"],"Status":status(actual,r["limit_pct"],"max")})
    lim=pd.DataFrame(lim_rows)
    st.dataframe(lim.style.format({"Actual":"{:.2%}","Limit":"{:.2%}"}),use_container_width=True)
    st.plotly_chart(px.bar(lim,x="Limit type",y=["Actual","Limit"],barmode="group",title="Actual vs Limit"),use_container_width=True)

elif selected_tab == menu_options[6]:
    st.subheader("7️⃣ Single Customer View")
    cust=st.selectbox("Select customer",filtered["customer_id"].sort_values().unique(), key="cust_view")
    one=filtered[filtered["customer_id"].eq(cust)]
    kpi_row([("Exposure",money(one["ead_bn_vnd"].sum()),None),("ECL",money(one["ecl_bn_vnd"].sum()),None),("Max EWS",f"{one['combined_ews_score'].max():.1f}",None),("Policy","Pass" if (one["policy_result"]=="Pass").all() else "Breach",None)])
    st.dataframe(one[["loan_id","group_id","industry","product","rating_grade","stage","ead_bn_vnd","pd_12m","lgd","ecl_bn_vnd","dpd","dscr","ltv","combined_ews_score","policy_result"]],use_container_width=True)

elif selected_tab == menu_options[7]:
    st.subheader("8️⃣ Credit Approval Memo Generator")
    cust_memo=st.selectbox("Select customer for memo",filtered["customer_id"].sort_values().unique(), key="cust_memo")
    memo_df=filtered[filtered["customer_id"].eq(cust_memo)]
    memo=generate_credit_memo(memo_df, external_alerts)
    st.text_area("Generated memo", memo, height=470)
    st.download_button("⬇️ Download Credit Memo TXT", memo, file_name=f"credit_memo_{cust_memo}.txt")

elif selected_tab == menu_options[8]:
    st.subheader("9️⃣ Early Warning System + External Alerts")
    c1,c2=st.columns(2)
    c1.plotly_chart(px.histogram(filtered,x="combined_ews_score",nbins=20,title="Combined EWS Distribution"),use_container_width=True)
    ews_bucket=filtered.groupby("risk_bucket",observed=False).agg(exposure=("ead_bn_vnd","sum")).reset_index()
    c2.plotly_chart(px.pie(ews_bucket,names="risk_bucket",values="exposure",title="Exposure by EWS Bucket"),use_container_width=True)
    st.dataframe(external_alerts,use_container_width=True)
    st.dataframe(filtered.sort_values("combined_ews_score",ascending=False)[["loan_id","customer_id","industry","stage","ead_bn_vnd","dpd","dscr","debt_to_ebitda","ltv","ews_score","external_alert_score","combined_ews_score"]],use_container_width=True,height=380)

elif selected_tab == menu_options[9]:
    st.subheader("🔟 IFRS9 ECL & Stress Testing")
    ecl_stage=filtered.groupby("stage",as_index=False).agg(base_ecl=("ecl_bn_vnd","sum"),stressed_ecl=("stressed_ecl_bn_vnd","sum"))
    st.write(f"Selected scenario: **{scenario}** | PD multiplier: **{sc['pd_multiplier']:.2f}x** | LGD multiplier: **{sc['lgd_multiplier']:.2f}x**")
    st.plotly_chart(px.bar(ecl_stage,x="stage",y=["base_ecl","stressed_ecl"],barmode="group",title="Base vs Stressed ECL"),use_container_width=True)
    st.dataframe(ecl_stage,use_container_width=True)

elif selected_tab == menu_options[10]:
    st.subheader("1️⃣1️⃣ Credit Migration Matrix")
    fig=px.imshow(migration,text_auto=".0%",aspect="auto",title="Rating Migration Matrix")
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(migration.style.format("{:.1%}"),use_container_width=True)

elif selected_tab == menu_options[11]:
    st.subheader("1️⃣2️⃣ Basel II Capital & RAROC Lite")
    cap=filtered.copy()
    risk_weight=cap["rating_grade"].map({"AAA":0.5,"AA":0.6,"A":0.75,"BBB":1.0,"BB":1.25,"B":1.5,"CCC":2.0}).fillna(1.0)
    cap["rwa_bn_vnd"]=cap["ead_bn_vnd"]*risk_weight
    cap["capital_required_bn_vnd"]=cap["rwa_bn_vnd"]*0.08
    cap["income_bn_vnd"]=cap["ead_bn_vnd"]*0.035
    raroc=(cap['income_bn_vnd'].sum()-cap['ecl_bn_vnd'].sum())/cap['capital_required_bn_vnd'].sum() if cap['capital_required_bn_vnd'].sum() else 0
    kpi_row([("RWA",money(cap["rwa_bn_vnd"].sum()),None),("Capital required",money(cap["capital_required_bn_vnd"].sum()),None),("Portfolio RAROC",f"{raroc:.2%}",None)])
    st.plotly_chart(px.bar(cap.groupby("industry",as_index=False).agg(rwa=("rwa_bn_vnd","sum")),x="industry",y="rwa",title="RWA by Industry"),use_container_width=True)

elif selected_tab == menu_options[12]:
    st.subheader("1️⃣3️⃣ Watchlist & Management Action Tracker")
    st.markdown("### Watchlist")
    st.dataframe(watchlist,use_container_width=True,height=240)
    st.markdown("### Management Action Tracker")
    st.dataframe(actions,use_container_width=True,height=260)

elif selected_tab == menu_options[13]:
    st.subheader("1️⃣4️⃣ Board Pack Export")
    st.dataframe(board_template,use_container_width=True)
    board_report = build_board_report_text(total, ecl, stressed, scenario, weighted_pd, npl, stage23, hhi(filtered), top_industry, len(policy_table), high_ews_count)
    st.text_area("Board pack draft", board_report, height=420)
    st.download_button("⬇️ Download Board Pack TXT", board_report, file_name="NCB_Board_Risk_Pack.txt")
    st.download_button("⬇️ Download Filtered Portfolio CSV", filtered.to_csv(index=False), file_name="NCB_Filtered_Portfolio.csv")
    if not policy_table.empty:
        st.download_button("⬇️ Download Policy Breaches CSV", policy_table.to_csv(index=False), file_name="NCB_Policy_Breaches.csv")

elif selected_tab == menu_options[14]:
    st.subheader("1️⃣5️⃣ Model Governance & Validation")
    st.markdown("Quản trị mô hình cho PD, IFRS9 ECL, EWS: owner, version, validation date, backtesting, override rate, limitation và next action.")
    st.dataframe(model_gov.style.format({"override_rate":"{:.1%}"}),use_container_width=True)
    st.plotly_chart(px.bar(model_gov,x="model_name",y="override_rate",color="backtest_result",title="Model Override Rate"),use_container_width=True)

elif selected_tab == menu_options[15]:
    st.subheader("1️⃣6️⃣ NCB Interview Mode")
    st.markdown("""
### Cách trình bày trong phỏng vấn NCB Credit Risk Manager

**1. Vấn đề kinh doanh:** Ngân hàng cần kiểm soát NPL, Stage 2, tập trung ngành, policy exceptions và hành động xử lý sau cảnh báo sớm.

**2. Giải pháp của dashboard:**
- Executive dashboard cho CRO/Ủy ban Rủi ro.
- Risk Appetite và Limit Monitoring để kiểm soát khẩu vị rủi ro.
- Policy Rule Engine để minh bạch hóa phê duyệt/ngoại lệ tín dụng.
- Single Customer View và Memo Generator để hỗ trợ phê duyệt tín dụng.
- EWS + External Alerts để phát hiện suy giảm chất lượng sớm.
- IFRS9/Stress/Basel để lượng hóa tác động lên dự phòng và vốn.
- Board Pack Export để chuẩn hóa báo cáo quản trị.

**3. Điểm mạnh cá nhân:** Kết hợp kinh nghiệm credit rating, corporate banking, macro analysis và Python/Excel dashboard để chuyển dữ liệu tín dụng thành quyết định quản trị rủi ro.

**4. Thông điệp chốt:** Đây không phải app IT đơn thuần, mà là mô hình điều hành danh mục tín dụng theo tư duy Credit Risk Manager/CRO Office.
""")


elif selected_tab == menu_options[16]:
    st.subheader("1️⃣7️⃣ ICAAP Lite")
    assumptions = dict(zip(icaap_assumptions['metric'], icaap_assumptions['value']))
    starting_car = st.slider("Starting CAR assumption", 0.08, 0.18, float(assumptions.get('starting_car',0.118)), 0.001, format="%.3f")
    min_car = float(assumptions.get('min_car_target',0.08))
    buffer = float(assumptions.get('management_buffer',0.025))
    icaap = icaap_lite(filtered, starting_car=starting_car, min_car_target=min_car, management_buffer=buffer)
    kpi_row([
        ("RWA", money(icaap['rwa_bn_vnd']), None),
        ("Starting CAR", f"{icaap['starting_car']:.2%}", None),
        ("Post-stress CAR", f"{icaap['post_stress_car']:.2%}", None),
        ("Buffer surplus", f"{icaap['buffer_surplus']:.2%}", icaap['icaap_status'])
    ])
    st.dataframe(pd.DataFrame([icaap]), use_container_width=True)
    st.markdown("ICAAP Lite giúp nối danh mục tín dụng → ECL stress → vốn → CAR sau stress, phù hợp demo cấp CRO Office.")

elif selected_tab == menu_options[17]:
    st.subheader("1️⃣8️⃣ Recovery Plan")
    actuals_for_recovery = compute_risk_appetite(filtered)
    actuals_for_recovery.update({
        'npl_ratio': npl,
        'stage2_ratio': filtered.loc[filtered['stage'].eq('Stage 2'),'ead_bn_vnd'].sum()/total if total else 0,
        'car': 0.118,
        'real_estate_exposure': filtered.loc[filtered['industry'].eq('Real Estate'),'ead_bn_vnd'].sum()/total if total else 0,
        'high_ews_count': high_ews_count
    })
    rec = recovery_plan_assessment(actuals_for_recovery, recovery_triggers)
    st.dataframe(rec, use_container_width=True)
    st.markdown("### Breached triggers and actions")
    st.dataframe(rec[rec['status'].eq('Breach')], use_container_width=True)

elif selected_tab == menu_options[18]:
    st.subheader("1️⃣9️⃣ Credit Strategy Simulator")
    strategy_name = st.selectbox("Select credit strategy", strategy_scenarios['strategy'].tolist())
    strat = strategy_scenarios[strategy_scenarios['strategy'].eq(strategy_name)].iloc[0]
    sim_df, sim_kpi = simulate_credit_strategy(filtered, strat)
    kpi_row([
        ("New exposure", money(sim_kpi['new_exposure_bn_vnd']), f"{sim_kpi['new_exposure_bn_vnd']-total:,.1f}"),
        ("New ECL", money(sim_kpi['new_ecl_bn_vnd']), f"{sim_kpi['new_ecl_bn_vnd']-ecl:,.1f}"),
        ("New RWA", money(sim_kpi['new_rwa_bn_vnd']), None),
        ("RAROC", f"{sim_kpi['raroc']:.2%}", None)
    ])
    by_strategy = sim_df.groupby('industry', as_index=False).agg(current_ead=('ead_bn_vnd','sum'), new_ead=('new_ead_bn_vnd','sum'), new_ecl=('new_ecl_bn_vnd','sum'))
    st.plotly_chart(px.bar(by_strategy, x='industry', y=['current_ead','new_ead'], barmode='group', title='Current vs Simulated Exposure by Industry'), use_container_width=True)
    st.dataframe(by_strategy, use_container_width=True)

elif selected_tab == menu_options[19]:
    st.subheader("2️⃣0️⃣ Collateral Haircut Engine")
    hc_scenario = st.radio("Haircut scenario", ['Base','Adverse'], horizontal=True)
    hc = collateral_haircut_analysis(filtered, haircuts, scenario=hc_scenario)
    kpi_row([
        ("Collateral value", money(hc['collateral_value_bn_vnd'].sum()), None),
        ("Post-haircut value", money(hc['post_haircut_collateral_bn_vnd'].sum()), None),
        ("Collateral shortfall", money(hc['collateral_shortfall_bn_vnd'].sum()), None)
    ])
    st.plotly_chart(px.bar(hc.groupby('collateral_type', as_index=False).agg(shortfall=('collateral_shortfall_bn_vnd','sum')), x='collateral_type', y='shortfall', title='Collateral Shortfall by Type'), use_container_width=True)
    st.dataframe(hc[['loan_id','customer_id','collateral_type','ead_bn_vnd','ltv','haircut','post_haircut_collateral_bn_vnd','collateral_shortfall_bn_vnd']].sort_values('collateral_shortfall_bn_vnd', ascending=False), use_container_width=True, height=420)

elif selected_tab == menu_options[20]:
    st.subheader("2️⃣1️⃣ Risk Committee Pack")
    assumptions = dict(zip(icaap_assumptions['metric'], icaap_assumptions['value']))
    icaap = icaap_lite(filtered, starting_car=float(assumptions.get('starting_car',0.118)), min_car_target=float(assumptions.get('min_car_target',0.08)), management_buffer=float(assumptions.get('management_buffer',0.025)))
    actuals_for_recovery = {'npl_ratio': npl, 'stage2_ratio': stage23-npl, 'car': icaap['post_stress_car'], 'real_estate_exposure': filtered.loc[filtered['industry'].eq('Real Estate'),'ead_bn_vnd'].sum()/total if total else 0, 'high_ews_count': high_ews_count}
    rec = recovery_plan_assessment(actuals_for_recovery, recovery_triggers)
    committee_text = build_risk_committee_pack(total, ecl, stressed, icaap, rec, top_industry, len(policy_table))
    st.dataframe(risk_committee_template, use_container_width=True)
    st.text_area("Generated Risk Committee Pack", committee_text, height=480)
    st.download_button("⬇️ Download Risk Committee Pack TXT", committee_text, file_name="NCB_Risk_Committee_Pack.txt")


st.caption(f"© {AUTHOR}. NCB Credit Risk Manager Platform.")
