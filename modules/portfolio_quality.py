import streamlit as st

def render(df):
    st.subheader('Portfolio Quality')
    stage=df.groupby('stage').ead_bn_vnd.sum()
    rating=df.groupby('internal_rating').ead_bn_vnd.sum()
    st.bar_chart(stage)
    st.bar_chart(rating)
    st.dataframe(df.sort_values('days_past_due',ascending=False).head(30), use_container_width=True)
