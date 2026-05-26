import streamlit as st
from utils.api import fetch_clients, add_new_client,fetch_invoices, add_new_invoice

st.set_page_config(page_title="AuditFlow Enterprise", page_icon="💼", layout="wide")

st.title("💼 AuditFlow: Client Management Dashboard")
st.markdown("Manage your audited client firms, track tax profiles, and view extracted invoices seamlessly.")
st.write("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Register New Client Firm")
    
    # Simple form inputs matching Pydantic schemas
    client_name = st.text_input("Official Firm Name", placeholder="e.g., ABC Trading Pvt. Ltd.")
    pan_number = st.text_input("Nepalese PAN (9 Digits)", max_chars=9, placeholder="e.g., 678546345")
    
    if st.button("Save Client to Database", type="primary"):
        if not client_name:
            st.error("❌ The Client Firm Name is required.")
        elif pan_number and (not pan_number.isdigit() or len(pan_number) != 9):
            st.error("❌ PAN number must be exactly 9 numeric digits matching Nepalese tax compliance laws.")
        else:
            with st.spinner("Writing to PostgreSQL..."):
                response = add_new_client(client_name, pan_number)
                
                if response is None:
                    st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
                elif response.status_code == 200:
                    st.success(f"🎉 '{client_name}' successfully added to the system!")
                    st.rerun() # Refresh the screen to update the table immediately!
                else:
                    error_detail = response.json().get('detail', 'Unknown validation error.')
                    st.error(f"❌ Failed to save: {error_detail}")

with col2:
    st.subheader("🏢 Registered Audit Clients")
    
    with st.spinner("Fetching client records from backend..."):
        clients = fetch_clients()
        
        if clients is None:
            st.error("🔌 Connection Error: Make sure your FastAPI backend is running on http://127.0.0.1:8000")
        elif len(clients) == 0:
            st.info("ℹ️ No client firms found in the system yet. Use the form on the left to add your first one!")
        else:
            
            st.metric(label="Total Active Client Profiles", value=len(clients))
            
            
            table_data = []
            for c in clients:
                table_data.append({
                    "Database ID": c["id"],
                    "Client Firm Name": c["name"],
                    "PAN Number": c["pan_number"] if c["pan_number"] else "N/A"
                })
            
            # Render the data directly into an interactive, sortable Excel-style grid
            st.dataframe(table_data, use_container_width=True, hide_index=True)





st.set_page_config(page_title="AuditFlow Enterprise", page_icon="💼", layout="wide")
st.title("💼 AuditFlow Workspace")

# Create Navigation Tabs at the very top
tab1, tab2 = st.tabs(["🏢 Client Directory", "📄 Invoice Ledger"])

# ==========================================
# TAB 1: CLIENT MANAGEMENT
# ==========================================
with tab1:
    st.subheader("Client Profiles")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Register New Client")
        client_name = st.text_input("Official Firm Name", placeholder="e.g., ABC Trading Pvt. Ltd.", key="register_client_name")
        pan_number = st.text_input("Nepalese PAN (9 Digits)", max_chars=9, placeholder="e.g., 678546345",key="tab1_pan_number")
        
        if st.button("Save Client Profile", type="primary", key="save_client_btn"):
            if not client_name:
                st.error("❌ Firm Name is required.")
            elif pan_number and (not pan_number.isdigit() or len(pan_number) != 9):
                st.error("❌ PAN must be exactly 9 numeric digits.")
            else:
                response = add_new_client(client_name, pan_number)
                if response and response.status_code == 200:
                    st.success(f"🎉 Saved '{client_name}' successfully!")
                    st.rerun()
                else:
                    st.error("❌ Error saving client to database.")
                    
    with col2:
        st.markdown("### Active Audit Profiles")
        clients = fetch_clients()
        if clients is None:
            st.error("🔌 Backend offline.")
        elif len(clients) == 0:
            st.info("No clients registered yet.")
        else:
            st.metric(label="Total Tracked Firms", value=len(clients))
            table_data = [{"ID": c["id"], "Firm Name": c["name"], "PAN Number": c["pan_number"] or "N/A"} for c in clients]
            st.dataframe(table_data, use_container_width=True, hide_index=True)


# ==========================================
# TAB 2: INVOICE MANAGEMENT
# ==========================================
with tab2:
    st.subheader("Invoice Records")
    
    # Refresh client list dynamically for the dropdown box selector
    clients_list = fetch_clients() or []
    
    if not clients_list:
        st.warning("⚠️ You must register at least one client in Tab 1 before you can log or process invoices.")
    else:
        inv_col1, inv_col2 = st.columns([1, 2])
        
        with inv_col1:
            st.markdown("### Log Invoice Manually")
            
            client_options = {c["name"]: c["id"] for c in clients_list}
            selected_client_name = st.selectbox("Assign to Client Firm", options=list(client_options.keys()))
            target_client_id = client_options[selected_client_name]
            
            # --- New Inputs to Match schemas.py ---
            vendor_name = st.text_input("Vendor Name (Seller)", placeholder="e.g., Bhat-Bhateni Supermarket", key="tab2_vendor_name")
            invoice_num = st.text_input("Invoice / Bill Number", placeholder="e.g., INV-2026-001", key="tab2_invoice_num")
            
            subtotal = st.number_input("Subtotal / Base Amount (Rs.)", min_value=0.0, step=100.0, format="%.2f", key="tab2_subtotal")
            vat_amount = st.number_input("VAT Amount (Rs.)", min_value=0.0, step=13.0, format="%.2f", key="tab2_vat")
            
            
            if st.button("Auto-Calculate 13% VAT"):
                st.info(f"Suggested VAT calculation: Rs. {subtotal * 0.13:.2f}")
            
            if st.button("Commit Invoice to Ledger", type="primary", key="save_invoice_btn"):
                if not vendor_name:
                    st.error("❌ Vendor Name is mandatory.")
                else:
                    with st.spinner("Linking to database..."):
                        # Send the corrected properties down the line
                        res = add_new_invoice(target_client_id, vendor_name, invoice_num, subtotal, vat_amount)
                        if res and res.status_code == 200:
                            st.success(f"🎉 Invoice {invoice_num} successfully pinned to {selected_client_name}!")
                            st.rerun()
                        else:
                            error_msg = res.json() if res else "Backend offline"
                            st.error(f"❌ Failed to register invoice. Server details: {error_msg}")

        with inv_col2:
            st.markdown("### Global Invoice Tracking Ledger")
            invoices = fetch_invoices()
            
            if invoices is None:
                st.error("🔌 Backend offline.")
            elif len(invoices) == 0:
                st.info("No invoices logged in the central repository yet.")
            else:
                st.metric(label="Total Logged Vouchers", value=len(invoices))
                
                # Format output table neatly, merging Client IDs with visible name placeholders if desired
                inv_table = []
                for i in invoices:
                    # Find matching name from our loaded client list for cleaner presentation
                    owner_name = next((c["name"] for c in clients_list if c["id"] == i["client_id"]), f"Client ID: {i['client_id']}")
                    inv_table.append({
                        "Invoice ID": i["id"],
                        "Assigned Client": owner_name,
                        "Vendor": i["vendor_name"],
                        "Bill Number": i["invoice_number"] or "N/A",
                        "Subtotal": f"Rs. {float(i['subtotal']):.2f}",
                        "VAT Amount": f"Rs. {float(i['vat']):.2f}",
                        "Total Bill": f"Rs. {float(i['total']):.2f}"
                    })
                st.dataframe(inv_table, use_container_width=True, hide_index=True)