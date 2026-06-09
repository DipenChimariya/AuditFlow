import streamlit as st
import pandas as pd  
import plotly.express as px  
from utils.api import fetch_clients, fetch_invoices

st.set_page_config(page_title="Dashboard - AuditFlow", page_icon="📊", layout="wide")

# --- AUTHENTICATION LAYER ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "forgot_password" not in st.session_state:
    st.session_state["forgot_password"] = False

def login():
    st.title("🔒 AuditFlow Secure Gateway")
    st.caption("Please authenticate to access client compliance matrices.")
    
    # If forgot password flag is active, show password recovery message
    if st.session_state["forgot_password"]:
        st.info("🔑 **Password Recovery Protocol**")
        st.markdown("""
        For data security and NFRS compliance, automated email recovery is disabled for this node.
        
        Please contact your System Administrator to verify your identity and reset your access keys:
        * 📧 **IT Support:** chimariyadipen@gmail.com""")
        if st.button("⬅️ Back to Login"):
            st.session_state["forgot_password"] = False
            st.rerun()
        return

    #Login Form Layout
    with st.form("Login Form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Log In")
        
        if submit_button:
            if username == "admin" and password == "auditflow2026":
                st.session_state["authenticated"] = True
                st.success("Authentication successful!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

    # Forgot Password link placement right below the form container
    if st.button("❓ Forgot Password?", help="Click here to see recovery options"):
        st.session_state["forgot_password"] = True
        st.rerun()

if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- MAIN DASHBOARD (Only shows if authenticated) ---

# Add a logout button in the sidebar for clean UX
if st.sidebar.button("🚪 Log Out"):
    st.session_state["authenticated"] = False
    st.rerun()

st.title("📊 AuditFlow Analytics Engine")
st.caption("Real-time compliance monitoring, VAT tracking, and client ledger synthesis.")
st.markdown("---")

# 1. Fetch live application metrics
clients = fetch_clients() or []
invoices = fetch_invoices() or []

if not clients:
    st.info("👋 Welcome to AuditFlow! To begin tracking metrics, navigate to the Client Directory sidebar tab and register your first firm.")
else:
    # 2. Global System Metrics Summary Cards
    tot_clients = len(clients)
    tot_vouchers = len(invoices)
    
    grand_total = 0.0
    for inv in invoices:
        raw_total = inv.get("total")
        if raw_total and str(raw_total).strip():
            try:
                grand_total += float(raw_total)
            except ValueError:
                pass  

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric(label="Registered Client Portfolios", value=tot_clients)
    with m_col2:
        st.metric(label="Central Ledger Voucher Count", value=tot_vouchers)
    with m_col3:
        st.metric(label="Aggregated Financial Volume", value=f"Rs. {grand_total:,.2f}")
        
    st.markdown("### 🏢 Client Compliance & VAT Position Matrix")
    
    # 3. Process records to compile per-client tax positions
    compliance_data = []
    
    for idx, client in enumerate(clients, start=1):
        c_id = client["id"]
        c_name = client["name"]
        c_pan = client.get("pan_number") or "N/A"
        
        client_invoices = [inv for inv in invoices if inv["client_id"] == c_id]
        
        purchases_sum = 0.0
        sales_sum = 0.0
        input_vat = 0.0
        output_vat = 0.0
        
        for inv in client_invoices:
            inv_type = inv.get("transaction_type", "Purchase")
            
            try:
                subtotal = float(inv.get("subtotal", 0.0))
            except (ValueError, TypeError):
                subtotal = 0.0
                
            try:
                vat = float(inv.get("vat", 0.0))
            except (ValueError, TypeError):
                vat = 0.0
            
            if inv_type == "Purchase":
                purchases_sum += subtotal
                input_vat += vat
            elif inv_type == "Sale":
                sales_sum += subtotal
                output_vat += vat
                
        net_vat_position = output_vat - input_vat
        
        if net_vat_position > 0:
            vat_status_label = f"Payable: Rs. {net_vat_position:,.2f}"
        elif net_vat_position < 0:
            vat_status_label = f"Credit (Refundable): Rs. {abs(net_vat_position):,.2f}"
        else:
            vat_status_label = "Balanced / Zero Tax"
            
        compliance_data.append({
            "S.No.": idx,
            "Client Business Name": c_name,
            "PAN / VAT Reg No.": c_pan,
            "Total Purchases (Rs.)": purchases_sum,
            "Total Sales (Rs.)": sales_sum,
            "Input VAT Credit (13%)": input_vat,
            "Output VAT Liability (13%)": output_vat,
            "Net VAT Position Status": vat_status_label
        })
        
    if not compliance_data:
        st.warning("No financial transactions logged yet. Data matrices will compile upon invoice entry.")
    else:
        # 4. Generate clean structured compliance sheet
        df_compliance = pd.DataFrame(compliance_data)
        df_render = df_compliance.copy()
        
        df_render["Total Purchases (Rs.)"] = df_render["Total Purchases (Rs.)"].apply(lambda x: f"Rs. {x:,.2f}")
        df_render["Total Sales (Rs.)"] = df_render["Total Sales (Rs.)"].apply(lambda x: f"Rs. {x:,.2f}")
        df_render["Input VAT Credit (13%)"] = df_render["Input VAT Credit (13%)"].apply(lambda x: f"Rs. {x:,.2f}")
        df_render["Output VAT Liability (13%)"] = df_render["Output VAT Liability (13%)"].apply(lambda x: f"Rs. {x:,.2f}")
        
        st.dataframe(df_render, use_container_width=True, hide_index=True)
        
        # 5. Visual Value Addition: Bar breakdown graph
        st.markdown("---")
        st.markdown("### 📈 Corporate Financial Volume Breakdown")
        
        if tot_vouchers > 0:
            total_purchases_calc = float(df_compliance["Total Purchases (Rs.)"].sum())
            total_sales_calc = float(df_compliance["Total Sales (Rs.)"].sum())

            chart_df = pd.DataFrame([
                {"Voucher Flow Category": "Purchases / Inbound Expenses", "Total Value Amount (Rs.)": total_purchases_calc},
                {"Voucher Flow Category": "Sales / Outbound Revenue", "Total Value Amount (Rs.)": total_sales_calc}
            ])
            
            fig = px.bar(
                chart_df, 
                x="Voucher Flow Category", 
                y="Total Value Amount (Rs.)", 
                color="Voucher Flow Category",
                text_auto=',.2f',
                title="Aggregated Portfolio Volume Balance Sheet"
            )
            st.plotly_chart(fig, use_container_width=True)