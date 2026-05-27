import streamlit as st
import io
from datetime import datetime
import pandas as pd
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
                    
                    if response is None:
                        st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
                    elif response.status_code == 200:
                        st.success(f"🎉 '{client_name}' successfully added!")
                        st.rerun()
                    elif response.status_code == 422:
                        try:
                            errors = response.json()["detail"]
                            err_msg = " | ".join([ f"{err['loc'][-1]}: {err['msg']}" for err in errors ])
                            st.error(f"❌ Structural Validation Mismatch (422): {err_msg}")
                        except Exception:
                            st.error("❌ Data formatting error. Check your input values.")
                    elif 400 <= response.status_code < 500:
                        try:
                            # Safely extracts the exact duplicate warning from crud.py
                            st.error(response.json()["detail"])
                        except Exception:
                            st.error(f"⚠️ Request failed with status code: {response.status_code}")
                    else:
                        st.error(f"❌ Server Error {response.status_code}. Unable to save client profile.")
        
    with col2:
        st.markdown("### Registered Audit Clients")
        clients = fetch_clients()
        if clients is None:
            st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
        elif len(clients) == 0:
            st.info("ℹ️ No client firms found in the system yet.")
        else:
            # --- Added: Client Search Bar Feature ---
            search_query = st.text_input(
                "🔍 Search Clients", 
                placeholder="Type Firm Name or 9-digit PAN to filter...", 
                key="client_search_input"
            ).strip().lower()
            
            # Map full data array to table format
            table_data = []
            for index, c in enumerate(clients, start=1):
                table_data.append({
                    "S.No.": index,                      
                    "Client Firm Name": c["name"],
                    "PAN Number": c["pan_number"] if c["pan_number"] else "N/A"
                })
            
            # Filter the table in real-time based on user input
            if search_query:
                filtered_data = [
                    row for row in table_data 
                    if search_query in row["Client Firm Name"].lower() or search_query in row["PAN Number"].lower()
                ]
                
                # Re-index the S.No. dynamically for search results
                for idx, row in enumerate(filtered_data, start=1):
                    row["S.No."] = idx
            else:
                filtered_data = table_data

            # Display KPIs and DataFrame based on filtered results
            st.metric(label="Total Active Client Profiles", value=len(clients))
            
            if not filtered_data:
                st.warning("Match empty. No registered client fits that description.")
            else:
                st.dataframe(filtered_data, use_container_width=True, hide_index=True)


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
            
            # --- Added Feature: Calendar Date Selector input ---
            invoice_date = st.date_input("Invoice Date", value=datetime.today(), key="tab2_invoice_date")
            
            if "calc_vat_val" not in st.session_state:
                st.session_state.calc_vat_val = 0.0

            subtotal = st.number_input("Subtotal / Base Amount (Rs.)", min_value=0.0, step=100.0, format="%.2f", key="tab2_subtotal")
            vat_amount = st.number_input("VAT Amount (Rs.)", min_value=0.0, step=13.0, format="%.2f", key="tab2_vat", value=st.session_state.calc_vat_val)
            
            if st.button("Auto-Calculate 13% VAT", key="tab2_calc_vat_btn"):
                st.session_state.calc_vat_val = round(subtotal * 0.13, 2)
                st.rerun()
            
            if st.button("Commit Invoice to Ledger", type="primary", key="tab2_save_invoice_btn"):
                if not vendor_name:
                    st.error("❌ Vendor Name is mandatory.")
                else:
                    with st.spinner("Linking to database..."):
                        # Included the invoice_date parameter here
                        res = add_new_invoice(target_client_id, vendor_name, invoice_num, subtotal, vat_amount, invoice_date)
                        
                        if res is None:
                            st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
                        elif res.status_code == 200:
                            st.success(f"🎉 Invoice {invoice_num} successfully pinned!")
                            st.session_state.calc_vat_val = 0.0
                            st.rerun()
                        elif res.status_code == 422:
                            try:
                                errors = res.json()["detail"]
                                err_msg = " | ".join([ f"{err['loc'][-1]}: {err['msg']}" for err in errors ])
                                st.error(f"❌ Schema Validation Error (422): {err_msg}")
                            except Exception:
                                st.error("❌ Data formatting error. Check your input values.")
                        elif 400 <= res.status_code < 500:
                            try:
                                st.error(res.json()["detail"])
                            except Exception:
                                st.error(f"⚠️ Request failed with status code: {res.status_code}")
                        else:
                            st.error(f"❌ Server Error {res.status_code}. Unable to register invoice.")
                            
        with inv_col2:
            st.markdown("### Global Invoice Tracking Ledger")
            invoices = fetch_invoices()
            
            if invoices is None:
                st.error("🔌 Backend offline.")
            elif len(invoices) == 0:
                st.info("No invoices logged in the central repository yet.")
            else:
                # --- Added Feature: Global Invoice Search Filtering ---
                inv_search = st.text_input(
                    "🔍 Search Invoices", 
                    placeholder="Type Vendor Name, Bill Number, or Assigned Client Name...", 
                    key="invoice_search_input"
                ).strip().lower()
                
                # Assemble baseline raw table layout matrix
                inv_table = []
                for index, i in enumerate(invoices, start=1):
                    owner_name = next((c["name"] for c in clients_list if c["id"] == i["client_id"]), f"Client ID: {i['client_id']}")
                    
                    # Convert date format if returned from backend cleanly
                    formatted_date = i.get("invoice_date") or "N/A"
                    
                    inv_table.append({
                        "S.No.": index,
                        "Assigned Client": owner_name,
                        "Vendor": i["vendor_name"],
                        "Bill Number": i["invoice_number"] or "N/A",
                        "Invoice Date": formatted_date,
                        "Subtotal (Rs.)": float(i['subtotal']),
                        "VAT Amount (Rs.)": float(i['vat']),
                        "Total Bill (Rs.)": float(i['total'])
                    })
                
                # In-memory search computation
                if inv_search:
                    filtered_invs = [
                        row for row in inv_table
                        if inv_search in row["Assigned Client"].lower() or 
                           inv_search in row["Vendor"].lower() or 
                           inv_search in row["Bill Number"].lower()
                    ]
                    # Dynamic sequential serial numbering recalculation
                    for idx, row in enumerate(filtered_invs, start=1):
                        row["S.No."] = idx
                else:
                    filtered_invs = inv_table

                st.metric(label="Total Logged Vouchers", value=len(filtered_invs))
                
                if not filtered_invs:
                    st.warning("No invoices found matching that specific search criteria.")
                else:
                    # Render the dynamic table layout with formatted money strings for cleaner readability
                    display_df = pd.DataFrame(filtered_invs)
                    
                    formatted_df = display_df.copy()
                    formatted_df["Subtotal (Rs.)"] = formatted_df["Subtotal (Rs.)"].map("Rs. {:.2f}".format)
                    formatted_df["VAT Amount (Rs.)"] = formatted_df["VAT Amount (Rs.)"].map("Rs. {:.2f}".format)
                    formatted_df["Total Bill (Rs.)"] = formatted_df["Total Bill (Rs.)"].map("Rs. {:.2f}".format)
                    
                    st.dataframe(formatted_df, use_container_width=True, hide_index=True)
                    
                    # --- Added Feature: Export Excel Ledger Spreadsheet Data Drop ---
                    st.write(" ")
                    # Convert our active filtered results back into raw Excel byte streams
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        # Dropping serialization serialization structures for clean data download
                        excel_df = display_df.drop(columns=["S.No."])
                        excel_df.to_excel(writer, sheet_name="AuditFlow Ledger", index=False)
                    
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Export Filtered Ledger to Excel",
                        data=excel_data,
                        file_name=f"AuditFlow_Ledger_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )