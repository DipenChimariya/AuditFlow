import streamlit as st
from utils.api import fetch_clients, add_new_client

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