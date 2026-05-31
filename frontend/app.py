import streamlit as st
import pandas as pd
from datetime import datetime
from utils.api import fetch_clients, fetch_invoices

# Initialize page configurations
st.set_page_config(page_title="AuditFlow Enterprise", page_icon="💼", layout="wide")

# Fetch live backend metrics to populate the dashboard on execution
clients = fetch_clients() or []
invoices = fetch_invoices() or []

# Calculate rapid dashboard aggregations safely
total_firms = len(clients)
total_vouchers = len(invoices)
grand_turnover = sum(float(inv.get("total", 0.0)) for inv in invoices)

# Title Header Configuration
st.title("💼 AuditFlow Command Center")
st.caption(f"Live workspace telemetry for the current fiscal period • Active System Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.write("---")

# ===================================================
# 📊 1. SYSTEM-WIDE HIGH-LEVEL METRICS
# ===================================================
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    with st.container(border=True):
        st.metric(
            label="Registered Audit Clients", 
            value=f"{total_firms} Firms", 
            delta="Active Profiles" if total_firms > 0 else "Action Required"
        )
with m_col2:
    with st.container(border=True):
        st.metric(
            label="Total Logged Vouchers", 
            value=f"{total_vouchers} Bills",
            delta=f"+{total_vouchers} entries total"
        )
with m_col3:
    with st.container(border=True):
        st.metric(
            label="Aggregate Vault Turnover", 
            value=f"Rs. {grand_turnover:,.2f}",
            delta="Processed Financials"
        )

st.markdown(" ")

# ===================================================
# 🛠️ 2. QUICK-START UTILITIES & NAVIGATION INFO (ORDERED 1, 2, 3)
# ===================================================
st.markdown("### ⚡ Quick Operational Hub")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    with st.container(border=True):
        st.markdown("#### 🏢 1. Client Registry")
        st.write("Initialize corporate profiles, configure Nepalese PAN fields, and organize basic client compliance files.")
        st.caption("👈 Use sidebar menu to launch **Client Directory**")

with nav_col2:
    with st.container(border=True):
        st.markdown("#### 📄 2. Ledger Management")
        st.write("Commit incoming tax bills, auto-compute 13% VAT, execute filtered audits, or pull reports into Excel data sets.")
        st.caption("👈 Use sidebar menu to launch **Invoice Ledger**")

with nav_col3:
    with st.container(border=True):
        st.markdown("#### 📦 3. Stock Audit Balance")
        st.write("Keep manual and structured inventory logs mapping items, incoming units, sales, and remaining on-hand stock.")
        st.caption("👈 Use sidebar menu to launch **Inventory Tracking**")

st.markdown("---")

# ===================================================
# 📜 3. RECENT WORKPLACE ACTIVITY FOOTPRINT
# ===================================================
st.markdown("### 🕒 Recent Ledger Activity Trail")

if not invoices:
    st.info("No documents have been committed to the central database ledger in this session yet.")
else:
    recent_entries = list(reversed(invoices))[:5]
    
    trail_rows = []
    for idx, inv in enumerate(recent_entries, start=1):
        target_name = next((c["name"] for c in clients if c["id"] == inv["client_id"]), f"ID: {inv['client_id']}")
        
        trail_rows.append({
            "S.No.": idx,
            "Date Entry": inv.get("invoice_date") or "N/A",
            "Audit Client Entity": target_name,
            "Counter-Party Vendor": inv.get("vendor_name"),
            "Bill Reference": inv.get("invoice_number") or "N/A",
            "Total Amount": f"Rs. {float(inv.get('total', 0.0)):,.2f}"
        })
        
    st.dataframe(pd.DataFrame(trail_rows), use_container_width=True, hide_index=True)