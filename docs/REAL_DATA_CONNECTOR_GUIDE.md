
# Real Data Connector Guide

Recommended production data files:

1. `loan_portfolio.csv`
- loan_id, customer_id, group_id, industry, product, rating_grade, stage
- ead_bn_vnd, pd_12m, lgd, ecl_bn_vnd, dpd, dscr, debt_to_ebitda, ltv
- collateral_type, collateral_value_bn_vnd, annual_revenue_bn_vnd, relationship_manager

2. `external_alerts.csv`
- customer_id, cic_status, tax_arrears_flag, legal_case_flag, negative_news_count, external_alert_score

3. `policy_rule_engine.csv`
- rule_id, rule_name, field, operator, threshold, severity, management_action

4. `model_governance.csv`
- model_name, version, owner, last_validation_date, backtest_result, auc_or_ks, override_rate, limitation, next_action

Keep column names unchanged for immediate Streamlit compatibility.
