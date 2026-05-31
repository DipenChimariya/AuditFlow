import streamlit as st
import pandas as pd
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from utils.api import fetch_clients, fetch_invoices, add_new_invoice, delete_invoice

st.set_page_config(page_title="Invoice Ledger - AuditFlow", page_icon="📄", layout="wide")
st.subheader("Invoice Records")

# Ensure form generation states exist within this page's lifecycle
if "form_generation" not in st.session_state:
    st.session_state.form_generation = 0
if "invoice_success_msg" not in st.session_state:
    st.session_state.invoice_success_msg = None
if "delete_success_msg" not in st.session_state:
    st.session_state.delete_success_msg = None

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
            selected_client_name = st.selectbox("Assign to Client Firm", options=list(client_options.keys()), key=f"p2_client_sel_{st.session_state.form_generation}")
            target_client_id = client_options[selected_client_name]
            
            vendor_name = st.text_input("Vendor Name (Seller)", placeholder="e.g., Bhat-Bhateni Supermarket", key=f"p2_vendor_{st.session_state.form_generation}")
            
            transaction_type = st.radio("Voucher Classification",
                options=["Purchase (Stock In / Expense)", "Sale (Stock Out / Revenue)"],
                horizontal=True, key=f"p2_type_radio_{st.session_state.form_generation}")
            
            
            clean_type_string = "Purchase" if "Purchase" in transaction_type else "Sale"

            meta_col1, meta_col2 = st.columns(2)
            with meta_col1:
                invoice_num = st.text_input("Invoice / Bill Number", placeholder="e.g., INV-2026-001", key=f"p2_inv_num_{st.session_state.form_generation}")
            with meta_col2:
                invoice_date = st.date_input("Invoice Date", value=datetime.today(), key=f"p2_date_{st.session_state.form_generation}")
            
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
            
            if st.session_state.invoice_success_msg:
                st.toast(st.session_state.invoice_success_msg, icon="📝")
                st.success(st.session_state.invoice_success_msg)
                st.session_state.invoice_success_msg = None 

            submit_clicked = st.button("Commit Invoice to Ledger", type="primary", key="p2_save_invoice_btn", use_container_width=True)

        if submit_clicked:
            if not vendor_name:
                st.error("❌ Vendor Name is mandatory.")
            else:
                with st.spinner("Linking to database..."):
                    #Explicitly named keywords protect against positional index crashes
                    res = add_new_invoice(
                        client_id=target_client_id, 
                        vendor_name=vendor_name, 
                        invoice_number=invoice_num, 
                        subtotal=float(subtotal_dec), 
                        vat=float(vat_dec),
                        transaction_type=clean_type_string, 
                        invoice_date=invoice_date
                    )
                    
                    if res is None:
                        st.error("🔌 Could not connect to Backend. Is your FastAPI server running?")
                    elif res.status_code in [200, 201]:
                        display_bill = invoice_num.strip() if invoice_num else "N/A"
                        st.session_state.invoice_success_msg = f"SUCCESS: Invoice Record '{display_bill}' ({clean_type_string}) for {selected_client_name} has been successfully committed to the database ledger."
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
            filter_col1, filter_col2 = st.columns([1, 1])
            
            with filter_col1:
                inv_search = st.text_input(
                    "🔍 Text Search", 
                    placeholder="Type Vendor, Bill, Type, Client Name...", 
                    key="invoice_search_input"
                ).strip().lower()
            
            with filter_col2:
                enable_date_filter = st.checkbox("📅 Filter by Date Range", value=False)
                if enable_date_filter:
                    date_range = st.date_input(
                        "Select Range (Start - End)",
                        value=(datetime.today(), datetime.today()),
                        key="invoice_date_filter"
                    )
                else:
                    date_range = None

            inv_table = []
            
            
            for index, i in enumerate(invoices, start=1):
                owner_name = next((c["name"] for c in clients_list if c["id"] == i["client_id"]), f"Client ID: {i['client_id']}")
                formatted_date = i.get("invoice_date") or "N/A"
                
                inv_table.append({
                    "id": i["id"],
                    "S.No.": index,
                    "Assigned Client": owner_name,
                    "Vendor": i["vendor_name"],
                    "Type": i.get("transaction_type", "Purchase"),
                    "Bill Number": i["invoice_number"] or "N/A",
                    "Invoice Date": formatted_date,
                    "Subtotal (Rs.)": float(i['subtotal']),
                    "VAT Amount (Rs.)": float(i['vat']),
                    "Total Bill (Rs.)": float(i['total'])
                })
            
            filtered_invs = []
            for row in inv_table:
                text_match = True
                if inv_search:
                    text_match = (
                        inv_search in row["Assigned Client"].lower() or 
                        inv_search in row["Vendor"].lower() or 
                        inv_search in row["Type"].lower() or
                        inv_search in row["Bill Number"].lower()
                    )
                
                date_match = True
                if enable_date_filter and date_range and row["Invoice Date"] != "N/A":
                    try:
                        row_date = datetime.strptime(row["Invoice Date"], "%Y-%m-%d").date()
                        if len(date_range) == 2:
                            start_date, end_date = date_range
                            date_match = (start_date <= row_date <= end_date)
                        elif len(date_range) == 1:
                            date_match = (row_date == date_range[0])
                    except Exception:
                        date_match = False
                
                if text_match and date_match:
                    filtered_invs.append(row)

            # Re-index visual serialization for tables
            for idx, row in enumerate(filtered_invs, start=1):
                row["S.No."] = idx

            st.metric(label="Total Filtered Vouchers", value=len(filtered_invs))
            
            if not filtered_invs:
                st.warning("No invoices found matching that specific text search or date timeline criteria.")
            else:
                display_df = pd.DataFrame(filtered_invs)
                render_df = display_df.drop(columns=["id"])
                
                formatted_df = render_df.copy()
                formatted_df["Subtotal (Rs.)"] = formatted_df["Subtotal (Rs.)"].map("Rs. {:.2f}".format)
                formatted_df["VAT Amount (Rs.)"] = formatted_df["VAT Amount (Rs.)"].map("Rs. {:.2f}".format)
                formatted_df["Total Bill (Rs.)"] = formatted_df["Total Bill (Rs.)"].map("Rs. {:.2f}".format)
                
                st.dataframe(formatted_df, use_container_width=True, hide_index=True)
                
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        excel_df = display_df.drop(columns=["id", "S.No."])
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
                        delete_options = {}
                        for r in filtered_invs:
                            bill_lbl = r['Bill Number'] if r['Bill Number'] else 'N/A'
                            lbl = f"S.No. {r['S.No.']} | {r['Assigned Client']} -> {r['Vendor']} ({r['Type']}) (Bill: {bill_lbl}, Total: Rs. {r['Total Bill (Rs.)']:,.2f})"
                            delete_options[lbl] = r["id"]

                        # OPTIMIZATION FIX: Handle empty search edge cases gracefully
                        if delete_options:
                            selected_delete_lbl = st.selectbox(
                                "Select row item to remove permanently:",
                                options=list(delete_options.keys()),
                                key="ledger_deletion_row_selector"
                            )
                            
                            target_invoice_id = delete_options[selected_delete_lbl]
                            
                            try:
                                extracted_bill_no = selected_delete_lbl.split("Bill: ")[1].split(",")[0]
                            except Exception:
                                extracted_bill_no = f"ID #{target_invoice_id}"

                            if st.session_state.delete_success_msg:
                                st.toast(st.session_state.delete_success_msg, icon="✅") 
                                st.success(st.session_state.delete_success_msg)
                                st.session_state.delete_success_msg = None
                                
                            if st.button("Delete Permanently", type="primary", use_container_width=True):
                                with st.spinner("Removing ledger entry..."):
                                    res = delete_invoice(target_invoice_id)

                                    if res is None:
                                        st.error("🔌 Backend server offline. Connection refused.")
                                    elif res.status_code in [200, 204]:
                                        st.session_state.delete_success_msg = f"SUCCESS: Invoice Record '{extracted_bill_no}' has been permanently purged from the tracking system."
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to execute deletion. System returned status code: {res.status_code}")
                        else:
                            st.caption("No records available to delete.")