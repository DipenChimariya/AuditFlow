import streamlit as st
import io
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import pandas as pd
from utils.api import fetch_clients, add_new_client, fetch_invoices, add_new_invoice, delete_invoice


st.set_page_config(page_title="AuditFlow Enterprise", page_icon="💼", layout="wide")
st.title("💼 AuditFlow Workspace")
st.markdown("Manage your audited client firms, track tax profiles, and view extracted invoices seamlessly.")
st.write("---")

# ==========================================
# STATE TRACKING INITIALIZATION
# ==========================================
if "form_generation" not in st.session_state:
    st.session_state.form_generation = 0

if "client_success_msg" not in st.session_state:
    st.session_state.client_success_msg = None
if "invoice_success_msg" not in st.session_state:
    st.session_state.invoice_success_msg = None
if "delete_success_msg" not in st.session_state:
    st.session_state.delete_success_msg = None

tab1, tab2 = st.tabs(["🏢 Client Directory", "📄 Invoice Ledger"])

# ==========================================
# TAB 1: CLIENT MANAGEMENT
# ==========================================
with tab1:
    st.subheader("Client Profiles")
    
    
    form_col, spacer_col = st.columns([1, 1]) 
    
    with form_col:
        with st.container(border=True):
            st.markdown("### 🏢 Register New Client Firm")
            st.caption("Add a new Client.")
            st.markdown("---")
                
            client_name = st.text_input("Client's official Name", placeholder="e.g., ABC Trading Pvt. Ltd.", key="tab1_client_name")
            pan_number = st.text_input("PAN Number(9 Digits)", max_chars=9, placeholder="e.g., 678546345", key="tab1_pan_number")
            
            st.markdown(" ")
            submit_client_clicked = st.button("Save Client to Database", type="primary", key="tab1_save_client_btn", use_container_width=True)
            
            
            if st.session_state.client_success_msg:
                st.markdown(" ")
                st.success(st.session_state.client_success_msg)
                st.session_state.client_success_msg = None 
                
            if submit_client_clicked:
                if not client_name:
                    st.error("❌ Client's Name is required.")
                elif pan_number and (not pan_number.isdigit() or len(pan_number) != 9):
                    st.error("❌ PAN number must be exactly 9 numeric digits.")
                else:
                    with st.spinner("Writing to PostgreSQL..."):
                        response = add_new_client(client_name, pan_number)
                        
                        if response is None:
                            st.error("🔌 Could not connect to Backend.")
                        elif response.status_code == 200:
                            st.session_state.client_success_msg = f"🎉 '{client_name}' successfully added!"
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
    
    
    st.markdown("---")
    
    st.markdown("### 🔍 Registered Audit Clients Directory")
    
    clients = fetch_clients()
    if clients is None:
        st.error("🔌 Could not connect to Backend.")
    elif len(clients) == 0:
        st.info("ℹ️ No client firms found in the system yet.")
    else:
        search_col, metric_col = st.columns([3, 1])
        
        with search_col:
            search_query = st.text_input(
                "Search Active Directory", 
                placeholder="🔍 Type Client's Name or  PAN Num to apply a live filter...", 
                key="client_search_input",
                label_visibility="collapsed"
            ).strip().lower()
            
        with metric_col:
            
            st.markdown(f"**Total Registered Firms:** `{len(clients)}`")
        
        
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
        
        
        if not filtered_data:
            st.warning("Match empty. No registered client fits that description.")
        else:
            st.dataframe(
                filtered_data, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "S.No.": st.column_config.NumberColumn(width="small"),
                    "PAN Number": st.column_config.TextColumn(width="medium"),
                }
            )


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
                
                dynamic_subtotal_key = f"subtotal_input_{st.session_state.form_generation}"
                vat_override_key = f"vat_input_{st.session_state.form_generation}"
                
                subtotal_raw = st.text_input(
                    "Subtotal / Base Amount (Rs.)", 
                    placeholder="e.g., 23500.00", 
                    key=dynamic_subtotal_key
                ).strip()
                
                try:
                    subtotal_dec = Decimal(subtotal_raw) if subtotal_raw else Decimal("0.00")
                except InvalidOperation:
                    st.error("⚠️ Invalid number format in Subtotal field.")
                    subtotal_dec = Decimal("0.00")
                
                calculated_vat = (subtotal_dec * Decimal("0.13")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                vat_amount_raw = st.text_input(
                    "VAT Amount (Rs.) [13% Auto-Computed]",
                    placeholder=f"Auto: {calculated_vat:.2f}" if subtotal_dec > 0 else "e.g., 3055.00",
                    key=vat_override_key
                ).strip()
                
                try:
                    if vat_amount_raw:
                        vat_dec = Decimal(vat_amount_raw)
                    else:
                        vat_dec = calculated_vat
                except InvalidOperation:
                    vat_dec = Decimal("0.00")
                
                total_dec = subtotal_dec + vat_dec
                
                st.info(f"📊 **Voucher Summary:** Base: **Rs. {subtotal_dec:,.2f}** | VAT: **Rs. {vat_dec:,.2f}** | Total Bill: **Rs. {total_dec:,.2f}**")
                
                st.markdown("---")
                submit_clicked = st.button("Commit Invoice to Ledger", type="primary", key="tab2_save_invoice_btn", use_container_width=True)

                if st.session_state.invoice_success_msg:
                    st.markdown(" ")
                    st.success(st.session_state.invoice_success_msg)
                    st.session_state.invoice_success_msg = None 

            if submit_clicked:
                if not vendor_name:
                    st.error("❌ Vendor Name is mandatory.")
                else:
                    with st.spinner("Linking to database..."):
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
                            st.session_state.invoice_success_msg = f"🎉 Invoice {invoice_num} successfully pinned!"
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
                # Create Layout Columns for Text Search vs Date Range Filter
                filter_col1, filter_col2 = st.columns([1, 1])
                
                with filter_col1:
                    inv_search = st.text_input(
                        "🔍 Text Search", 
                        placeholder="Type Vendor, Bill Number, Client Name...", 
                        key="invoice_search_input"
                    ).strip().lower()
                
                with filter_col2:
                    # Provide a checkbox option so filtering by date is optional
                    enable_date_filter = st.checkbox("📅 Filter by Date Range", value=False)
                    if enable_date_filter:
                       
                        date_range = st.date_input(
                            "Select Range (Start - End)",
                            value=(datetime.today(), datetime.today()),
                            key="invoice_date_filter"
                        )
                    else:
                        date_range = None

                # Build the complete data table list from database objects
                inv_table = []
                id_map = {} 
                
                for index, i in enumerate(invoices, start=1):
                    owner_name = next((c["name"] for c in clients_list if c["id"] == i["client_id"]), f"Client ID: {i['client_id']}")
                    formatted_date = i.get("invoice_date") or "N/A"
                    display_label = f"S.No. {index} | {owner_name} ({i['vendor_name']}) - Bill: {i['invoice_number'] or 'N/A'}"
                    
                    id_map[display_label] = i["id"]
                    
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
                
                # 2. RUN MULTI-LAYER FILTERING (Text Search + Date Window)
                filtered_invs = []
                for row in inv_table:
                    # Check text matches
                    text_match = True
                    if inv_search:
                        text_match = (
                            inv_search in row["Assigned Client"].lower() or 
                            inv_search in row["Vendor"].lower() or 
                            inv_search in row["Bill Number"].lower()
                        )
                    
                    # Check date range boundaries matches
                    date_match = True
                    if enable_date_filter and date_range and row["Invoice Date"] != "N/A":
                        try:
                            # Safely convert row date string back to date object for perfect boundary comparison
                            row_date = datetime.strptime(row["Invoice Date"], "%Y-%m-%d").date()
                            
                            # Handle both cases: complete range selection or single date clicked
                            if len(date_range) == 2:
                                start_date, end_date = date_range
                                date_match = (start_date <= row_date <= end_date)
                            elif len(date_range) == 1:
                                date_match = (row_date == date_range[0])
                        except Exception:
                            date_match = False
                    
                    # Row only passes if it matches BOTH text and date constraints
                    if text_match and date_match:
                        filtered_invs.append(row)

                # Re-index the S.No. dynamically based on filtered subset list order
                for idx, row in enumerate(filtered_invs, start=1):
                    row["S.No."] = idx

                st.metric(label="Total Filtered Vouchers", value=len(filtered_invs))
                
                if not filtered_invs:
                    st.warning("No invoices found matching that specific text search or date timeline criteria.")
                else:
                    display_df = pd.DataFrame(filtered_invs)
                    
                    formatted_df = display_df.copy()
                    formatted_df["Subtotal (Rs.)"] = formatted_df["Subtotal (Rs.)"].map("Rs. {:.2f}".format)
                    formatted_df["VAT Amount (Rs.)"] = formatted_df["VAT Amount (Rs.)"].map("Rs. {:.2f}".format)
                    formatted_df["Total Bill (Rs.)"] = formatted_df["Total Bill (Rs.)"].map("Rs. {:.2f}".format)
                    
                    st.dataframe(formatted_df, use_container_width=True, hide_index=True)
                    
                    # Action blocks for Export and Delete remain exactly the same below...
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
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
                    
                    with action_col2:
                        with st.expander("🗑️ Delete an Incorrect Record"):
                            target_label = st.selectbox(
                                "Select row to remove permanently:", 
                                options=list(id_map.keys()),
                                index=0,
                                key="invoice_delete_selector"
                            )
                            
                            confirm_delete = st.button("Delete Permanently", type="primary", use_container_width=True)
                            delete_alert_placeholder = st.empty()
                            
                            if confirm_delete:
                                target_id = id_map[target_label]
                                with st.spinner("Removing row from database..."):
                                    del_res = delete_invoice(target_id)
                                    
                                    if del_res is None:
                                        st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
                                    elif del_res.status_code == 200:
                                        delete_alert_placeholder.success("🗑️ Record Successfully Deleted from Database!")
                                        import time
                                        time.sleep(2.5)
                                        delete_alert_placeholder.empty()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to delete. Backend returned status code: {del_res.status_code}")
                    
        