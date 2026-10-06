import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Risk, Fraud and Regulatory Intelligence Copilot",
    page_icon=":material/shield:",
    layout="wide",
)

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))

ACCENT = "#00D4AA"
ACCENT2 = "#6C63FF"
ACCENT3 = "#FF6B6B"
ACCENT4 = "#FFB347"
ACCENT5 = "#4FC3F7"
C = {
    "accent": ACCENT,
    "purple": ACCENT2,
    "red": ACCENT3,
    "orange": ACCENT4,
    "blue": ACCENT5,
}


def render_risk():
    st.header("Risk Intelligence")
    st.caption("Customer risk scoring, distribution, and trend analysis")

    @st.cache_data(ttl="5m")
    def load_risk_data():
        scores = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE ORDER BY CALCULATION_DATE")
        customers = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER")
        return scores, customers

    with st.spinner("Loading risk data..."):
        scores, customers = load_risk_data()

    avg_score = scores["RISK_SCORE"].mean()
    max_score = scores["RISK_SCORE"].max()
    critical_count = len(scores[scores["RISK_LEVEL"] == "Critical"])

    with st.container(horizontal=True):
        st.metric("Total risk records", str(len(scores)), border=True)
        st.metric("Average risk score", f"{avg_score:.1f}", border=True)
        st.metric("Max risk score", str(max_score), border=True)
        st.metric("Critical records", str(critical_count), border=True)

    risk_filter = st.multiselect("Risk level filter", scores["RISK_LEVEL"].unique().tolist(), default=scores["RISK_LEVEL"].unique().tolist(), key="risk_level_filter")

    filtered = scores[scores["RISK_LEVEL"].isin(risk_filter)]

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("Risk score distribution")
            dist = filtered.groupby("RISK_LEVEL").size().reset_index(name="COUNT")
            st.bar_chart(dist, x="RISK_LEVEL", y="COUNT", color=C["accent"])

    with col2:
        with st.container(border=True):
            st.subheader("Risk score trend")
            trend = filtered.groupby("CALCULATION_DATE")["RISK_SCORE"].mean().reset_index()
            trend.columns = ["DATE", "AVG_RISK_SCORE"]
            st.line_chart(trend, x="DATE", y="AVG_RISK_SCORE", color=C["red"])

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.subheader("Credit risk vs operational risk")
            st.scatter_chart(filtered, x="CREDIT_RISK", y="OPERATIONAL_RISK", color="RISK_LEVEL")

    with col4:
        with st.container(border=True):
            st.subheader("Country risk by customer")
            country_risk = customers.groupby("COUNTRY").size().reset_index(name="COUNT")
            st.bar_chart(country_risk, x="COUNTRY", y="COUNT", color=C["blue"])

    with st.container(border=True):
        st.subheader("Top risk customers")
        top_risk = conn.query("""
            SELECT r.CUSTOMER_ID, m.CUSTOMER_NAME, m.COUNTRY, r.RISK_SCORE, r.RISK_LEVEL, r.CREDIT_RISK, r.OPERATIONAL_RISK
            FROM RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE r
            JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON r.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY r.RISK_SCORE DESC
            LIMIT 15
        """)
        st.dataframe(top_risk, hide_index=True, use_container_width=True)

    if st.button("Refresh data", icon=":material/refresh:", key="refresh_risk"):
        load_risk_data.clear()
        st.rerun()


