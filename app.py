
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
from modules.risk_calculations import (
    compute_risk_appetite, status, hhi, ews_score, policy_breaches, stress_ecl,
    apply_policy_rule_engine, generate_credit_memo, build_board_report_text, collateral_haircut_analysis, icaap_lite, recovery_plan_assessment, simulate_credit_strategy, build_risk_committee_pack
)

st.set_page_config(page_title="NCB Credit Risk Manager Platform v2.3", page_icon="🏦", layout="wide")
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

st.sidebar.title("⚙️ NCB V2.3 Settings")
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

st.title("🏦 NCB Credit Risk Manager Platform v2.3")
st.caption(f"Author: {AUTHOR} | CRO / ICAAP Edition | Upgraded from Techcombank Credit Risk Analytics Platform")
st.info("V2.3 bổ sung: ICAAP Lite, Recovery Plan, Credit Strategy Simulator, Collateral Haircut Engine và Risk Committee Pack.")

total=filtered["ead_bn_vnd"].sum()
ecl=filtered["ecl_bn_vnd"].sum()
stressed=filtered["stressed_ecl_bn_vnd"].sum()
weighted_pd=(filtered["pd_12m"]*filtered["ead_bn_vnd"]).sum()/total if total else 0
stage23=filtered[filtered["stage"].isin(["Stage 2","Stage 3"])] ["ead_bn_vnd"].sum()/total if total else 0
npl=filtered[filtered["stage"].eq("Stage 3")]["ead_bn_vnd"].sum()/total if total else 0
policy_table = apply_policy_rule_engine(filtered, policy_rules)
high_ews_count = int((filtered["combined_ews_score"]>=60).sum())
top_industry = filtered.groupby("industry")["ead_bn_vnd"].sum().sort_values(ascending=False).index[0] if len(filtered) else "N/A"

kpi_row([
    ("Total exposure",money(total),None),("Base ECL",money(ecl),None),("Stressed ECL",money(stressed),f"+{stressed-ecl:,.1f}"),
    ("Weighted PD",pct(weighted_pd),None),("NPL / Stage 3",pct(npl),None),("Policy breaches",f"{len(policy_table)}",None)
])

tabs=st.tabs([
    "1 Executive","2 Portfolio","3 Risk Appetite","4 Concentration","5 Policy Rule Engine",
    "6 Limit Monitoring","7 Single Customer View","8 Memo Generator","9 EWS + External Alerts",
    "10 IFRS9 & Stress","11 Migration","12 Basel Capital","13 Watchlist & Actions","14 Board Pack Export","15 Model Governance","16 NCB Interview Mode","17 ICAAP Lite","18 Recovery Plan","19 Credit Strategy Simulator","20 Collateral Haircut","21 Risk Committee Pack"
])

with tabs[0]:
    st.subheader("1️⃣ Executive Risk Dashboard")
    c1,c2=st.columns(2)
    stage=filtered.groupby("stage",as_index=False).agg(exposure=("ead_bn_vnd","sum"),ecl=("ecl_bn_vnd","sum"))
    c1.plotly_chart(px.bar(stage,x="stage",y="exposure",title="Exposure by IFRS9 Stage"),use_container_width=True)
    c2.plotly_chart(px.pie(stage,names="stage",values="ecl",title="ECL by Stage"),use_container_width=True)
    st.markdown("**Management message:** kiểm soát Stage 2, ngành tập trung cao, policy breaches, high-EWS accounts và watchlist overdue actions.")

with tabs[1]:
    st.subheader("2️⃣ Portfolio Quality")
    by_ind=filtered.groupby("industry",as_index=False).agg(exposure=("ead_bn_vnd","sum"),ecl=("ecl_bn_vnd","sum"),avg_pd=("pd_12m","mean"),avg_ews=("combined_ews_score","mean"))
    st.plotly_chart(px.bar(by_ind.sort_values("exposure",ascending=False),x="industry",y="exposure",title="Exposure by Industry"),use_container_width=True)
    st.dataframe(by_ind,use_container_width=True)

with tabs[2]:
    st.subheader("3️⃣ Risk Appetite Monitoring")
    actuals=compute_risk_appetite(filtered)
    rows=[]
    for _,r in risk_app.iterrows():
        a=actuals.get(r["metric"],np.nan)
        rows.append({"Metric":r["metric"],"Actual":a,"Limit":r["limit"],"Direction":r["direction"],"Status":status(a,r["limit"],r["direction"])})
    ra=pd.DataFrame(rows)
    st.dataframe(ra.style.format({"Actual":"{:.2%}","Limit":"{:.2%}"}),use_container_width=True)
    st.plotly_chart(px.bar(ra,x="Metric",y="Actual",color="Status",title="Risk Appetite Actuals"),use_container_width=True)

