import streamlit as st

def render(watchlist):
    st.subheader('Watchlist & Remedial Management')
    st.metric('Watchlist Exposure', f"{watchlist.ead_bn_vnd.sum():,.0f} bn VND")
    st.bar_chart(watchlist.groupby('trigger').ead_bn_vnd.sum())
    st.dataframe(watchlist, use_container_width=True)
