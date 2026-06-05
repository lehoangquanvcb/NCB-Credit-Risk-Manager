import streamlit as st

def render(df):
    d=df.copy()
    risk_weight_map={'AAA':0.2,'AA':0.3,'A':0.5,'BBB':0.75,'BB':1.0,'B':1.5,'CCC':1.5,'Default':1.5}
    d['risk_weight']=d.internal_rating.map(risk_weight_map).fillna(1.0)
    d['rwa_bn_vnd']=d.ead_bn_vnd*d.risk_weight
    d['capital_req_bn_vnd']=d.rwa_bn_vnd*0.08
    d['raroc_proxy']=(d.ead_bn_vnd*0.025-d.ecl_bn_vnd)/d.capital_req_bn_vnd.replace(0,1)
    c=st.columns(3)
    c[0].metric('RWA', f"{d.rwa_bn_vnd.sum():,.0f} bn VND")
    c[1].metric('Capital Requirement', f"{d.capital_req_bn_vnd.sum():,.0f} bn VND")
    c[2].metric('Portfolio RAROC Proxy', f"{((d.ead_bn_vnd*0.025-d.ecl_bn_vnd).sum()/d.capital_req_bn_vnd.sum()):.2%}")
    st.dataframe(d.sort_values('capital_req_bn_vnd',ascending=False).head(40), use_container_width=True)
