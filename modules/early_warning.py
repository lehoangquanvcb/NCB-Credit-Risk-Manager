import streamlit as st
from .metrics import ews_score

def render(df):
    scored=ews_score(df)
    c=st.columns(3)
    c[0].metric('High EWS Accounts', int((scored.ews_bucket=='High').sum()))
    c[1].metric('Medium EWS Accounts', int((scored.ews_bucket=='Medium').sum()))
    c[2].metric('Avg EWS Score', f"{scored.score.mean():.1f}")
    st.bar_chart(scored.groupby('ews_bucket', observed=True).ead_bn_vnd.sum())
    st.dataframe(scored.sort_values('score', ascending=False).head(40), use_container_width=True)
