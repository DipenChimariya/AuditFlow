import streamlit as st
import pandas as pd
from utils.api import fetch_clients, add_new_client

st.set_page_config(page_title="Client Directory - AuditFlow", page_icon="🏢", layout="wide")
st.subheader("Client Profiles")

if "client_success_msg" not in st.session_state:
    st.session_state.client_success_msg = None

# ---- REGISTRATION FORM ----
form_col, _ = st.columns([1, 1])  # Limits the input container so it doesn't look stretched
with form_col:
    with st.container(border=True):
        st.markdown("### 🏢 Register New Client Firm")
        st.markdown("---")
        client_name = st.text_input("Official Firm Name", placeholder="e.g., ABC Trading Pvt. Ltd.", key="p1_client_name")
        pan_number = st.text_input("Nepalese PAN (9 Digits)", max_chars=9, placeholder="e.g., 678546345", key="p1_pan_number")
        
        st.markdown(" ")
        
        if st.session_state.client_success_msg:
            st.toast(st.session_state.client_success_msg, icon="🏢")  
            st.success(st.session_state.client_success_msg)
            st.session_state.client_success_msg = None 

        if st.button("Save Client to Database", type="primary", use_container_width=True):
            if not client_name.strip():
                st.error("❌ The Client Firm Name is required.")
            elif pan_number and (not pan_number.strip().isdigit() or len(pan_number.strip()) != 9):
                st.error("❌ PAN number must be exactly 9 numeric digits.")
            else:
                with st.spinner("Writing to PostgreSQL..."):
                    clean_name = client_name.strip()
                    clean_pan = pan_number.strip() if pan_number else None
                    
                    response = add_new_client(clean_name, clean_pan)
                    
                    if response is None:
                        st.error("🔌 Network Connection Refused. Is your backend server completely shut down?")
                    elif response.status_code in [200, 201]:
                        display_pan = f" (PAN: {clean_pan})" if clean_pan else ""
                        st.session_state.client_success_msg = f"SUCCESS: Client '{clean_name}'{display_pan} has been successfully initialized."
                        st.rerun()
                    elif response.status_code == 422:
                        # 🚨 CATCHES FIELD NAME MISMATCHES (Data Type errors)
                        try:
                            st.error(f"❌ Backend Validation Mismatch (422): {response.json()['detail']}")
                        except Exception:
                            st.error(f"❌ Backend Validation Mismatch (422): {response.text}")
                    elif response.status_code == 400:
                        # 🚨 CATCHES DUPLICATES OR DATABASE CONSTRAINTS
                        try:
                            st.error(f"❌ Database Rejection (400 Bad Request): {response.json()['detail']}")
                        except Exception:
                            st.error(f"❌ Database Rejection (400 Bad Request): {response.text}")
                    else:
                        st.error(f"❌ Server Error {response.status_code}: {response.text}")

st.markdown("---")

# ---- LOOKUP DIRECTORY ----
st.markdown("### 🔍 Registered Audit Clients Directory")
clients = fetch_clients()

if clients is None:
    st.error("🔌 Backend API server unreachable.")
elif clients:
    # Split lookup controls into a searchable column and a metric counter column
    search_col, metric_col = st.columns([3, 1])
    
    with search_col:
        search_query = st.text_input(
            "Search Active Directory", 
            placeholder="Type a Firm Name or 9-digit PAN to apply a live filter...", 
            key="p1_search",
            label_visibility="collapsed" # Keeps the look exceptionally clean
        ).strip().lower()
        
    with metric_col:
        st.markdown(f"**Total Registered Firms:** `{len(clients)}`")
    
    # Process table rows
    table_data = [{"S.No.": i+1, "Client Firm Name": c["name"], "PAN Number": c["pan_number"] or "N/A"} for i, c in enumerate(clients)]
    
    if search_query:
        table_data = [row for row in table_data if search_query in row["Client Firm Name"].lower() or search_query in row["PAN Number"].lower()]
        # Reset serial indexes dynamically for search matching views
        for idx, row in enumerate(table_data, start=1):
            row["S.No."] = idx
            
    if not table_data:
        st.warning("Match empty. No registered client fits that description.")
    else:
        # Render full screen width dataframe with clean layout constraints
        st.dataframe(
            table_data, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "S.No.": st.column_config.NumberColumn(width="small"),
                "PAN Number": st.column_config.TextColumn(width="medium"),
            }
        )
else:
    st.info("ℹ️ No client firms found in the system yet.")