with tabs[3]:
    st.subheader("4️⃣ Concentration Risk")
    st.metric("Industry HHI",f"{hhi(filtered):.3f}")
    top=filtered.groupby(["group_id","industry"],as_index=False).agg(exposure=("ead_bn_vnd","sum")).sort_values("exposure",ascending=False).head(20)
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(top,x="group_id",y="exposure",color="industry",title="Top 20 Group Borrowers"),use_container_width=True)
    c2.plotly_chart(px.treemap(filtered,path=["industry","group_id"],values="ead_bn_vnd",title="Concentration Treemap"),use_container_width=True)
    st.dataframe(top,use_container_width=True)

with tabs[4]:
    st.subheader("5️⃣ Credit Policy Rule Engine")
    st.markdown("Rule engine giải thích khoản vay vi phạm điều khoản nào, mức độ nghiêm trọng và hành động quản lý đề xuất.")
    st.dataframe(policy_rules,use_container_width=True)
    st.markdown("### Breach details")
    st.dataframe(policy_table,use_container_width=True,height=430)
    if not policy_table.empty:
        st.plotly_chart(px.histogram(policy_table,x="severity",color="rule_name",title="Policy Breaches by Severity"),use_container_width=True)

with tabs[5]:
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

with tabs[6]:
    st.subheader("7️⃣ Single Customer View")
    cust=st.selectbox("Select customer",filtered["customer_id"].sort_values().unique(), key="cust_view")
    one=filtered[filtered["customer_id"].eq(cust)]
    kpi_row([("Exposure",money(one["ead_bn_vnd"].sum()),None),("ECL",money(one["ecl_bn_vnd"].sum()),None),("Max EWS",f"{one['combined_ews_score'].max():.1f}",None),("Policy","Pass" if (one["policy_result"]=="Pass").all() else "Breach",None)])
    st.dataframe(one[["loan_id","group_id","industry","product","rating_grade","stage","ead_bn_vnd","pd_12m","lgd","ecl_bn_vnd","dpd","dscr","ltv","combined_ews_score","policy_result"]],use_container_width=True)

with tabs[7]:
    st.subheader("8️⃣ Credit Approval Memo Generator")
    cust_memo=st.selectbox("Select customer for memo",filtered["customer_id"].sort_values().unique(), key="cust_memo")
    memo_df=filtered[filtered["customer_id"].eq(cust_memo)]
    memo=generate_credit_memo(memo_df, external_alerts)
    st.text_area("Generated memo", memo, height=470)
    st.download_button("⬇️ Download Credit Memo TXT", memo, file_name=f"credit_memo_{cust_memo}.txt")

with tabs[8]:
    st.subheader("9️⃣ Early Warning System + External Alerts")
    c1,c2=st.columns(2)
    c1.plotly_chart(px.histogram(filtered,x="combined_ews_score",nbins=20,title="Combined EWS Distribution"),use_container_width=True)
    ews_bucket=filtered.groupby("risk_bucket",observed=False).agg(exposure=("ead_bn_vnd","sum")).reset_index()
    c2.plotly_chart(px.pie(ews_bucket,names="risk_bucket",values="exposure",title="Exposure by EWS Bucket"),use_container_width=True)
    st.dataframe(external_alerts,use_container_width=True)
    st.dataframe(filtered.sort_values("combined_ews_score",ascending=False)[["loan_id","customer_id","industry","stage","ead_bn_vnd","dpd","dscr","debt_to_ebitda","ltv","ews_score","external_alert_score","combined_ews_score"]],use_container_width=True,height=380)

with tabs[9]:
    st.subheader("🔟 IFRS9 ECL & Stress Testing")
    ecl_stage=filtered.groupby("stage",as_index=False).agg(base_ecl=("ecl_bn_vnd","sum"),stressed_ecl=("stressed_ecl_bn_vnd","sum"))
    st.write(f"Selected scenario: **{scenario}** | PD multiplier: **{sc['pd_multiplier']:.2f}x** | LGD multiplier: **{sc['lgd_multiplier']:.2f}x**")
    st.plotly_chart(px.bar(ecl_stage,x="stage",y=["base_ecl","stressed_ecl"],barmode="group",title="Base vs Stressed ECL"),use_container_width=True)
    st.dataframe(ecl_stage,use_container_width=True)

with tabs[10]:
    st.subheader("1️⃣1️⃣ Credit Migration Matrix")
    fig=px.imshow(migration,text_auto=".0%",aspect="auto",title="Rating Migration Matrix")
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(migration.style.format("{:.1%}"),use_container_width=True)

