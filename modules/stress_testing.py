import streamlit as st
from .metrics import stress_result

def render(df, scenarios):
    scenario_name=st.selectbox('Scenario', scenarios.scenario.tolist(), index=0)
    s=scenarios[scenarios.scenario==scenario_name]
    stressed=stress_result(df,s)
    base=df.ecl_bn_vnd.sum(); stress=stressed.ecl_stress_bn_vnd.sum()
    c=st.columns(3)
    c[0].metric('Base ECL', f'{base:,.1f} bn VND')
    c[1].metric('Stress ECL', f'{stress:,.1f} bn VND')
    c[2].metric('ECL Increase', f'{(stress/base-1):.1%}')
    st.dataframe(stressed.nlargest(30,'ecl_stress_bn_vnd'), use_container_width=True)
