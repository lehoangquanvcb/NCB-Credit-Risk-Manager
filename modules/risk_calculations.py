
import numpy as np
import pandas as pd
BAD_RATINGS = ['BB','B','CCC']

def status(actual, limit, direction):
    if pd.isna(actual) or pd.isna(limit):
        return 'NA'
    if direction == 'max':
        if actual <= limit: return 'Green'
        if actual <= limit * 1.15: return 'Amber'
        return 'Red'
    if actual >= limit: return 'Green'
    if actual >= limit * 0.9: return 'Amber'
    return 'Red'

def compute_risk_appetite(df):
    total = df['ead_bn_vnd'].sum()
    if total == 0: return {}
    return {
        'NPL ratio': df.loc[df['stage'].eq('Stage 3'),'ead_bn_vnd'].sum()/total,
        'Stage 2 ratio': df.loc[df['stage'].eq('Stage 2'),'ead_bn_vnd'].sum()/total,
        'Real estate exposure': df.loc[df['industry'].eq('Real Estate'),'ead_bn_vnd'].sum()/total,
        'Top 20 exposure': df.nlargest(20,'ead_bn_vnd')['ead_bn_vnd'].sum()/total,
        'CAR': 0.118,
        'Cost of risk': df['ecl_bn_vnd'].sum()/total,
        'BB-or-worse exposure': df.loc[df['rating_grade'].isin(BAD_RATINGS),'ead_bn_vnd'].sum()/total,
    }

def hhi(df, col='industry'):
    total = df['ead_bn_vnd'].sum()
    if total == 0: return 0.0
    s = df.groupby(col)['ead_bn_vnd'].sum() / total
    return float((s*s).sum())

def ews_score(row):
    score = 0
    score += min(row.get('dpd',0),90) * 0.35
    score += max(0, 1.25-row.get('dscr',1.25)) * 30
    score += max(0, row.get('debt_to_ebitda',0)-5) * 5
    score += max(0, row.get('ltv',0)-0.75) * 80
    if row.get('stage') == 'Stage 2': score += 18
    if row.get('stage') == 'Stage 3': score += 35
    return min(100, round(score,1))

def policy_breaches(row):
    breaches=[]
    if row['dscr'] < 1.2: breaches.append('DSCR < 1.20')
    if row['ltv'] > 0.8: breaches.append('LTV > 80%')
    if row['debt_to_ebitda'] > 6: breaches.append('Debt/EBITDA > 6.0x')
    if row['dpd'] >= 30: breaches.append('DPD >= 30 days')
    if row['collateral_type'] == 'Unsecured': breaches.append('Unsecured exposure')
    return '; '.join(breaches) if breaches else 'Pass'

def stress_ecl(df, pd_mult=1.0, lgd_mult=1.0):
    pd_s = np.clip(df['pd_12m']*pd_mult,0.0001,0.95)
    lgd_s = np.clip(df['lgd']*lgd_mult,0.05,0.95)
    return pd_s*lgd_s*df['ead_bn_vnd']

def apply_policy_rule_engine(df, rules):
    rows=[]
    for _, loan in df.iterrows():
        for _, r in rules.iterrows():
            field, op, threshold = r['field'], r['operator'], r['threshold']
            value = loan.get(field)
            breach = False
            try:
                threshold_num = float(threshold)
            except Exception:
                threshold_num = threshold
            if op == '>=': breach = value < threshold_num
            elif op == '<=': breach = value > threshold_num
            elif op == '<': breach = value >= threshold_num
            elif op == '>': breach = value <= threshold_num
            elif op == '!=': breach = value == threshold_num
            elif op == '==': breach = value != threshold_num
            if breach:
                rows.append({
                    'loan_id': loan.get('loan_id'), 'customer_id': loan.get('customer_id'),
                    'industry': loan.get('industry'), 'ead_bn_vnd': loan.get('ead_bn_vnd'),
                    'rule_id': r['rule_id'], 'rule_name': r['rule_name'], 'field': field,
                    'actual_value': value, 'threshold': threshold, 'severity': r['severity'],
                    'management_action': r['management_action']
                })
    return pd.DataFrame(rows)

