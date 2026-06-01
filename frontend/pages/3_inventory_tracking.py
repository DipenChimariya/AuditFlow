import streamlit as st
import pandas as pd
from utils.api import fetch_clients, fetch_invoices

st.set_page_config(page_title="Inventory Tracker - AuditFlow", page_icon="📦", layout="wide")

st.title("📦 Client Inventory Tracker")
st.caption("A simple prototype tracker showing how stock balances shift based on purchases and sales.")
st.markdown("---")

clients_list = fetch_clients() or []
invoices_list = fetch_invoices() or []

if not clients_list:
    st.warning("⚠️ Register a corporate client in the directory to initialize inventory auditing.")
else:
    # 1. Top Input Bar
    col_config1, col_config2 = st.columns([2, 1])
    
    with col_config1:
        client_options = {c["name"]: c["id"] for c in clients_list}
        selected_client_name = st.selectbox(
            "Select Client Profile", 
            options=list(client_options.keys()),
            key="auto_inventory_client_selector"
        )
        target_client_id = client_options[selected_client_name]
        
    with col_config2:
        opening_stock = st.number_input(
            "Starting Stock Value (Rs.)", 
            min_value=0.0, 
            value=0.0, 
            step=10000.0,
            format="%.2f",
            help="Enter the value of stock the business started with this year."
        )

    st.markdown("---")

    # 2. Simple Math Calculations
    client_invoices = [inv for inv in invoices_list if inv["client_id"] == target_client_id]
    
    total_purchases = sum(float(inv.get("subtotal", 0.0)) for inv in client_invoices if inv.get("transaction_type") == "Purchase")
    total_sales = sum(float(inv.get("subtotal", 0.0)) for inv in client_invoices if inv.get("transaction_type") == "Sale")
    
    # Simple prototype equation
    final_stock_balance = (opening_stock + total_purchases) - total_sales

    # 3. Clean, Easy-to-Read Visual Cards
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        st.markdown(f"""
        <div style="background-color:#1e293b; padding:15px; border-radius:8px; border-left: 5px solid #3b82f6;">
            <p style="margin:0; font-size:14px; color:#94a3b8;">1. Starting Stock</p>
            <h3 style="margin:5px 0 0 0; font-size:20px; color:white;">Rs. {opening_stock:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col2:
        num_purchases = len([i for i in client_invoices if i.get('transaction_type') == 'Purchase'])
        st.markdown(f"""
        <div style="background-color:#1e293b; padding:15px; border-radius:8px; border-left: 5px solid #10b981;">
            <p style="margin:0; font-size:14px; color:#94a3b8;">2. Stock Added (+)</p>
            <h3 style="margin:5px 0 0 0; font-size:20px; color:white;">Rs. {total_purchases:,.2f}</h3>
            <span style="font-size:12px; color:#10b981;">From {num_purchases} purchase bills</span>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col3:
        num_sales = len([i for i in client_invoices if i.get('transaction_type') == 'Sale'])
        st.markdown(f"""
        <div style="background-color:#1e293b; padding:15px; border-radius:8px; border-left: 5px solid #f59e0b;">
            <p style="margin:0; font-size:14px; color:#94a3b8;">3. Stock Removed (-)</p>
            <h3 style="margin:5px 0 0 0; font-size:20px; color:white;">Rs. {total_sales:,.2f}</h3>
            <span style="font-size:12px; color:#f59e0b;">From {num_sales} sales invoices</span>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col4:
        status_color = "#10b981" if final_stock_balance >= 0 else "#ef4444"
        st.markdown(f"""
        <div style="background-color:#1e293b; padding:15px; border-radius:8px; border-left: 5px solid {status_color};">
            <p style="margin:0; font-size:14px; color:#94a3b8;">4. Available Stock</p>
            <h3 style="margin:5px 0 0 0; font-size:20px; color:white;">Rs. {final_stock_balance:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)

    st.write("") 
    st.markdown("---")
    
    # 4. Simple Audit Trail Table
    st.markdown(f"### 📑 Stock Activity History: {selected_client_name}")
    
    if not client_invoices:
        st.info("No invoices found for this client.")
    else:
        audit_trail = []
        for idx, inv in enumerate(client_invoices, start=1):
            inv_type = inv.get("transaction_type", "Purchase")
            subtotal = float(inv.get("subtotal", 0.0))
            
            audit_trail.append({
                "S.No.": idx,
                "Date": inv.get("invoice_date") or "N/A",
                "Invoice Number": inv.get("invoice_number") or "N/A",
                "Description / Company Name": inv.get("vendor_name"),
                "Action": "Stock In" if inv_type == "Purchase" else "Stock Out",
                "Value": f"Rs. {subtotal:,.2f}"
            })
            
        df_trail = pd.DataFrame(audit_trail)
        st.dataframe(df_trail, use_container_width=True, hide_index=True)