"""
Inventory Planner - Streamlit UI
==================================
Invokes the Inventory Planner API on AWS Fargate and displays results.

Run: conda activate ticket-env
     streamlit run Inventory_UI.py
"""
import streamlit as st
import requests
import json

API_BASE = "http://98.92.198.159:8001"

st.set_page_config(page_title="Inventory Planner Agent", page_icon="📦", layout="wide")
st.title("📦 Inventory Planner Agent")
st.caption(f"Powered by LangGraph + Groq  |  API: `{API_BASE}`")


# ── Helper: render report ─────────────────────────────────────────────────────
def render_report(data):
    report  = data.get("report", data)
    summary = report.get("report_summary", {})

    st.success(f"✅ Completed  |  Confidence: {summary.get('overall_confidence', 0):.0%}  |  Attempts: {summary.get('attempts_used', data.get('attempts_used', 'N/A'))}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("SKUs",          summary.get("total_skus_analyzed", 0))
    c2.metric("Out of Stock",  summary.get("out_of_stock_count", 0))
    c3.metric("Low Stock",     summary.get("low_stock_count", 0))
    c4.metric("Orders",        f"{summary.get('purchase_orders_count',0)} ({summary.get('urgent_orders_count',0)} urgent)")
    c5.metric("Order Value",   f"${summary.get('total_order_value_usd', 0):,.2f}")

    st.divider()

    with st.expander("🔔 Stock Alerts", expanded=True):
        for a in report.get("stock_alerts", []):
            icon = {"OUT_OF_STOCK":"🔴","LOW_STOCK":"🟡","OVERSTOCK":"🔵","OK":"🟢"}.get(a["alert"],"⚪")
            st.write(f"{icon} **[{a['sku']}]** {a['name']} — Stock: `{a['current_stock']}` → **{a['alert']}**")

    with st.expander("📈 Demand Forecast (next 30 days)"):
        for f in report.get("demand_forecast", []):
            st.write(f"**[{f['sku']}]** Predicted: `{f.get('predicted_demand_30d','?')}` | Trend: `{f.get('trend','?')}` | Score: `{f.get('confidence_score','?')}`")
            if f.get("reasoning"):
                st.caption(f"  ↳ {f['reasoning']}")

    with st.expander("🛒 Purchase Orders"):
        pos = report.get("purchase_orders", [])
        if pos:
            for o in pos:
                icon = {"urgent":"🚨","high":"⚠️","normal":"✅"}.get(o.get("priority",""),"")
                st.write(f"{icon} **[{o['sku']}]** {o.get('name','')} — Qty: `{o.get('order_qty','?')}` | Cost: `${o.get('total_cost',0):,.2f}` | Priority: `{o.get('priority','?')}` | Confidence: `{o.get('confidence_score','?')}`")
                if o.get("detailed_reasoning"):
                    st.caption(f"  ↳ {o['detailed_reasoning']}")
        else:
            st.info("No purchase orders required.")

    with st.expander("⚠️ Risk Flags"):
        risks = report.get("risk_flags", [])
        if risks:
            for r in risks:
                icon = {"critical":"🚨","high":"⚠️ ","medium":"🔶","low":"ℹ️"}.get(r.get("severity",""),"")
                st.write(f"{icon} **[{r.get('sku','N/A')}]** {r.get('risk_type','')} — Severity: `{r.get('severity','?')}` | Confidence: `{r.get('confidence_score','?')}`")
                if r.get("detailed_reasoning"):
                    st.caption(f"  ↳ {r['detailed_reasoning']}")
                if r.get("recommendation"):
                    st.caption(f"  → {r['recommendation']}")
        else:
            st.info("No risks identified.")

    with st.expander("📄 Full JSON Response"):
        st.json(data)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    api_url = st.text_input("API Base URL", value=API_BASE)

    st.divider()
    st.subheader("📡 API Health")
    if st.button("Check Health"):
        try:
            r = requests.get(f"{api_url}/", timeout=5)
            st.success("✅ API is healthy")
            st.json(r.json())
        except Exception as e:
            st.error(f"❌ {e}")

    st.divider()
    st.subheader("📋 Input Data")
    if st.button("View Input JSON"):
        try:
            r = requests.get(f"{api_url}/input", timeout=5)
            st.json(r.json())
        except Exception as e:
            st.error(f"❌ {e}")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🚀 Run from Server File", "📝 Run with Custom Data"])

with tab1:
    st.subheader("Run using `Inventory_Planner_Input.json` on the server")
    st.info("Uses the input file already deployed on the Fargate container.")

    if st.button("▶ Run Inventory Planner", type="primary", key="btn_file"):
        with st.spinner("Running agent... (30-90 seconds)"):
            try:
                r = requests.post(f"{api_url}/plan/file", timeout=300)
                if r.status_code == 200:
                    render_report(r.json())
                else:
                    st.error(f"API Error {r.status_code}: {r.text}")
            except requests.Timeout:
                st.error("Timed out. The agent may still be running — try again.")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.subheader("Run with your own inventory data")

    sample = {
        "inventory": [
            {"sku": "SKU-001", "name": "Laptop 15in", "current_stock": 5,  "reorder_point": 10, "max_stock": 50},
            {"sku": "SKU-002", "name": "Webcam HD",   "current_stock": 0,  "reorder_point": 8,  "max_stock": 35},
            {"sku": "SKU-003", "name": "USB-C Hub",   "current_stock": 8,  "reorder_point": 15, "max_stock": 60}
        ],
        "sales_history": [
            {"sku": "SKU-001", "last_30_days": 18, "last_60_days": 32, "last_90_days": 45},
            {"sku": "SKU-002", "last_30_days": 15, "last_60_days": 28, "last_90_days": 40},
            {"sku": "SKU-003", "last_30_days": 22, "last_60_days": 40, "last_90_days": 58}
        ],
        "supplier_info": [
            {"sku": "SKU-001", "supplier": "TechDist Ltd",  "lead_days": 14, "moq": 10, "unit_cost": 850.00},
            {"sku": "SKU-002", "supplier": "VisionTech",    "lead_days": 8,  "moq": 10, "unit_cost": 45.00},
            {"sku": "SKU-003", "supplier": "ConnectHub Co", "lead_days": 10, "moq": 20, "unit_cost": 28.00}
        ]
    }

    payload_str = st.text_area("Edit JSON payload:", value=json.dumps(sample, indent=2), height=350)

    if st.button("▶ Run with Custom Data", type="primary", key="btn_custom"):
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
            st.stop()

        with st.spinner("Running agent..."):
            try:
                r = requests.post(f"{api_url}/plan", json=payload, timeout=300)
                if r.status_code == 200:
                    render_report(r.json())
                else:
                    st.error(f"API Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Error: {e}")
