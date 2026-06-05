import streamlit as st
import pandas as pd
from .metrics import portfolio_metrics
from .utils import status_badge

def render(df, appetite):
    m=portfolio_metrics(df)
    actuals={'NPL Ratio':m['npl_ratio'],'Stage 2 Ratio':m['stage2_ratio'],'Real Estate Exposure':m['real_estate_exposure'],'Top 20 Exposure':m['top20_exposure'],'CAR':m['car_proxy'],'Cost of Risk':m['cost_of_risk'],'Single Industry Limit':df.groupby('industry').ead_bn_vnd.sum().max()/df.ead_bn_vnd.sum()}
    rows=[]
    for _,r in appetite.iterrows():
        a=actuals.get(r.metric,0)
        rows.append([r.metric,a,r.amber_limit,r.red_limit,status_badge(a,r.amber_limit,r.red_limit,r.direction)])
    out=pd.DataFrame(rows,columns=['Metric','Actual','Amber Limit','Red Limit','Status'])
    st.dataframe(out.style.format({'Actual':'{:.2%}','Amber Limit':'{:.2%}','Red Limit':'{:.2%}'}), use_container_width=True)
