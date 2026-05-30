import streamlit as st
import pandas as pd
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from utils.api import fetch_clients, fetch_inventory_by_client, add_inventory_item

st.set_page_config(page_title="Inventory Valuation - AuditFlow", page_icon="📦", layout="wide")
st.subheader("Inventory Financial Ledger")

if "inventory_success_msg" not in st.session_state:
    st.session_state.inventory_success_msg = None
if "inv_form_gen" not in st.session_state:
    st.session_state.inv_form_gen = 0

clients_list = fetch_clients() or []

if not clients_list:
    st.warning("⚠️ No registered client profiles found. Add clients in the Client Directory page first!")
else:
    # 1. CLIENT SELECTOR
    client_options = {c["name"]: c["id"] for c in clients_list}
    selected_client_name = st.selectbox(
        "Select Client Firm to view Valuation Sheets:",
        options=list(client_options.keys()),
        key="inventory_global_client_selector"
    )
    target_client_id = client_options[selected_client_name]
    st.markdown("---")

    inv_col1, inv_col2 = st.columns([1, 2])

    # 2. FINANCIAL ENTRY FORM
    with inv_col1:
        with st.container(border=True):
            st.markdown(f"### 📊 Inventory Valuation Balances")
            st.caption(f"Record monetary inventory balances for {selected_client_name}")
            st.markdown("---")
            
            period_lbl = st.text_input(
                "Audit Period / Inventory Category", 
                placeholder="e.g., FY 2025/26 Summary, Raw Materials, etc.",
                key=f"inv_prd_{st.session_state.inv_form_gen}"
            )
            
            # Currency Value Inputs using text fields for precision mapping
            op_raw = st.text_input("Opening Inventory Value (Rs.)", value="0.00", key=f"inv_op_{st.session_state.inv_form_gen}").strip()
            pur_raw = st.text_input("Total Purchases Value (Rs.)", value="0.00", key=f"inv_pur_{st.session_state.inv_form_gen}").strip()
            sold_raw = st.text_input("Cost of Goods Sold (COGS) (Rs.)", value="0.00", key=f"inv_sld_{st.session_state.inv_form_gen}").strip()
            
            try:
                op_val = Decimal(op_raw) if op_raw else Decimal("0.00")
                pur_val = Decimal(pur_raw) if pur_raw else Decimal("0.00")
                sold_val = Decimal(sold_raw) if sold_raw else Decimal("0.00")
            except InvalidOperation:
                st.error("⚠️ Value input contains invalid formatting. Use numbers only.")
                op_val, pur_val, sold_val = Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
                
            # Audit Math Formula calculation
            closing_val = op_val + pur_val - sold_val
            
            st.info(f"📋 **Calculated Closing Stock Value:** Rs. {closing_val:,.2f}")
            st.markdown("---")
            
            if st.session_state.inventory_success_msg:
                st.toast(st.session_state.inventory_success_msg, icon="📦")
                st.success(st.session_state.inventory_success_msg)
                st.session_state.inventory_success_msg = None

            submit_val = st.button("Commit Balances to Database", type="primary", use_container_width=True)
            
        if submit_val:
            if not period_lbl:
                st.error("❌ Specifying the Audit Period or Category label is mandatory.")
            elif closing_val < 0:
                st.error("❌ Arithmetic Warning: Closing inventory calculation resulted in a negative asset value.")
            else:
                with st.spinner("Writing ledger values..."):
                    res = add_inventory_item(
                        target_client_id,
                        period_lbl.strip(),
                        float(op_val),
                        float(pur_val),
                        float(sold_val)
                    )
                    if res and res.status_code in [200, 201]:
                        st.session_state.inventory_success_msg = f"SUCCESS: Valuation records for '{period_lbl}' committed for {selected_client_name}."
                        st.session_state.inv_form_gen += 1
                        st.rerun()
                    else:
                        st.error("❌ Connection failure or database mapping rejection.")

    # 3. DIRECTORY TABLE VIEW
    with inv_col2:
        st.markdown(f"### 📋 Current Valuation Records: {selected_client_name}")
        records = fetch_inventory_by_client(target_client_id)
        
        if records is None:
            st.error("🔌 Backend API server unreachable.")
        elif not records:
            st.info("No monetary inventory lines recorded for this client firm yet.")
        else:
            table_rows = []
            for idx, r in enumerate(records, start=1):
                op = float(r.get("opening_stock", 0))
                pur = float(r.get("purchased", 0))
                sld = float(r.get("sold", 0))
                closing = op + pur - sld
                
                table_rows.append({
                    "S.No.": idx,
                    "Audit Period / Category": r.get("product_name", "N/A"),
                    "Opening Asset Value": f"Rs. {op:,.2f}",
                    "Total Purchases": f"Rs. {pur:,.2f}",
                    "Cost of Goods Sold (COGS)": f"Rs. {sld:,.2f}",
                    "Closing Asset Valuation": f"Rs. {closing:,.2f}"
                })
                
            df = pd.DataFrame(table_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)