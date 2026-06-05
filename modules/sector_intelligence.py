import streamlit as st
import pandas as pd

def render(df):
    outlook_map={'Real Estate':'Negative','Construction':'Cautious','Manufacturing':'Stable','Power':'Positive','Logistics':'Stable','Retail':'Cautious','Agriculture':'Stable','Services':'Stable','Trading':'Cautious','Healthcare':'Positive'}
    score_map={'Positive':-0.05,'Stable':0.00,'Cautious':0.10,'Negative':0.20}
    out=df.groupby('industry').agg(exposure=('ead_bn_vnd','sum'), avg_pd=('pd','mean'), npl=('is_npl','mean')).reset_index()
    out['sector_outlook']=out.industry.map(outlook_map)
    out['pd_overlay']=out.sector_outlook.map(score_map)
    out['adjusted_pd']=out.avg_pd*(1+out.pd_overlay)
    st.dataframe(out.sort_values('exposure',ascending=False).style.format({'avg_pd':'{:.2%}','npl':'{:.2%}','pd_overlay':'{:.1%}','adjusted_pd':'{:.2%}'}), use_container_width=True)