def generate_credit_memo(customer_df, external_df=None):
    if customer_df.empty:
        return 'No customer selected.'
    c = customer_df.iloc[0]
    exposure = customer_df['ead_bn_vnd'].sum()
    ecl = customer_df['ecl_bn_vnd'].sum()
    max_ews = customer_df['ews_score'].max() if 'ews_score' in customer_df else np.nan
    breaches = '; '.join(sorted(set(customer_df.get('policy_result', pd.Series(['Pass'])).astype(str))))
    ext_text = 'No material external alert recorded.'
    if external_df is not None and not external_df.empty:
        hit = external_df[external_df['customer_id'].eq(c['customer_id'])]
        if not hit.empty:
            h = hit.iloc[0]
            ext_text = f"CIC: {h['cic_status']}; tax arrears: {h['tax_arrears_flag']}; legal case: {h['legal_case_flag']}; negative news: {h['negative_news_count']}."
    recommendation = 'Approve with conditions' if max_ews < 60 and breaches == 'Pass' else 'Escalate / approve only with risk mitigation conditions'
    memo = f"""CREDIT APPROVAL MEMO - PROTOTYPE\n\nCustomer: {c['customer_id']}\nGroup: {c.get('group_id','N/A')}\nIndustry: {c['industry']}\nProduct(s): {', '.join(sorted(customer_df.get('product', pd.Series(['Facility'])).astype(str).unique()))}\nTotal EAD: {exposure:,.1f} bn VND\nRating: {c['rating_grade']}\nIFRS9 Stage(s): {', '.join(sorted(customer_df['stage'].astype(str).unique()))}\nBase ECL: {ecl:,.1f} bn VND\nMax EWS score: {max_ews:.1f}\nPolicy result: {breaches}\nExternal alerts: {ext_text}\n\nKey risks:\n- Repayment capacity: DSCR range {customer_df['dscr'].min():.2f}x - {customer_df['dscr'].max():.2f}x.\n- Leverage: Debt/EBITDA range {customer_df['debt_to_ebitda'].min():.2f}x - {customer_df['debt_to_ebitda'].max():.2f}x.\n- Collateral: LTV range {customer_df['ltv'].min():.0%} - {customer_df['ltv'].max():.0%}.\n\nRecommended risk mitigants:\n- Tighten covenants on DSCR, leverage and overdue status.\n- Require additional collateral where LTV exceeds policy threshold.\n- Move to watchlist if DPD or EWS deteriorates.\n\nRecommendation: {recommendation}.\n"""
    return memo

def build_board_report_text(total, ecl, stressed, scenario, weighted_pd, npl, stage23, hhi_value, top_industry, breaches_count, high_ews_count):
    return f"""NCB CREDIT RISK BOARD PACK - PROTOTYPE\n\n1. Executive Summary\nTotal exposure: {total:,.1f} bn VND\nBase ECL: {ecl:,.1f} bn VND\nStressed ECL ({scenario}): {stressed:,.1f} bn VND\nWeighted PD: {weighted_pd:.2%}\nNPL / Stage 3 ratio: {npl:.2%}\nStage 2+3 ratio: {stage23:.2%}\nIndustry HHI: {hhi_value:.3f}\nTop risk industry: {top_industry}\n\n2. Key Risk Issues\n- Policy breaches: {breaches_count} loans require exception governance or remediation.\n- High EWS accounts: {high_ews_count} loans need named action plans.\n- Concentration risk should be reviewed through industry and borrower limits.\n\n3. Recommended Decisions\n- Approve monthly Watchlist Committee escalation.\n- Require Risk Appetite breach action plans for Amber/Red limits.\n- Formalize model governance for PD, IFRS9 ECL and EWS tools.\n- Use this dashboard as a CRO Office / Credit Risk Manager prototype.\n"""


def collateral_haircut_analysis(df, haircuts, scenario='base'):
    col = 'adverse_haircut' if scenario.lower().startswith('adverse') else 'base_haircut'
    h = haircuts[['collateral_type', col]].rename(columns={col:'haircut'})
    out = df.merge(h, on='collateral_type', how='left')
    out['haircut'] = out['haircut'].fillna(0.50)
    out['collateral_value_bn_vnd'] = out['ead_bn_vnd'] / out['ltv'].replace(0, np.nan)
    out['post_haircut_collateral_bn_vnd'] = out['collateral_value_bn_vnd'] * (1 - out['haircut'])
    out['collateral_shortfall_bn_vnd'] = np.maximum(out['ead_bn_vnd'] - out['post_haircut_collateral_bn_vnd'], 0)
    return out

def icaap_lite(df, starting_car=0.118, min_car_target=0.08, management_buffer=0.025, stress_ecl_col='stressed_ecl_bn_vnd'):
    rating_rw = {'AAA':0.5,'AA':0.6,'A':0.75,'BBB':1.0,'BB':1.25,'B':1.5,'CCC':2.0}
    tmp = df.copy()
    tmp['rw'] = tmp['rating_grade'].map(rating_rw).fillna(1.0)
    tmp['rwa_bn_vnd'] = tmp['ead_bn_vnd'] * tmp['rw']
    rwa = tmp['rwa_bn_vnd'].sum()
    capital = starting_car * rwa
    stress_loss = max(tmp.get(stress_ecl_col, tmp['ecl_bn_vnd']).sum() - tmp['ecl_bn_vnd'].sum(), 0)
    post_stress_capital = max(capital - stress_loss, 0)
    post_stress_car = post_stress_capital / rwa if rwa else 0
    required_car = min_car_target + management_buffer
    buffer_surplus = post_stress_car - required_car
    return {
        'rwa_bn_vnd': rwa,
        'starting_capital_bn_vnd': capital,
        'stress_loss_bn_vnd': stress_loss,
        'post_stress_capital_bn_vnd': post_stress_capital,
        'starting_car': starting_car,
        'post_stress_car': post_stress_car,
        'required_car_including_buffer': required_car,
        'buffer_surplus': buffer_surplus,
        'icaap_status': 'Green' if buffer_surplus >= 0.01 else ('Amber' if buffer_surplus >= 0 else 'Red')
    }

