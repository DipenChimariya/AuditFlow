import streamlit as st
from utils.api import fetch_clients, add_new_client, fetch_invoices, add_new_invoice


st.set_page_config(page_title="AuditFlow Enterprise", page_icon="💼", layout="wide")
st.title("💼 AuditFlow Workspace")
st.markdown("Manage your audited client firms, track tax profiles, and view extracted invoices seamlessly.")
st.write("---")


tab1, tab2 = st.tabs(["🏢 Client Directory", "📄 Invoice Ledger"])

# ==========================================
# TAB 1: CLIENT MANAGEMENT
# ==========================================
with tab1:
    st.subheader("Client Profiles")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Register New Client Firm")
        # Unique keys added to prevent ID clashes
        client_name = st.text_input("Official Firm Name", placeholder="e.g., ABC Trading Pvt. Ltd.", key="tab1_client_name")
        pan_number = st.text_input("Nepalese PAN (9 Digits)", max_chars=9, placeholder="e.g., 678546345", key="tab1_pan_number")
        
        if st.button("Save Client to Database", type="primary", key="tab1_save_client_btn"):
            if not client_name:
                st.error("❌ The Client Firm Name is required.")
            elif pan_number and (not pan_number.isdigit() or len(pan_number) != 9):
                st.error("❌ PAN number must be exactly 9 numeric digits.")
            else:
                with st.spinner("Writing to PostgreSQL..."):
                    response = add_new_client(client_name, pan_number)
                    if response and response.status_code == 200:
                        st.success(f"🎉 '{client_name}' successfully added!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save client profile.")
                        
    with col2:
        st.markdown("### Registered Audit Clients")
        clients = fetch_clients()
        if clients is None:
            st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
        elif len(clients) == 0:
            st.info("ℹ️ No client firms found in the system yet.")
        else:
            st.metric(label="Total Active Client Profiles", value=len(clients))
            
            # Formating data with a clean frontend serial number
            table_data = []
            for index, c in enumerate(clients, start=1):
                table_data.append({
                    "S.No.": index,                      
                    "Client Firm Name": c["name"],
                    "PAN Number": c["pan_number"] if c["pan_number"] else "N/A"
                })
            
            # Hide the internal dataframe index and show our clean S.No.
            st.dataframe(table_data, use_container_width=True, hide_index=True)


# ==========================================
# TAB 2: INVOICE MANAGEMENT
# ==========================================
with tab2:
    st.subheader("Invoice Records")
    clients_list = fetch_clients() or []
    
    if not clients_list:
        st.warning("⚠️ You must register at least one client in the Client Directory tab before logging invoices.")
    else:
        inv_col1, inv_col2 = st.columns([1, 2])
        
        with inv_col1:
            st.markdown("### Log Invoice Manually")
            
            client_options = {c["name"]: c["id"] for c in clients_list}
            selected_client_name = st.selectbox("Assign to Client Firm", options=list(client_options.keys()), key="tab2_client_selector")
            target_client_id = client_options[selected_client_name]
            
            vendor_name = st.text_input("Vendor Name (Seller)", placeholder="e.g., Bhat-Bhateni Supermarket", key="tab2_vendor_name")
            invoice_num = st.text_input("Invoice / Bill Number", placeholder="e.g., INV-2026-001", key="tab2_invoice_num")
            
            subtotal = st.number_input("Subtotal / Base Amount (Rs.)", min_value=0.0, step=100.0, format="%.2f", key="tab2_subtotal")
            vat_amount = st.number_input("VAT Amount (Rs.)", min_value=0.0, step=13.0, format="%.2f", key="tab2_vat")
            
            if st.button("Auto-Calculate 13% VAT", key="tab2_calc_vat_btn"):
                st.info(f"Suggested VAT calculation: Rs. {subtotal * 0.13:.2f}")
            
            if st.button("Commit Invoice to Ledger", type="primary", key="tab2_save_invoice_btn"):
                if not vendor_name:
                    st.error("❌ Vendor Name is mandatory.")
                else:
                    with st.spinner("Linking to database..."):
                        res = add_new_invoice(target_client_id, vendor_name, invoice_num, subtotal, vat_amount)
                        if res and res.status_code == 200:
                            st.success(f"🎉 Invoice {invoice_num} successfully pinned!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to register invoice.")
                            
        with inv_col2:
            st.markdown("### Global Invoice Tracking Ledger")
            invoices = fetch_invoices()
            
            if invoices is None:
                st.error("🔌 Backend offline.")
            elif len(invoices) == 0:
                st.info("No invoices logged in the central repository yet.")
            else:
                st.metric(label="Total Logged Vouchers", value=len(invoices))
                
                inv_table = []
                
                for index, i in enumerate(invoices, start=1):
                    owner_name = next((c["name"] for c in clients_list if c["id"] == i["client_id"]), f"Client ID: {i['client_id']}")
                    inv_table.append({
                        "S.No.": index,
                        "Assigned Client": owner_name,
                        "Vendor": i["vendor_name"],
                        "Bill Number": i["invoice_number"] or "N/A",
                        "Subtotal": f"Rs. {float(i['subtotal']):.2f}",
                        "VAT Amount": f"Rs. {float(i['vat']):.2f}",
                        "Total Bill": f"Rs. {float(i['total']):.2f}"
                    })
                st.dataframe(inv_table, use_container_width=True, hide_index=True)