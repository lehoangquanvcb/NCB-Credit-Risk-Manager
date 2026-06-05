import streamlit as st
import pandas as pd
from .metrics import portfolio_metrics

def render(df):
    m=portfolio_metrics(df)
    c=st.columns(5)
    c[0].metric('Total Exposure', f"{m['total_exposure']:,.0f} bn VND")
    c[1].metric('NPL Ratio', f"{m['npl_ratio']:.2%}")
    c[2].metric('Stage 2 Ratio', f"{m['stage2_ratio']:.2%}")
    c[3].metric('ECL', f"{m['ecl']:,.1f} bn VND")
    c[4].metric('CAR Proxy', f"{m['car_proxy']:.2%}")
    st.subheader('Exposure by industry')
    st.bar_chart(df.groupby('industry').ead_bn_vnd.sum().sort_values(ascending=False))
    st.subheader('Top 10 borrowers')
    st.dataframe(df.nlargest(10,'ead_bn_vnd'), use_container_width=True)
