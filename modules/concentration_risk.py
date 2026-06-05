import streamlit as st
from .metrics import portfolio_metrics

def render(df, industry_limit):
    total=df.ead_bn_vnd.sum()
    by=df.groupby('industry').ead_bn_vnd.sum().reset_index()
    by['share']=by.ead_bn_vnd/total
    by=by.merge(industry_limit,on='industry',how='left')
    by['limit_breach']=by.share>by.limit_pct
    st.metric('Industry HHI', f"{portfolio_metrics(df)['industry_hhi']:.3f}")
    st.bar_chart(by.set_index('industry')['share'])
    st.dataframe(by.sort_values('share',ascending=False), use_container_width=True)
