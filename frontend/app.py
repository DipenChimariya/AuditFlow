import streamlit as st
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import pandas as pd
from utils.api import fetch_clients, add_new_client, fetch_invoices, add_new_invoice


st.set_page_config(page_title="AuditFlow Enterprise", page_icon="💼", layout="wide")
st.title("💼 AuditFlow Workspace")
st.markdown("Manage your audited client firms, track tax profiles, and view extracted invoices seamlessly.")
st.write("---")

# ==========================================
# STATE TRACKING INITIALIZATION
# ==========================================
if "form_generation" not in st.session_state:
    st.session_state.form_generation = 0
tab1, tab2 = st.tabs(["🏢 Client Directory", "📄 Invoice Ledger"])

# TAB 1: CLIENT MANAGEMENT

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
            search_query = st.text_input(
                "🔍 Search Clients", 
                placeholder="Type Firm Name or 9-digit PAN to filter...", 
                key="client_search_input"
            ).strip().lower()
            
            table_data = []
            for index, c in enumerate(clients, start=1):
                table_data.append({
                    "S.No.": index,                      
                    "Client Firm Name": c["name"],
                    "PAN Number": c["pan_number"] if c["pan_number"] else "N/A"
                })
            
            if search_query:
                filtered_data = [
                    row for row in table_data 
                    if search_query in row["Client Firm Name"].lower() or search_query in row["PAN Number"].lower()
                ]
                
                for idx, row in enumerate(filtered_data, start=1):
                    row["S.No."] = idx
            else:
                filtered_data = table_data

            st.metric(label="Total Active Client Profiles", value=len(clients))
            
            if not filtered_data:
                st.warning("Match empty. No registered client fits that description.")
            else:
                st.dataframe(filtered_data, use_container_width=True, hide_index=True)