def render_fraud():
    st.header("Fraud Intelligence")
    st.caption("Transaction monitoring, fraud alerts, and detection analytics")

    @st.cache_data(ttl="5m")
    def load_fraud_data():
        alerts = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS ORDER BY ALERT_DATE")
        txns = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.TRANSACTION_DATA ORDER BY TXN_DATE")
        return alerts, txns

    with st.spinner("Loading fraud data..."):
        alerts, txns = load_fraud_data()

    total_alerts = len(alerts)
    critical = len(alerts[alerts["SEVERITY"] == "Critical"])
    detection_rate = round(total_alerts / len(txns) * 100, 1) if len(txns) > 0 else 0

    with st.container(horizontal=True):
        st.metric("Total transactions", f"{len(txns):,}", border=True)
        st.metric("Fraud alerts", str(total_alerts), border=True)
        st.metric("Critical alerts", str(critical), border=True)
        st.metric("Detection rate", f"{detection_rate}%", border=True)

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        severity_filter = st.multiselect("Severity", alerts["SEVERITY"].unique().tolist(), default=alerts["SEVERITY"].unique().tolist(), key="fraud_severity_filter")
    with f_col2:
        status_filter = st.multiselect("Alert status", alerts["ALERT_STATUS"].unique().tolist(), default=alerts["ALERT_STATUS"].unique().tolist(), key="fraud_status_filter")

    filtered = alerts[(alerts["SEVERITY"].isin(severity_filter)) & (alerts["ALERT_STATUS"].isin(status_filter))]

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("Alerts by type")
            by_type = filtered.groupby("ALERT_TYPE").size().reset_index(name="COUNT")
            st.bar_chart(by_type, x="ALERT_TYPE", y="COUNT", color=C["red"])

    with col2:
        with st.container(border=True):
            st.subheader("Alert severity distribution")
            by_sev = filtered.groupby("SEVERITY").size().reset_index(name="COUNT")
            st.bar_chart(by_sev, x="SEVERITY", y="COUNT", color=C["orange"])

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.subheader("Fraud alert trend")
            trend = filtered.groupby("ALERT_DATE").size().reset_index(name="COUNT")
            trend.columns = ["DATE", "ALERTS"]
            st.line_chart(trend, x="DATE", y="ALERTS", color=C["accent"])

    with col4:
        with st.container(border=True):
            st.subheader("Transactions by country")
            by_country = txns.groupby("COUNTRY")["TXN_AMOUNT"].sum().reset_index()
            by_country.columns = ["COUNTRY", "TOTAL_AMOUNT"]
            st.bar_chart(by_country, x="COUNTRY", y="TOTAL_AMOUNT", color=C["purple"])

    with st.container(border=True):
        st.subheader("Recent fraud alerts")
        recent = conn.query("""
            SELECT f.ALERT_ID, f.CUSTOMER_ID, m.CUSTOMER_NAME, f.ALERT_TYPE, f.ALERT_SCORE, f.SEVERITY, f.ALERT_DATE, f.ALERT_STATUS
            FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS f
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON f.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY f.ALERT_DATE DESC
            LIMIT 20
        """)
        st.dataframe(recent, hide_index=True, use_container_width=True)

    if st.button("Refresh data", icon=":material/refresh:", key="refresh_fraud"):
        load_fraud_data.clear()
        st.rerun()


