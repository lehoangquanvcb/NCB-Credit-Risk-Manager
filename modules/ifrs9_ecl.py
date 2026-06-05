import streamlit as st

def render(df):
    st.subheader('IFRS9 ECL by Stage')
    st.bar_chart(df.groupby('stage').ecl_bn_vnd.sum())
    out=df.groupby(['stage','industry']).agg(ead_bn_vnd=('ead_bn_vnd','sum'), ecl_bn_vnd=('ecl_bn_vnd','sum'), avg_pd=('pd','mean'), avg_lgd=('lgd','mean')).reset_index()
    st.dataframe(out, use_container_width=True)