with tabs[11]:
    st.subheader("1️⃣2️⃣ Basel II Capital & RAROC Lite")
    cap=filtered.copy()
    risk_weight=cap["rating_grade"].map({"AAA":0.5,"AA":0.6,"A":0.75,"BBB":1.0,"BB":1.25,"B":1.5,"CCC":2.0}).fillna(1.0)
    cap["rwa_bn_vnd"]=cap["ead_bn_vnd"]*risk_weight
    cap["capital_required_bn_vnd"]=cap["rwa_bn_vnd"]*0.08
    cap["income_bn_vnd"]=cap["ead_bn_vnd"]*0.035
    raroc=(cap['income_bn_vnd'].sum()-cap['ecl_bn_vnd'].sum())/cap['capital_required_bn_vnd'].sum() if cap['capital_required_bn_vnd'].sum() else 0
    kpi_row([("RWA",money(cap["rwa_bn_vnd"].sum()),None),("Capital required",money(cap["capital_required_bn_vnd"].sum()),None),("Portfolio RAROC",f"{raroc:.2%}",None)])
    st.plotly_chart(px.bar(cap.groupby("industry",as_index=False).agg(rwa=("rwa_bn_vnd","sum")),x="industry",y="rwa",title="RWA by Industry"),use_container_width=True)

with tabs[12]:
    st.subheader("1️⃣3️⃣ Watchlist & Management Action Tracker")
    st.markdown("### Watchlist")
    st.dataframe(watchlist,use_container_width=True,height=240)
    st.markdown("### Management Action Tracker")
    st.dataframe(actions,use_container_width=True,height=260)

with tabs[13]:
    st.subheader("1️⃣4️⃣ Board Pack Export")
    st.dataframe(board_template,use_container_width=True)
    board_report = build_board_report_text(total, ecl, stressed, scenario, weighted_pd, npl, stage23, hhi(filtered), top_industry, len(policy_table), high_ews_count)
    st.text_area("Board pack draft", board_report, height=420)
    st.download_button("⬇️ Download Board Pack TXT", board_report, file_name="NCB_Board_Risk_Pack_V22.txt")
    st.download_button("⬇️ Download Filtered Portfolio CSV", filtered.to_csv(index=False), file_name="NCB_Filtered_Portfolio_V22.csv")
    if not policy_table.empty:
        st.download_button("⬇️ Download Policy Breaches CSV", policy_table.to_csv(index=False), file_name="NCB_Policy_Breaches_V22.csv")

with tabs[14]:
    st.subheader("1️⃣5️⃣ Model Governance & Validation")
    st.markdown("Quản trị mô hình cho PD, IFRS9 ECL, EWS: owner, version, validation date, backtesting, override rate, limitation và next action.")
    st.dataframe(model_gov.style.format({"override_rate":"{:.1%}"}),use_container_width=True)
    st.plotly_chart(px.bar(model_gov,x="model_name",y="override_rate",color="backtest_result",title="Model Override Rate"),use_container_width=True)

with tabs[15]:
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


with tabs[16]:
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

with tabs[17]:
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

with tabs[18]:
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

with tabs[19]:
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

with tabs[20]:
    st.subheader("2️⃣1️⃣ Risk Committee Pack")
    assumptions = dict(zip(icaap_assumptions['metric'], icaap_assumptions['value']))
    icaap = icaap_lite(filtered, starting_car=float(assumptions.get('starting_car',0.118)), min_car_target=float(assumptions.get('min_car_target',0.08)), management_buffer=float(assumptions.get('management_buffer',0.025)))
    actuals_for_recovery = {'npl_ratio': npl, 'stage2_ratio': stage23-npl, 'car': icaap['post_stress_car'], 'real_estate_exposure': filtered.loc[filtered['industry'].eq('Real Estate'),'ead_bn_vnd'].sum()/total if total else 0, 'high_ews_count': high_ews_count}
    rec = recovery_plan_assessment(actuals_for_recovery, recovery_triggers)
    committee_text = build_risk_committee_pack(total, ecl, stressed, icaap, rec, top_industry, len(policy_table))
    st.dataframe(risk_committee_template, use_container_width=True)
    st.text_area("Generated Risk Committee Pack", committee_text, height=480)
    st.download_button("⬇️ Download Risk Committee Pack TXT", committee_text, file_name="NCB_Risk_Committee_Pack_V23.txt")


st.caption(f"© {AUTHOR}. Prototype for NCB Credit Risk Manager interview, portfolio risk governance and CRO Office demonstration.")