def recovery_plan_assessment(metrics, triggers):
    rows=[]
    for _, r in triggers.iterrows():
        val = metrics.get(r['indicator'], np.nan)
        th = float(r['threshold'])
        direction = r['direction']
        breach = (val > th) if direction == 'max' else (val < th)
        rows.append({
            'trigger': r['trigger'], 'indicator': r['indicator'], 'actual': val,
            'threshold': th, 'status': 'Breach' if breach else 'OK',
            'recovery_action': r['recovery_action']
        })
    return pd.DataFrame(rows)

def simulate_credit_strategy(df, strategy_row):
    tmp = df.copy()
    growth_map = {
        'Real Estate': strategy_row.get('real_estate_growth_pct',0),
        'Manufacturing': strategy_row.get('manufacturing_growth_pct',0),
        'Construction': strategy_row.get('construction_growth_pct',0)
    }
    tmp['growth_pct'] = tmp['industry'].map(growth_map).fillna(0.05)
    tmp.loc[tmp['collateral_type'].eq('Unsecured'),'growth_pct'] = strategy_row.get('unsecured_growth_pct',0)
    tmp['new_ead_bn_vnd'] = tmp['ead_bn_vnd'] * (1 + tmp['growth_pct'])
    pd_mult = strategy_row.get('pd_multiplier',1.0)
    rwa_mult = strategy_row.get('rwa_multiplier',1.0)
    nim = strategy_row.get('nim_pct',0.032)
    tmp['new_ecl_bn_vnd'] = np.clip(tmp['pd_12m']*pd_mult,0.0001,0.95) * tmp['lgd'] * tmp['new_ead_bn_vnd']
    rating_rw = {'AAA':0.5,'AA':0.6,'A':0.75,'BBB':1.0,'BB':1.25,'B':1.5,'CCC':2.0}
    tmp['new_rwa_bn_vnd'] = tmp['new_ead_bn_vnd'] * tmp['rating_grade'].map(rating_rw).fillna(1.0) * rwa_mult
    income = tmp['new_ead_bn_vnd'].sum() * nim
    ecl = tmp['new_ecl_bn_vnd'].sum()
    cap = tmp['new_rwa_bn_vnd'].sum() * 0.08
    raroc = (income - ecl) / cap if cap else 0
    return tmp, {'new_exposure_bn_vnd':tmp['new_ead_bn_vnd'].sum(), 'new_ecl_bn_vnd':ecl, 'new_rwa_bn_vnd':tmp['new_rwa_bn_vnd'].sum(), 'income_bn_vnd':income, 'raroc':raroc}

def build_risk_committee_pack(total, ecl, stressed, icaap, recovery_df, top_industry, breaches_count):
    breaches = recovery_df[recovery_df['status'].eq('Breach')]
    actions = '\n'.join([f"- {r['trigger']}: {r['recovery_action']}" for _, r in breaches.iterrows()]) or '- No recovery trigger breached.'
    return f"""NCB RISK COMMITTEE PACK - V2.3 CRO / ICAAP EDITION\n\n1. Executive Summary\nTotal credit exposure: {total:,.1f} bn VND\nBase ECL: {ecl:,.1f} bn VND\nStressed ECL: {stressed:,.1f} bn VND\nTop concentration industry: {top_industry}\nPolicy breach count: {breaches_count}\n\n2. ICAAP Lite\nRWA: {icaap['rwa_bn_vnd']:,.1f} bn VND\nStarting CAR: {icaap['starting_car']:.2%}\nPost-stress CAR: {icaap['post_stress_car']:.2%}\nRequired CAR including management buffer: {icaap['required_car_including_buffer']:.2%}\nICAAP status: {icaap['icaap_status']}\n\n3. Recovery Plan Triggers\n{actions}\n\n4. Proposed Committee Decisions\n- Approve risk appetite remediation for all Amber/Red limits.\n- Require named owners and due dates for watchlist and breached policy exceptions.\n- Use ICAAP Lite results to guide credit growth by industry.\n- Review collateral haircut shortfall for top secured exposures.\n"""