# TAB 2: INVOICE MANAGEMENT
with tab2:
    st.subheader("Invoice Records")
    clients_list = fetch_clients() or []
    
    if not clients_list:
        st.warning("⚠️ You must register at least one client in the Client Directory tab before logging invoices.")
    else:
        inv_col1, inv_col2 = st.columns([1, 2])
        
        with inv_col1:
            with st.container(border=True):
                st.markdown("### 📝 Log Invoice Voucher")
                st.caption("Manually record incoming client receipts")
                st.markdown("---")
                
                client_options = {c["name"]: c["id"] for c in clients_list}
                selected_client_name = st.selectbox("Assign to Client Firm", options=list(client_options.keys()), key=f"tab2_client_sel_{st.session_state.form_generation}")
                target_client_id = client_options[selected_client_name]
                
                vendor_name = st.text_input("Vendor Name (Seller)", placeholder="e.g., Bhat-Bhateni Supermarket", key=f"tab2_vendor_{st.session_state.form_generation}")
                
                meta_col1, meta_col2 = st.columns(2)
                with meta_col1:
                    invoice_num = st.text_input("Invoice / Bill Number", placeholder="e.g., INV-2026-001", key=f"tab2_inv_num_{st.session_state.form_generation}")
                with meta_col2:
                    invoice_date = st.date_input("Invoice Date", value=datetime.today(), key=f"tab2_date_{st.session_state.form_generation}")
                
                st.markdown(" ")
                st.markdown("**Financial Breakdown**")
                
                # Dynamic keys to ensure absolute form isolation across submission cycles
                subtotal_key = f"subtotal_input_{st.session_state.form_generation}"
                vat_override_key = f"vat_input_{st.session_state.form_generation}"
                
                # 1. Base Subtotal Field
                subtotal_raw = st.text_input(
                    "Subtotal / Base Amount (Rs.)", 
                    placeholder="e.g., 23500.00", 
                    key=subtotal_key
                ).strip()
                
                try:
                    subtotal_dec = Decimal(subtotal_raw) if subtotal_raw else Decimal("0.00")
                except InvalidOperation:
                    st.error("⚠️ Invalid number format in Subtotal field.")
                    subtotal_dec = Decimal("0.00")
                
                # 2. Automated Real-time VAT computation
                calculated_vat = (subtotal_dec * Decimal("0.13")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                # 3. VAT field 
                vat_amount_raw = st.text_input(
                    "VAT Amount (Rs.) [13% Auto-Computed]",
                    placeholder=f"Auto: {calculated_vat:.2f}" if subtotal_dec > 0 else "e.g., 3055.00",
                    key=vat_override_key
                ).strip()
                
                # FIX: If the user hasn't overridden the field manually, fall back to the calculated VAT automatically!
                try:
                    if vat_amount_raw:
                        vat_dec = Decimal(vat_amount_raw)
                    else:
                       
                        vat_dec = calculated_vat
                except InvalidOperation:
                    vat_dec = Decimal("0.00")
                
                
                total_dec = subtotal_dec + vat_dec
                
                # Display a clear, read-only total voucher KPI metrics banner
                st.info(f"📊 **Voucher Summary:** Base: **Rs. {subtotal_dec:,.2f}** | VAT: **Rs. {vat_dec:,.2f}** | Total Bill: **Rs. {total_dec:,.2f}**")
                
                st.markdown("---")
                submit_clicked = st.button("Commit Invoice to Ledger", type="primary", key="tab2_save_invoice_btn", use_container_width=True)

            if submit_clicked:
                if not vendor_name:
                    st.error("❌ Vendor Name is mandatory.")
                else:
                    with st.spinner("Linking to database..."):
                        # Convert decimals back to native system floats exclusively for FastAPI transmission parameters
                        res = add_new_invoice(
                            target_client_id, 
                            vendor_name, 
                            invoice_num, 
                            float(subtotal_dec), 
                            float(vat_dec), 
                            invoice_date
                        )
                        
                        if res is None:
                            st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
                        elif res.status_code == 200:
                            st.success(f"🎉 Invoice {invoice_num} successfully pinned!")
                            
                            # Cleanly drop old state mappings, increment ID generator, and refresh instantly
                            st.session_state.form_generation += 1
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
                inv_search = st.text_input(
                    "🔍 Search Invoices", 
                    placeholder="Type Vendor Name, Bill Number, or Assigned Client Name...", 
                    key="invoice_search_input"
                ).strip().lower()
                
                inv_table = []
                for index, i in enumerate(invoices, start=1):
                    owner_name = next((c["name"] for c in clients_list if c["id"] == i["client_id"]), f"Client ID: {i['client_id']}")
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
                
                if inv_search:
                    filtered_invs = [
                        row for row in inv_table
                        if inv_search in row["Assigned Client"].lower() or 
                           inv_search in row["Vendor"].lower() or 
                           inv_search in row["Bill Number"].lower()
                    ]
                    for idx, row in enumerate(filtered_invs, start=1):
                        row["S.No."] = idx
                else:
                    filtered_invs = inv_table

                st.metric(label="Total Logged Vouchers", value=len(filtered_invs))
                
                if not filtered_invs:
                    st.warning("No invoices found matching that specific search criteria.")
                else:
                    display_df = pd.DataFrame(filtered_invs)
                    
                    formatted_df = display_df.copy()
                    formatted_df["Subtotal (Rs.)"] = formatted_df["Subtotal (Rs.)"].map("Rs. {:.2f}".format)
                    formatted_df["VAT Amount (Rs.)"] = formatted_df["VAT Amount (Rs.)"].map("Rs. {:.2f}".format)
                    formatted_df["Total Bill (Rs.)"] = formatted_df["Total Bill (Rs.)"].map("Rs. {:.2f}".format)
                    
                    st.dataframe(formatted_df, use_container_width=True, hide_index=True)
                    
                    st.write(" ")
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        excel_df = display_df.drop(columns=["S.No."])
                        excel_df.to_excel(writer, sheet_name="AuditFlow Ledger", index=False)
                    
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Export to Excel",
                        data=excel_data,
                        file_name=f"AuditFlow_Ledger_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )