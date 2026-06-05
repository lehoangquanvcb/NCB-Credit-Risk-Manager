import pandas as pd
from .utils import hhi

def portfolio_metrics(df):
    total = df.ead_bn_vnd.sum()
    npl = df.loc[df.is_npl.astype(bool), 'ead_bn_vnd'].sum() / total
    stage2 = df.loc[df.stage.eq(2), 'ead_bn_vnd'].sum() / total
    stage3 = df.loc[df.stage.eq(3), 'ead_bn_vnd'].sum() / total
    ecl = df.ecl_bn_vnd.sum()
    cost_of_risk = ecl / total
    top20 = df.nlargest(20, 'ead_bn_vnd').ead_bn_vnd.sum() / total
    re = df.loc[df.industry.eq('Real Estate'), 'ead_bn_vnd'].sum() / total
    car_proxy = 0.125 - cost_of_risk * 0.8
    shares = df.groupby('industry').ead_bn_vnd.sum() / total
    return dict(total_exposure=total, npl_ratio=npl, stage2_ratio=stage2, stage3_ratio=stage3, ecl=ecl, cost_of_risk=cost_of_risk, top20_exposure=top20, real_estate_exposure=re, car_proxy=car_proxy, industry_hhi=hhi(shares))

def ews_score(df):
    out = df.copy()
    out['score'] = (
        out.days_past_due.clip(0, 120) / 120 * 30 +
        (out.stage - 1) / 2 * 20 +
        (1.5 - out.dscr).clip(0, 1.5) / 1.5 * 20 +
        (2.5 - out.interest_coverage).clip(0, 2.5) / 2.5 * 15 +
        (-out.ebitda_growth).clip(0, .5) / .5 * 15
    ).round(1)
    out['ews_bucket'] = pd.cut(out.score, [-1,30,60,100], labels=['Low','Medium','High'])
    return out

def stress_result(df, scenario):
    s = scenario.iloc[0] if hasattr(scenario, 'iloc') else scenario
    d=df.copy()
    d['pd_stress']=(d.pd*s['pd_multiplier']).clip(0,1)
    d['lgd_stress']=(d.lgd+s['lgd_addon']).clip(0,1)
    d['ecl_stress_bn_vnd']=d.ead_bn_vnd*d.pd_stress*d.lgd_stress
    return d
