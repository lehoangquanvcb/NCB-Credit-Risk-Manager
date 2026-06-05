import streamlit as st
import pandas as pd

def render(migration):
    mat=migration.pivot(index='from_rating', columns='to_rating', values='probability').fillna(0)
    st.dataframe(mat.style.format('{:.2%}'), use_container_width=True)
    st.bar_chart(mat.get('Default'))