def render_compliance():
    st.header("Regulatory Intelligence")
    st.caption("Anti-money laundering alerts, KYC status, and regulatory violations")

    @st.cache_data(ttl="5m")
    def load_compliance_data():
        aml = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.AML_ALERTS ORDER BY ALERT_DATE")
        kyc = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.KYC_COMPLIANCE")
        violations = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.REGULATORY_VIOLATIONS ORDER BY VIOLATION_DATE")
        return aml, kyc, violations

    with st.spinner("Loading compliance data..."):
        aml, kyc, violations = load_compliance_data()

    high_aml = len(aml[aml["SEVERITY"].isin(["High", "Critical"])])
    avg_compliance = round(kyc["COMPLIANCE_SCORE"].mean(), 1)

    with st.container(horizontal=True):
        st.metric("AML alerts", str(len(aml)), border=True)
        st.metric("High severity AML", str(high_aml), border=True)
        st.metric("Avg compliance score", str(avg_compliance), border=True)
        st.metric("Regulatory violations", str(len(violations)), border=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("AML alerts by rule")
            by_rule = aml.groupby("RULE_NAME").size().reset_index(name="COUNT")
            st.bar_chart(by_rule, x="RULE_NAME", y="COUNT", color=C["accent"])

    with col2:
        with st.container(border=True):
            st.subheader("KYC status breakdown")
            kyc_status = kyc.groupby("KYC_STATUS").size().reset_index(name="COUNT")
            st.bar_chart(kyc_status, x="KYC_STATUS", y="COUNT", color=C["purple"])

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.subheader("Violations by regulation")
            by_reg = violations.groupby("REGULATION_NAME").size().reset_index(name="COUNT")
            st.bar_chart(by_reg, x="REGULATION_NAME", y="COUNT", color=C["orange"])

    with col4:
        with st.container(border=True):
            st.subheader("AML alert trend")
            aml_trend = aml.groupby("ALERT_DATE").size().reset_index(name="COUNT")
            aml_trend.columns = ["DATE", "ALERTS"]
            st.line_chart(aml_trend, x="DATE", y="ALERTS", color=C["red"])

    with st.container(border=True):
        st.subheader("Compliance scorecard")
        scorecard = conn.query("""
            SELECT k.CUSTOMER_ID, m.CUSTOMER_NAME, k.KYC_STATUS, k.COMPLIANCE_SCORE, k.REVIEW_DATE, k.EXPIRY_DATE
            FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.KYC_COMPLIANCE k
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON k.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY k.COMPLIANCE_SCORE ASC
        """)
        st.dataframe(scorecard, hide_index=True, use_container_width=True)

    with st.container(border=True):
        st.subheader("Recent regulatory violations")
        recent_v = conn.query("""
            SELECT v.VIOLATION_ID, v.CUSTOMER_ID, m.CUSTOMER_NAME, v.REGULATION_NAME, v.SEVERITY, v.VIOLATION_DATE, v.STATUS
            FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.REGULATORY_VIOLATIONS v
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON v.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY v.VIOLATION_DATE DESC
            LIMIT 20
        """)
        st.dataframe(recent_v, hide_index=True, use_container_width=True)

    if st.button("Refresh data", icon=":material/refresh:", key="refresh_compliance"):
        load_compliance_data.clear()
        st.rerun()


def render_alerts():
    st.header("Alerts & Monitoring")
    st.caption("Consolidated view of all active alerts across risk, fraud, and compliance")

    @st.cache_data(ttl="5m")
    def load_alerts_data():
        fraud_alerts = conn.query("""
            SELECT f.ALERT_ID, f.CUSTOMER_ID, m.CUSTOMER_NAME, 'Fraud' AS DOMAIN, f.ALERT_TYPE, f.ALERT_SCORE, f.SEVERITY, f.ALERT_DATE, f.ALERT_STATUS AS STATUS
            FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS f
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON f.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY f.ALERT_DATE DESC
        """)
        aml_alerts = conn.query("""
            SELECT a.AML_ID AS ALERT_ID, a.CUSTOMER_ID, m.CUSTOMER_NAME, 'AML' AS DOMAIN, a.RULE_NAME AS ALERT_TYPE, a.ALERT_SCORE, a.SEVERITY, a.ALERT_DATE, a.STATUS
            FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.AML_ALERTS a
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON a.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY a.ALERT_DATE DESC
        """)
        high_risk = conn.query("""
            SELECT r.CUSTOMER_ID, m.CUSTOMER_NAME, r.RISK_SCORE, r.RISK_LEVEL, r.CALCULATION_DATE
            FROM RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE r
            JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON r.CUSTOMER_ID = m.CUSTOMER_ID
            WHERE r.RISK_LEVEL IN ('Critical', 'High')
            ORDER BY r.RISK_SCORE DESC
        """)
        return fraud_alerts, aml_alerts, high_risk

    with st.spinner("Loading alerts..."):
        fraud_alerts, aml_alerts, high_risk = load_alerts_data()

    total = len(fraud_alerts) + len(aml_alerts)

    with st.container(horizontal=True):
        st.metric("Fraud alerts", str(len(fraud_alerts)), border=True)
        st.metric("AML alerts", str(len(aml_alerts)), border=True)
        st.metric("High/Critical risk customers", str(len(high_risk)), border=True)
        st.metric("Total active alerts", str(total), border=True)

    alert_view = st.segmented_control("View", ["Fraud Alerts", "AML Alerts", "High Risk Customers"], default="Fraud Alerts", key="alert_view")

    if alert_view == "Fraud Alerts":
        severity_filter = st.multiselect("Filter by severity", fraud_alerts["SEVERITY"].unique().tolist(), default=fraud_alerts["SEVERITY"].unique().tolist(), key="alert_sev_filter")
        filtered = fraud_alerts[fraud_alerts["SEVERITY"].isin(severity_filter)]
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("Fraud alerts by severity")
                by_sev = filtered.groupby("SEVERITY").size().reset_index(name="COUNT")
                st.bar_chart(by_sev, x="SEVERITY", y="COUNT", color=C["red"])
        with col2:
            with st.container(border=True):
                st.subheader("Fraud alerts by type")
                by_type = filtered.groupby("ALERT_TYPE").size().reset_index(name="COUNT")
                st.bar_chart(by_type, x="ALERT_TYPE", y="COUNT", color=C["orange"])
        with st.container(border=True):
            st.subheader("Fraud alert details")
            st.dataframe(filtered, hide_index=True, use_container_width=True)

    elif alert_view == "AML Alerts":
        severity_filter = st.multiselect("Filter by severity", aml_alerts["SEVERITY"].unique().tolist(), default=aml_alerts["SEVERITY"].unique().tolist(), key="aml_sev_filter")
        filtered = aml_alerts[aml_alerts["SEVERITY"].isin(severity_filter)]
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("AML alerts by severity")
                by_sev = filtered.groupby("SEVERITY").size().reset_index(name="COUNT")
                st.bar_chart(by_sev, x="SEVERITY", y="COUNT", color=C["purple"])
        with col2:
            with st.container(border=True):
                st.subheader("AML alerts by rule")
                by_rule = filtered.groupby("ALERT_TYPE").size().reset_index(name="COUNT")
                st.bar_chart(by_rule, x="ALERT_TYPE", y="COUNT", color=C["accent"])
        with st.container(border=True):
            st.subheader("AML alert details")
            st.dataframe(filtered, hide_index=True, use_container_width=True)

    elif alert_view == "High Risk Customers":
        with st.container(border=True):
            st.subheader("Risk score distribution")
            by_level = high_risk.groupby("RISK_LEVEL").size().reset_index(name="COUNT")
            st.bar_chart(by_level, x="RISK_LEVEL", y="COUNT", color=C["red"])
        with st.container(border=True):
            st.subheader("High and critical risk customers")
            st.dataframe(high_risk, hide_index=True, use_container_width=True)

    if st.button("Refresh data", icon=":material/refresh:", key="refresh_alerts"):
        load_alerts_data.clear()
        st.rerun()


def render_investigations():
    st.header("Investigations")
    st.caption("Case management, investigator workload, and case status tracking")

    @st.cache_data(ttl="5m")
    def load_cases():
        cases = conn.query("SELECT * FROM RISK_INTELLIGENCE_DB.CASE_MANAGEMENT.INVESTIGATION_CASES ORDER BY CREATED_DATE DESC")
        return cases

    with st.spinner("Loading investigation data..."):
        cases = load_cases()

    open_c = len(cases[cases["STATUS"] == "Open"])
    in_progress = len(cases[cases["STATUS"] == "In Progress"])
    closed = len(cases[cases["STATUS"] == "Closed"])
    escalated = len(cases[cases["STATUS"] == "Escalated"])

    with st.container(horizontal=True):
        st.metric("Open cases", str(open_c), border=True)
        st.metric("In progress", str(in_progress), border=True)
        st.metric("Closed cases", str(closed), border=True)
        st.metric("Escalated cases", str(escalated), border=True)

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        case_type_filter = st.multiselect("Case type", cases["CASE_TYPE"].unique().tolist(), default=cases["CASE_TYPE"].unique().tolist(), key="inv_case_type")
    with f_col2:
        priority_filter = st.multiselect("Priority", cases["PRIORITY"].unique().tolist(), default=cases["PRIORITY"].unique().tolist(), key="inv_priority")

    filtered = cases[(cases["CASE_TYPE"].isin(case_type_filter)) & (cases["PRIORITY"].isin(priority_filter))]

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("Case status funnel")
            by_status = filtered.groupby("STATUS").size().reset_index(name="COUNT")
            st.bar_chart(by_status, x="STATUS", y="COUNT", color=C["accent"])

    with col2:
        with st.container(border=True):
            st.subheader("Cases by type")
            by_type = filtered.groupby("CASE_TYPE").size().reset_index(name="COUNT")
            st.bar_chart(by_type, x="CASE_TYPE", y="COUNT", color=C["purple"])

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.subheader("Priority distribution")
            by_prio = filtered.groupby("PRIORITY").size().reset_index(name="COUNT")
            st.bar_chart(by_prio, x="PRIORITY", y="COUNT", color=C["orange"])

    with col4:
        with st.container(border=True):
            st.subheader("Investigator workload")
            by_analyst = filtered.groupby("ASSIGNED_TO").size().reset_index(name="COUNT")
            st.bar_chart(by_analyst, x="ASSIGNED_TO", y="COUNT", color=C["blue"])

    with st.container(border=True):
        st.subheader("All investigation cases")
        display_cases = conn.query("""
            SELECT c.CASE_ID, c.CUSTOMER_ID, m.CUSTOMER_NAME, c.CASE_TYPE, c.PRIORITY, c.ASSIGNED_TO, c.STATUS, c.CREATED_DATE
            FROM RISK_INTELLIGENCE_DB.CASE_MANAGEMENT.INVESTIGATION_CASES c
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON c.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY c.CREATED_DATE DESC
        """)
        st.dataframe(display_cases, hide_index=True, use_container_width=True)

    if st.button("Refresh data", icon=":material/refresh:", key="refresh_investigations"):
        load_cases.clear()
        st.rerun()


def render_reports():
    st.header("Reports & Insights")
    st.caption("Executive summaries, trend analysis, and cross-domain intelligence")

    @st.cache_data(ttl="5m")
    def load_executive_data():
        total_customers = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER").iloc[0]["CNT"]
        high_risk = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.RISK_DATA.HIGH_RISK_CUSTOMERS").iloc[0]["CNT"]
        avg_risk = conn.query("SELECT ROUND(AVG(RISK_SCORE),1) AS val FROM RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE").iloc[0]["VAL"]
        critical_risk = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE WHERE RISK_LEVEL='Critical'").iloc[0]["CNT"]
        total_txn = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.TRANSACTION_DATA").iloc[0]["CNT"]
        fraud_alerts = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS").iloc[0]["CNT"]
        critical_alerts = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS WHERE SEVERITY='Critical'").iloc[0]["CNT"]
        aml_alerts = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.AML_ALERTS").iloc[0]["CNT"]
        kyc_expired = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.KYC_COMPLIANCE WHERE KYC_STATUS='Expired'").iloc[0]["CNT"]
        violations = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.REGULATORY_VIOLATIONS").iloc[0]["CNT"]
        open_cases = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.CASE_MANAGEMENT.OPEN_CASES").iloc[0]["CNT"]
        closed_cases = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.CASE_MANAGEMENT.INVESTIGATION_CASES WHERE STATUS='Closed'").iloc[0]["CNT"]
        escalated = conn.query("SELECT COUNT(*) AS cnt FROM RISK_INTELLIGENCE_DB.CASE_MANAGEMENT.INVESTIGATION_CASES WHERE STATUS='Escalated'").iloc[0]["CNT"]
        return {
            "total_customers": int(total_customers), "high_risk": int(high_risk),
            "avg_risk": float(avg_risk), "critical_risk": int(critical_risk),
            "total_txn": int(total_txn), "fraud_alerts": int(fraud_alerts),
            "critical_alerts": int(critical_alerts), "aml_alerts": int(aml_alerts),
            "kyc_expired": int(kyc_expired), "violations": int(violations),
            "open_cases": int(open_cases), "closed_cases": int(closed_cases),
            "escalated": int(escalated),
        }

    with st.spinner("Loading executive summary..."):
        d = load_executive_data()

    st.subheader("Executive summary")

    st.markdown("**Risk overview**")
    with st.container(horizontal=True):
        st.metric("Total customers", str(d["total_customers"]), border=True)
        st.metric("High risk customers", str(d["high_risk"]), border=True)
        st.metric("Average risk score", str(d["avg_risk"]), border=True)
        st.metric("Critical risk", str(d["critical_risk"]), border=True)

    st.markdown("**Fraud overview**")
    with st.container(horizontal=True):
        st.metric("Total transactions", f"{d['total_txn']:,}", border=True)
        st.metric("Fraud alerts", str(d["fraud_alerts"]), border=True)
        st.metric("Critical alerts", str(d["critical_alerts"]), border=True)

    st.markdown("**Compliance overview**")
    with st.container(horizontal=True):
        st.metric("AML alerts", str(d["aml_alerts"]), border=True)
        st.metric("KYC expired", str(d["kyc_expired"]), border=True)
        st.metric("Regulatory violations", str(d["violations"]), border=True)

    st.markdown("**Investigation overview**")
    with st.container(horizontal=True):
        st.metric("Open cases", str(d["open_cases"]), border=True)
        st.metric("Closed cases", str(d["closed_cases"]), border=True)
        st.metric("Escalated cases", str(d["escalated"]), border=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("Risk level distribution")
            risk_dist = conn.query("SELECT RISK_LEVEL, COUNT(*) AS COUNT FROM RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE GROUP BY RISK_LEVEL ORDER BY COUNT DESC")
            st.bar_chart(risk_dist, x="RISK_LEVEL", y="COUNT", color=C["accent"])

    with col2:
        with st.container(border=True):
            st.subheader("Fraud alerts by type")
            fraud_type = conn.query("SELECT ALERT_TYPE, COUNT(*) AS COUNT FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS GROUP BY ALERT_TYPE ORDER BY COUNT DESC")
            st.bar_chart(fraud_type, x="ALERT_TYPE", y="COUNT", color=C["purple"])

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.subheader("AML alerts by rule")
            aml_rule = conn.query("SELECT RULE_NAME, COUNT(*) AS COUNT FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.AML_ALERTS GROUP BY RULE_NAME ORDER BY COUNT DESC")
            st.bar_chart(aml_rule, x="RULE_NAME", y="COUNT", color=C["orange"])

    with col4:
        with st.container(border=True):
            st.subheader("Case status")
            case_status = conn.query("SELECT STATUS, COUNT(*) AS COUNT FROM RISK_INTELLIGENCE_DB.CASE_MANAGEMENT.INVESTIGATION_CASES GROUP BY STATUS ORDER BY COUNT DESC")
            st.bar_chart(case_status, x="STATUS", y="COUNT", color=C["blue"])

    st.subheader("AI Copilot")
    st.caption("Ask natural language questions about your risk and compliance data")

    QUERY_MAP = {
        "Show customers with risk score above 90": """
            SELECT r.CUSTOMER_ID, m.CUSTOMER_NAME, m.COUNTRY, r.RISK_SCORE, r.RISK_LEVEL
            FROM RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE r
            JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON r.CUSTOMER_ID = m.CUSTOMER_ID
            WHERE r.RISK_SCORE > 90
            ORDER BY r.RISK_SCORE DESC
        """,
        "Which customers have expired KYC?": """
            SELECT k.CUSTOMER_ID, m.CUSTOMER_NAME, m.COUNTRY, k.KYC_STATUS, k.EXPIRY_DATE, k.COMPLIANCE_SCORE
            FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.KYC_COMPLIANCE k
            JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON k.CUSTOMER_ID = m.CUSTOMER_ID
            WHERE k.KYC_STATUS = 'Expired'
            ORDER BY k.EXPIRY_DATE
        """,
        "Show critical fraud alerts": """
            SELECT f.ALERT_ID, f.CUSTOMER_ID, m.CUSTOMER_NAME, f.ALERT_TYPE, f.ALERT_SCORE, f.ALERT_DATE, f.ALERT_STATUS
            FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS f
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON f.CUSTOMER_ID = m.CUSTOMER_ID
            WHERE f.SEVERITY = 'Critical'
            ORDER BY f.ALERT_DATE DESC
        """,
        "Show top countries with fraud exposure": """
            SELECT t.COUNTRY, COUNT(DISTINCT f.ALERT_ID) AS FRAUD_ALERTS, SUM(t.TXN_AMOUNT) AS TOTAL_TXN_AMOUNT
            FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.TRANSACTION_DATA t
            JOIN RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS f ON t.CUSTOMER_ID = f.CUSTOMER_ID
            GROUP BY t.COUNTRY
            ORDER BY FRAUD_ALERTS DESC
        """,
        "List customers with both AML and fraud alerts": """
            SELECT DISTINCT m.CUSTOMER_ID, m.CUSTOMER_NAME, m.COUNTRY, m.RISK_CATEGORY
            FROM RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m
            WHERE m.CUSTOMER_ID IN (SELECT CUSTOMER_ID FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS)
              AND m.CUSTOMER_ID IN (SELECT CUSTOMER_ID FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.AML_ALERTS)
            ORDER BY m.CUSTOMER_NAME
        """,
    }

    selected = st.pills("Quick queries", list(QUERY_MAP.keys()), selection_mode="single", key="report_queries")

    if selected:
        with st.spinner("Running query..."):
            result = conn.query(QUERY_MAP[selected])
        st.dataframe(result, hide_index=True, use_container_width=True)
        st.caption(f"{len(result)} rows returned")

    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []

    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    SYSTEM_PROMPT = (
        "You are a Risk Intelligence Copilot. You help analysts understand risk, fraud, and compliance data.\n"
        "You have access to these tables in RISK_INTELLIGENCE_DB:\n"
        "- MASTER_DATA.CUSTOMER_MASTER (CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_TYPE, COUNTRY, INDUSTRY, RISK_CATEGORY, KYC_STATUS)\n"
        "- RISK_DATA.CUSTOMER_RISK_SCORE (CUSTOMER_ID, RISK_SCORE, CREDIT_RISK, OPERATIONAL_RISK, LIQUIDITY_RISK, COUNTRY_RISK, RISK_LEVEL)\n"
        "- FRAUD_DATA.TRANSACTION_DATA (TXN_ID, CUSTOMER_ID, TXN_DATE, TXN_AMOUNT, TXN_TYPE, COUNTRY, CHANNEL, STATUS)\n"
        "- FRAUD_DATA.FRAUD_ALERTS (ALERT_ID, CUSTOMER_ID, ALERT_TYPE, ALERT_SCORE, SEVERITY, ALERT_DATE, ALERT_STATUS)\n"
        "- COMPLIANCE_DATA.AML_ALERTS (AML_ID, CUSTOMER_ID, RULE_NAME, ALERT_SCORE, SEVERITY, ALERT_DATE, STATUS)\n"
        "- COMPLIANCE_DATA.KYC_COMPLIANCE (CUSTOMER_ID, KYC_STATUS, REVIEW_DATE, EXPIRY_DATE, COMPLIANCE_SCORE)\n"
        "- COMPLIANCE_DATA.REGULATORY_VIOLATIONS (VIOLATION_ID, CUSTOMER_ID, REGULATION_NAME, SEVERITY, VIOLATION_DATE, STATUS)\n"
        "- CASE_MANAGEMENT.INVESTIGATION_CASES (CASE_ID, CUSTOMER_ID, ALERT_ID, CASE_TYPE, PRIORITY, ASSIGNED_TO, STATUS, CREATED_DATE)\n\n"
        "Provide concise, actionable insights. When asked about data, describe what you see and recommend next steps."
    )

    if prompt := st.chat_input("Ask about risk, fraud, or compliance data..."):
        st.session_state.copilot_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            full_prompt = SYSTEM_PROMPT + "\n\nUser question: " + prompt
            session = conn.session()
            result = session.sql(
                "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS response",
                params=["claude-3-5-sonnet", full_prompt],
            ).collect()
            response = result[0]["RESPONSE"] if result else "Sorry, I could not generate a response."
            st.write(response)

        st.session_state.copilot_messages.append({"role": "assistant", "content": response})

    if st.button("Refresh data", icon=":material/refresh:", key="refresh_reports"):
        load_executive_data.clear()
        st.rerun()


def render_documents():
    st.header("Document Analysis")
    st.caption("Upload and analyze risk, fraud, and compliance documents")

    st.subheader("Document upload")
    uploaded_file = st.file_uploader("Upload a document for analysis", type=["pdf", "csv", "txt", "xlsx"], key="doc_upload")

    if uploaded_file is not None:
        st.success("Uploaded: " + uploaded_file.name + " (" + f"{uploaded_file.size:,}" + " bytes)")

        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            st.subheader("Document preview")
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.caption(str(len(df)) + " rows, " + str(len(df.columns)) + " columns")
        elif uploaded_file.name.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8")
            st.subheader("Document content")
            st.text_area("Content", content, height=300, disabled=True, key="doc_content_display")
        else:
            st.info("File **" + uploaded_file.name + "** uploaded successfully. Advanced parsing for this file type can be configured in Settings.")

    st.divider()

    st.subheader("Quick document queries")
    st.caption("Run predefined queries to generate compliance and risk reports")

    report_type = st.selectbox("Select report type", [
        "Customer risk summary",
        "Fraud exposure by country",
        "KYC compliance status",
        "Regulatory violation summary",
        "Investigation case summary",
    ], key="doc_report_type")

    report_queries = {
        "Customer risk summary": """
            SELECT m.CUSTOMER_ID, m.CUSTOMER_NAME, m.COUNTRY, m.RISK_CATEGORY,
                   r.RISK_SCORE, r.RISK_LEVEL, r.CREDIT_RISK, r.OPERATIONAL_RISK
            FROM RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m
            LEFT JOIN RISK_INTELLIGENCE_DB.RISK_DATA.CUSTOMER_RISK_SCORE r ON m.CUSTOMER_ID = r.CUSTOMER_ID
            ORDER BY r.RISK_SCORE DESC NULLS LAST
        """,
        "Fraud exposure by country": """
            SELECT t.COUNTRY, COUNT(DISTINCT t.TXN_ID) AS TOTAL_TXNS,
                   COUNT(DISTINCT f.ALERT_ID) AS FRAUD_ALERTS,
                   SUM(t.TXN_AMOUNT) AS TOTAL_AMOUNT
            FROM RISK_INTELLIGENCE_DB.FRAUD_DATA.TRANSACTION_DATA t
            LEFT JOIN RISK_INTELLIGENCE_DB.FRAUD_DATA.FRAUD_ALERTS f ON t.CUSTOMER_ID = f.CUSTOMER_ID
            GROUP BY t.COUNTRY
            ORDER BY FRAUD_ALERTS DESC
        """,
        "KYC compliance status": """
            SELECT k.CUSTOMER_ID, m.CUSTOMER_NAME, m.COUNTRY,
                   k.KYC_STATUS, k.COMPLIANCE_SCORE, k.REVIEW_DATE, k.EXPIRY_DATE
            FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.KYC_COMPLIANCE k
            LEFT JOIN RISK_INTELLIGENCE_DB.MASTER_DATA.CUSTOMER_MASTER m ON k.CUSTOMER_ID = m.CUSTOMER_ID
            ORDER BY k.COMPLIANCE_SCORE ASC
        """,
        "Regulatory violation summary": """
            SELECT v.REGULATION_NAME, v.SEVERITY, COUNT(*) AS VIOLATION_COUNT,
                   MIN(v.VIOLATION_DATE) AS EARLIEST, MAX(v.VIOLATION_DATE) AS LATEST
            FROM RISK_INTELLIGENCE_DB.COMPLIANCE_DATA.REGULATORY_VIOLATIONS v
            GROUP BY v.REGULATION_NAME, v.SEVERITY
            ORDER BY VIOLATION_COUNT DESC
        """,
        "Investigation case summary": """
            SELECT c.CASE_TYPE, c.PRIORITY, c.STATUS, COUNT(*) AS CASE_COUNT
            FROM RISK_INTELLIGENCE_DB.CASE_MANAGEMENT.INVESTIGATION_CASES c
            GROUP BY c.CASE_TYPE, c.PRIORITY, c.STATUS
            ORDER BY CASE_COUNT DESC
        """,
    }

    if st.button("Generate report", icon=":material/description:", key="gen_report"):
        with st.spinner("Generating report..."):
            result = conn.query(report_queries[report_type])
        st.dataframe(result, hide_index=True, use_container_width=True)
        st.caption(str(len(result)) + " rows returned")


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

PAGES = {
    ":material/warning: Risk Intelligence": render_risk,
    ":material/gpp_bad: Fraud Intelligence": render_fraud,
    ":material/verified_user: Regulatory Intelligence": render_compliance,
    ":material/notifications_active: Alerts & Monitoring": render_alerts,
    ":material/search: Investigations": render_investigations,
    ":material/insights: Reports & Insights": render_reports,
    ":material/description: Document Analysis": render_documents,
}

with st.sidebar:
    st.title(":material/shield: Risk Intelligence Copilot")
    selection = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

PAGES[selection]()
